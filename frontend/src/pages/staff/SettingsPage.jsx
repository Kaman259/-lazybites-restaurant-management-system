import { useEffect, useState } from "react";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Spinner from "../../components/common/Spinner";
import { useToast } from "../../context/ToastContext";
import {
  getBackendAssetUrl,
  getRestaurantSettings,
  updateRestaurantSettings,
  uploadRestaurantLogo,
} from "../../api/settingsApi";

const emptyForm = {
  restaurant_name: "",
  address: "",
  phone: "",
  email: "",
  gstin: "",
  default_gst_percentage: "5.00",
  currency: "INR",
  invoice_prefix: "INV",
  receipt_footer: "",
  timezone: "Asia/Kolkata",
};

export default function SettingsPage() {
  const { showToast } = useToast();

  const [formData, setFormData] = useState(emptyForm);
  const [logoPath, setLogoPath] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    async function loadSettings() {
      try {
        const settingsData = await getRestaurantSettings();

        setFormData({
          restaurant_name: settingsData.restaurant_name,
          address: settingsData.address,
          phone: settingsData.phone,
          email: settingsData.email ?? "",
          gstin: settingsData.gstin ?? "",
          default_gst_percentage:
            settingsData.default_gst_percentage,
          currency: settingsData.currency,
          invoice_prefix: settingsData.invoice_prefix,
          receipt_footer: settingsData.receipt_footer ?? "",
          timezone: settingsData.timezone,
        });

        setLogoPath(settingsData.logo_path ?? "");
      } catch (error) {
        setPageError(
          error.message ?? "Restaurant settings could not be loaded.",
        );
      } finally {
        setPageLoading(false);
      }
    }

    loadSettings();
  }, []);

  function updateField(event) {
    const { name, value } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }));

    setPageError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setSaving(true);
    setPageError("");

    try {
      const updatedSettings =
        await updateRestaurantSettings({
          ...formData,
          email: formData.email.trim() || null,
          gstin: formData.gstin.trim() || null,
          receipt_footer:
            formData.receipt_footer.trim() || null,
          default_gst_percentage:
            formData.default_gst_percentage,
        });

      setFormData({
        restaurant_name: updatedSettings.restaurant_name,
        address: updatedSettings.address,
        phone: updatedSettings.phone,
        email: updatedSettings.email ?? "",
        gstin: updatedSettings.gstin ?? "",
        default_gst_percentage:
          updatedSettings.default_gst_percentage,
        currency: updatedSettings.currency,
        invoice_prefix: updatedSettings.invoice_prefix,
        receipt_footer:
          updatedSettings.receipt_footer ?? "",
        timezone: updatedSettings.timezone,
      });

      showToast("Restaurant settings saved.");
    } catch (error) {
      setPageError(
        error.message ?? "Restaurant settings could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleLogoChange(event) {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    setUploadingLogo(true);
    setPageError("");

    try {
      const updatedSettings =
        await uploadRestaurantLogo(selectedFile);

      setLogoPath(updatedSettings.logo_path ?? "");
      showToast("Restaurant logo updated.");
    } catch (error) {
      setPageError(
        error.message ?? "The restaurant logo could not be uploaded.",
      );
    } finally {
      setUploadingLogo(false);
      event.target.value = "";
    }
  }

  if (pageLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner size="lg" label="Loading restaurant settings" />
      </div>
    );
  }

  return (
    <section className="max-w-5xl">
      <div className="mb-8">
        <p className="text-sm font-semibold text-teal-700">
          Administration
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Restaurant settings
        </h1>

        <p className="mt-2 text-slate-500">
          These details will later appear on invoices and receipts.
        </p>
      </div>

      {pageError && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-bold text-slate-900">
          Restaurant logo
        </h2>

        <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-center">
          <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            {logoPath ? (
              <img
                src={getBackendAssetUrl(logoPath)}
                alt="Restaurant logo"
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="text-3xl font-black text-teal-700">
                L
              </span>
            )}
          </div>

          <div>
            <label className="inline-flex cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              {uploadingLogo ? "Uploading..." : "Choose logo"}

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleLogoChange}
                disabled={uploadingLogo}
                className="hidden"
              />
            </label>

            <p className="mt-2 text-sm text-slate-500">
              JPG, PNG or WebP. Maximum 5 MB.
            </p>
          </div>
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-slate-200 bg-white p-6"
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <FormField
              label="Restaurant name"
              name="restaurant_name"
              required
            >
              <input
                id="restaurant_name"
                name="restaurant_name"
                value={formData.restaurant_name}
                onChange={updateField}
                className="form-input"
              />
            </FormField>
          </div>

          <div className="sm:col-span-2">
            <FormField
              label="Address"
              name="address"
              required
            >
              <textarea
                id="address"
                name="address"
                rows="3"
                value={formData.address}
                onChange={updateField}
                className="form-input resize-none"
              />
            </FormField>
          </div>

          <FormField label="Phone" name="phone" required>
            <input
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField label="Email" name="email">
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField label="GSTIN" name="gstin">
            <input
              id="gstin"
              name="gstin"
              value={formData.gstin}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField
            label="Default GST percentage"
            name="default_gst_percentage"
            required
          >
            <input
              id="default_gst_percentage"
              name="default_gst_percentage"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={formData.default_gst_percentage}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField
            label="Currency"
            name="currency"
            required
          >
            <input
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField
            label="Invoice prefix"
            name="invoice_prefix"
            required
          >
            <input
              id="invoice_prefix"
              name="invoice_prefix"
              value={formData.invoice_prefix}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <FormField
            label="Timezone"
            name="timezone"
            required
          >
            <input
              id="timezone"
              name="timezone"
              value={formData.timezone}
              onChange={updateField}
              className="form-input"
            />
          </FormField>

          <div className="sm:col-span-2">
            <FormField
              label="Receipt footer"
              name="receipt_footer"
            >
              <textarea
                id="receipt_footer"
                name="receipt_footer"
                rows="3"
                value={formData.receipt_footer}
                onChange={updateField}
                className="form-input resize-none"
              />
            </FormField>
          </div>
        </div>

        <div className="mt-7 flex justify-end">
          <Button type="submit" loading={saving}>
            Save settings
          </Button>
        </div>
      </form>
    </section>
  );
}