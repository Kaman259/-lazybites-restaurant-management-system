import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  createCustomer,
  getCustomer,
  getCustomers,
  updateCustomer,
  updateCustomerStatus,
} from "../../api/customerApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../context/ToastContext";

const emptyCustomerForm = {
  full_name: "",
  phone: "",
  email: "",
  address: "",
  notes: "",
  is_active: true,
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value ?? 0));
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
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

export default function CustomersPage() {
  const { showToast } = useToast();

  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [includeInactive, setIncludeInactive] =
    useState(true);

  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [formModalOpen, setFormModalOpen] =
    useState(false);
  const [editingCustomer, setEditingCustomer] =
    useState(null);
  const [customerForm, setCustomerForm] =
    useState(emptyCustomerForm);
  const [formSaving, setFormSaving] =
    useState(false);
  const [formError, setFormError] = useState("");

  const [detailCustomer, setDetailCustomer] =
    useState(null);
  const [detailLoading, setDetailLoading] =
    useState(false);
  const [detailError, setDetailError] =
    useState("");

  const [statusCustomer, setStatusCustomer] =
    useState(null);
  const [statusSaving, setStatusSaving] =
    useState(false);
  const [statusError, setStatusError] =
    useState("");

  const loadCustomers = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const customerData = await getCustomers({
        search,
        includeInactive,
      });

      setCustomers(customerData);
    } catch (error) {
      setPageError(
        error.message ??
          "Customers could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [search, includeInactive]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadCustomers();
    }, 300);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadCustomers]);

  function openCreateModal() {
    setEditingCustomer(null);
    setCustomerForm(emptyCustomerForm);
    setFormError("");
    setFormModalOpen(true);
  }

  function openEditModal(customer) {
    setEditingCustomer(customer);

    setCustomerForm({
      full_name: customer.full_name ?? "",
      phone: customer.phone ?? "",
      email: customer.email ?? "",
      address: customer.address ?? "",
      notes: customer.notes ?? "",
      is_active: customer.is_active,
    });

    setFormError("");
    setFormModalOpen(true);
  }

  function closeFormModal() {
    if (formSaving) {
      return;
    }

    setFormModalOpen(false);
    setEditingCustomer(null);
    setCustomerForm(emptyCustomerForm);
    setFormError("");
  }

  function updateFormField(event) {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setCustomerForm((currentForm) => ({
      ...currentForm,
      [name]:
        type === "checkbox" ? checked : value,
    }));

    setFormError("");
  }

  async function submitCustomer(event) {
    event.preventDefault();

    if (!customerForm.full_name.trim()) {
      setFormError("Customer name is required.");
      return;
    }

    if (!customerForm.phone.trim()) {
      setFormError("Phone number is required.");
      return;
    }

    const payload = {
      full_name: customerForm.full_name.trim(),
      phone: customerForm.phone.trim(),
      email:
        customerForm.email.trim() || null,
      address:
        customerForm.address.trim() || null,
      notes:
        customerForm.notes.trim() || null,
      is_active: customerForm.is_active,
    };

    setFormSaving(true);
    setFormError("");

    try {
      if (editingCustomer) {
        await updateCustomer(
          editingCustomer.id,
          payload,
        );

        showToast("Customer updated successfully.");
      } else {
        await createCustomer(payload);

        showToast("Customer created successfully.");
      }

      setFormModalOpen(false);
      setEditingCustomer(null);
      setCustomerForm(emptyCustomerForm);

      await loadCustomers();
    } catch (error) {
      setFormError(
        error.message ??
          "Customer information could not be saved.",
      );
    } finally {
      setFormSaving(false);
    }
  }

  async function openDetailModal(customer) {
    setDetailCustomer(null);
    setDetailError("");
    setDetailLoading(true);

    try {
      const customerData = await getCustomer(
        customer.id,
      );

      setDetailCustomer(customerData);
    } catch (error) {
      setDetailError(
        error.message ??
          "Customer activity could not be loaded.",
      );
    } finally {
      setDetailLoading(false);
    }
  }

  function closeDetailModal() {
    setDetailCustomer(null);
    setDetailError("");
    setDetailLoading(false);
  }

  function openStatusModal(customer) {
    setStatusCustomer(customer);
    setStatusError("");
  }

  function closeStatusModal() {
    if (statusSaving) {
      return;
    }

    setStatusCustomer(null);
    setStatusError("");
  }

  async function submitStatusChange() {
    setStatusSaving(true);
    setStatusError("");

    try {
      await updateCustomerStatus(
        statusCustomer.id,
        !statusCustomer.is_active,
      );

      showToast(
        statusCustomer.is_active
          ? "Customer deactivated."
          : "Customer activated.",
      );

      setStatusCustomer(null);

      await loadCustomers();
    } catch (error) {
      setStatusError(
        error.message ??
          "Customer status could not be changed.",
      );
    } finally {
      setStatusSaving(false);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-teal-700">
            Customer records
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Customers
          </h1>

          <p className="mt-2 text-slate-500">
            Manage customer details and review their activity.
          </p>
        </div>

        <Button onClick={openCreateModal}>
          Add customer
        </Button>
      </div>

      <div className="mb-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-[1fr_auto] sm:items-end">
        <div>
          <label
            htmlFor="customerSearch"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            Search customers
          </label>

          <input
            id="customerSearch"
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            className="form-input"
            placeholder="Search by name, phone or email"
          />
        </div>

        <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(event) =>
              setIncludeInactive(
                event.target.checked,
              )
            }
            className="h-4 w-4 rounded border-slate-300 text-teal-600"
          />

          Include inactive
        </label>
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
            label="Loading customers"
          />
        </div>
      ) : customers.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <h2 className="text-lg font-bold text-slate-900">
            No customers found
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Add a customer or change the search filter.
          </p>

          <Button
            onClick={openCreateModal}
            className="mt-6"
          >
            Add customer
          </Button>
        </div>
      ) : (
        <div className="grid gap-5 xl:grid-cols-2">
          {customers.map((customer) => (
            <article
              key={customer.id}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-bold text-slate-900">
                      {customer.full_name}
                    </h2>

                    <StatusBadge
                      status={
                        customer.is_active
                          ? "ACTIVE"
                          : "INACTIVE"
                      }
                    />
                  </div>

                  <p className="mt-2 text-sm text-slate-600">
                    {customer.phone}
                  </p>

                  {customer.email && (
                    <p className="mt-1 text-sm text-slate-500">
                      {customer.email}
                    </p>
                  )}
                </div>

                <div className="flex flex-wrap justify-end gap-2">
                  <Button
                    variant="secondary"
                    onClick={() =>
                      openDetailModal(customer)
                    }
                  >
                    View
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={() =>
                      openEditModal(customer)
                    }
                  >
                    Edit
                  </Button>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Reservations
                  </p>

                  <p className="mt-1 text-xl font-bold text-slate-900">
                    {customer.reservation_count}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Orders
                  </p>

                  <p className="mt-1 text-xl font-bold text-slate-900">
                    {customer.order_count}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Completed
                  </p>

                  <p className="mt-1 text-xl font-bold text-slate-900">
                    {customer.completed_order_count}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Paid
                  </p>

                  <p className="mt-1 font-bold text-slate-900">
                    {formatCurrency(
                      customer.total_paid_spending,
                    )}
                  </p>
                </div>
              </div>

              {customer.address && (
                <p className="mt-4 text-sm text-slate-600">
                  <strong>Address:</strong>{" "}
                  {customer.address}
                </p>
              )}

              {customer.notes && (
                <p className="mt-2 text-sm text-slate-600">
                  <strong>Notes:</strong>{" "}
                  {customer.notes}
                </p>
              )}

              <div className="mt-5 border-t border-slate-200 pt-4">
                <Button
                  variant={
                    customer.is_active
                      ? "danger"
                      : "secondary"
                  }
                  onClick={() =>
                    openStatusModal(customer)
                  }
                >
                  {customer.is_active
                    ? "Deactivate"
                    : "Activate"}
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        open={formModalOpen}
        title={
          editingCustomer
            ? "Edit customer"
            : "Add customer"
        }
        onClose={closeFormModal}
        maxWidth="max-w-2xl"
      >
        <form
          onSubmit={submitCustomer}
          className="space-y-5"
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              label="Full name"
              name="full_name"
              required
            >
              <input
                id="full_name"
                name="full_name"
                type="text"
                value={customerForm.full_name}
                onChange={updateFormField}
                className="form-input"
              />
            </FormField>

            <FormField
              label="Phone"
              name="phone"
              required
            >
              <input
                id="phone"
                name="phone"
                type="tel"
                value={customerForm.phone}
                onChange={updateFormField}
                className="form-input"
              />
            </FormField>
          </div>

          <FormField
            label="Email"
            name="email"
          >
            <input
              id="email"
              name="email"
              type="email"
              value={customerForm.email}
              onChange={updateFormField}
              className="form-input"
            />
          </FormField>

          <FormField
            label="Address"
            name="address"
          >
            <textarea
              id="address"
              name="address"
              rows="3"
              value={customerForm.address}
              onChange={updateFormField}
              className="form-input resize-none"
            />
          </FormField>

          <FormField
            label="Notes"
            name="notes"
          >
            <textarea
              id="notes"
              name="notes"
              rows="3"
              value={customerForm.notes}
              onChange={updateFormField}
              className="form-input resize-none"
            />
          </FormField>

          <label className="flex items-center gap-3 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700">
            <input
              type="checkbox"
              name="is_active"
              checked={customerForm.is_active}
              onChange={updateFormField}
              className="h-4 w-4 rounded border-slate-300 text-teal-600"
            />

            Customer is active
          </label>

          {formError && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {formError}
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={closeFormModal}
              disabled={formSaving}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              loading={formSaving}
            >
              {editingCustomer
                ? "Save changes"
                : "Create customer"}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={
          detailLoading ||
          Boolean(detailCustomer) ||
          Boolean(detailError)
        }
        title="Customer activity"
        onClose={closeDetailModal}
        maxWidth="max-w-5xl"
      >
        {detailLoading ? (
          <div className="flex min-h-48 items-center justify-center">
            <Spinner
              size="lg"
              label="Loading customer activity"
            />
          </div>
        ) : detailError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {detailError}
          </div>
        ) : detailCustomer ? (
          <div className="space-y-6">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-xl font-bold text-slate-900">
                  {detailCustomer.full_name}
                </h2>

                <StatusBadge
                  status={
                    detailCustomer.is_active
                      ? "ACTIVE"
                      : "INACTIVE"
                  }
                />
              </div>

              <p className="mt-2 text-sm text-slate-600">
                {detailCustomer.phone}
              </p>

              {detailCustomer.email && (
                <p className="mt-1 text-sm text-slate-500">
                  {detailCustomer.email}
                </p>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                [
                  "Reservations",
                  detailCustomer.reservation_count,
                ],
                [
                  "Orders",
                  detailCustomer.order_count,
                ],
                [
                  "Completed orders",
                  detailCustomer.completed_order_count,
                ],
                [
                  "Paid spending",
                  formatCurrency(
                    detailCustomer.total_paid_spending,
                  ),
                ],
              ].map(([label, value]) => (
                <article
                  key={label}
                  className="rounded-xl bg-slate-50 p-4"
                >
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    {label}
                  </p>

                  <p className="mt-2 text-xl font-bold text-slate-900">
                    {value}
                  </p>
                </article>
              ))}
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Recent reservations
              </h3>

              {detailCustomer.reservations.length ===
              0 ? (
                <p className="mt-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                  No reservation activity.
                </p>
              ) : (
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[650px] text-left">
                    <thead>
                      <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                        <th className="pb-3">
                          Reservation
                        </th>
                        <th className="pb-3">
                          Table
                        </th>
                        <th className="pb-3">
                          Guests
                        </th>
                        <th className="pb-3">
                          Time
                        </th>
                        <th className="pb-3">
                          Status
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {detailCustomer.reservations.map(
                        (reservation) => (
                          <tr
                            key={reservation.id}
                            className="border-b border-slate-100"
                          >
                            <td className="py-3 font-semibold text-slate-900">
                              {
                                reservation.reservation_number
                              }
                            </td>

                            <td className="py-3 text-sm text-slate-600">
                              {reservation.table_number}
                            </td>

                            <td className="py-3 text-sm text-slate-600">
                              {reservation.guest_count}
                            </td>

                            <td className="py-3 text-sm text-slate-600">
                              {formatDateTime(
                                reservation.start_time,
                              )}
                            </td>

                            <td className="py-3">
                              <StatusBadge
                                status={
                                  reservation.status
                                }
                              />
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Recent orders
              </h3>

              {detailCustomer.orders.length === 0 ? (
                <p className="mt-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                  No order activity.
                </p>
              ) : (
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[650px] text-left">
                    <thead>
                      <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                        <th className="pb-3">
                          Order
                        </th>
                        <th className="pb-3">
                          Type
                        </th>
                        <th className="pb-3">
                          Status
                        </th>
                        <th className="pb-3">
                          Invoice
                        </th>
                        <th className="pb-3 text-right">
                          Total
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {detailCustomer.orders.map(
                        (order) => (
                          <tr
                            key={order.id}
                            className="border-b border-slate-100"
                          >
                            <td className="py-3">
                              <p className="font-semibold text-slate-900">
                                {order.order_number}
                              </p>

                              <p className="mt-1 text-xs text-slate-500">
                                {formatDateTime(
                                  order.created_at,
                                )}
                              </p>
                            </td>

                            <td className="py-3 text-sm text-slate-600">
                              {humaniseValue(
                                order.order_type,
                              )}
                            </td>

                            <td className="py-3">
                              <StatusBadge
                                status={order.status}
                              />
                            </td>

                            <td className="py-3 text-sm text-slate-600">
                              {order.invoice_number ??
                                "Not generated"}
                            </td>

                            <td className="py-3 text-right font-semibold text-slate-900">
                              {order.grand_total
                                ? formatCurrency(
                                    order.grand_total,
                                  )
                                : "—"}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Modal>

      <Modal
        open={Boolean(statusCustomer)}
        title={
          statusCustomer?.is_active
            ? "Deactivate customer"
            : "Activate customer"
        }
        onClose={closeStatusModal}
      >
        {statusCustomer && (
          <div className="space-y-5">
            <p className="text-sm text-slate-600">
              {statusCustomer.is_active
                ? `Deactivate ${statusCustomer.full_name}? They will remain in previous orders and reservations.`
                : `Activate ${statusCustomer.full_name}?`}
            </p>

            {statusError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {statusError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={closeStatusModal}
                disabled={statusSaving}
              >
                Cancel
              </Button>

              <Button
                variant={
                  statusCustomer.is_active
                    ? "danger"
                    : "primary"
                }
                loading={statusSaving}
                onClick={submitStatusChange}
              >
                Confirm
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </section>
  );
}