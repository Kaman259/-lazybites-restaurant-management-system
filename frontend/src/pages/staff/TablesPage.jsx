import { useCallback, useEffect, useState } from "react";

import {
  createDiningTable,
  deleteDiningTable,
  getDiningTables,
  updateDiningTable,
} from "../../api/tablesApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

const emptyTableForm = {
  table_number: "",
  capacity: "2",
  area: "",
  description: "",
  is_active: true,
};

export default function TablesPage() {
  const { role } = useAuth();
  const { showToast } = useToast();

  const [tables, setTables] = useState([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [includeInactive, setIncludeInactive] = useState(true);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTable, setEditingTable] = useState(null);
  const [formData, setFormData] = useState(emptyTableForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const isAdmin = role === "ADMIN";

  const loadTables = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const tableData = await getDiningTables(includeInactive);
      setTables(tableData);
    } catch (error) {
      setPageError(
        error.message ?? "Dining tables could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [includeInactive]);

  useEffect(() => {
    loadTables();
  }, [loadTables]);

  function openCreateModal() {
    setEditingTable(null);
    setFormData(emptyTableForm);
    setFormError("");
    setModalOpen(true);
  }

  function openEditModal(table) {
    setEditingTable(table);
    setFormData({
      table_number: table.table_number,
      capacity: String(table.capacity),
      area: table.area,
      description: table.description ?? "",
      is_active: table.is_active,
    });
    setFormError("");
    setModalOpen(true);
  }

  function closeModal() {
    if (saving) {
      return;
    }

    setModalOpen(false);
    setEditingTable(null);
    setFormData(emptyTableForm);
    setFormError("");
  }

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setFormData((currentForm) => ({
      ...currentForm,
      [name]: type === "checkbox" ? checked : value,
    }));

    setFormError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!formData.table_number.trim()) {
      setFormError("Table number is required.");
      return;
    }

    if (!formData.area.trim()) {
      setFormError("Area is required.");
      return;
    }

    const capacity = Number(formData.capacity);

    if (!Number.isInteger(capacity) || capacity < 1) {
      setFormError("Capacity must be at least 1.");
      return;
    }

    const payload = {
      table_number: formData.table_number.trim(),
      capacity,
      area: formData.area.trim(),
      description: formData.description.trim() || null,
      is_active: formData.is_active,
    };

    setSaving(true);
    setFormError("");

    try {
      if (editingTable) {
        await updateDiningTable(editingTable.id, payload);
        showToast("Dining table updated.");
      } else {
        await createDiningTable(payload);
        showToast("Dining table created.");
      }

      closeModal();
      await loadTables();
    } catch (error) {
      setFormError(
        error.message ?? "The dining table could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(table) {
    const confirmed = window.confirm(
      `Delete table ${table.table_number}? This works only when the table has no reservation or order history.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteDiningTable(table.id);
      showToast("Dining table deleted.");
      await loadTables();
    } catch (error) {
      showToast(
        error.message ?? "The dining table could not be deleted.",
        "error",
      );
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-teal-700">
            Restaurant floor
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Dining tables
          </h1>

          <p className="mt-2 text-slate-500">
            Manage table numbers, seating capacity and restaurant areas.
          </p>
        </div>

        {isAdmin && (
          <Button onClick={openCreateModal}>
            Add dining table
          </Button>
        )}
      </div>

      <div className="mb-5 flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-4">
        <div>
          <p className="font-semibold text-slate-900">
            Show inactive tables
          </p>

          <p className="text-sm text-slate-500">
            Disabled tables cannot appear in customer availability.
          </p>
        </div>

        <label className="relative inline-flex cursor-pointer items-center">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(event) =>
              setIncludeInactive(event.target.checked)
            }
            className="peer sr-only"
          />

          <span className="h-6 w-11 rounded-full bg-slate-300 transition peer-checked:bg-teal-600" />

          <span className="absolute left-1 h-4 w-4 rounded-full bg-white transition peer-checked:translate-x-5" />
        </label>
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner size="lg" label="Loading dining tables" />
        </div>
      ) : tables.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <h2 className="text-lg font-bold text-slate-900">
            No dining tables added
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Add the restaurant tables before customers can make
            reservations.
          </p>

          {isAdmin && (
            <Button
              onClick={openCreateModal}
              className="mt-6"
            >
              Add first table
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {tables.map((table) => (
            <article
              key={table.id}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-500">
                    Table number
                  </p>

                  <h2 className="mt-1 text-2xl font-bold text-slate-900">
                    {table.table_number}
                  </h2>
                </div>

                <StatusBadge
                  status={table.is_active ? "ACTIVE" : "INACTIVE"}
                />
              </div>

              <dl className="mt-5 space-y-3">
                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-slate-500">Capacity</dt>
                  <dd className="font-semibold text-slate-900">
                    {table.capacity} guests
                  </dd>
                </div>

                <div className="flex justify-between gap-4">
                  <dt className="text-sm text-slate-500">Area</dt>
                  <dd className="text-right font-semibold text-slate-900">
                    {table.area}
                  </dd>
                </div>
              </dl>

              {table.description && (
                <p className="mt-4 rounded-xl bg-slate-50 px-3 py-3 text-sm leading-6 text-slate-600">
                  {table.description}
                </p>
              )}

              {isAdmin && (
                <div className="mt-5 flex gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => openEditModal(table)}
                    className="flex-1"
                  >
                    Edit
                  </Button>

                  <Button
                    variant="danger"
                    onClick={() => handleDelete(table)}
                  >
                    Delete
                  </Button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        title={editingTable ? "Edit dining table" : "Add dining table"}
        onClose={closeModal}
      >
        {formError && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <FormField
            label="Table number"
            name="table_number"
            required
          >
            <input
              id="table_number"
              name="table_number"
              value={formData.table_number}
              onChange={updateField}
              placeholder="Example: T-01"
              className="form-input"
            />
          </FormField>

          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              label="Capacity"
              name="capacity"
              required
            >
              <input
                id="capacity"
                name="capacity"
                type="number"
                min="1"
                max="100"
                value={formData.capacity}
                onChange={updateField}
                className="form-input"
              />
            </FormField>

            <FormField
              label="Area"
              name="area"
              required
            >
              <input
                id="area"
                name="area"
                value={formData.area}
                onChange={updateField}
                placeholder="Main Hall"
                className="form-input"
              />
            </FormField>
          </div>

          <FormField
            label="Description"
            name="description"
          >
            <textarea
              id="description"
              name="description"
              rows="3"
              value={formData.description}
              onChange={updateField}
              placeholder="Near the window"
              className="form-input resize-none"
            />
          </FormField>

          <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
            <div>
              <p className="font-semibold text-slate-900">
                Active table
              </p>

              <p className="text-sm text-slate-500">
                Active tables can be reserved by customers.
              </p>
            </div>

            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={updateField}
              className="h-5 w-5 rounded border-slate-300 text-teal-600"
            />
          </label>

          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={closeModal}
              disabled={saving}
            >
              Cancel
            </Button>

            <Button type="submit" loading={saving}>
              {editingTable ? "Save changes" : "Create table"}
            </Button>
          </div>
        </form>
      </Modal>
    </section>
  );
}