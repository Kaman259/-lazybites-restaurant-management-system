import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getMenuItems } from "../../api/menuApi";
import {
  createOrder,
  getOrders,
  updateOrderStatus,
} from "../../api/orderApi";
import { getAllReservations } from "../../api/reservationsApi";
import { getDiningTables } from "../../api/tablesApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../context/ToastContext";

const orderStatuses = [
  "",
  "PENDING",
  "PREPARING",
  "READY",
  "SERVED",
  "COMPLETED",
  "CANCELLED",
];

const orderTypes = [
  "",
  "DINE_IN",
  "TAKEAWAY",
  "DELIVERY",
];

const statusActions = {
  PENDING: ["PREPARING", "CANCELLED"],
  PREPARING: ["READY", "CANCELLED"],
  READY: ["SERVED", "COMPLETED", "CANCELLED"],
  SERVED: ["COMPLETED"],
  COMPLETED: [],
  CANCELLED: [],
};

const emptyOrderForm = {
  order_type: "DINE_IN",
  table_id: "",
  reservation_id: "",
  special_instructions: "",
  delivery_address: "",
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function OrdersPage() {
  const { showToast } = useToast();

  const [orders, setOrders] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [tables, setTables] = useState([]);
  const [reservations, setReservations] = useState([]);

  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [menuSearch, setMenuSearch] = useState("");

  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [createModalOpen, setCreateModalOpen] =
    useState(false);
  const [orderForm, setOrderForm] =
    useState(emptyOrderForm);
  const [cart, setCart] = useState([]);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const [selectedOrder, setSelectedOrder] =
    useState(null);
  const [selectedStatus, setSelectedStatus] =
    useState("");
  const [cancellationReason, setCancellationReason] =
    useState("");
  const [statusUpdating, setStatusUpdating] =
    useState(false);
  const [statusError, setStatusError] = useState("");

  const filteredMenuItems = useMemo(() => {
    const searchValue = menuSearch.trim().toLowerCase();

    if (!searchValue) {
      return menuItems;
    }

    return menuItems.filter((item) =>
      [
        item.name,
        item.description ?? "",
        item.category?.name ?? "",
      ].some((value) =>
        value.toLowerCase().includes(searchValue),
      ),
    );
  }, [menuItems, menuSearch]);

  const cartSubtotal = useMemo(
    () =>
      cart.reduce(
        (total, item) =>
          total +
          Number(item.price) * Number(item.quantity),
        0,
      ),
    [cart],
  );

  const loadOrders = useCallback(async () => {
    const orderData = await getOrders({
      status: statusFilter,
      orderType: typeFilter,
    });

    setOrders(orderData);
  }, [statusFilter, typeFilter]);

  const loadSupportingData = useCallback(async () => {
    const [
      menuData,
      tableData,
      confirmedReservations,
      seatedReservations,
    ] = await Promise.all([
      getMenuItems({
        includeInactive: false,
        availableOnly: true,
      }),
      getDiningTables(false),
      getAllReservations("CONFIRMED"),
      getAllReservations("SEATED"),
    ]);

    setMenuItems(menuData);
    setTables(tableData);

    setReservations([
      ...confirmedReservations,
      ...seatedReservations,
    ]);
  }, []);

  const loadPage = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      await Promise.all([
        loadOrders(),
        loadSupportingData(),
      ]);
    } catch (error) {
      setPageError(
        error.message ??
          "Order information could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [loadOrders, loadSupportingData]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  function openCreateModal() {
    setOrderForm(emptyOrderForm);
    setCart([]);
    setMenuSearch("");
    setCreateError("");
    setCreateModalOpen(true);
  }

  function closeCreateModal() {
    if (creating) {
      return;
    }

    setCreateModalOpen(false);
    setOrderForm(emptyOrderForm);
    setCart([]);
    setCreateError("");
  }

  function updateOrderField(event) {
    const { name, value } = event.target;

    setOrderForm((currentForm) => {
      if (name === "order_type") {
        return {
          ...currentForm,
          order_type: value,
          table_id:
            value === "DINE_IN"
              ? currentForm.table_id
              : "",
          reservation_id:
            value === "DINE_IN"
              ? currentForm.reservation_id
              : "",
          delivery_address:
            value === "DELIVERY"
              ? currentForm.delivery_address
              : "",
        };
      }

      if (name === "reservation_id") {
        const reservation = reservations.find(
          (item) => String(item.id) === value,
        );

        return {
          ...currentForm,
          reservation_id: value,
          table_id: reservation
            ? String(reservation.table_id)
            : currentForm.table_id,
        };
      }

      return {
        ...currentForm,
        [name]: value,
      };
    });

    setCreateError("");
  }

  function addMenuItem(item) {
    setCart((currentCart) => {
      const existingItem = currentCart.find(
        (cartItem) =>
          cartItem.menu_item_id === item.id,
      );

      if (existingItem) {
        return currentCart.map((cartItem) =>
          cartItem.menu_item_id === item.id
            ? {
                ...cartItem,
                quantity: cartItem.quantity + 1,
              }
            : cartItem,
        );
      }

      return [
        ...currentCart,
        {
          menu_item_id: item.id,
          name: item.name,
          price: item.price,
          quantity: 1,
          special_instruction: "",
        },
      ];
    });
  }

  function updateCartItem(
    menuItemId,
    fieldName,
    fieldValue,
  ) {
    setCart((currentCart) =>
      currentCart.map((item) =>
        item.menu_item_id === menuItemId
          ? {
              ...item,
              [fieldName]: fieldValue,
            }
          : item,
      ),
    );
  }

  function removeCartItem(menuItemId) {
    setCart((currentCart) =>
      currentCart.filter(
        (item) => item.menu_item_id !== menuItemId,
      ),
    );
  }

  async function submitOrder(event) {
    event.preventDefault();

    if (cart.length === 0) {
      setCreateError(
        "Add at least one available menu item.",
      );
      return;
    }

    if (
      orderForm.order_type === "DINE_IN" &&
      !orderForm.table_id
    ) {
      setCreateError(
        "Select a dining table for the dine-in order.",
      );
      return;
    }

    if (
      orderForm.order_type === "DELIVERY" &&
      !orderForm.delivery_address.trim()
    ) {
      setCreateError(
        "Enter the delivery address.",
      );
      return;
    }

    const invalidQuantity = cart.some(
      (item) =>
        !Number.isInteger(Number(item.quantity)) ||
        Number(item.quantity) < 1,
    );

    if (invalidQuantity) {
      setCreateError(
        "Every cart quantity must be at least 1.",
      );
      return;
    }

    const selectedReservation = reservations.find(
      (reservation) =>
        String(reservation.id) ===
        orderForm.reservation_id,
    );

    const payload = {
      customer_id:
        selectedReservation?.customer_id ?? null,
      table_id:
        orderForm.order_type === "DINE_IN"
          ? Number(orderForm.table_id)
          : null,
      reservation_id: orderForm.reservation_id
        ? Number(orderForm.reservation_id)
        : null,
      order_type: orderForm.order_type,
      special_instructions:
        orderForm.special_instructions.trim() || null,
      delivery_address:
        orderForm.order_type === "DELIVERY"
          ? orderForm.delivery_address.trim()
          : null,
      items: cart.map((item) => ({
        menu_item_id: item.menu_item_id,
        quantity: Number(item.quantity),
        special_instruction:
          item.special_instruction.trim() || null,
      })),
    };

    setCreating(true);
    setCreateError("");

    try {
      await createOrder(payload);

      showToast("Order created successfully.");
      closeCreateModal();
      await loadOrders();
    } catch (error) {
      setCreateError(
        error.message ?? "The order could not be created.",
      );
    } finally {
      setCreating(false);
    }
  }

  function openStatusModal(order, status) {
    setSelectedOrder(order);
    setSelectedStatus(status);
    setCancellationReason("");
    setStatusError("");
  }

  function closeStatusModal() {
    if (statusUpdating) {
      return;
    }

    setSelectedOrder(null);
    setSelectedStatus("");
    setCancellationReason("");
    setStatusError("");
  }

  async function submitStatusUpdate(event) {
    event.preventDefault();

    if (
      selectedStatus === "CANCELLED" &&
      !cancellationReason.trim()
    ) {
      setStatusError(
        "Enter a reason for cancelling the order.",
      );
      return;
    }

    setStatusUpdating(true);
    setStatusError("");

    try {
      await updateOrderStatus(
        selectedOrder.id,
        selectedStatus,
        cancellationReason,
      );

      showToast("Order status updated.");
      closeStatusModal();
      await loadOrders();
    } catch (error) {
      setStatusError(
        error.message ??
          "The order status could not be updated.",
      );
    } finally {
      setStatusUpdating(false);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-teal-700">
            Restaurant operations
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Orders
          </h1>

          <p className="mt-2 text-slate-500">
            Create food orders and update kitchen status.
          </p>
        </div>

        <Button onClick={openCreateModal}>
          Create order
        </Button>
      </div>

      <div className="mb-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-2">
        <div>
          <label
            htmlFor="orderStatusFilter"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            Status
          </label>

          <select
            id="orderStatusFilter"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
            className="form-input"
          >
            {orderStatuses.map((status) => (
              <option
                key={status || "ALL"}
                value={status}
              >
                {status
                  ? status.replaceAll("_", " ")
                  : "All statuses"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="orderTypeFilter"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            Order type
          </label>

          <select
            id="orderTypeFilter"
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(event.target.value)
            }
            className="form-input"
          >
            {orderTypes.map((type) => (
              <option
                key={type || "ALL"}
                value={type}
              >
                {type
                  ? type.replaceAll("_", " ")
                  : "All order types"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner size="lg" label="Loading orders" />
        </div>
      ) : orders.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <h2 className="text-lg font-bold text-slate-900">
            No orders found
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Create the first restaurant order or change the filters.
          </p>

          <Button
            onClick={openCreateModal}
            className="mt-6"
          >
            Create order
          </Button>
        </div>
      ) : (
        <div className="space-y-5">
          {orders.map((order) => (
            <article
              key={order.id}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-bold text-slate-900">
                      {order.order_number}
                    </h2>

                    <StatusBadge status={order.status} />

                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                      {order.order_type.replaceAll("_", " ")}
                    </span>
                  </div>

                  <p className="mt-2 text-sm text-slate-500">
                    {formatDateTime(order.created_at)}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {(statusActions[order.status] ?? []).map(
                    (status) => (
                      <Button
                        key={status}
                        variant={
                          status === "CANCELLED"
                            ? "danger"
                            : "secondary"
                        }
                        onClick={() =>
                          openStatusModal(order, status)
                        }
                      >
                        Mark{" "}
                        {status
                          .replaceAll("_", " ")
                          .toLowerCase()}
                      </Button>
                    ),
                  )}
                </div>
              </div>

              <div className="mt-5 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Table
                  </p>

                  <p className="mt-1 font-semibold text-slate-900">
                    {order.table?.table_number ?? "Not assigned"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Customer
                  </p>

                  <p className="mt-1 font-semibold text-slate-900">
                    {order.customer?.full_name ?? "Guest order"}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Items
                  </p>

                  <p className="mt-1 font-semibold text-slate-900">
                    {order.items.reduce(
                      (count, item) =>
                        count + item.quantity,
                      0,
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Subtotal
                  </p>

                  <p className="mt-1 font-bold text-slate-900">
                    {formatCurrency(order.subtotal)}
                  </p>
                </div>
              </div>

              <div className="mt-5 overflow-x-auto">
                <table className="w-full min-w-[650px] text-left">
                  <thead>
                    <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                      <th className="pb-3 font-semibold">
                        Item
                      </th>
                      <th className="pb-3 font-semibold">
                        Price
                      </th>
                      <th className="pb-3 font-semibold">
                        Quantity
                      </th>
                      <th className="pb-3 text-right font-semibold">
                        Total
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {order.items.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-slate-100"
                      >
                        <td className="py-3">
                          <p className="font-semibold text-slate-900">
                            {item.item_name}
                          </p>

                          {item.special_instruction && (
                            <p className="mt-1 text-xs text-slate-500">
                              {item.special_instruction}
                            </p>
                          )}
                        </td>

                        <td className="py-3 text-sm text-slate-600">
                          {formatCurrency(item.unit_price)}
                        </td>

                        <td className="py-3 text-sm text-slate-600">
                          {item.quantity}
                        </td>

                        <td className="py-3 text-right font-semibold text-slate-900">
                          {formatCurrency(item.line_total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {order.delivery_address && (
                <p className="mt-4 rounded-xl bg-blue-50 px-4 py-3 text-sm text-blue-800">
                  Delivery address: {order.delivery_address}
                </p>
              )}

              {order.special_instructions && (
                <p className="mt-4 text-sm text-slate-600">
                  <strong>Order note:</strong>{" "}
                  {order.special_instructions}
                </p>
              )}

              {order.cancellation_reason && (
                <p className="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
                  Cancellation reason:{" "}
                  {order.cancellation_reason}
                </p>
              )}
            </article>
          ))}
        </div>
      )}

      <Modal
        open={createModalOpen}
        title="Create restaurant order"
        onClose={closeCreateModal}
        maxWidth="max-w-6xl"
      >
        <form
          onSubmit={submitOrder}
          className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"
        >
          <div>
            <div className="grid gap-5 sm:grid-cols-2">
              <FormField
                label="Order type"
                name="order_type"
                required
              >
                <select
                  id="order_type"
                  name="order_type"
                  value={orderForm.order_type}
                  onChange={updateOrderField}
                  className="form-input"
                >
                  <option value="DINE_IN">
                    Dine-in
                  </option>
                  <option value="TAKEAWAY">
                    Takeaway
                  </option>
                  <option value="DELIVERY">
                    Delivery
                  </option>
                </select>
              </FormField>

              {orderForm.order_type === "DINE_IN" && (
                <FormField
                  label="Dining table"
                  name="table_id"
                  required
                >
                  <select
                    id="table_id"
                    name="table_id"
                    value={orderForm.table_id}
                    onChange={updateOrderField}
                    className="form-input"
                    disabled={Boolean(
                      orderForm.reservation_id,
                    )}
                  >
                    <option value="">
                      Select table
                    </option>

                    {tables.map((table) => (
                      <option
                        key={table.id}
                        value={table.id}
                      >
                        {table.table_number} · {table.area} ·{" "}
                        {table.capacity} seats
                      </option>
                    ))}
                  </select>
                </FormField>
              )}
            </div>

            {orderForm.order_type === "DINE_IN" && (
              <div className="mt-5">
                <FormField
                  label="Linked reservation"
                  name="reservation_id"
                  helperText="Optional. Selecting a reservation automatically selects its table and customer."
                >
                  <select
                    id="reservation_id"
                    name="reservation_id"
                    value={orderForm.reservation_id}
                    onChange={updateOrderField}
                    className="form-input"
                  >
                    <option value="">
                      No reservation
                    </option>

                    {reservations.map((reservation) => (
                      <option
                        key={reservation.id}
                        value={reservation.id}
                      >
                        {reservation.reservation_number} ·{" "}
                        {reservation.customer.full_name} ·{" "}
                        {reservation.table.table_number}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>
            )}

            {orderForm.order_type === "DELIVERY" && (
              <div className="mt-5">
                <FormField
                  label="Delivery address"
                  name="delivery_address"
                  required
                >
                  <textarea
                    id="delivery_address"
                    name="delivery_address"
                    rows="3"
                    value={orderForm.delivery_address}
                    onChange={updateOrderField}
                    className="form-input resize-none"
                    placeholder="Enter the complete delivery address"
                  />
                </FormField>
              </div>
            )}

            <div className="mt-5">
              <FormField
                label="Order instructions"
                name="special_instructions"
              >
                <textarea
                  id="special_instructions"
                  name="special_instructions"
                  rows="2"
                  value={orderForm.special_instructions}
                  onChange={updateOrderField}
                  className="form-input resize-none"
                  placeholder="Optional instruction for the complete order"
                />
              </FormField>
            </div>

            <div className="mt-7 border-t border-slate-200 pt-6">
              <div className="mb-4">
                <label
                  htmlFor="orderMenuSearch"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Search available menu
                </label>

                <input
                  id="orderMenuSearch"
                  type="search"
                  value={menuSearch}
                  onChange={(event) =>
                    setMenuSearch(event.target.value)
                  }
                  className="form-input"
                  placeholder="Search item or category"
                />
              </div>

              <div className="grid max-h-[430px] gap-3 overflow-y-auto pr-1 sm:grid-cols-2">
                {filteredMenuItems.map((item) => (
                  <article
                    key={item.id}
                    className="rounded-xl border border-slate-200 p-4"
                  >
                    <p className="text-xs font-semibold text-teal-700">
                      {item.category.name}
                    </p>

                    <h3 className="mt-1 font-bold text-slate-900">
                      {item.name}
                    </h3>

                    <p className="mt-2 font-semibold text-slate-700">
                      {formatCurrency(item.price)}
                    </p>

                    <Button
                      variant="secondary"
                      onClick={() => addMenuItem(item)}
                      className="mt-4 w-full"
                    >
                      Add to order
                    </Button>
                  </article>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-5">
            <h3 className="text-lg font-bold text-slate-900">
              Order cart
            </h3>

            {cart.length === 0 ? (
              <div className="mt-5 rounded-xl border border-dashed border-slate-300 px-5 py-12 text-center text-sm text-slate-500">
                No items added.
              </div>
            ) : (
              <div className="mt-5 space-y-4">
                {cart.map((item) => (
                  <article
                    key={item.menu_item_id}
                    className="rounded-xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex justify-between gap-3">
                      <div>
                        <h4 className="font-bold text-slate-900">
                          {item.name}
                        </h4>

                        <p className="mt-1 text-sm text-slate-500">
                          {formatCurrency(item.price)} each
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          removeCartItem(
                            item.menu_item_id,
                          )
                        }
                        className="text-sm font-semibold text-red-600"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="mt-4">
                      <label className="mb-1 block text-xs font-semibold text-slate-600">
                        Quantity
                      </label>

                      <input
                        type="number"
                        min="1"
                        max="100"
                        value={item.quantity}
                        onChange={(event) =>
                          updateCartItem(
                            item.menu_item_id,
                            "quantity",
                            Number(event.target.value),
                          )
                        }
                        className="form-input"
                      />
                    </div>

                    <div className="mt-3">
                      <label className="mb-1 block text-xs font-semibold text-slate-600">
                        Item instruction
                      </label>

                      <input
                        type="text"
                        value={item.special_instruction}
                        onChange={(event) =>
                          updateCartItem(
                            item.menu_item_id,
                            "special_instruction",
                            event.target.value,
                          )
                        }
                        className="form-input"
                        placeholder="Example: less spicy"
                      />
                    </div>

                    <p className="mt-4 text-right font-bold text-slate-900">
                      {formatCurrency(
                        Number(item.price) *
                          Number(item.quantity),
                      )}
                    </p>
                  </article>
                ))}
              </div>
            )}

            <div className="mt-6 flex items-center justify-between border-t border-slate-200 pt-5">
              <span className="font-semibold text-slate-600">
                Subtotal
              </span>

              <span className="text-2xl font-bold text-slate-900">
                {formatCurrency(cartSubtotal)}
              </span>
            </div>

            {createError && (
              <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {createError}
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <Button
                variant="secondary"
                onClick={closeCreateModal}
                disabled={creating}
                className="flex-1"
              >
                Cancel
              </Button>

              <Button
                type="submit"
                loading={creating}
                className="flex-1"
              >
                Create order
              </Button>
            </div>
          </div>
        </form>
      </Modal>

      <Modal
        open={Boolean(selectedOrder)}
        title="Update order status"
        onClose={closeStatusModal}
      >
        {selectedOrder && (
          <form
            onSubmit={submitStatusUpdate}
            className="space-y-5"
          >
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">
                Order
              </p>

              <p className="mt-1 font-bold text-slate-900">
                {selectedOrder.order_number}
              </p>

              <p className="mt-2 text-sm text-slate-600">
                Change status to{" "}
                <strong>
                  {selectedStatus.replaceAll("_", " ")}
                </strong>
              </p>
            </div>

            {selectedStatus === "CANCELLED" && (
              <FormField
                label="Cancellation reason"
                name="orderCancellationReason"
                required
              >
                <textarea
                  id="orderCancellationReason"
                  rows="3"
                  value={cancellationReason}
                  onChange={(event) => {
                    setCancellationReason(
                      event.target.value,
                    );
                    setStatusError("");
                  }}
                  className="form-input resize-none"
                />
              </FormField>
            )}

            {statusError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {statusError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={closeStatusModal}
                disabled={statusUpdating}
              >
                Close
              </Button>

              <Button
                type="submit"
                loading={statusUpdating}
                variant={
                  selectedStatus === "CANCELLED"
                    ? "danger"
                    : "primary"
                }
              >
                Confirm update
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
}