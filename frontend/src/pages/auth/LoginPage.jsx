import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

function getFirebaseErrorMessage(error) {
  const code = error?.code ?? "";

  const messages = {
    "auth/invalid-credential": "The email or password is incorrect.",
    "auth/user-disabled": "This Firebase account has been disabled.",
    "auth/too-many-requests":
      "Too many login attempts. Please wait and try again.",
    "auth/network-request-failed":
      "The network request failed. Check your internet connection.",
  };

  return (
    messages[code] ??
    error?.message ??
    "Login could not be completed."
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const location = useLocation();
  const redirect = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

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

    if (!formData.email.trim()) {
      errors.email = "Email is required.";
    }

    if (!formData.password) {
      errors.password = "Password is required.";
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
      const result = await login(formData);
      const requestedPath = location.state?.from;

      showToast("You have signed in successfully.");

      redirect(requestedPath || result.redirectTo, {
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
          Welcome back
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Sign in to LazyBites
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Customers can manage reservations. Staff can access restaurant
          operations.
        </p>
      </div>

      {formError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
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
            autoComplete="current-password"
            placeholder="Enter your password"
            className="form-input"
          />
        </FormField>

        <div className="flex justify-end">
          <Link
            to="/forgot-password"
            className="text-sm font-semibold text-teal-700 hover:text-teal-800"
          >
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          loading={submitting}
          className="w-full"
        >
          Sign in
        </Button>
      </form>

      <p className="mt-7 text-center text-sm text-slate-600">
        Booking a table for the first time?{" "}
        <Link
          to="/register"
          className="font-semibold text-teal-700 hover:text-teal-800"
        >
          Create a customer account
        </Link>
      </p>
    </div>
  );
}