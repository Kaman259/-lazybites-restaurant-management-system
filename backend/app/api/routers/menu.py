"""Menu management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.dependencies import DatabaseSession
from app.auth.permissions import (
    require_admin,
    require_staff_or_admin,
)
from app.core.config import settings
from app.core.responses import success_response
from app.models.user import User
from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryResponse,
    MenuCategoryUpdate,
    MenuItemAvailabilityUpdate,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)
from app.services.menu_service import (
    create_menu_category,
    create_menu_item,
    delete_menu_category,
    delete_menu_item,
    get_menu_category,
    get_menu_item,
    list_menu_categories,
    list_menu_items,
    update_menu_category,
    update_menu_item,
    update_menu_item_availability,
    update_menu_item_image,
)
from app.utils.enums import FoodType
from app.utils.file_upload import (
    delete_local_upload,
    save_image_upload,
)


router = APIRouter(
    prefix="/menu",
    tags=["Menu"],
)

AdminUser = Annotated[User, Depends(require_admin)]
StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def serialise_menu_item(menu_item):
    """Convert one menu item into response data."""

    return MenuItemResponse.model_validate(
        menu_item
    ).model_dump(mode="json")


@router.get("/categories")
def read_menu_categories(
    database: DatabaseSession,
    current_user: StaffUser,
    include_inactive: bool = Query(default=True),
):
    """Return menu categories for restaurant staff."""

    del current_user

    categories = list_menu_categories(
        database=database,
        include_inactive=include_inactive,
    )

    response_data = [
        MenuCategoryResponse.model_validate(
            category
        ).model_dump(mode="json")
        for category in categories
    ]

    return success_response(
        message="Menu categories retrieved successfully.",
        data=response_data,
    )


@router.post("/categories", status_code=201)
def add_menu_category(
    category_data: MenuCategoryCreate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Create a menu category."""

    del current_user

    category = create_menu_category(
        database=database,
        category_data=category_data,
    )

    response_data = MenuCategoryResponse.model_validate(
        category
    )

    return success_response(
        message="Menu category created successfully.",
        data=response_data.model_dump(mode="json"),
        status_code=201,
    )


@router.put("/categories/{category_id}")
def edit_menu_category(
    category_id: int,
    category_data: MenuCategoryUpdate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Update a menu category."""

    del current_user

    category = get_menu_category(database, category_id)

    updated_category = update_menu_category(
        database=database,
        category=category,
        category_data=category_data,
    )

    response_data = MenuCategoryResponse.model_validate(
        updated_category
    )

    return success_response(
        message="Menu category updated successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.delete("/categories/{category_id}")
def remove_menu_category(
    category_id: int,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Delete an empty menu category."""

    del current_user

    category = get_menu_category(database, category_id)

    delete_menu_category(
        database=database,
        category=category,
    )

    return success_response(
        message="Menu category deleted successfully.",
        data=None,
    )


@router.get("/items")
def read_menu_items(
    database: DatabaseSession,
    current_user: StaffUser,
    category_id: int | None = Query(default=None),
    food_type: FoodType | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    include_inactive: bool = Query(default=True),
    available_only: bool = Query(default=False),
):
    """Return filtered menu items."""

    del current_user

    menu_items = list_menu_items(
        database=database,
        category_id=category_id,
        food_type=food_type,
        search=search,
        include_inactive=include_inactive,
        available_only=available_only,
    )

    return success_response(
        message="Menu items retrieved successfully.",
        data=[
            serialise_menu_item(menu_item)
            for menu_item in menu_items
        ],
    )


@router.post("/items", status_code=201)
def add_menu_item(
    item_data: MenuItemCreate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Create a menu item."""

    del current_user

    menu_item = create_menu_item(
        database=database,
        item_data=item_data,
    )

    return success_response(
        message="Menu item created successfully.",
        data=serialise_menu_item(menu_item),
        status_code=201,
    )


@router.put("/items/{item_id}")
def edit_menu_item(
    item_id: int,
    item_data: MenuItemUpdate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Update a menu item."""

    del current_user

    menu_item = get_menu_item(database, item_id)

    updated_item = update_menu_item(
        database=database,
        menu_item=menu_item,
        item_data=item_data,
    )

    return success_response(
        message="Menu item updated successfully.",
        data=serialise_menu_item(updated_item),
    )


@router.patch("/items/{item_id}/availability")
def change_menu_item_availability(
    item_id: int,
    availability_data: MenuItemAvailabilityUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Allow Staff and Admin to change item availability."""

    del current_user

    menu_item = get_menu_item(database, item_id)

    updated_item = update_menu_item_availability(
        database=database,
        menu_item=menu_item,
        is_available=availability_data.is_available,
    )

    return success_response(
        message="Menu item availability updated successfully.",
        data=serialise_menu_item(updated_item),
    )


@router.post("/items/{item_id}/image")
async def upload_menu_item_image(
    item_id: int,
    database: DatabaseSession,
    current_user: AdminUser,
    image: Annotated[UploadFile, File()],
):
    """Upload or replace a menu-item image."""

    del current_user

    menu_item = get_menu_item(database, item_id)

    old_image_file = None

    if menu_item.image_path:
        old_file_name = menu_item.image_path.rsplit("/", 1)[-1]
        old_image_file = (
            settings.menu_upload_path / old_file_name
        )

    saved_file_name = await save_image_upload(
        upload=image,
        destination=settings.menu_upload_path,
        maximum_size_mb=settings.max_upload_size_mb,
    )

    public_image_path = (
        f"/uploads/menu-items/{saved_file_name}"
    )

    try:
        updated_item = update_menu_item_image(
            database=database,
            menu_item=menu_item,
            image_path=public_image_path,
        )
    except Exception:
        delete_local_upload(
            settings.menu_upload_path / saved_file_name
        )
        raise

    delete_local_upload(old_image_file)

    return success_response(
        message="Menu item image uploaded successfully.",
        data=serialise_menu_item(updated_item),
    )


@router.delete("/items/{item_id}")
def remove_menu_item(
    item_id: int,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Delete a menu item without order history."""

    del current_user

    menu_item = get_menu_item(database, item_id)
    old_image_file = None

    if menu_item.image_path:
        old_file_name = menu_item.image_path.rsplit("/", 1)[-1]
        old_image_file = (
            settings.menu_upload_path / old_file_name
        )

    delete_menu_item(
        database=database,
        menu_item=menu_item,
    )

    delete_local_upload(old_image_file)

    return success_response(
        message="Menu item deleted successfully.",
        data=None,
    )