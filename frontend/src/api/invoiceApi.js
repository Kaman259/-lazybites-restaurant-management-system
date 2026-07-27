import apiClient from "./axios";

export async function createInvoice(invoiceData) {
  const response = await apiClient.post(
    "/invoices",
    invoiceData,
  );

  return response.data.data;
}

export async function getInvoices({
  paymentStatus = "",
  paymentMethod = "",
} = {}) {
  const params = {};

  if (paymentStatus) {
    params.payment_status = paymentStatus;
  }

  if (paymentMethod) {
    params.payment_method = paymentMethod;
  }

  const response = await apiClient.get("/invoices", {
    params,
  });

  return response.data.data;
}

export async function getInvoice(invoiceId) {
  const response = await apiClient.get(
    `/invoices/${invoiceId}`,
  );

  return response.data.data;
}

export async function markInvoicePaid(
  invoiceId,
  paymentMethod,
) {
  const response = await apiClient.patch(
    `/invoices/${invoiceId}/payment`,
    {
      payment_method: paymentMethod,
    },
  );

  return response.data.data;
}

export async function refundInvoice(
  invoiceId,
  refundReason,
) {
  const response = await apiClient.patch(
    `/invoices/${invoiceId}/refund`,
    {
      refund_reason: refundReason.trim(),
    },
  );

  return response.data.data;
}