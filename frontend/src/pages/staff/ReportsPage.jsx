import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { getReports } from "../../api/reportApi";
import Button from "../../components/common/Button";
import Spinner from "../../components/common/Spinner";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value ?? 0));
}

function humaniseValue(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function getDateString(date) {
  return date.toISOString().slice(0, 10);
}

export default function ReportsPage() {
  const today = new Date();
  const thirtyDaysAgo = new Date();

  thirtyDaysAgo.setDate(
    thirtyDaysAgo.getDate() - 29,
  );

  const [startDate, setStartDate] = useState(
    getDateString(thirtyDaysAgo),
  );

  const [endDate, setEndDate] = useState(
    getDateString(today),
  );

  const [reports, setReports] = useState(null);
  const [pageLoading, setPageLoading] =
    useState(true);
  const [pageError, setPageError] = useState("");

  const loadReports = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      const reportData = await getReports({
        startDate,
        endDate,
      });

      setReports(reportData);
    } catch (error) {
      setPageError(
        error.message ??
          "Reports could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  function submitFilters(event) {
    event.preventDefault();
    loadReports();
  }

  return (
    <section>
      <div className="mb-7">
        <p className="text-sm font-semibold text-teal-700">
          Restaurant performance
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Reports
        </h1>

        <p className="mt-2 text-slate-500">
          Review revenue, payments, orders and reservations.
        </p>
      </div>

      <form
        onSubmit={submitFilters}
        className="mb-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
      >
        <div>
          <label
            htmlFor="reportStartDate"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            Start date
          </label>

          <input
            id="reportStartDate"
            type="date"
            value={startDate}
            onChange={(event) =>
              setStartDate(event.target.value)
            }
            className="form-input"
          />
        </div>

        <div>
          <label
            htmlFor="reportEndDate"
            className="mb-2 block text-sm font-semibold text-slate-700"
          >
            End date
          </label>

          <input
            id="reportEndDate"
            type="date"
            value={endDate}
            onChange={(event) =>
              setEndDate(event.target.value)
            }
            className="form-input"
          />
        </div>

        <Button type="submit">
          Apply dates
        </Button>
      </form>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner
            size="lg"
            label="Loading reports"
          />
        </div>
      ) : reports ? (
        <div className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            {[
              [
                "Net revenue",
                formatCurrency(
                  reports.sales.net_revenue,
                ),
              ],
              [
                "Gross paid revenue",
                formatCurrency(
                  reports.sales.gross_paid_revenue,
                ),
              ],
              [
                "Refunded revenue",
                formatCurrency(
                  reports.sales.refunded_revenue,
                ),
              ],
              [
                "Average invoice",
                formatCurrency(
                  reports.sales.average_paid_invoice,
                ),
              ],
            ].map(([label, value]) => (
              <article
                key={label}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >
                <p className="text-sm font-medium text-slate-500">
                  {label}
                </p>

                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {value}
                </p>
              </article>
            ))}
          </div>

          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            {[
              [
                "Paid invoices",
                reports.sales.paid_invoice_count,
              ],
              [
                "Unpaid invoices",
                reports.sales.unpaid_invoice_count,
              ],
              [
                "Refunded invoices",
                reports.sales.refunded_invoice_count,
              ],
              [
                "GST collected",
                formatCurrency(
                  reports.sales.total_gst,
                ),
              ],
            ].map(([label, value]) => (
              <article
                key={label}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >
                <p className="text-sm font-medium text-slate-500">
                  {label}
                </p>

                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {value}
                </p>
              </article>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-bold text-slate-900">
                Payment breakdown
              </h2>

              {reports.payment_breakdown.length ===
              0 ? (
                <p className="mt-4 text-sm text-slate-500">
                  No paid invoices in this period.
                </p>
              ) : (
                <div className="mt-4 space-y-3">
                  {reports.payment_breakdown.map(
                    (payment) => (
                      <div
                        key={payment.payment_method}
                        className="flex items-center justify-between rounded-xl bg-slate-50 p-4"
                      >
                        <div>
                          <p className="font-semibold text-slate-900">
                            {humaniseValue(
                              payment.payment_method,
                            )}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {payment.invoice_count} invoices
                          </p>
                        </div>

                        <p className="font-bold text-slate-900">
                          {formatCurrency(
                            payment.total_amount,
                          )}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              )}
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-bold text-slate-900">
                Popular menu items
              </h2>

              {reports.popular_items.length === 0 ? (
                <p className="mt-4 text-sm text-slate-500">
                  No paid item sales in this period.
                </p>
              ) : (
                <div className="mt-4 space-y-3">
                  {reports.popular_items.map(
                    (item, index) => (
                      <div
                        key={`${item.menu_item_id}-${item.item_name}`}
                        className="flex items-center justify-between rounded-xl bg-slate-50 p-4"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-sm font-bold text-slate-700">
                            {index + 1}
                          </div>

                          <div>
                            <p className="font-semibold text-slate-900">
                              {item.item_name}
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                              {item.quantity_sold} sold
                            </p>
                          </div>
                        </div>

                        <p className="font-bold text-slate-900">
                          {formatCurrency(
                            item.sales_amount,
                          )}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              )}
            </article>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-bold text-slate-900">
                Order status summary
              </h2>

              {reports.order_statuses.length === 0 ? (
                <p className="mt-4 text-sm text-slate-500">
                  No orders in this period.
                </p>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {reports.order_statuses.map(
                    (entry) => (
                      <div
                        key={entry.status}
                        className="rounded-xl bg-slate-50 p-4"
                      >
                        <p className="text-sm text-slate-500">
                          {humaniseValue(
                            entry.status,
                          )}
                        </p>

                        <p className="mt-2 text-2xl font-bold text-slate-900">
                          {entry.count}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              )}
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-bold text-slate-900">
                Reservation status summary
              </h2>

              {reports.reservation_statuses.length ===
              0 ? (
                <p className="mt-4 text-sm text-slate-500">
                  No reservations in this period.
                </p>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {reports.reservation_statuses.map(
                    (entry) => (
                      <div
                        key={entry.status}
                        className="rounded-xl bg-slate-50 p-4"
                      >
                        <p className="text-sm text-slate-500">
                          {humaniseValue(
                            entry.status,
                          )}
                        </p>

                        <p className="mt-2 text-2xl font-bold text-slate-900">
                          {entry.count}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              )}
            </article>
          </div>

          <article className="rounded-2xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-bold text-slate-900">
              Additional totals
            </h2>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">
                  Total discounts
                </p>

                <p className="mt-2 text-xl font-bold text-slate-900">
                  {formatCurrency(
                    reports.sales.total_discount,
                  )}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">
                  Report period
                </p>

                <p className="mt-2 font-bold text-slate-900">
                  {reports.sales.start_date} to{" "}
                  {reports.sales.end_date}
                </p>
              </div>
            </div>
          </article>
        </div>
      ) : null}
    </section>
  );
}