import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function CustomerHomePage() {
  const { customer } = useAuth();

  return (
    <section>
      <div className="overflow-hidden rounded-3xl bg-teal-900 text-white">
        <div className="grid items-center gap-8 p-7 sm:p-10 lg:grid-cols-[1fr_0.8fr]">
          <div>
            <span className="inline-flex rounded-full bg-white/10 px-4 py-2 text-sm text-teal-100">
              Table booking is almost ready
            </span>

            <h1 className="mt-5 max-w-xl text-4xl font-bold leading-tight sm:text-5xl">
              Your table by the lazy river is waiting.
            </h1>

            <p className="mt-5 max-w-xl leading-7 text-teal-100">
              Choose your date, time and guest count. The booking module
              will be connected after table management is complete.
            </p>

            <Link
              to="/customer/book-table"
              className="mt-7 inline-flex rounded-xl bg-white px-5 py-3 font-semibold text-teal-800 transition hover:bg-teal-50"
            >
              Book a table
            </Link>
          </div>

          <div className="relative min-h-64 overflow-hidden rounded-3xl bg-gradient-to-br from-cyan-200 via-teal-200 to-emerald-300">
            <div className="absolute left-8 top-8 h-24 w-24 rounded-full bg-white/70" />
            <div className="absolute -bottom-16 left-0 right-0 h-52 rounded-[50%] bg-cyan-500/70" />
            <div className="absolute bottom-10 left-1/2 h-20 w-40 -translate-x-1/2 rounded-[50%] border-[10px] border-orange-400 bg-orange-200" />
            <p className="absolute bottom-4 left-0 right-0 text-center text-sm font-semibold text-teal-950">
              Lazy river dining area
            </p>
          </div>
        </div>
      </div>

      <div className="mt-7 grid gap-5 md:grid-cols-3">
        {[
          ["Book ahead", "Choose your preferred time before arriving."],
          ["Track status", "See whether the restaurant confirmed your booking."],
          ["Easy cancellation", "Cancel eligible bookings from your account."],
        ].map(([title, description]) => (
          <article
            key={title}
            className="rounded-2xl border border-teal-100 bg-white p-5"
          >
            <h2 className="font-bold text-slate-900">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              {description}
            </p>
          </article>
        ))}
      </div>

      <div className="mt-7 rounded-2xl border border-teal-100 bg-white p-5">
        <p className="text-sm text-slate-500">Customer phone</p>
        <p className="mt-1 font-semibold text-slate-900">
          {customer?.phone}
        </p>
      </div>
    </section>
  );
}