import apiClient from "./axios";

export async function searchAvailableTables(searchData) {
  const response = await apiClient.post(
    "/reservations/availability",
    searchData,
  );

  return response.data.data;
}

export async function createReservation(reservationData) {
  const response = await apiClient.post(
    "/reservations",
    reservationData,
  );

  return response.data.data;
}

export async function getMyReservations() {
  const response = await apiClient.get("/reservations/me");

  return response.data.data;
}

export async function cancelReservation(
  reservationId,
  cancellationReason,
) {
  const response = await apiClient.patch(
    `/reservations/${reservationId}/cancel`,
    {
      cancellation_reason: cancellationReason || null,
    },
  );

  return response.data.data;
}

export async function getAllReservations(status = "") {
  const response = await apiClient.get("/reservations", {
    params: status
      ? {
          status,
        }
      : {},
  });

  return response.data.data;
}

export async function updateReservationStatus(
  reservationId,
  status,
  cancellationReason = "",
) {
  const response = await apiClient.patch(
    `/reservations/${reservationId}/status`,
    {
      status,
      cancellation_reason:
        status === "CANCELLED"
          ? cancellationReason || null
          : null,
    },
  );

  return response.data.data;
}