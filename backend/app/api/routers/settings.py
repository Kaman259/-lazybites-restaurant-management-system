"""Restaurant settings endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import DatabaseSession
from app.auth.permissions import (
    require_admin,
    require_staff_or_admin,
)
from app.core.config import settings
from app.core.responses import success_response
from app.models.user import User
from app.schemas.restaurant_settings import (
    RestaurantSettingsResponse,
    RestaurantSettingsUpdate,
)
from app.services.settings_service import (
    get_restaurant_settings,
    update_restaurant_logo,
    update_restaurant_settings,
)
from app.utils.file_upload import (
    delete_local_upload,
    save_image_upload,
)


router = APIRouter(
    prefix="/settings",
    tags=["Restaurant Settings"],
)

AdminUser = Annotated[User, Depends(require_admin)]
StaffUser = Annotated[User, Depends(require_staff_or_admin)]


@router.get(
    "",
    summary="Get restaurant settings",
)
def read_restaurant_settings(
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Return restaurant settings for Staff and Admin users."""

    del current_user

    settings_record = get_restaurant_settings(database)

    response_data = RestaurantSettingsResponse.model_validate(
        settings_record
    )

    return success_response(
        message="Restaurant settings retrieved successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.put(
    "",
    summary="Update restaurant settings",
)
def edit_restaurant_settings(
    update_data: RestaurantSettingsUpdate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Allow an Admin to update restaurant settings."""

    del current_user

    settings_record = get_restaurant_settings(database)

    updated_settings = update_restaurant_settings(
        database=database,
        settings_record=settings_record,
        update_data=update_data,
    )

    response_data = RestaurantSettingsResponse.model_validate(
        updated_settings
    )

    return success_response(
        message="Restaurant settings updated successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.post(
    "/logo",
    summary="Upload restaurant logo",
)
async def upload_restaurant_logo(
    database: DatabaseSession,
    current_user: AdminUser,
    logo: Annotated[UploadFile, File()],
):
    """Allow an Admin to upload or replace the logo."""

    del current_user

    settings_record = get_restaurant_settings(database)

    old_logo_file = None

    if settings_record.logo_path:
        old_file_name = settings_record.logo_path.rsplit("/", 1)[-1]
        old_logo_file = settings.restaurant_upload_path / old_file_name

    saved_file_name = await save_image_upload(
        upload=logo,
        destination=settings.restaurant_upload_path,
        maximum_size_mb=settings.max_upload_size_mb,
    )

    public_logo_path = (
        f"/uploads/restaurant/{saved_file_name}"
    )

    try:
        updated_settings = update_restaurant_logo(
            database=database,
            settings_record=settings_record,
            logo_path=public_logo_path,
        )
    except Exception:
        delete_local_upload(
            settings.restaurant_upload_path / saved_file_name
        )
        raise

    delete_local_upload(old_logo_file)

    response_data = RestaurantSettingsResponse.model_validate(
        updated_settings
    )

    return success_response(
        message="Restaurant logo uploaded successfully.",
        data=response_data.model_dump(mode="json"),
    )