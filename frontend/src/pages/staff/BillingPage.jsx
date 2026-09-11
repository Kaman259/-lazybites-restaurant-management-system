import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  createInvoice,
  getInvoices,
  markInvoicePaid,
  refundInvoice,
} from "../../api/invoiceApi";
import { getOrders } from "../../api/orderApi";
import {
  getBackendAssetUrl,
  getRestaurantSettings,
} from "../../api/settingsApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../context/ToastContext";

const emptyInvoiceForm = {
  order_id: "",
  discount_type: "NONE",
  discount_value: "0",
};

const ACTIVE_ORDER_STATUSES = new Set([
  "PENDING",
  "PREPARING",
  "READY",
  "SERVED",
]);

function formatCurrency(
  value,
  currency = "INR",
) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function humaniseValue(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) => letter.toUpperCase(),
    );
}

function getInvoiceOrders(invoice) {
  if (
    Array.isArray(invoice?.orders) &&
    invoice.orders.length > 0
  ) {
    return invoice.orders;
  }

  if (invoice?.order) {
    return [invoice.order];
  }

  return [];
}

function calculateOrdersSubtotal(orders) {
  return orders.reduce(
    (total, order) =>
      total + Number(order.subtotal ?? 0),
    0,
  );
}

export default function BillingPage() {
  const { showToast } = useToast();

  const [invoices, setInvoices] = useState([]);
  const [orders, setOrders] = useState([]);
  const [
    restaurantSettings,
    setRestaurantSettings,
  ] = useState(null);

  const [
    paymentStatusFilter,
    setPaymentStatusFilter,
  ] = useState("");

  const [
    paymentMethodFilter,
    setPaymentMethodFilter,
  ] = useState("");

  const [
    pageLoading,
    setPageLoading,
  ] = useState(true);

  const [
    pageError,
    setPageError,
  ] = useState("");

  const [
    invoiceModalOpen,
    setInvoiceModalOpen,
  ] = useState(false);

  const [
    invoiceForm,
    setInvoiceForm,
  ] = useState(emptyInvoiceForm);

  const [
    invoiceSaving,
    setInvoiceSaving,
  ] = useState(false);

  const [
    invoiceError,
    setInvoiceError,
  ] = useState("");

  const [
    paymentInvoice,
    setPaymentInvoice,
  ] = useState(null);

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState("CASH");

  const [
    paymentSaving,
    setPaymentSaving,
  ] = useState(false);

  const [
    paymentError,
    setPaymentError,
  ] = useState("");

  const [
    refundInvoiceRecord,
    setRefundInvoiceRecord,
  ] = useState(null);

  const [
    refundReason,
    setRefundReason,
  ] = useState("");

  const [
    refundSaving,
    setRefundSaving,
  ] = useState(false);

  const [
    refundError,
    setRefundError,
  ] = useState("");

  const [
    printInvoiceRecord,
    setPrintInvoiceRecord,
  ] = useState(null);

  const currency =
    restaurantSettings?.currency || "INR";

  const billingGroups = useMemo(() => {
    const groups = [];

    const processedReservations =
      new Set();

    const completedUnbilledOrders =
      orders.filter(
        (order) =>
          order.status === "COMPLETED" &&
          !order.invoice_id,
      );

    for (
      const order
      of completedUnbilledOrders
    ) {
      if (!order.reservation_id) {
        groups.push({
          key: `order-${order.id}`,
          representativeOrder: order,
          orders: [order],
          reservationId: null,
          reservationNumber: null,
        });

        continue;
      }

      if (
        processedReservations.has(
          order.reservation_id,
        )
      ) {
        continue;
      }

      processedReservations.add(
        order.reservation_id,
      );

      const reservationOrders =
        orders.filter(
          (candidate) =>
            candidate.reservation_id ===
            order.reservation_id,
        );

      const alreadyBilled =
        reservationOrders.some(
          (candidate) =>
            Boolean(
              candidate.invoice_id,
            ),
        );

      if (alreadyBilled) {
        continue;
      }

      const hasActiveOrders =
        reservationOrders.some(
          (candidate) =>
            ACTIVE_ORDER_STATUSES.has(
              candidate.status,
            ),
        );

      if (hasActiveOrders) {
        continue;
      }

      const completedOrders =
        reservationOrders.filter(
          (candidate) =>
            candidate.status ===
              "COMPLETED" &&
            !candidate.invoice_id,
        );

      if (
        completedOrders.length === 0
      ) {
        continue;
      }

      groups.push({
        key: `reservation-${order.reservation_id}`,
        representativeOrder:
          completedOrders[0],
        orders: completedOrders,
        reservationId:
          order.reservation_id,
        reservationNumber:
          order.reservation
            ?.reservation_number ??
          null,
      });
    }

    return groups;
  }, [orders]);

  const selectedBillingGroup =
    useMemo(
      () =>
        billingGroups.find(
          (group) =>
            String(
              group
                .representativeOrder
                .id,
            ) ===
            invoiceForm.order_id,
        ) ?? null,
      [
        billingGroups,
        invoiceForm.order_id,
      ],
    );

  const estimatedInvoice =
    useMemo(() => {
      if (!selectedBillingGroup) {
        return null;
      }

      const subtotal =
        calculateOrdersSubtotal(
          selectedBillingGroup.orders,
        );

      const discountValue =
        Number(
          invoiceForm.discount_value,
        ) || 0;

      let discountAmount = 0;

      if (
        invoiceForm.discount_type ===
        "PERCENTAGE"
      ) {
        discountAmount =
          subtotal *
          (discountValue / 100);
      }

      if (
        invoiceForm.discount_type ===
        "FIXED"
      ) {
        discountAmount =
          discountValue;
      }

      discountAmount = Math.min(
        Math.max(
          discountAmount,
          0,
        ),
        subtotal,
      );

      const taxableAmount =
        subtotal - discountAmount;

      const gstPercentage = Number(
        restaurantSettings
          ?.default_gst_percentage ??
          0,
      );

      const gstAmount =
        taxableAmount *
        (gstPercentage / 100);

      return {
        subtotal,
        discountAmount,
        gstPercentage,
        gstAmount,
        grandTotal:
          taxableAmount + gstAmount,
      };
    }, [
      selectedBillingGroup,
      invoiceForm.discount_type,
      invoiceForm.discount_value,
      restaurantSettings,
    ]);

  const loadInvoices =
    useCallback(async () => {
      const invoiceData =
        await getInvoices({
          paymentStatus:
            paymentStatusFilter,
          paymentMethod:
            paymentMethodFilter,
        });

      setInvoices(invoiceData);
    }, [
      paymentStatusFilter,
      paymentMethodFilter,
    ]);

  const loadPage =
    useCallback(async () => {
      setPageLoading(true);
      setPageError("");

      try {
        const [
          invoiceData,
          orderData,
          settingsData,
        ] = await Promise.all([
          getInvoices({
            paymentStatus:
              paymentStatusFilter,
            paymentMethod:
              paymentMethodFilter,
          }),
          getOrders(),
          getRestaurantSettings(),
        ]);

        setInvoices(invoiceData);
        setOrders(orderData);
        setRestaurantSettings(
          settingsData,
        );
      } catch (error) {
        setPageError(
          error.message ??
            "Billing information could not be loaded.",
        );
      } finally {
        setPageLoading(false);
      }
    }, [
      paymentStatusFilter,
      paymentMethodFilter,
    ]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  function openInvoiceModal() {
    if (
      billingGroups.length === 0
    ) {
      showToast(
        "There are no completed orders ready for final billing.",
        "error",
      );

      return;
    }

    setInvoiceForm({
      ...emptyInvoiceForm,
      order_id: String(
        billingGroups[0]
          .representativeOrder.id,
      ),
    });

    setInvoiceError("");
    setInvoiceModalOpen(true);
  }

  function closeInvoiceModal() {
    if (invoiceSaving) {
      return;
    }

    setInvoiceModalOpen(false);

    setInvoiceForm(
      emptyInvoiceForm,
    );

    setInvoiceError("");
  }

  function updateInvoiceField(
    event,
  ) {
    const {
      name,
      value,
    } = event.target;

    setInvoiceForm(
      (currentForm) => {
        if (
          name ===
          "discount_type"
        ) {
          return {
            ...currentForm,
            discount_type: value,
            discount_value:
              value === "NONE"
                ? "0"
                : currentForm
                    .discount_value,
          };
        }

        return {
          ...currentForm,
          [name]: value,
        };
      },
    );

    setInvoiceError("");
  }

  async function submitInvoice(
    event,
  ) {
    event.preventDefault();

    if (
      !invoiceForm.order_id
    ) {
      setInvoiceError(
        "Select an order or reservation.",
      );

      return;
    }

    if (
      !selectedBillingGroup
    ) {
      setInvoiceError(
        "The selected billing group is no longer available.",
      );

      return;
    }

    const discountValue =
      Number(
        invoiceForm.discount_value,
      );

    if (
      !Number.isFinite(
        discountValue,
      ) ||
      discountValue < 0
    ) {
      setInvoiceError(
        "Discount value cannot be negative.",
      );

      return;
    }

    if (
      invoiceForm.discount_type ===
        "PERCENTAGE" &&
      discountValue > 100
    ) {
      setInvoiceError(
        "Percentage discount cannot exceed 100.",
      );

      return;
    }

    if (
      invoiceForm.discount_type ===
        "FIXED" &&
      estimatedInvoice &&
      discountValue >
        estimatedInvoice.subtotal
    ) {
      setInvoiceError(
        "Fixed discount cannot exceed the subtotal.",
      );

      return;
    }

    const payload = {
      order_id: Number(
        invoiceForm.order_id,
      ),
      discount_type:
        invoiceForm.discount_type,
      discount_value:
        invoiceForm
          .discount_type ===
        "NONE"
          ? "0.00"
          : discountValue.toFixed(
              2,
            ),
    };

    setInvoiceSaving(true);
    setInvoiceError("");

    try {
      await createInvoice(payload);

      showToast(
        selectedBillingGroup
          .orders.length > 1
          ? "Combined invoice generated successfully."
          : "Invoice generated successfully.",
      );

      setInvoiceModalOpen(false);

      setInvoiceForm(
        emptyInvoiceForm,
      );

      await loadPage();
    } catch (error) {
      setInvoiceError(
        error.message ??
          "The invoice could not be generated.",
      );
    } finally {
      setInvoiceSaving(false);
    }
  }

  function openPaymentModal(
    invoice,
  ) {
    setPaymentInvoice(invoice);

    setPaymentMethod("CASH");
    setPaymentError("");
  }

  function closePaymentModal() {
    if (paymentSaving) {
      return;
    }

    setPaymentInvoice(null);
    setPaymentMethod("CASH");
    setPaymentError("");
  }

  async function submitPayment(
    event,
  ) {
    event.preventDefault();

    setPaymentSaving(true);
    setPaymentError("");

    try {
      await markInvoicePaid(
        paymentInvoice.id,
        paymentMethod,
      );

      showToast(
        "Invoice marked as paid.",
      );

      setPaymentInvoice(null);

      await loadInvoices();
    } catch (error) {
      setPaymentError(
        error.message ??
          "Payment could not be recorded.",
      );
    } finally {
      setPaymentSaving(false);
    }
  }

  function openRefundModal(
    invoice,
  ) {
    setRefundInvoiceRecord(
      invoice,
    );

    setRefundReason("");
    setRefundError("");
  }

  function closeRefundModal() {
    if (refundSaving) {
      return;
    }

    setRefundInvoiceRecord(null);
    setRefundReason("");
    setRefundError("");
  }

  async function submitRefund(
    event,
  ) {
    event.preventDefault();

    if (
      !refundReason.trim()
    ) {
      setRefundError(
        "Refund reason is required.",
      );

      return;
    }

    setRefundSaving(true);
    setRefundError("");

    try {
      await refundInvoice(
        refundInvoiceRecord.id,
        refundReason,
      );

      showToast(
        "Invoice refunded successfully.",
      );

      setRefundInvoiceRecord(null);
      setRefundReason("");

      await loadInvoices();
    } catch (error) {
      setRefundError(
        error.message ??
          "The refund could not be completed.",
      );
    } finally {
      setRefundSaving(false);
    }
  }

  function printInvoice(invoice) {
    setPrintInvoiceRecord(
      invoice,
    );

    window.setTimeout(
      () => {
        window.print();
      },
      100,
    );
  }

  return (
    <section>
      <div className="print:hidden">
        <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-semibold text-teal-700">
              Payments and receipts
            </p>

            <h1 className="mt-2 text-3xl font-bold text-slate-900">
              Billing and invoices
            </h1>

            <p className="mt-2 text-slate-500">
              Reservation orders are combined into one final invoice.
            </p>
          </div>

          <Button
            onClick={
              openInvoiceModal
            }
          >
            Generate invoice
          </Button>
        </div>

        <div className="mb-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-2">
          <div>
            <label
              htmlFor="paymentStatusFilter"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Payment status
            </label>

            <select
              id="paymentStatusFilter"
              value={
                paymentStatusFilter
              }
              onChange={(event) =>
                setPaymentStatusFilter(
                  event.target.value,
                )
              }
              className="form-input"
            >
              <option value="">
                All statuses
              </option>

              <option value="UNPAID">
                Unpaid
              </option>

              <option value="PAID">
                Paid
              </option>

              <option value="REFUNDED">
                Refunded
              </option>
            </select>
          </div>

          <div>
            <label
              htmlFor="paymentMethodFilter"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Payment method
            </label>

            <select
              id="paymentMethodFilter"
              value={
                paymentMethodFilter
              }
              onChange={(event) =>
                setPaymentMethodFilter(
                  event.target.value,
                )
              }
              className="form-input"
            >
              <option value="">
                All methods
              </option>

              <option value="CASH">
                Cash
              </option>

              <option value="UPI">
                UPI
              </option>

              <option value="CARD">
                Card
              </option>
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
            <Spinner
              size="lg"
              label="Loading invoices"
            />
          </div>
        ) : invoices.length ===
          0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
            <h2 className="text-lg font-bold text-slate-900">
              No invoices found
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Complete all orders for a visit before generating its invoice.
            </p>

            <Button
              onClick={
                openInvoiceModal
              }
              className="mt-6"
            >
              Generate invoice
            </Button>
          </div>
        ) : (
          <div className="space-y-5">
            {invoices.map(
              (invoice) => {
                const invoiceOrders =
                  getInvoiceOrders(
                    invoice,
                  );

                const primaryOrder =
                  invoiceOrders[0] ??
                  null;

                return (
                  <article
                    key={
                      invoice.id
                    }
                    className="rounded-2xl border border-slate-200 bg-white p-5"
                  >
                    <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h2 className="text-lg font-bold text-slate-900">
                            {
                              invoice.invoice_number
                            }
                          </h2>

                          <StatusBadge
                            status={
                              invoice.payment_status
                            }
                          />
                        </div>

                        <p className="mt-2 text-sm text-slate-500">
                          {invoiceOrders.length >
                          1
                            ? `${invoiceOrders.length} combined orders`
                            : primaryOrder
                              ? `Order ${primaryOrder.order_number}`
                              : "No order information"}
                        </p>

                        {invoiceOrders.length >
                          1 &&
                          primaryOrder
                            ?.reservation_id && (
                            <p className="mt-1 text-sm text-slate-500">
                              Reservation #
                              {
                                primaryOrder.reservation_id
                              }
                            </p>
                          )}

                        <p className="mt-1 text-sm text-slate-500">
                          {formatDateTime(
                            invoice.created_at,
                          )}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          onClick={() =>
                            printInvoice(
                              invoice,
                            )
                          }
                        >
                          Print invoice
                        </Button>

                        {invoice.payment_status ===
                          "UNPAID" && (
                          <Button
                            onClick={() =>
                              openPaymentModal(
                                invoice,
                              )
                            }
                          >
                            Record payment
                          </Button>
                        )}

                        {invoice.payment_status ===
                          "PAID" && (
                          <Button
                            variant="danger"
                            onClick={() =>
                              openRefundModal(
                                invoice,
                              )
                            }
                          >
                            Refund
                          </Button>
                        )}
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2 lg:grid-cols-4">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Customer
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                          {primaryOrder
                            ?.customer
                            ?.full_name ??
                            "Guest"}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Orders
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                          {
                            invoiceOrders.length
                          }
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Payment
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                          {invoice.payment_method
                            ? humaniseValue(
                                invoice.payment_method,
                              )
                            : "Not paid"}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Total
                        </p>

                        <p className="mt-1 text-lg font-bold text-slate-900">
                          {formatCurrency(
                            invoice.grand_total,
                            currency,
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 overflow-x-auto">
                      <table className="w-full min-w-[760px] text-left">
                        <thead>
                          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                            <th className="pb-3 font-semibold">
                              Order
                            </th>

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
                          {invoiceOrders.flatMap(
                            (order) =>
                              order.items.map(
                                (
                                  item,
                                ) => (
                                  <tr
                                    key={`${order.id}-${item.id}`}
                                    className="border-b border-slate-100"
                                  >
                                    <td className="py-3 pr-4 text-sm font-semibold text-slate-700">
                                      {
                                        order.order_number
                                      }
                                    </td>

                                    <td className="py-3">
                                      <p className="font-semibold text-slate-900">
                                        {
                                          item.item_name
                                        }
                                      </p>

                                      {item.special_instruction && (
                                        <p className="mt-1 text-xs text-slate-500">
                                          {
                                            item.special_instruction
                                          }
                                        </p>
                                      )}
                                    </td>

                                    <td className="py-3 text-sm text-slate-600">
                                      {formatCurrency(
                                        item.unit_price,
                                        currency,
                                      )}
                                    </td>

                                    <td className="py-3 text-sm text-slate-600">
                                      {
                                        item.quantity
                                      }
                                    </td>

                                    <td className="py-3 text-right font-semibold text-slate-900">
                                      {formatCurrency(
                                        item.line_total,
                                        currency,
                                      )}
                                    </td>
                                  </tr>
                                ),
                              ),
                          )}
                        </tbody>
                      </table>
                    </div>

                    <div className="mt-5 ml-auto max-w-sm space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">
                          Subtotal
                        </span>

                        <span className="font-semibold text-slate-900">
                          {formatCurrency(
                            invoice.subtotal,
                            currency,
                          )}
                        </span>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">
                          Discount
                        </span>

                        <span className="font-semibold text-slate-900">
                          -
                          {formatCurrency(
                            invoice.discount_amount,
                            currency,
                          )}
                        </span>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">
                          GST (
                          {
                            invoice.gst_percentage
                          }
                          %)
                        </span>

                        <span className="font-semibold text-slate-900">
                          {formatCurrency(
                            invoice.gst_amount,
                            currency,
                          )}
                        </span>
                      </div>

                      <div className="flex justify-between border-t border-slate-200 pt-3">
                        <span className="font-bold text-slate-900">
                          Grand total
                        </span>

                        <span className="text-xl font-bold text-slate-900">
                          {formatCurrency(
                            invoice.grand_total,
                            currency,
                          )}
                        </span>
                      </div>
                    </div>

                    {invoice.refund_reason && (
                      <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        Refund reason:{" "}
                        {
                          invoice.refund_reason
                        }
                      </div>
                    )}
                  </article>
                );
              },
            )}
          </div>
        )}

        <Modal
          open={invoiceModalOpen}
          title="Generate invoice"
          onClose={
            closeInvoiceModal
          }
          maxWidth="max-w-2xl"
        >
          <form
            onSubmit={
              submitInvoice
            }
            className="space-y-5"
          >
            <FormField
              label="Completed order or reservation"
              name="order_id"
              required
            >
              <select
                id="order_id"
                name="order_id"
                value={
                  invoiceForm.order_id
                }
                onChange={
                  updateInvoiceField
                }
                className="form-input"
              >
                <option value="">
                  Select billing group
                </option>

                {billingGroups.map(
                  (group) => {
                    const subtotal =
                      calculateOrdersSubtotal(
                        group.orders,
                      );

                    return (
                      <option
                        key={
                          group.key
                        }
                        value={
                          group
                            .representativeOrder
                            .id
                        }
                      >
                        {group.reservationId
                          ? `${
                              group.reservationNumber ??
                              `Reservation #${group.reservationId}`
                            } · ${group.orders.length} orders · ${formatCurrency(
                              subtotal,
                              currency,
                            )}`
                          : `${
                              group
                                .representativeOrder
                                .order_number
                            } · ${formatCurrency(
                              subtotal,
                              currency,
                            )}`}
                      </option>
                    );
                  },
                )}
              </select>
            </FormField>

            {selectedBillingGroup && (
              <div className="rounded-xl border border-teal-100 bg-teal-50/60 p-4">
                <p className="text-sm font-semibold text-teal-800">
                  {selectedBillingGroup
                    .reservationId
                    ? `${selectedBillingGroup.orders.length} completed orders will be combined into this invoice.`
                    : "This invoice contains one standalone order."}
                </p>

                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedBillingGroup.orders.map(
                    (order) => (
                      <span
                        key={
                          order.id
                        }
                        className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-slate-700"
                      >
                        {
                          order.order_number
                        }
                      </span>
                    ),
                  )}
                </div>
              </div>
            )}

            <div className="grid gap-5 sm:grid-cols-2">
              <FormField
                label="Discount type"
                name="discount_type"
                required
              >
                <select
                  id="discount_type"
                  name="discount_type"
                  value={
                    invoiceForm.discount_type
                  }
                  onChange={
                    updateInvoiceField
                  }
                  className="form-input"
                >
                  <option value="NONE">
                    No discount
                  </option>

                  <option value="PERCENTAGE">
                    Percentage
                  </option>

                  <option value="FIXED">
                    Fixed amount
                  </option>
                </select>
              </FormField>

              <FormField
                label={
                  invoiceForm.discount_type ===
                  "PERCENTAGE"
                    ? "Discount percentage"
                    : "Discount value"
                }
                name="discount_value"
                required
              >
                <input
                  id="discount_value"
                  name="discount_value"
                  type="number"
                  min="0"
                  max={
                    invoiceForm.discount_type ===
                    "PERCENTAGE"
                      ? "100"
                      : undefined
                  }
                  step="0.01"
                  value={
                    invoiceForm.discount_value
                  }
                  onChange={
                    updateInvoiceField
                  }
                  disabled={
                    invoiceForm.discount_type ===
                    "NONE"
                  }
                  className="form-input"
                />
              </FormField>
            </div>

            {estimatedInvoice && (
              <div className="rounded-xl bg-slate-50 p-4">
                <h3 className="font-bold text-slate-900">
                  Invoice calculation
                </h3>

                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Subtotal
                    </span>

                    <span className="font-semibold">
                      {formatCurrency(
                        estimatedInvoice.subtotal,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Discount
                    </span>

                    <span className="font-semibold">
                      -
                      {formatCurrency(
                        estimatedInvoice.discountAmount,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      GST (
                      {
                        estimatedInvoice.gstPercentage
                      }
                      %)
                    </span>

                    <span className="font-semibold">
                      {formatCurrency(
                        estimatedInvoice.gstAmount,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between border-t border-slate-200 pt-3 text-base">
                    <span className="font-bold">
                      Grand total
                    </span>

                    <span className="font-bold">
                      {formatCurrency(
                        estimatedInvoice.grandTotal,
                        currency,
                      )}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {invoiceError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {invoiceError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={
                  closeInvoiceModal
                }
                disabled={
                  invoiceSaving
                }
              >
                Cancel
              </Button>

              <Button
                type="submit"
                loading={
                  invoiceSaving
                }
              >
                Generate invoice
              </Button>
            </div>
          </form>
        </Modal>

        <Modal
          open={Boolean(
            paymentInvoice,
          )}
          title="Record payment"
          onClose={
            closePaymentModal
          }
        >
          {paymentInvoice && (
            <form
              onSubmit={
                submitPayment
              }
              className="space-y-5"
            >
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">
                  Invoice
                </p>

                <p className="mt-1 font-bold text-slate-900">
                  {
                    paymentInvoice.invoice_number
                  }
                </p>

                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {formatCurrency(
                    paymentInvoice.grand_total,
                    currency,
                  )}
                </p>
              </div>

              <FormField
                label="Payment method"
                name="payment_method"
                required
              >
                <select
                  id="payment_method"
                  value={
                    paymentMethod
                  }
                  onChange={(
                    event,
                  ) => {
                    setPaymentMethod(
                      event.target
                        .value,
                    );

                    setPaymentError(
                      "",
                    );
                  }}
                  className="form-input"
                >
                  <option value="CASH">
                    Cash
                  </option>

                  <option value="UPI">
                    UPI
                  </option>

                  <option value="CARD">
                    Card
                  </option>
                </select>
              </FormField>

              {paymentError && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {paymentError}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={
                    closePaymentModal
                  }
                  disabled={
                    paymentSaving
                  }
                >
                  Cancel
                </Button>

                <Button
                  type="submit"
                  loading={
                    paymentSaving
                  }
                >
                  Confirm payment
                </Button>
              </div>
            </form>
          )}
        </Modal>

        <Modal
          open={Boolean(
            refundInvoiceRecord,
          )}
          title="Refund invoice"
          onClose={
            closeRefundModal
          }
        >
          {refundInvoiceRecord && (
            <form
              onSubmit={
                submitRefund
              }
              className="space-y-5"
            >
              <div className="rounded-xl border border-red-100 bg-red-50 p-4">
                <p className="text-sm text-red-700">
                  Refund{" "}
                  <strong>
                    {
                      refundInvoiceRecord.invoice_number
                    }
                  </strong>{" "}
                  for{" "}
                  <strong>
                    {formatCurrency(
                      refundInvoiceRecord.grand_total,
                      currency,
                    )}
                  </strong>
                  .
                </p>
              </div>

              <FormField
                label="Refund reason"
                name="refund_reason"
                required
              >
                <textarea
                  id="refund_reason"
                  rows="4"
                  value={
                    refundReason
                  }
                  onChange={(
                    event,
                  ) => {
                    setRefundReason(
                      event.target
                        .value,
                    );

                    setRefundError(
                      "",
                    );
                  }}
                  className="form-input resize-none"
                  placeholder="Enter the reason for this refund"
                />
              </FormField>

              {refundError && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {refundError}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={
                    closeRefundModal
                  }
                  disabled={
                    refundSaving
                  }
                >
                  Cancel
                </Button>

                <Button
                  type="submit"
                  variant="danger"
                  loading={
                    refundSaving
                  }
                >
                  Confirm refund
                </Button>
              </div>
            </form>
          )}
        </Modal>
      </div>

      {printInvoiceRecord &&
        (() => {
          const printOrders =
            getInvoiceOrders(
              printInvoiceRecord,
            );

          const primaryOrder =
            printOrders[0] ??
            null;

          return (
            <div className="hidden bg-white p-8 text-slate-900 print:block">
              <div className="mx-auto max-w-3xl">
                <header className="flex items-start justify-between border-b border-slate-300 pb-6">
                  <div className="flex items-center gap-4">
                    {restaurantSettings?.logo_path ? (
                      <img
                        src={getBackendAssetUrl(
                          restaurantSettings.logo_path,
                        )}
                        alt="Restaurant logo"
                        className="h-16 w-16 object-contain"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-slate-900 text-2xl font-black text-white">
                        L
                      </div>
                    )}

                    <div>
                      <h1 className="text-2xl font-bold">
                        {restaurantSettings
                          ?.restaurant_name ??
                          "LazyBites Restaurant"}
                      </h1>

                      <p className="mt-1 text-sm">
                        {
                          restaurantSettings?.address
                        }
                      </p>

                      <p className="text-sm">
                        Phone:{" "}
                        {
                          restaurantSettings?.phone
                        }
                      </p>

                      {restaurantSettings?.email && (
                        <p className="text-sm">
                          Email:{" "}
                          {
                            restaurantSettings.email
                          }
                        </p>
                      )}

                      {restaurantSettings?.gstin && (
                        <p className="text-sm">
                          GSTIN:{" "}
                          {
                            restaurantSettings.gstin
                          }
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <h2 className="text-xl font-bold">
                      TAX INVOICE
                    </h2>

                    <p className="mt-2 text-sm">
                      {
                        printInvoiceRecord.invoice_number
                      }
                    </p>

                    <p className="text-sm">
                      {formatDateTime(
                        printInvoiceRecord.created_at,
                      )}
                    </p>
                  </div>
                </header>

                <div className="grid grid-cols-2 gap-6 border-b border-slate-300 py-6 text-sm">
                  <div>
                    <p className="font-bold">
                      Customer information
                    </p>

                    <p className="mt-2">
                      {primaryOrder
                        ?.customer
                        ?.full_name ??
                        "Guest customer"}
                    </p>

                    {primaryOrder
                      ?.customer
                      ?.phone && (
                      <p>
                        {
                          primaryOrder
                            .customer
                            .phone
                        }
                      </p>
                    )}

                    {primaryOrder
                      ?.customer
                      ?.email && (
                      <p>
                        {
                          primaryOrder
                            .customer
                            .email
                        }
                      </p>
                    )}
                  </div>

                  <div className="text-right">
                    <p>
                      <strong>
                        Orders:
                      </strong>{" "}
                      {
                        printOrders.length
                      }
                    </p>

                    {primaryOrder
                      ?.reservation_id && (
                      <p>
                        <strong>
                          Reservation:
                        </strong>{" "}
                        #
                        {
                          primaryOrder.reservation_id
                        }
                      </p>
                    )}

                    {primaryOrder?.table && (
                      <p>
                        <strong>
                          Table:
                        </strong>{" "}
                        {
                          primaryOrder
                            .table
                            .table_number
                        }
                      </p>
                    )}

                    <p>
                      <strong>
                        Payment:
                      </strong>{" "}
                      {printInvoiceRecord.payment_method
                        ? humaniseValue(
                            printInvoiceRecord.payment_method,
                          )
                        : "Unpaid"}
                    </p>
                  </div>
                </div>

                <table className="mt-6 w-full text-left text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-900">
                      <th className="py-3">
                        Order
                      </th>

                      <th className="py-3">
                        Item
                      </th>

                      <th className="py-3 text-right">
                        Price
                      </th>

                      <th className="py-3 text-right">
                        Quantity
                      </th>

                      <th className="py-3 text-right">
                        Total
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {printOrders.flatMap(
                      (order) =>
                        order.items.map(
                          (item) => (
                            <tr
                              key={`${order.id}-${item.id}`}
                              className="border-b border-slate-200"
                            >
                              <td className="py-3 pr-3">
                                {
                                  order.order_number
                                }
                              </td>

                              <td className="py-3">
                                {
                                  item.item_name
                                }
                              </td>

                              <td className="py-3 text-right">
                                {formatCurrency(
                                  item.unit_price,
                                  currency,
                                )}
                              </td>

                              <td className="py-3 text-right">
                                {
                                  item.quantity
                                }
                              </td>

                              <td className="py-3 text-right">
                                {formatCurrency(
                                  item.line_total,
                                  currency,
                                )}
                              </td>
                            </tr>
                          ),
                        ),
                    )}
                  </tbody>
                </table>

                <div className="mt-6 ml-auto max-w-sm space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>
                      Subtotal
                    </span>

                    <span>
                      {formatCurrency(
                        printInvoiceRecord.subtotal,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>
                      Discount
                    </span>

                    <span>
                      -
                      {formatCurrency(
                        printInvoiceRecord.discount_amount,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>
                      GST (
                      {
                        printInvoiceRecord.gst_percentage
                      }
                      %)
                    </span>

                    <span>
                      {formatCurrency(
                        printInvoiceRecord.gst_amount,
                        currency,
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between border-t-2 border-slate-900 pt-3 text-lg font-bold">
                    <span>
                      Grand total
                    </span>

                    <span>
                      {formatCurrency(
                        printInvoiceRecord.grand_total,
                        currency,
                      )}
                    </span>
                  </div>
                </div>

                <footer className="mt-12 border-t border-slate-300 pt-6 text-center text-sm">
                  <p>
                    {restaurantSettings
                      ?.receipt_footer ??
                      "Thank you for dining with us."}
                  </p>
                </footer>
              </div>
            </div>
          );
        })()}
    </section>
  );
}