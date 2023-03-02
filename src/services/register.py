from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import UserAuth
from src.models.base import User as UserDB
from src.services.auth import get_password_hash


async def create_user(
        user: UserAuth, session: AsyncSession
) -> dict[str, str] | None:
    try:
        new_user = UserDB(id=uuid4(),
                          username=user.username,
                          password=get_password_hash(user.password))
        session.add(new_user)
        await session.commit()
        return {'username': new_user.username}
    except IntegrityError:
        return
