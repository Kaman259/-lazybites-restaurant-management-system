import axios from "axios";

import { firebaseAuth } from "../firebase/config";

const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  async (requestConfig) => {
    const firebaseUser = firebaseAuth.currentUser;

    if (firebaseUser) {
      const idToken = await firebaseUser.getIdToken();

      requestConfig.headers.Authorization = `Bearer ${idToken}`;
    }

    return requestConfig;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalisedError = {
      status: error.response?.status ?? 0,
      message:
        error.response?.data?.message ??
        error.message ??
        "The request could not be completed.",
      errors: error.response?.data?.errors ?? [],
      originalError: error,
    };

    return Promise.reject(normalisedError);
  },
);

export default apiClient;