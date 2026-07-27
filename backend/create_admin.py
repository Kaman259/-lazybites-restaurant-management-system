"""Create or update a local Admin account for an existing Firebase user."""

from getpass import getpass

from firebase_admin import auth
from sqlalchemy import select

from app.auth.firebase import get_firebase_app
from app.database.session import SessionLocal
from app.models.user import User
from app.utils.enums import UserRole


def main() -> None:
    """Create a Firebase Admin user and matching local database record."""

    get_firebase_app()

    full_name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ").strip()

    if not full_name:
        raise ValueError("Admin full name is required.")

    if not email:
        raise ValueError("Admin email is required.")

    if len(password) < 6:
        raise ValueError("Password must contain at least 6 characters.")

    try:
        firebase_user = auth.get_user_by_email(email)
        print("Existing Firebase account found.")
    except auth.UserNotFoundError:
        firebase_user = auth.create_user(
            email=email,
            password=password,
            display_name=full_name,
            email_verified=False,
            disabled=False,
        )
        print("Firebase Admin account created.")

    database = SessionLocal()

    try:
        statement = select(User).where(
            User.firebase_uid == firebase_user.uid
        )
        local_user = database.scalar(statement)

        if local_user is None:
            email_statement = select(User).where(
                User.email == email
            )
            local_user = database.scalar(email_statement)

        if local_user is None:
            local_user = User(
                firebase_uid=firebase_user.uid,
                full_name=full_name,
                email=email,
                role=UserRole.ADMIN,
                is_active=True,
            )
            database.add(local_user)
            message = "Local Admin account created."
        else:
            local_user.firebase_uid = firebase_user.uid
            local_user.full_name = full_name
            local_user.email = email
            local_user.role = UserRole.ADMIN
            local_user.is_active = True
            database.add(local_user)
            message = "Existing local account updated to Admin."

        database.commit()
        database.refresh(local_user)

        print(message)
        print(f"User ID: {local_user.id}")
        print(f"Email: {local_user.email}")
        print(f"Role: {local_user.role.value}")
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


if __name__ == "__main__":
    main()