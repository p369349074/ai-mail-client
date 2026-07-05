from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def get_or_create_default_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == settings.default_user_email))
    if user is not None:
        return user

    user = User(
        email=settings.default_user_email,
        display_name=settings.default_user_display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
