import apiClient from "./axios";

export async function getMenuCategories(
  includeInactive = true,
) {
  const response = await apiClient.get("/menu/categories", {
    params: {
      include_inactive: includeInactive,
    },
  });

  return response.data.data;
}

export async function createMenuCategory(categoryData) {
  const response = await apiClient.post(
    "/menu/categories",
    categoryData,
  );

  return response.data.data;
}

export async function updateMenuCategory(
  categoryId,
  categoryData,
) {
  const response = await apiClient.put(
    `/menu/categories/${categoryId}`,
    categoryData,
  );

  return response.data.data;
}

export async function deleteMenuCategory(categoryId) {
  const response = await apiClient.delete(
    `/menu/categories/${categoryId}`,
  );

  return response.data.data;
}

export async function getMenuItems({
  categoryId = "",
  foodType = "",
  search = "",
  includeInactive = true,
  availableOnly = false,
} = {}) {
  const params = {
    include_inactive: includeInactive,
    available_only: availableOnly,
  };

  if (categoryId) {
    params.category_id = categoryId;
  }

  if (foodType) {
    params.food_type = foodType;
  }

  if (search.trim()) {
    params.search = search.trim();
  }

  const response = await apiClient.get("/menu/items", {
    params,
  });

  return response.data.data;
}

export async function createMenuItem(itemData) {
  const response = await apiClient.post(
    "/menu/items",
    itemData,
  );

  return response.data.data;
}

export async function updateMenuItem(itemId, itemData) {
  const response = await apiClient.put(
    `/menu/items/${itemId}`,
    itemData,
  );

  return response.data.data;
}

export async function updateMenuItemAvailability(
  itemId,
  isAvailable,
) {
  const response = await apiClient.patch(
    `/menu/items/${itemId}/availability`,
    {
      is_available: isAvailable,
    },
  );

  return response.data.data;
}

export async function uploadMenuItemImage(
  itemId,
  imageFile,
) {
  const formData = new FormData();
  formData.append("image", imageFile);

  const response = await apiClient.post(
    `/menu/items/${itemId}/image`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data.data;
}

export async function deleteMenuItem(itemId) {
  const response = await apiClient.delete(
    `/menu/items/${itemId}`,
  );

  return response.data.data;
}