import apiClient from "./axios";

export async function createOrder(orderData) {
  const response = await apiClient.post("/orders", orderData);

  return response.data.data;
}

export async function getOrders({
  status = "",
  orderType = "",
} = {}) {
  const params = {};

  if (status) {
    params.status = status;
  }

  if (orderType) {
    params.order_type = orderType;
  }

  const response = await apiClient.get("/orders", {
    params,
  });

  return response.data.data;
}

export async function getOrder(orderId) {
  const response = await apiClient.get(
    `/orders/${orderId}`,
  );

  return response.data.data;
}

export async function updateOrderStatus(
  orderId,
  status,
  cancellationReason = "",
) {
  const response = await apiClient.patch(
    `/orders/${orderId}/status`,
    {
      status,
      cancellation_reason:
        status === "CANCELLED"
          ? cancellationReason.trim() || null
          : null,
    },
  );

  return response.data.data;
}