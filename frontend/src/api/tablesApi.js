import apiClient from "./axios";

export async function getDiningTables(includeInactive = true) {
  const response = await apiClient.get("/tables", {
    params: {
      include_inactive: includeInactive,
    },
  });

  return response.data.data;
}

export async function createDiningTable(tableData) {
  const response = await apiClient.post("/tables", tableData);

  return response.data.data;
}

export async function updateDiningTable(tableId, tableData) {
  const response = await apiClient.put(
    `/tables/${tableId}`,
    tableData,
  );

  return response.data.data;
}

export async function deleteDiningTable(tableId) {
  const response = await apiClient.delete(`/tables/${tableId}`);

  return response.data.data;
}