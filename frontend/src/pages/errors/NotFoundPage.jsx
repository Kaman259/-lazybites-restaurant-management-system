import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function NotFoundPage() {
  const { role, getDefaultPath } = useAuth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5">
      <div className="max-w-lg text-center">
        <p className="text-7xl font-black text-teal-600">404</p>

        <h1 className="mt-4 text-3xl font-bold text-slate-900">
          This page does not exist
        </h1>

        <p className="mt-3 text-slate-500">
          The address may be incorrect or the page may have moved.
        </p>

        <Link
          to={role ? getDefaultPath(role) : "/login"}
          className="mt-7 inline-flex rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white hover:bg-teal-700"
        >
          Return
        </Link>
      </div>
    </main>
  );
}