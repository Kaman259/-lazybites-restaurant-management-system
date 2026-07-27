const statusClasses = {
  PENDING:
    "border-amber-200 bg-amber-50 text-amber-700",
  CONFIRMED:
    "border-blue-200 bg-blue-50 text-blue-700",
  SEATED:
    "border-violet-200 bg-violet-50 text-violet-700",
  PREPARING:
    "border-orange-200 bg-orange-50 text-orange-700",
  READY:
    "border-cyan-200 bg-cyan-50 text-cyan-700",
  SERVED:
    "border-indigo-200 bg-indigo-50 text-indigo-700",
  COMPLETED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
  CANCELLED:
    "border-red-200 bg-red-50 text-red-700",
  NO_SHOW:
    "border-slate-300 bg-slate-100 text-slate-700",
  ACTIVE:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
  INACTIVE:
    "border-slate-300 bg-slate-100 text-slate-600",
  PAID:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
  UNPAID:
    "border-amber-200 bg-amber-50 text-amber-700",
  REFUNDED:
    "border-violet-200 bg-violet-50 text-violet-700",
};

export default function StatusBadge({ status }) {
  const displayStatus = String(status ?? "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${
        statusClasses[status] ??
        "border-slate-200 bg-slate-50 text-slate-700"
      }`}
    >
      {displayStatus}
    </span>
  );
}