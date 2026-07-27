"""Create or update a Staff account in Firebase and the local database."""

from getpass import getpass

from firebase_admin import auth
from sqlalchemy import select

from app.auth.firebase import get_firebase_app
from app.database.session import SessionLocal
from app.models.user import User
from app.utils.enums import UserRole


def main() -> None:
    """Create a Firebase Staff user and matching local user record."""

    get_firebase_app()

    full_name = input("Staff full name: ").strip()
    email = input("Staff email: ").strip().lower()
    password = getpass("Staff password: ").strip()

    if not full_name:
        raise ValueError("Staff full name is required.")

    if not email:
        raise ValueError("Staff email is required.")

    if len(password) < 6:
        raise ValueError(
            "Password must contain at least 6 characters."
        )

    try:
        firebase_user = auth.get_user_by_email(email)

        auth.update_user(
            firebase_user.uid,
            display_name=full_name,
            password=password,
            disabled=False,
        )

        firebase_user = auth.get_user(firebase_user.uid)

        print(
            "Existing Firebase account found and updated."
        )
    except auth.UserNotFoundError:
        firebase_user = auth.create_user(
            email=email,
            password=password,
            display_name=full_name,
            email_verified=False,
            disabled=False,
        )

        print("Firebase Staff account created.")

    database = SessionLocal()

    try:
        uid_statement = select(User).where(
            User.firebase_uid == firebase_user.uid
        )

        local_user = database.scalar(uid_statement)

        if local_user is None:
            email_statement = select(User).where(
                User.email == email
            )

            local_user = database.scalar(
                email_statement
            )

        if local_user is None:
            local_user = User(
                firebase_uid=firebase_user.uid,
                full_name=full_name,
                email=email,
                role=UserRole.STAFF,
                is_active=True,
            )

            database.add(local_user)

            message = "Local Staff account created."
        else:
            local_user.firebase_uid = (
                firebase_user.uid
            )
            local_user.full_name = full_name
            local_user.email = email
            local_user.role = UserRole.STAFF
            local_user.is_active = True

            database.add(local_user)

            message = (
                "Existing local account updated to Staff."
            )

        database.commit()
        database.refresh(local_user)

        print(message)
        print(f"User ID: {local_user.id}")
        print(f"Full name: {local_user.full_name}")
        print(f"Email: {local_user.email}")
        print(f"Role: {local_user.role.value}")
        print(f"Active: {local_user.is_active}")
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


if __name__ == "__main__":
    main()