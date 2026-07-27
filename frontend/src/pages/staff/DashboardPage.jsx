import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { getDashboardSummary } from "../../api/reportApi";
import Spinner from "../../components/common/Spinner";
import { useAuth } from "../../context/AuthContext";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value ?? 0));
}

export default function DashboardPage() {
  const { user } = useAuth();

  const [summary, setSummary] = useState(null);
  const [pageLoading, setPageLoading] =
    useState(true);
  const [pageError, setPageError] = useState("");

  const loadDashboard = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const summaryData =
        await getDashboardSummary();

      setSummary(summaryData);
    } catch (error) {
      setPageError(
        error.message ??
          "Dashboard information could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return (
    <section>
      <div className="mb-8">
        <p className="text-sm font-semibold text-teal-700">
          Staff workspace
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Welcome, {user?.full_name}
        </h1>

        <p className="mt-2 text-slate-500">
          Review today&apos;s restaurant activity.
        </p>
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner
            size="lg"
            label="Loading dashboard"
          />
        </div>
      ) : summary ? (
        <>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {[
              [
                "Today's revenue",
                formatCurrency(
                  summary.today_revenue,
                ),
              ],
              [
                "Today's orders",
                summary.today_orders,
              ],
              [
                "Pending orders",
                summary.pending_orders,
              ],
              [
                "Active reservations",
                summary.active_reservations,
              ],
              [
                "Active customers",
                summary.total_customers,
              ],
              [
                "Unpaid invoices",
                summary.unpaid_invoices,
              ],
            ].map(([label, value]) => (
              <article
                key={label}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >
                <p className="text-sm font-medium text-slate-500">
                  {label}
                </p>

                <p className="mt-3 text-3xl font-bold text-slate-900">
                  {value}
                </p>
              </article>
            ))}
          </div>

          <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            {[
              [
                "/staff/orders",
                "Manage orders",
                "Create orders and update kitchen status.",
              ],
              [
                "/staff/reservations",
                "Reservations",
                "Review upcoming table bookings.",
              ],
              [
                "/staff/billing",
                "Billing",
                "Generate invoices and record payments.",
              ],
              [
                "/staff/customers",
                "Customers",
                "Review customer records and activity.",
              ],
            ].map(([path, title, description]) => (
              <Link
                key={path}
                to={path}
                className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-teal-300 hover:bg-teal-50/40"
              >
                <h2 className="font-bold text-slate-900">
                  {title}
                </h2>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {description}
                </p>

                <p className="mt-4 text-sm font-semibold text-teal-700">
                  Open
                </p>
              </Link>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}