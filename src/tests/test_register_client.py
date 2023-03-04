from typing import Any, Callable

import pytest
from fastapi import status
from httpx import AsyncClient

from src.api.v1.register import register
from src.tests.conftest import RegisteredUserOne


async def test_post_correct_data(client: AsyncClient,
                                 url_path_for: Callable) -> None:
    response = await client.post(url_path_for(
        register.__name__),
        json={'username': RegisteredUserOne.username,
              'password': RegisteredUserOne.password}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'username': RegisteredUserOne.username}


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
                                   client: AsyncClient,
                                   url_path_for: Callable) -> None:
    response = await client.post(url_path_for(register.__name__),
                                 json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_post_existing_username(registered_client: AsyncClient,
                                      url_path_for: Callable) -> None:
    response = await registered_client.post(url_path_for(
        register.__name__),
        json={'username': RegisteredUserOne.username,
              'password': 123}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
