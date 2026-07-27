import { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import { useAuth } from "../../context/AuthContext";

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth();

  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!email.trim()) {
      setFieldError("Email is required.");
      return;
    }

    setSubmitting(true);
    setFieldError("");
    setFormError("");
    setSuccessMessage("");

    try {
      await resetPassword(email);

      setSuccessMessage(
        "A password reset email has been requested. Check your inbox.",
      );
    } catch (error) {
      setFormError(
        error?.message ??
          "The password reset request could not be completed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold text-teal-700">
          Password recovery
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Reset your password
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Enter the email connected to your Firebase account.
        </p>
      </div>

      {successMessage && (
        <div className="mb-5 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800">
          {successMessage}
        </div>
      )}

      {formError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          label="Email address"
          name="resetEmail"
          required
          error={fieldError}
        >
          <input
            id="resetEmail"
            type="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setFieldError("");
              setFormError("");
            }}
            autoComplete="email"
            placeholder="you@example.com"
            className="form-input"
          />
        </FormField>

        <Button
          type="submit"
          loading={submitting}
          className="w-full"
        >
          Send reset email
        </Button>
      </form>

      <p className="mt-7 text-center text-sm text-slate-600">
        Remember your password?{" "}
        <Link
          to="/login"
          className="font-semibold text-teal-700 hover:text-teal-800"
        >
          Return to login
        </Link>
      </p>
    </div>
  );
}