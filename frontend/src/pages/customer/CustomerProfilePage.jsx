import {
  useEffect,
  useState,
} from "react";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

export default function CustomerProfilePage() {
  const {
    user,
    customer,
    saveProfile,
  } = useAuth();

  const {
    showToast,
  } = useToast();

  const [
    form,
    setForm,
  ] = useState({
    full_name: "",
    phone: "",
    address: "",
  });

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  useEffect(() => {
    setForm({
      full_name:
        customer?.full_name ??
        user?.full_name ??
        "",
      phone:
        customer?.phone ?? "",
      address:
        customer?.address ?? "",
    });
  }, [
    customer,
    user,
  ]);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));

    setError("");
  }

  async function submitProfile(
    event,
  ) {
    event.preventDefault();

    if (
      form.full_name.trim()
        .length < 2
    ) {
      setError(
        "Enter a valid full name.",
      );
      return;
    }

    if (
      form.phone.trim()
        .length < 7
    ) {
      setError(
        "Enter a valid phone number.",
      );
      return;
    }

    setSaving(true);
    setError("");

    try {
      await saveProfile({
        fullName:
          form.full_name,
        phone:
          form.phone,
        address:
          form.address,
      });

      showToast(
        "Profile updated successfully.",
      );
    } catch (requestError) {
      setError(
        requestError.message ??
          "The profile could not be updated.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="max-w-2xl">
      <div className="rounded-2xl border border-teal-100 bg-white p-7">
        <p className="text-sm font-semibold text-teal-700">
          Customer profile
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Your account
        </h1>

        <p className="mt-2 text-slate-500">
          Keep your contact details updated for reservations.
        </p>

        <form
          onSubmit={submitProfile}
          className="mt-8 space-y-6"
        >
          <FormField
            label="Full name"
            name="full_name"
            required
          >
            <input
              id="full_name"
              name="full_name"
              type="text"
              minLength="2"
              maxLength="120"
              value={
                form.full_name
              }
              onChange={
                updateField
              }
              className="form-input"
              autoComplete="name"
            />
          </FormField>

          <FormField
            label="Email"
            name="email"
            helperText="Login email cannot be changed from this page."
          >
            <input
              id="email"
              type="email"
              value={
                customer?.email ??
                user?.email ??
                ""
              }
              disabled
              className="form-input cursor-not-allowed bg-slate-50 text-slate-500"
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
              minLength="7"
              maxLength="20"
              value={form.phone}
              onChange={
                updateField
              }
              className="form-input"
              autoComplete="tel"
            />
          </FormField>

          <FormField
            label="Address"
            name="address"
          >
            <textarea
              id="address"
              name="address"
              rows="4"
              maxLength="500"
              value={
                form.address
              }
              onChange={
                updateField
              }
              className="form-input resize-none"
              autoComplete="street-address"
              placeholder="Enter your address"
            />
          </FormField>

          <FormField
            label="Role"
            name="role"
            helperText="Your role is managed by the system."
          >
            <input
              id="role"
              type="text"
              value={
                user?.role ?? ""
              }
              disabled
              className="form-input cursor-not-allowed bg-slate-50 text-slate-500"
            />
          </FormField>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex justify-end">
            <Button
              type="submit"
              loading={saving}
            >
              Save profile
            </Button>
          </div>
        </form>
      </div>
    </section>
  );
}