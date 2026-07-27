import apiClient from "./axios";

export async function getDashboardSummary() {
  const response = await apiClient.get(
    "/reports/dashboard",
  );

  return response.data.data;
}

export async function getReports({
  startDate = "",
  endDate = "",
} = {}) {
  const params = {};

  if (startDate) {
    params.start_date = startDate;
  }

  if (endDate) {
    params.end_date = endDate;
  }

  const response = await apiClient.get(
    "/reports/summary",
    {
      params,
    },
  );

  return response.data.data;
}