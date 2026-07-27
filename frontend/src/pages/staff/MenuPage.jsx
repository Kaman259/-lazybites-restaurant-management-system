import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  createMenuCategory,
  createMenuItem,
  deleteMenuCategory,
  deleteMenuItem,
  getMenuCategories,
  getMenuItems,
  updateMenuCategory,
  updateMenuItem,
  updateMenuItemAvailability,
  uploadMenuItemImage,
} from "../../api/menuApi";
import { getBackendAssetUrl } from "../../api/settingsApi";
import Button from "../../components/common/Button";
import FormField from "../../components/common/FormField";
import Modal from "../../components/common/Modal";
import Spinner from "../../components/common/Spinner";
import StatusBadge from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";

const emptyCategoryForm = {
  name: "",
  description: "",
  display_order: "0",
  is_active: true,
};

const emptyItemForm = {
  category_id: "",
  name: "",
  description: "",
  price: "",
  food_type: "VEG",
  is_available: true,
  is_active: true,
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export default function MenuPage() {
  const { role } = useAuth();
  const { showToast } = useToast();

  const isAdmin = role === "ADMIN";

  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);

  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [categoryFilter, setCategoryFilter] = useState("");
  const [foodTypeFilter, setFoodTypeFilter] = useState("");
  const [searchText, setSearchText] = useState("");
  const [includeInactive, setIncludeInactive] = useState(true);
  const [availableOnly, setAvailableOnly] = useState(false);

  const [categoryModalOpen, setCategoryModalOpen] =
    useState(false);
  const [editingCategory, setEditingCategory] =
    useState(null);
  const [categoryForm, setCategoryForm] =
    useState(emptyCategoryForm);
  const [categorySaving, setCategorySaving] =
    useState(false);
  const [categoryFormError, setCategoryFormError] =
    useState("");

  const [itemModalOpen, setItemModalOpen] =
    useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState(emptyItemForm);
  const [selectedImage, setSelectedImage] = useState(null);
  const [itemSaving, setItemSaving] = useState(false);
  const [itemFormError, setItemFormError] = useState("");

  const activeCategories = useMemo(
    () => categories.filter((category) => category.is_active),
    [categories],
  );

  const loadCategories = useCallback(async () => {
    const categoryData = await getMenuCategories(true);
    setCategories(categoryData);
  }, []);

  const loadItems = useCallback(async () => {
    const itemData = await getMenuItems({
      categoryId: categoryFilter,
      foodType: foodTypeFilter,
      search: searchText,
      includeInactive,
      availableOnly,
    });

    setMenuItems(itemData);
  }, [
    categoryFilter,
    foodTypeFilter,
    searchText,
    includeInactive,
    availableOnly,
  ]);

  const loadPage = useCallback(async () => {
    setPageLoading(true);
    setPageError("");

    try {
      await Promise.all([
        loadCategories(),
        loadItems(),
      ]);
    } catch (error) {
      setPageError(
        error.message ?? "Menu information could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [loadCategories, loadItems]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  function openCreateCategoryModal() {
    setEditingCategory(null);
    setCategoryForm(emptyCategoryForm);
    setCategoryFormError("");
    setCategoryModalOpen(true);
  }

  function openEditCategoryModal(category) {
    setEditingCategory(category);

    setCategoryForm({
      name: category.name,
      description: category.description ?? "",
      display_order: String(category.display_order),
      is_active: category.is_active,
    });

    setCategoryFormError("");
    setCategoryModalOpen(true);
  }

  function closeCategoryModal() {
    if (categorySaving) {
      return;
    }

    setCategoryModalOpen(false);
    setEditingCategory(null);
    setCategoryForm(emptyCategoryForm);
    setCategoryFormError("");
  }

  function updateCategoryField(event) {
    const { name, value, type, checked } = event.target;

    setCategoryForm((currentForm) => ({
      ...currentForm,
      [name]: type === "checkbox" ? checked : value,
    }));

    setCategoryFormError("");
  }

  async function submitCategory(event) {
    event.preventDefault();

    if (!categoryForm.name.trim()) {
      setCategoryFormError("Category name is required.");
      return;
    }

    const displayOrder = Number(
      categoryForm.display_order,
    );

    if (
      !Number.isInteger(displayOrder) ||
      displayOrder < 0
    ) {
      setCategoryFormError(
        "Display order must be zero or a positive number.",
      );
      return;
    }

    const payload = {
      name: categoryForm.name.trim(),
      description:
        categoryForm.description.trim() || null,
      display_order: displayOrder,
      is_active: categoryForm.is_active,
    };

    setCategorySaving(true);
    setCategoryFormError("");

    try {
      if (editingCategory) {
        await updateMenuCategory(
          editingCategory.id,
          payload,
        );

        showToast("Menu category updated.");
      } else {
        await createMenuCategory(payload);
        showToast("Menu category created.");
      }

      closeCategoryModal();
      await loadCategories();
    } catch (error) {
      setCategoryFormError(
        error.message ??
          "The menu category could not be saved.",
      );
    } finally {
      setCategorySaving(false);
    }
  }

  async function handleDeleteCategory(category) {
    const confirmed = window.confirm(
      `Delete category "${category.name}"? This only works when the category contains no menu items.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteMenuCategory(category.id);
      showToast("Menu category deleted.");
      await loadCategories();
    } catch (error) {
      showToast(
        error.message ??
          "The menu category could not be deleted.",
        "error",
      );
    }
  }

  function openCreateItemModal() {
    if (activeCategories.length === 0) {
      showToast(
        "Create an active menu category first.",
        "error",
      );
      return;
    }

    setEditingItem(null);

    setItemForm({
      ...emptyItemForm,
      category_id: String(activeCategories[0].id),
    });

    setSelectedImage(null);
    setItemFormError("");
    setItemModalOpen(true);
  }

  function openEditItemModal(item) {
    setEditingItem(item);

    setItemForm({
      category_id: String(item.category_id),
      name: item.name,
      description: item.description ?? "",
      price: String(item.price),
      food_type: item.food_type,
      is_available: item.is_available,
      is_active: item.is_active,
    });

    setSelectedImage(null);
    setItemFormError("");
    setItemModalOpen(true);
  }

  function closeItemModal() {
    if (itemSaving) {
      return;
    }

    setItemModalOpen(false);
    setEditingItem(null);
    setItemForm(emptyItemForm);
    setSelectedImage(null);
    setItemFormError("");
  }

  function updateItemField(event) {
    const { name, value, type, checked } = event.target;

    setItemForm((currentForm) => ({
      ...currentForm,
      [name]: type === "checkbox" ? checked : value,
    }));

    setItemFormError("");
  }

  async function submitItem(event) {
    event.preventDefault();

    if (!itemForm.category_id) {
      setItemFormError("Select a menu category.");
      return;
    }

    if (!itemForm.name.trim()) {
      setItemFormError("Menu item name is required.");
      return;
    }

    const price = Number(itemForm.price);

    if (!Number.isFinite(price) || price <= 0) {
      setItemFormError(
        "Enter a valid price greater than zero.",
      );
      return;
    }

    const payload = {
      category_id: Number(itemForm.category_id),
      name: itemForm.name.trim(),
      description: itemForm.description.trim() || null,
      price: price.toFixed(2),
      food_type: itemForm.food_type,
      is_available: itemForm.is_available,
      is_active: itemForm.is_active,
    };

    setItemSaving(true);
    setItemFormError("");

    try {
      let savedItem;

      if (editingItem) {
        savedItem = await updateMenuItem(
          editingItem.id,
          payload,
        );
      } else {
        savedItem = await createMenuItem(payload);
      }

      if (selectedImage) {
        await uploadMenuItemImage(
          savedItem.id,
          selectedImage,
        );
      }

      showToast(
        editingItem
          ? "Menu item updated."
          : "Menu item created.",
      );

      closeItemModal();
      await loadItems();
    } catch (error) {
      setItemFormError(
        error.message ??
          "The menu item could not be saved.",
      );
    } finally {
      setItemSaving(false);
    }
  }

  async function toggleAvailability(item) {
    try {
      await updateMenuItemAvailability(
        item.id,
        !item.is_available,
      );

      showToast(
        item.is_available
          ? `${item.name} marked unavailable.`
          : `${item.name} marked available.`,
      );

      await loadItems();
    } catch (error) {
      showToast(
        error.message ??
          "Item availability could not be changed.",
        "error",
      );
    }
  }

  async function handleDeleteItem(item) {
    const confirmed = window.confirm(
      `Delete "${item.name}"? Items with order history cannot be deleted.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteMenuItem(item.id);
      showToast("Menu item deleted.");
      await loadItems();
    } catch (error) {
      showToast(
        error.message ??
          "The menu item could not be deleted.",
        "error",
      );
    }
  }

  async function refreshFilters() {
    setPageLoading(true);
    setPageError("");

    try {
      await loadItems();
    } catch (error) {
      setPageError(
        error.message ?? "Menu items could not be loaded.",
      );
    } finally {
      setPageLoading(false);
    }
  }

  return (
    <section>
      <div className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-semibold text-teal-700">
            Food and beverages
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Menu management
          </h1>

          <p className="mt-2 text-slate-500">
            Manage categories, prices, availability and item images.
          </p>
        </div>

        {isAdmin && (
          <div className="flex flex-wrap gap-3">
            <Button
              variant="secondary"
              onClick={openCreateCategoryModal}
            >
              Add category
            </Button>

            <Button onClick={openCreateItemModal}>
              Add menu item
            </Button>
          </div>
        )}
      </div>

      {pageError && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label
              htmlFor="menuSearch"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Search
            </label>

            <input
              id="menuSearch"
              type="search"
              value={searchText}
              onChange={(event) =>
                setSearchText(event.target.value)
              }
              placeholder="Search menu items"
              className="form-input"
            />
          </div>

          <div>
            <label
              htmlFor="categoryFilter"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Category
            </label>

            <select
              id="categoryFilter"
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(event.target.value)
              }
              className="form-input"
            >
              <option value="">All categories</option>

              {categories.map((category) => (
                <option
                  key={category.id}
                  value={category.id}
                >
                  {category.name}
                  {!category.is_active ? " (Inactive)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="foodTypeFilter"
              className="mb-2 block text-sm font-semibold text-slate-700"
            >
              Food type
            </label>

            <select
              id="foodTypeFilter"
              value={foodTypeFilter}
              onChange={(event) =>
                setFoodTypeFilter(event.target.value)
              }
              className="form-input"
            >
              <option value="">All food types</option>
              <option value="VEG">Veg</option>
              <option value="NON_VEG">Non-Veg</option>
            </select>
          </div>

          <div className="flex items-end">
            <Button
              onClick={refreshFilters}
              className="w-full"
            >
              Apply filters
            </Button>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-slate-100 pt-5 sm:flex-row sm:items-center">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(event) =>
                setIncludeInactive(event.target.checked)
              }
              className="h-5 w-5 rounded border-slate-300 text-teal-600"
            />

            <span className="text-sm font-medium text-slate-700">
              Include inactive items
            </span>
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={availableOnly}
              onChange={(event) =>
                setAvailableOnly(event.target.checked)
              }
              className="h-5 w-5 rounded border-slate-300 text-teal-600"
            />

            <span className="text-sm font-medium text-slate-700">
              Available items only
            </span>
          </label>
        </div>
      </div>

      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Categories
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Categories control how menu items are grouped.
            </p>
          </div>

          {isAdmin && (
            <Button
              variant="secondary"
              onClick={openCreateCategoryModal}
            >
              Add category
            </Button>
          )}
        </div>

        {categories.length === 0 ? (
          <div className="mt-5 rounded-xl border border-dashed border-slate-300 px-5 py-10 text-center">
            <p className="font-semibold text-slate-700">
              No categories added
            </p>
          </div>
        ) : (
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {categories.map((category) => (
              <article
                key={category.id}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-slate-900">
                      {category.name}
                    </h3>

                    <p className="mt-1 text-xs text-slate-500">
                      Display order: {category.display_order}
                    </p>
                  </div>

                  <StatusBadge
                    status={
                      category.is_active
                        ? "ACTIVE"
                        : "INACTIVE"
                    }
                  />
                </div>

                {category.description && (
                  <p className="mt-3 text-sm leading-6 text-slate-500">
                    {category.description}
                  </p>
                )}

                {isAdmin && (
                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        openEditCategoryModal(category)
                      }
                      className="flex-1"
                    >
                      Edit
                    </Button>

                    <Button
                      variant="danger"
                      onClick={() =>
                        handleDeleteCategory(category)
                      }
                    >
                      Delete
                    </Button>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>

      {pageLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner size="lg" label="Loading menu items" />
        </div>
      ) : menuItems.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <h2 className="text-lg font-bold text-slate-900">
            No menu items found
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Add a menu item or change the selected filters.
          </p>

          {isAdmin && (
            <Button
              onClick={openCreateItemModal}
              className="mt-6"
            >
              Add menu item
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {menuItems.map((item) => (
            <article
              key={item.id}
              className="overflow-hidden rounded-2xl border border-slate-200 bg-white"
            >
              <div className="flex h-48 items-center justify-center bg-slate-100">
                {item.image_path ? (
                  <img
                    src={getBackendAssetUrl(
                      item.image_path,
                    )}
                    alt={item.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white text-2xl font-black text-teal-700">
                      L
                    </div>

                    <p className="mt-3 text-sm text-slate-500">
                      No item image
                    </p>
                  </div>
                )}
              </div>

              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-teal-700">
                      {item.category.name}
                    </p>

                    <h2 className="mt-1 text-xl font-bold text-slate-900">
                      {item.name}
                    </h2>
                  </div>

                  <span
                    className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
                      item.food_type === "VEG"
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-red-200 bg-red-50 text-red-700"
                    }`}
                  >
                    {item.food_type === "VEG"
                      ? "Veg"
                      : "Non-Veg"}
                  </span>
                </div>

                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {formatCurrency(item.price)}
                </p>

                {item.description && (
                  <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500">
                    {item.description}
                  </p>
                )}

                <div className="mt-4 flex flex-wrap gap-2">
                  <StatusBadge
                    status={
                      item.is_available
                        ? "ACTIVE"
                        : "INACTIVE"
                    }
                  />

                  {!item.is_active && (
                    <span className="inline-flex rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                      Item disabled
                    </span>
                  )}
                </div>

                <div className="mt-5">
                  <Button
                    variant={
                      item.is_available
                        ? "secondary"
                        : "primary"
                    }
                    onClick={() =>
                      toggleAvailability(item)
                    }
                    className="w-full"
                  >
                    {item.is_available
                      ? "Mark unavailable"
                      : "Mark available"}
                  </Button>
                </div>

                {isAdmin && (
                  <div className="mt-3 flex gap-3">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        openEditItemModal(item)
                      }
                      className="flex-1"
                    >
                      Edit
                    </Button>

                    <Button
                      variant="danger"
                      onClick={() =>
                        handleDeleteItem(item)
                      }
                    >
                      Delete
                    </Button>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        open={categoryModalOpen}
        title={
          editingCategory
            ? "Edit menu category"
            : "Add menu category"
        }
        onClose={closeCategoryModal}
      >
        {categoryFormError && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {categoryFormError}
          </div>
        )}

        <form
          onSubmit={submitCategory}
          className="space-y-5"
        >
          <FormField
            label="Category name"
            name="name"
            required
          >
            <input
              id="name"
              name="name"
              value={categoryForm.name}
              onChange={updateCategoryField}
              placeholder="Example: Main Course"
              className="form-input"
            />
          </FormField>

          <FormField
            label="Description"
            name="description"
          >
            <textarea
              id="description"
              name="description"
              rows="3"
              value={categoryForm.description}
              onChange={updateCategoryField}
              className="form-input resize-none"
              placeholder="Optional category description"
            />
          </FormField>

          <FormField
            label="Display order"
            name="display_order"
            required
          >
            <input
              id="display_order"
              name="display_order"
              type="number"
              min="0"
              value={categoryForm.display_order}
              onChange={updateCategoryField}
              className="form-input"
            />
          </FormField>

          <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
            <div>
              <p className="font-semibold text-slate-900">
                Active category
              </p>

              <p className="text-sm text-slate-500">
                Active categories can be used for menu items.
              </p>
            </div>

            <input
              type="checkbox"
              name="is_active"
              checked={categoryForm.is_active}
              onChange={updateCategoryField}
              className="h-5 w-5 rounded border-slate-300 text-teal-600"
            />
          </label>

          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={closeCategoryModal}
              disabled={categorySaving}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              loading={categorySaving}
            >
              {editingCategory
                ? "Save category"
                : "Create category"}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={itemModalOpen}
        title={
          editingItem
            ? "Edit menu item"
            : "Add menu item"
        }
        onClose={closeItemModal}
        maxWidth="max-w-2xl"
      >
        {itemFormError && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {itemFormError}
          </div>
        )}

        <form
          onSubmit={submitItem}
          className="space-y-5"
        >
          <FormField
            label="Category"
            name="category_id"
            required
          >
            <select
              id="category_id"
              name="category_id"
              value={itemForm.category_id}
              onChange={updateItemField}
              className="form-input"
            >
              <option value="">Select category</option>

              {categories.map((category) => (
                <option
                  key={category.id}
                  value={category.id}
                >
                  {category.name}
                  {!category.is_active
                    ? " (Inactive)"
                    : ""}
                </option>
              ))}
            </select>
          </FormField>

          <FormField
            label="Item name"
            name="name"
            required
          >
            <input
              id="item_name"
              name="name"
              value={itemForm.name}
              onChange={updateItemField}
              placeholder="Example: Paneer Butter Masala"
              className="form-input"
            />
          </FormField>

          <FormField
            label="Description"
            name="description"
          >
            <textarea
              id="item_description"
              name="description"
              rows="4"
              value={itemForm.description}
              onChange={updateItemField}
              placeholder="Describe the dish"
              className="form-input resize-none"
            />
          </FormField>

          <div className="grid gap-5 sm:grid-cols-2">
            <FormField
              label="Price"
              name="price"
              required
            >
              <input
                id="price"
                name="price"
                type="number"
                min="0.01"
                step="0.01"
                value={itemForm.price}
                onChange={updateItemField}
                placeholder="220.00"
                className="form-input"
              />
            </FormField>

            <FormField
              label="Food type"
              name="food_type"
              required
            >
              <select
                id="food_type"
                name="food_type"
                value={itemForm.food_type}
                onChange={updateItemField}
                className="form-input"
              >
                <option value="VEG">Veg</option>
                <option value="NON_VEG">Non-Veg</option>
              </select>
            </FormField>
          </div>

          <FormField
            label="Item image"
            name="item_image"
            helperText="Optional. JPG, PNG or WebP, maximum 5 MB."
          >
            <input
              id="item_image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => {
                setSelectedImage(
                  event.target.files?.[0] ?? null,
                );
                setItemFormError("");
              }}
              className="form-input"
            />
          </FormField>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
              <div>
                <p className="font-semibold text-slate-900">
                  Available now
                </p>

                <p className="text-sm text-slate-500">
                  Staff can change this later.
                </p>
              </div>

              <input
                type="checkbox"
                name="is_available"
                checked={itemForm.is_available}
                onChange={updateItemField}
                className="h-5 w-5 rounded border-slate-300 text-teal-600"
              />
            </label>

            <label className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3">
              <div>
                <p className="font-semibold text-slate-900">
                  Active item
                </p>

                <p className="text-sm text-slate-500">
                  Disabled items remain stored.
                </p>
              </div>

              <input
                type="checkbox"
                name="is_active"
                checked={itemForm.is_active}
                onChange={updateItemField}
                className="h-5 w-5 rounded border-slate-300 text-teal-600"
              />
            </label>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={closeItemModal}
              disabled={itemSaving}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              loading={itemSaving}
            >
              {editingItem
                ? "Save item"
                : "Create item"}
            </Button>
          </div>
        </form>
      </Modal>
    </section>
  );
}