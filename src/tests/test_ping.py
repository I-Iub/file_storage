from typing import Callable

from fastapi import status
from httpx import AsyncClient

from src.api.v1.base import ping


async def test_unregistered_client(
        client: AsyncClient,
        url_path_for: Callable,
) -> None:
    response = await client.get(url_path_for(ping.__name__))
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('db') is not None
    # assert isinstance(response.json().get('db'), float)


async def test_registered_client(
        registered_client: AsyncClient,
        url_path_for: Callable,
        user_one_token: str
) -> None:
    response = await registered_client.get(
        url_path_for(ping.__name__),
        headers={'Authorization': f'Bearer {user_one_token}'}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('db') is not None
    # assert isinstance(response.json().get('db'), float)
