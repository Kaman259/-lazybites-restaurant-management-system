import apiClient from "./axios";

export async function registerCustomerAccount(
  customerData,
) {
  const response = await apiClient.post(
    "/auth/register-customer",
    customerData,
  );

  return response.data.data;
}

export async function createApplicationSession() {
  const response = await apiClient.post(
    "/auth/session",
  );

  return response.data.data;
}

export async function getCurrentAccount() {
  const response = await apiClient.get(
    "/auth/me",
  );

  return response.data.data;
}

export async function updateCurrentAccount(
  profileData,
) {
  const response = await apiClient.patch(
    "/auth/me",
    profileData,
  );

  return response.data.data;
}

export async function checkAdminAccess() {
  const response = await apiClient.get(
    "/auth/admin-check",
  );

  return response.data.data;
}

export async function checkStaffAccess() {
  const response = await apiClient.get(
    "/auth/staff-check",
  );

  return response.data.data;
}