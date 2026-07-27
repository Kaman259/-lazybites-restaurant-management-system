"""Menu category and menu item service functions."""

from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.menu_category import MenuCategory
from app.models.menu_item import MenuItem
from app.models.order_item import OrderItem
from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuItemCreate,
    MenuItemUpdate,
)
from app.utils.enums import FoodType


def list_menu_categories(
    database: Session,
    include_inactive: bool = True,
) -> list[MenuCategory]:
    """Return categories in their configured display order."""

    statement = select(MenuCategory)

    if not include_inactive:
        statement = statement.where(
            MenuCategory.is_active.is_(True)
        )

    statement = statement.order_by(
        MenuCategory.display_order.asc(),
        MenuCategory.name.asc(),
    )

    return list(database.scalars(statement).all())


def get_menu_category(
    database: Session,
    category_id: int,
) -> MenuCategory:
    """Return one menu category."""

    category = database.get(MenuCategory, category_id)

    if category is None:
        raise AppException(
            message="Menu category was not found.",
            status_code=404,
        )

    return category


def create_menu_category(
    database: Session,
    category_data: MenuCategoryCreate,
) -> MenuCategory:
    """Create a uniquely named menu category."""

    existing = database.scalar(
        select(MenuCategory).where(
            func.lower(MenuCategory.name)
            == category_data.name.lower()
        )
    )

    if existing is not None:
        raise AppException(
            message="A menu category with this name already exists.",
            status_code=409,
        )

    category = MenuCategory(
        **category_data.model_dump(),
    )

    database.add(category)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The menu category could not be created.",
            status_code=409,
        ) from error

    database.refresh(category)
    return category


def update_menu_category(
    database: Session,
    category: MenuCategory,
    category_data: MenuCategoryUpdate,
) -> MenuCategory:
    """Update a menu category."""

    duplicate = database.scalar(
        select(MenuCategory).where(
            func.lower(MenuCategory.name)
            == category_data.name.lower(),
            MenuCategory.id != category.id,
        )
    )

    if duplicate is not None:
        raise AppException(
            message="A menu category with this name already exists.",
            status_code=409,
        )

    for field_name, field_value in category_data.model_dump().items():
        setattr(category, field_name, field_value)

    database.add(category)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The menu category could not be updated.",
            status_code=409,
        ) from error

    database.refresh(category)
    return category


def delete_menu_category(
    database: Session,
    category: MenuCategory,
) -> None:
    """Delete a category only when it contains no items."""

    item_count = database.scalar(
        select(func.count(MenuItem.id)).where(
            MenuItem.category_id == category.id
        )
    )

    if item_count:
        raise AppException(
            message=(
                "This category contains menu items. "
                "Disable it instead of deleting it."
            ),
            status_code=409,
        )

    database.delete(category)
    database.commit()


def menu_item_query():
    """Build the standard menu-item query."""

    return select(MenuItem).options(
        joinedload(MenuItem.category)
    )


def list_menu_items(
    database: Session,
    category_id: int | None = None,
    food_type: FoodType | None = None,
    search: str | None = None,
    include_inactive: bool = True,
    available_only: bool = False,
) -> list[MenuItem]:
    """Return filtered menu items."""

    statement = menu_item_query()

    if category_id is not None:
        statement = statement.where(
            MenuItem.category_id == category_id
        )

    if food_type is not None:
        statement = statement.where(
            MenuItem.food_type == food_type
        )

    if not include_inactive:
        statement = statement.where(
            MenuItem.is_active.is_(True),
            MenuCategory.is_active.is_(True),
        ).join(MenuCategory)

    if available_only:
        statement = statement.where(
            MenuItem.is_available.is_(True)
        )

    if search:
        search_value = f"%{search.strip().lower()}%"

        statement = statement.where(
            or_(
                func.lower(MenuItem.name).like(search_value),
                func.lower(
                    func.coalesce(MenuItem.description, "")
                ).like(search_value),
            )
        )

    statement = statement.order_by(
        MenuItem.category_id.asc(),
        MenuItem.name.asc(),
    )

    return list(database.scalars(statement).unique().all())


def get_menu_item(
    database: Session,
    item_id: int,
) -> MenuItem:
    """Return one menu item with its category."""

    statement = menu_item_query().where(
        MenuItem.id == item_id
    )

    menu_item = database.scalar(statement)

    if menu_item is None:
        raise AppException(
            message="Menu item was not found.",
            status_code=404,
        )

    return menu_item


def validate_category_for_item(
    database: Session,
    category_id: int,
) -> MenuCategory:
    """Ensure the selected category exists."""

    category = database.get(MenuCategory, category_id)

    if category is None:
        raise AppException(
            message="The selected menu category was not found.",
            status_code=404,
        )

    return category


def ensure_unique_item_name(
    database: Session,
    category_id: int,
    item_name: str,
    excluded_item_id: int | None = None,
) -> None:
    """Ensure the item name is unique inside a category."""

    statement = select(MenuItem.id).where(
        MenuItem.category_id == category_id,
        func.lower(MenuItem.name) == item_name.lower(),
    )

    if excluded_item_id is not None:
        statement = statement.where(
            MenuItem.id != excluded_item_id
        )

    if database.scalar(statement) is not None:
        raise AppException(
            message=(
                "An item with this name already exists "
                "inside the selected category."
            ),
            status_code=409,
        )


def create_menu_item(
    database: Session,
    item_data: MenuItemCreate,
) -> MenuItem:
    """Create a menu item."""

    validate_category_for_item(
        database,
        item_data.category_id,
    )

    ensure_unique_item_name(
        database=database,
        category_id=item_data.category_id,
        item_name=item_data.name,
    )

    item_values = item_data.model_dump()
    item_values["price"] = Decimal(item_data.price)

    menu_item = MenuItem(**item_values)

    database.add(menu_item)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The menu item could not be created.",
            status_code=409,
        ) from error

    return get_menu_item(database, menu_item.id)


def update_menu_item(
    database: Session,
    menu_item: MenuItem,
    item_data: MenuItemUpdate,
) -> MenuItem:
    """Update a menu item."""

    validate_category_for_item(
        database,
        item_data.category_id,
    )

    ensure_unique_item_name(
        database=database,
        category_id=item_data.category_id,
        item_name=item_data.name,
        excluded_item_id=menu_item.id,
    )

    update_values = item_data.model_dump()
    update_values["price"] = Decimal(item_data.price)

    for field_name, field_value in update_values.items():
        setattr(menu_item, field_name, field_value)

    database.add(menu_item)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The menu item could not be updated.",
            status_code=409,
        ) from error

    return get_menu_item(database, menu_item.id)


def update_menu_item_availability(
    database: Session,
    menu_item: MenuItem,
    is_available: bool,
) -> MenuItem:
    """Change whether an item can currently be ordered."""

    menu_item.is_available = is_available

    database.add(menu_item)
    database.commit()

    return get_menu_item(database, menu_item.id)


def update_menu_item_image(
    database: Session,
    menu_item: MenuItem,
    image_path: str,
) -> MenuItem:
    """Save a menu item's public image path."""

    menu_item.image_path = image_path

    database.add(menu_item)
    database.commit()

    return get_menu_item(database, menu_item.id)


def delete_menu_item(
    database: Session,
    menu_item: MenuItem,
) -> None:
    """Delete an unused menu item."""

    order_item_count = database.scalar(
        select(func.count(OrderItem.id)).where(
            OrderItem.menu_item_id == menu_item.id
        )
    )

    if order_item_count:
        raise AppException(
            message=(
                "This menu item has order history. "
                "Disable it instead of deleting it."
            ),
            status_code=409,
        )

    database.delete(menu_item)
    database.commit()