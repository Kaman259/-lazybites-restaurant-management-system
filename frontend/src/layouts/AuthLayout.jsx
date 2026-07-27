import { Outlet } from "react-router-dom";

export default function AuthLayout() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden overflow-hidden bg-teal-900 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute -left-20 top-20 h-72 w-72 rounded-full bg-cyan-300 blur-3xl" />
            <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-teal-300 blur-3xl" />
          </div>

          <div className="relative">
            <div className="inline-flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-xl font-black text-teal-700">
                L
              </div>

              <div>
                <p className="text-xl font-bold">LazyBites</p>
                <p className="text-sm text-teal-100">
                  Restaurant Management System
                </p>
              </div>
            </div>
          </div>

          <div className="relative max-w-xl">
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">
              Simple restaurant operations
            </p>

            <h1 className="text-5xl font-bold leading-tight">
              Manage tables, orders and guests from one place.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-teal-100">
              Staff get a focused dashboard. Customers get an easy way to
              reserve their table before arriving.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              {["Table booking", "Order billing", "Daily reports"].map(
                (item) => (
                  <span
                    key={item}
                    className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm"
                  >
                    {item}
                  </span>
                ),
              )}
            </div>
          </div>

          <p className="relative text-sm text-teal-200">
            Built for one restaurant, with clear and focused workflows.
          </p>
        </section>

        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600 font-black text-white">
                L
              </div>

              <div>
                <p className="font-bold text-slate-900">LazyBites</p>
                <p className="text-xs text-slate-500">
                  Restaurant Management System
                </p>
              </div>
            </div>

            <Outlet />
          </div>
        </section>
      </div>
    </main>
  );
}