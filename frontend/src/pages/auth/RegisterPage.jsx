import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

const initialFormData = {
  fullName: "",
  email: "",
  phone: "",
  address: "",
  password: "",
  confirmPassword: "",
};

function getFirebaseErrorMessage(error) {
  const code = error?.code ?? "";

  const messages = {
    "auth/email-already-in-use":
      "A Firebase account already uses this email.",
    "auth/invalid-email": "Enter a valid email address.",
    "auth/weak-password":
      "Use a stronger password with at least six characters.",
    "auth/network-request-failed":
      "The network request failed. Check your internet connection.",
  };

  return (
    messages[code] ??
    error?.message ??
    "The account could not be created."
  );
}

export default function RegisterPage() {
  const { registerCustomer } = useAuth();
  const { showToast } = useToast();
  const redirect = useNavigate();

  const [formData, setFormData] = useState(initialFormData);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }));

    setFieldErrors((currentErrors) => ({
      ...currentErrors,
      [name]: "",
    }));

    setFormError("");
  }

  function validateForm() {
    const errors = {};
    const phonePattern = /^[0-9+\-\s()]{7,20}$/;

    if (formData.fullName.trim().length < 2) {
      errors.fullName = "Enter your full name.";
    }

    if (!formData.email.trim()) {
      errors.email = "Email is required.";
    }

    if (!phonePattern.test(formData.phone.trim())) {
      errors.phone = "Enter a valid phone number.";
    }

    if (formData.password.length < 6) {
      errors.password = "Use at least six characters.";
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = "The passwords do not match.";
    }

    setFieldErrors(errors);

    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setFormError("");

    try {
      const result = await registerCustomer(formData);

      showToast("Your customer account has been created.");

      redirect(result.redirectTo, {
        replace: true,
      });
    } catch (error) {
      setFormError(getFirebaseErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold text-teal-700">
          Customer registration
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Reserve your favourite table
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Create an account using email and password. No phone OTP is
          required.
        </p>
      </div>

      {formError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          label="Full name"
          name="fullName"
          required
          error={fieldErrors.fullName}
        >
          <input
            id="fullName"
            name="fullName"
            type="text"
            value={formData.fullName}
            onChange={updateField}
            autoComplete="name"
            placeholder="Your full name"
            className="form-input"
          />
        </FormField>

        <div className="grid gap-5 sm:grid-cols-2">
          <FormField
            label="Email address"
            name="email"
            required
            error={fieldErrors.email}
          >
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={updateField}
              autoComplete="email"
              placeholder="you@example.com"
              className="form-input"
            />
          </FormField>

          <FormField
            label="Phone number"
            name="phone"
            required
            error={fieldErrors.phone}
          >
            <input
              id="phone"
              name="phone"
              type="tel"
              value={formData.phone}
              onChange={updateField}
              autoComplete="tel"
              placeholder="9876543210"
              className="form-input"
            />
          </FormField>
        </div>

        <FormField
          label="Address"
          name="address"
          error={fieldErrors.address}
          helperText="Optional now, required later for delivery orders."
        >
          <textarea
            id="address"
            name="address"
            rows="3"
            value={formData.address}
            onChange={updateField}
            autoComplete="street-address"
            placeholder="Your address"
            className="form-input resize-none"
          />
        </FormField>

        <div className="grid gap-5 sm:grid-cols-2">
          <FormField
            label="Password"
            name="password"
            required
            error={fieldErrors.password}
          >
            <input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={updateField}
              autoComplete="new-password"
              placeholder="Minimum 6 characters"
              className="form-input"
            />
          </FormField>

          <FormField
            label="Confirm password"
            name="confirmPassword"
            required
            error={fieldErrors.confirmPassword}
          >
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={updateField}
              autoComplete="new-password"
              placeholder="Enter it again"
              className="form-input"
            />
          </FormField>
        </div>

        <Button
          type="submit"
          loading={submitting}
          className="w-full"
        >
          Create customer account
        </Button>
      </form>

      <p className="mt-7 text-center text-sm text-slate-600">
        Already registered?{" "}
        <Link
          to="/login"
          className="font-semibold text-teal-700 hover:text-teal-800"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}