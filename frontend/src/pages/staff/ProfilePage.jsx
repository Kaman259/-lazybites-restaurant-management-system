import {
  useEffect,
  useState,
} from "react";

import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

export default function ProfilePage() {
  const {
    user,
    saveProfile,
  } = useAuth();

  const {
    showToast,
  } = useToast();

  const [
    fullName,
    setFullName,
  ] = useState("");

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  useEffect(() => {
    setFullName(
      user?.full_name ?? "",
    );
  }, [user]);

  async function submitProfile(
    event,
  ) {
    event.preventDefault();

    const cleanedName =
      fullName.trim();

    if (
      cleanedName.length < 2
    ) {
      setError(
        "Enter a valid full name.",
      );
      return;
    }

    setSaving(true);
    setError("");

    try {
      await saveProfile({
        fullName:
          cleanedName,
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
      <div className="rounded-2xl border border-slate-200 bg-white p-7">
        <p className="text-sm font-semibold text-teal-700">
          Account profile
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Your profile
        </h1>

        <p className="mt-2 text-slate-500">
          Update the name shown inside LazyBites.
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
              value={fullName}
              onChange={(event) => {
                setFullName(
                  event.target.value,
                );
                setError("");
              }}
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
                user?.email ?? ""
              }
              disabled
              className="form-input cursor-not-allowed bg-slate-50 text-slate-500"
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