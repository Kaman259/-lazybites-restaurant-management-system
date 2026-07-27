import apiClient from "./axios";

export async function getRestaurantSettings() {
  const response = await apiClient.get("/settings");

  return response.data.data;
}

export async function updateRestaurantSettings(settingsData) {
  const response = await apiClient.put("/settings", settingsData);

  return response.data.data;
}

export async function uploadRestaurantLogo(imageFile) {
  const formData = new FormData();
  formData.append("logo", imageFile);

  const response = await apiClient.post(
    "/settings/logo",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data.data;
}

export function getBackendAssetUrl(filePath) {
  if (!filePath) {
    return "";
  }

  if (filePath.startsWith("http")) {
    return filePath;
  }

  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, "");

  return `${backendBaseUrl}${filePath}`;
}