from typing import Any, Callable

import pytest
from fastapi import status
from httpx import AsyncClient

from src.api.v1.auth import login_for_access_token
from src.tests.conftest import RegisteredUserOne


async def test_post_correct_data(registered_client: AsyncClient,
                                 url_path_for: Callable) -> None:
    response = await registered_client.post(url_path_for(
        login_for_access_token.__name__),
        data={'username': RegisteredUserOne.username,
              'password': RegisteredUserOne.password}
    )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json().get('access_token'), str)
    assert response.json().get('token_type') == 'bearer'


async def test_post_wrong_username(registered_client: AsyncClient,
                                   url_path_for: Callable) -> None:
    response = await registered_client.post(url_path_for(
        login_for_access_token.__name__),
        data={'username': RegisteredUserOne.username,
              'password': 'wrong'}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_post_wrong_password(registered_client: AsyncClient,
                                   url_path_for: Callable) -> None:
    response = await registered_client.post(url_path_for(
        login_for_access_token.__name__),
        data={'username': 'wrong',
              'password': RegisteredUserOne.password}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    'data',
    [
        {'username': RegisteredUserOne.username},
        {},
        {'password': RegisteredUserOne.password},
        {'username': RegisteredUserOne.username,
         'password': ''},
        {'username': '',
         'password': RegisteredUserOne.password},
    ]
)
async def test_post_incorrect_data(data: dict[str, Any],
                                   registered_client: AsyncClient,
                                   url_path_for: Callable) -> None:
    response = await registered_client.post(url_path_for(
        login_for_access_token.__name__),
        data=data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_unregistered_client_post(client: AsyncClient,
                                        url_path_for: Callable) -> None:
    response = await client.post(url_path_for(
        login_for_access_token.__name__),
        data={'username': RegisteredUserOne.username,
              'password': RegisteredUserOne.password}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
