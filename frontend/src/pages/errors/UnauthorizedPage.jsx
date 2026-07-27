import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function UnauthorizedPage() {
  const { role, getDefaultPath } = useAuth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5">
      <div className="max-w-lg text-center">
        <p className="text-sm font-semibold text-red-600">
          Access denied
        </p>

        <h1 className="mt-3 text-4xl font-bold text-slate-900">
          You cannot open this page
        </h1>

        <p className="mt-4 leading-7 text-slate-500">
          Your account does not have the required role for this section.
        </p>

        <Link
          to={role ? getDefaultPath(role) : "/login"}
          className="mt-7 inline-flex rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white hover:bg-teal-700"
        >
          Return to your home page
        </Link>
      </div>
    </main>
  );
}