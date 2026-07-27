import { useCallback, useEffect, useState } from "react";

import {
  cancelReservation,
  getMyReservations,
} from "../../api/reservationsApi";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../context/ToastContext";

const cancellableStatuses = ["PENDING", "CONFIRMED"];

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function MyReservationsPage() {
  const { showToast } = useToast();

  const [reservations, setReservations] = useState([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [selectedReservation, setSelectedReservation] =
    useState(null);
  const [cancellationReason, setCancellationReason] =
    useState("");
  const [cancelling, setCancelling] = useState(false);
  const [modalError, setModalError] = useState("");

  const loadReservations = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const reservationData = await getMyReservations();
      setReservations(reservationData);
    } catch (error) {
      setPageError(
        error.message ?? "Your reservations could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReservations();
  }, [loadReservations]);

  function openCancelModal(reservation) {
    setSelectedReservation(reservation);
    setCancellationReason("");
    setModalError("");
  }

  function closeCancelModal() {
    if (cancelling) {
      return;
    }

    setSelectedReservation(null);
    setCancellationReason("");
    setModalError("");
  }

  async function submitCancellation(event) {
    event.preventDefault();

    setCancelling(true);
    setModalError("");

    try {
      await cancelReservation(
        selectedReservation.id,
        cancellationReason.trim(),
      );

      showToast("Reservation cancelled.");
      closeCancelModal();
      await loadReservations();
    } catch (error) {
      setModalError(
        error.message ??
          "The reservation could not be cancelled.",
      );
    } finally {
      setCancelling(false);
    }
  }

  return (
    <section>
      <div className="mb-7">
        <p className="text-sm font-semibold text-teal-700">
          Your bookings
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          My reservations
        </h1>

        <p className="mt-2 text-slate-500">
          Check confirmation status and cancel eligible bookings.
        </p>
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner size="lg" label="Loading your reservations" />
        </div>
      ) : reservations.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-teal-200 bg-white px-6 py-16 text-center">
          <h2 className="text-xl font-bold text-slate-900">
            No reservations yet
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Book a table and your reservation will appear here.
          </p>

          <a
            href="/customer/book-table"
            className="mt-6 inline-flex rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white hover:bg-teal-700"
          >
            Book a table
          </a>
        </div>
      ) : (
        <div className="space-y-5">
          {reservations.map((reservation) => {
            const canCancel =
              cancellableStatuses.includes(reservation.status) &&
              new Date(reservation.start_time) > new Date();

            return (
              <article
                key={reservation.id}
                className="rounded-3xl border border-teal-100 bg-white p-6"
              >
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-lg font-bold text-slate-900">
                        {reservation.reservation_number}
                      </h2>

                      <StatusBadge status={reservation.status} />
                    </div>

                    <p className="mt-2 text-sm text-slate-500">
                      Created on{" "}
                      {formatDateTime(reservation.start_time)}
                    </p>
                  </div>

                  {canCancel && (
                    <Button
                      variant="danger"
                      onClick={() =>
                        openCancelModal(reservation)
                      }
                    >
                      Cancel reservation
                    </Button>
                  )}
                </div>

                <div className="mt-5 grid gap-4 rounded-2xl bg-[#f6fbfa] p-5 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Table
                    </p>

                    <p className="mt-1 font-bold text-slate-900">
                      {reservation.table.table_number}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Area
                    </p>

                    <p className="mt-1 font-bold text-slate-900">
                      {reservation.table.area}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Guests
                    </p>

                    <p className="mt-1 font-bold text-slate-900">
                      {reservation.guest_count}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Ends
                    </p>

                    <p className="mt-1 font-bold text-slate-900">
                      {formatDateTime(reservation.end_time)}
                    </p>
                  </div>
                </div>

                {reservation.notes && (
                  <p className="mt-4 text-sm leading-6 text-slate-600">
                    <span className="font-semibold text-slate-800">
                      Your note:
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
            );
          })}
        </div>
      )}

      <Modal
        open={Boolean(selectedReservation)}
        title="Cancel reservation"
        onClose={closeCancelModal}
      >
        {selectedReservation && (
          <form
            onSubmit={submitCancellation}
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
                {formatDateTime(selectedReservation.start_time)}
              </p>
            </div>

            <div>
              <label
                htmlFor="customerCancellationReason"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Reason
              </label>

              <textarea
                id="customerCancellationReason"
                rows="3"
                value={cancellationReason}
                onChange={(event) => {
                  setCancellationReason(event.target.value);
                  setModalError("");
                }}
                className="form-input resize-none"
                placeholder="Optional reason for cancellation"
              />
            </div>

            {modalError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {modalError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={closeCancelModal}
                disabled={cancelling}
              >
                Keep reservation
              </Button>

              <Button
                type="submit"
                variant="danger"
                loading={cancelling}
              >
                Confirm cancellation
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
}