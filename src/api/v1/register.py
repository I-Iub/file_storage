from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import User, UserAuth
from src.db.database import get_session
from src.services.register import create_user

router = APIRouter()


@router.post('/register',
             response_model=User,
             status_code=status.HTTP_201_CREATED,
             summary='Регистрация пользователя.',
             description='Метод принимает в теле запроса "username" и '
                         '"password" и создаёт для нового пользователя запись '
                         'в базе данных.')
async def register(user: UserAuth,
                   session: AsyncSession = Depends(get_session)) -> Any:
    user = await create_user(user, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким именем уже существует'
        )
    return user
