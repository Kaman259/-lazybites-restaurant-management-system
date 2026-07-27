import { useCallback, useEffect, useState } from "react";

import {
  getAllReservations,
  updateReservationStatus,
} from "../../api/reservationsApi";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../context/ToastContext";

const statuses = [
  "",
  "PENDING",
  "CONFIRMED",
  "SEATED",
  "COMPLETED",
  "CANCELLED",
  "NO_SHOW",
];

const statusActions = {
  PENDING: ["CONFIRMED", "CANCELLED"],
  CONFIRMED: ["SEATED", "CANCELLED", "NO_SHOW"],
  SEATED: ["COMPLETED"],
  COMPLETED: [],
  CANCELLED: [],
  NO_SHOW: [],
};

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function ReservationsPage() {
  const { showToast } = useToast();

  const [reservations, setReservations] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [selectedReservation, setSelectedReservation] =
    useState(null);
  const [selectedStatus, setSelectedStatus] = useState("");
  const [cancellationReason, setCancellationReason] =
    useState("");
  const [updating, setUpdating] = useState(false);
  const [modalError, setModalError] = useState("");

  const loadReservations = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const reservationData =
        await getAllReservations(statusFilter);

      setReservations(reservationData);
    } catch (error) {
      setPageError(
        error.message ?? "Reservations could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadReservations();
  }, [loadReservations]);

  function openStatusModal(reservation, newStatus) {
    setSelectedReservation(reservation);
    setSelectedStatus(newStatus);
    setCancellationReason("");
    setModalError("");
  }

  function closeStatusModal() {
    if (updating) {
      return;
    }

    setSelectedReservation(null);
    setSelectedStatus("");
    setCancellationReason("");
    setModalError("");
  }

  async function submitStatusUpdate(event) {
    event.preventDefault();

    if (
      selectedStatus === "CANCELLED" &&
      !cancellationReason.trim()
    ) {
      setModalError("Enter a cancellation reason.");
      return;
    }

    setUpdating(true);
    setModalError("");

    try {
      await updateReservationStatus(
        selectedReservation.id,
        selectedStatus,
        cancellationReason.trim(),
      );

      showToast("Reservation status updated.");
      closeStatusModal();
      await loadReservations();
    } catch (error) {
      setModalError(
        error.message ??
          "The reservation status could not be updated.",
      );
    } finally {
      setUpdating(false);
    }
  }

  return (
    <section>
      <div className="mb-7">
        <p className="text-sm font-semibold text-teal-700">
          Guest bookings
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Reservations
        </h1>

        <p className="mt-2 text-slate-500">
          Confirm bookings, seat guests and complete reservations.
        </p>
      </div>

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4">
        <label
          htmlFor="reservationStatus"
          className="mb-2 block text-sm font-semibold text-slate-700"
        >
          Filter by status
        </label>

        <select
          id="reservationStatus"
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
          className="form-input max-w-xs"
        >
          {statuses.map((status) => (
            <option key={status || "ALL"} value={status}>
              {status
                ? status.replaceAll("_", " ")
                : "All reservations"}
            </option>
          ))}
        </select>
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner size="lg" label="Loading reservations" />
        </div>
      ) : reservations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <h2 className="text-lg font-bold text-slate-900">
            No reservations found
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Reservations matching the selected status will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {reservations.map((reservation) => (
            <article
              key={reservation.id}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-bold text-slate-900">
                      {reservation.reservation_number}
                    </h2>

                    <StatusBadge status={reservation.status} />
                  </div>

                  <p className="mt-2 text-sm text-slate-500">
                    Created for {reservation.customer.full_name}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {(statusActions[reservation.status] ?? []).map(
                    (status) => (
                      <Button
                        key={status}
                        variant={
                          status === "CANCELLED"
                            ? "danger"
                            : "secondary"
                        }
                        onClick={() =>
                          openStatusModal(reservation, status)
                        }
                      >
                        Mark {status.replaceAll("_", " ").toLowerCase()}
                      </Button>
                    ),
                  )}
                </div>
              </div>

              <div className="mt-5 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2 xl:grid-cols-5">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Date and time
                  </p>
                  <p className="mt-1 font-semibold text-slate-900">
                    {formatDateTime(reservation.start_time)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Table
                  </p>
                  <p className="mt-1 font-semibold text-slate-900">
                    {reservation.table.table_number}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Area
                  </p>
                  <p className="mt-1 font-semibold text-slate-900">
                    {reservation.table.area}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Guests
                  </p>
                  <p className="mt-1 font-semibold text-slate-900">
                    {reservation.guest_count}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Phone
                  </p>
                  <p className="mt-1 font-semibold text-slate-900">
                    {reservation.customer.phone}
                  </p>
                </div>
              </div>

              {reservation.notes && (
                <p className="mt-4 text-sm leading-6 text-slate-600">
                  <span className="font-semibold text-slate-800">
                    Guest note:
                  </span>{" "}
                  {reservation.notes}
                </p>
              )}

              {reservation.cancellation_reason && (
                <p className="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
                  Cancellation reason:{" "}
                  {reservation.cancellation_reason}
                </p>
              )}
            </article>
          ))}
        </div>
      )}

      <Modal
        open={Boolean(selectedReservation)}
        title="Update reservation status"
        onClose={closeStatusModal}
      >
        {selectedReservation && (
          <form
            onSubmit={submitStatusUpdate}
            className="space-y-5"
          >
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">
                Reservation
              </p>

              <p className="mt-1 font-bold text-slate-900">
                {selectedReservation.reservation_number}
              </p>

              <p className="mt-2 text-sm text-slate-600">
                Change status to{" "}
                <strong>
                  {selectedStatus.replaceAll("_", " ")}
                </strong>
              </p>
            </div>

            {selectedStatus === "CANCELLED" && (
              <div>
                <label
                  htmlFor="staffCancellationReason"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Cancellation reason
                </label>

                <textarea
                  id="staffCancellationReason"
                  rows="3"
                  value={cancellationReason}
                  onChange={(event) => {
                    setCancellationReason(event.target.value);
                    setModalError("");
                  }}
                  className="form-input resize-none"
                  placeholder="Reason for cancelling"
                />
              </div>
            )}

            {modalError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {modalError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={closeStatusModal}
                disabled={updating}
              >
                Close
              </Button>

              <Button
                type="submit"
                loading={updating}
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