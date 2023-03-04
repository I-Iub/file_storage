from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import Token
from src.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.db.database import get_session
from src.services.auth import authenticate_user, create_access_token

router = APIRouter()


@router.post('/auth',
             response_model=Token,
             status_code=status.HTTP_200_OK,
             summary='Получить токен авторизации.',
             description='Метод принимает форму с полями "username" и '
                         '"password" и возвращает токен.')
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session)
) -> Any:
    user = await authenticate_user(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
