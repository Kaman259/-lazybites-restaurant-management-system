export default function Spinner({
  size = "md",
  label = "Loading",
}) {
  const sizeClass = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  }[size];

  return (
    <div
      className="inline-flex items-center justify-center"
      role="status"
      aria-label={label}
    >
      <span
        className={`${sizeClass} animate-spin rounded-full border-slate-200 border-t-teal-600`}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}