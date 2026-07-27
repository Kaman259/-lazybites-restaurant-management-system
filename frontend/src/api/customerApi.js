import apiClient from "./axios";

export async function getCustomers({
  search = "",
  includeInactive = true,
} = {}) {
  const params = {
    include_inactive: includeInactive,
  };

  if (search.trim()) {
    params.search = search.trim();
  }

  const response = await apiClient.get("/customers", {
    params,
  });

  return response.data.data;
}

export async function getCustomer(customerId) {
  const response = await apiClient.get(
    `/customers/${customerId}`,
  );

  return response.data.data;
}

export async function createCustomer(customerData) {
  const response = await apiClient.post(
    "/customers",
    customerData,
  );

  return response.data.data;
}

export async function updateCustomer(
  customerId,
  customerData,
) {
  const response = await apiClient.put(
    `/customers/${customerId}`,
    customerData,
  );

  return response.data.data;
}

export async function updateCustomerStatus(
  customerId,
  isActive,
) {
  const response = await apiClient.patch(
    `/customers/${customerId}/status`,
    {
      is_active: isActive,
    },
  );

  return response.data.data;
}