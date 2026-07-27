import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createReservation,
  searchAvailableTables,
} from "../../api/reservationsApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Spinner from "../../components/common/Spinner";
import { useToast } from "../../context/ToastContext";

function createInitialSearchForm() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);

  const date = tomorrow.toISOString().slice(0, 10);

  return {
    date,
    startTime: "19:00",
    duration: "2",
    guestCount: "2",
  };
}

function buildReservationTimes(formData) {
  const startDateTime = new Date(
    `${formData.date}T${formData.startTime}:00`,
  );

  const endDateTime = new Date(
    startDateTime.getTime() +
      Number(formData.duration) * 60 * 60 * 1000,
  );

  return {
    start_time: startDateTime.toISOString(),
    end_time: endDateTime.toISOString(),
  };
}

export default function BookTablePage() {
  const { showToast } = useToast();
  const redirect = useNavigate();

  const [formData, setFormData] = useState(
    createInitialSearchForm,
  );
  const [availableTables, setAvailableTables] = useState([]);
  const [searched, setSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [selectedTableId, setSelectedTableId] =
    useState(null);
  const [notes, setNotes] = useState("");
  const [booking, setBooking] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;

    setFormData((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));

    setSearchError("");
    setSearched(false);
    setAvailableTables([]);
    setSelectedTableId(null);
  }

  async function handleSearch(event) {
    event.preventDefault();

    const guestCount = Number(formData.guestCount);
    const duration = Number(formData.duration);

    if (!formData.date || !formData.startTime) {
      setSearchError("Choose the reservation date and time.");
      return;
    }

    if (!Number.isInteger(guestCount) || guestCount < 1) {
      setSearchError("Guest count must be at least 1.");
      return;
    }

    if (!Number.isFinite(duration) || duration <= 0) {
      setSearchError("Choose a valid reservation duration.");
      return;
    }

    const { start_time, end_time } =
      buildReservationTimes(formData);

    if (new Date(start_time) <= new Date()) {
      setSearchError("Choose a future reservation time.");
      return;
    }

    setSearching(true);
    setSearchError("");
    setSelectedTableId(null);

    try {
      const tableData = await searchAvailableTables({
        start_time,
        end_time,
        guest_count: guestCount,
      });

      setAvailableTables(tableData);
      setSearched(true);
    } catch (error) {
      setSearchError(
        error.message ?? "Available tables could not be loaded.",
      );
    } finally {
      setSearching(false);
    }
  }

  async function handleBooking() {
    if (!selectedTableId) {
      setSearchError("Select one available table.");
      return;
    }

    const { start_time, end_time } =
      buildReservationTimes(formData);

    setBooking(true);
    setSearchError("");

    try {
      await createReservation({
        table_id: selectedTableId,
        start_time,
        end_time,
        guest_count: Number(formData.guestCount),
        notes: notes.trim() || null,
      });

      showToast(
        "Reservation created. The restaurant will confirm it shortly.",
      );

      redirect("/customer/reservations", {
        replace: true,
      });
    } catch (error) {
      setSearchError(
        error.message ?? "The reservation could not be created.",
      );
    } finally {
      setBooking(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-3xl border border-teal-100 bg-white p-6">
        <p className="text-sm font-semibold text-teal-700">
          Find a table
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Book your table
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Select the date, time and number of guests to see free
          tables.
        </p>

        <form onSubmit={handleSearch} className="mt-7 space-y-5">
          <FormField label="Date" name="date" required>
            <input
              id="date"
              name="date"
              type="date"
              value={formData.date}
              onChange={updateField}
              min={new Date().toISOString().slice(0, 10)}
              className="form-input"
            />
          </FormField>

          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              label="Start time"
              name="startTime"
              required
            >
              <input
                id="startTime"
                name="startTime"
                type="time"
                value={formData.startTime}
                onChange={updateField}
                className="form-input"
              />
            </FormField>

            <FormField
              label="Duration"
              name="duration"
              required
            >
              <select
                id="duration"
                name="duration"
                value={formData.duration}
                onChange={updateField}
                className="form-input"
              >
                <option value="1">1 hour</option>
                <option value="1.5">1 hour 30 minutes</option>
                <option value="2">2 hours</option>
                <option value="2.5">2 hours 30 minutes</option>
                <option value="3">3 hours</option>
              </select>
            </FormField>
          </div>

          <FormField
            label="Number of guests"
            name="guestCount"
            required
          >
            <input
              id="guestCount"
              name="guestCount"
              type="number"
              min="1"
              max="100"
              value={formData.guestCount}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <Button
            type="submit"
            loading={searching}
            className="w-full"
          >
            Check availability
          </Button>
        </form>
      </div>

      <div className="rounded-3xl border border-teal-100 bg-white p-6">
        <p className="text-sm font-semibold text-teal-700">
          Available seating
        </p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">
          Select a table
        </h2>

        {searchError && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {searchError}
          </div>
        )}

        {searching ? (
          <div className="flex min-h-72 items-center justify-center">
            <Spinner size="lg" label="Searching available tables" />
          </div>
        ) : !searched ? (
          <div className="mt-6 flex min-h-72 items-center justify-center rounded-2xl bg-teal-50 px-6 text-center">
            <div>
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white text-2xl font-black text-teal-700">
                L
              </div>

              <p className="mt-4 font-semibold text-slate-800">
                Choose your reservation details
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Free tables will appear here.
              </p>
            </div>
          </div>
        ) : availableTables.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 px-6 py-14 text-center">
            <p className="font-semibold text-slate-800">
              No suitable table is free
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Try another time, shorter duration or smaller guest count.
            </p>
          </div>
        ) : (
          <>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {availableTables.map((table) => {
                const selected = selectedTableId === table.id;

                return (
                  <button
                    key={table.id}
                    type="button"
                    onClick={() => setSelectedTableId(table.id)}
                    className={`rounded-2xl border p-5 text-left transition ${
                      selected
                        ? "border-teal-600 bg-teal-50 ring-2 ring-teal-100"
                        : "border-slate-200 hover:border-teal-300"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm text-slate-500">
                          Table
                        </p>

                        <p className="mt-1 text-2xl font-bold text-slate-900">
                          {table.table_number}
                        </p>
                      </div>

                      <span
                        className={`flex h-6 w-6 items-center justify-center rounded-full border ${
                          selected
                            ? "border-teal-600 bg-teal-600 text-white"
                            : "border-slate-300"
                        }`}
                      >
                        {selected ? "✓" : ""}
                      </span>
                    </div>

                    <p className="mt-4 text-sm font-semibold text-slate-700">
                      {table.area}
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      Seats up to {table.capacity} guests
                    </p>

                    {table.description && (
                      <p className="mt-3 text-sm leading-6 text-slate-500">
                        {table.description}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-6">
              <FormField
                label="Special note"
                name="reservationNotes"
                helperText="Optional. Example: birthday dinner or wheelchair access."
              >
                <textarea
                  id="reservationNotes"
                  rows="3"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  className="form-input resize-none"
                  placeholder="Add a note for the restaurant"
                />
              </FormField>
            </div>

            <Button
              onClick={handleBooking}
              loading={booking}
              disabled={!selectedTableId}
              className="mt-6 w-full"
            >
              Confirm reservation
            </Button>
          </>
        )}
      </div>
    </section>
  );
}