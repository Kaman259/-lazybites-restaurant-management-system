import { useAuth } from "../../context/AuthContext";

export default function CustomerProfilePage() {
  const { user, customer } = useAuth();

  return (
    <section className="max-w-2xl rounded-2xl border border-teal-100 bg-white p-7">
      <p className="text-sm font-semibold text-teal-700">
        Customer profile
      </p>

      <h1 className="mt-2 text-3xl font-bold text-slate-900">
        Your account
      </h1>

      <dl className="mt-8 divide-y divide-slate-100">
        {[
          ["Full name", customer?.full_name ?? user?.full_name],
          ["Email", customer?.email ?? user?.email],
          ["Phone", customer?.phone],
          ["Address", customer?.address || "Not provided"],
          ["Role", user?.role],
        ].map(([label, value]) => (
          <div
            key={label}
            className="grid gap-1 py-4 sm:grid-cols-[160px_1fr]"
          >
            <dt className="text-sm font-medium text-slate-500">
              {label}
            </dt>

            <dd className="font-medium text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}