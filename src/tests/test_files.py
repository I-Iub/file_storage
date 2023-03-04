from typing import Callable

from fastapi import status
from httpx import AsyncClient

from src.api.v1.base import get_files
from src.tests.conftest import RegisteredUserOne


async def test_unauthorized_client(
        client: AsyncClient,
        registered_client: AsyncClient,
        url_path_for: Callable,
) -> None:
    response = await client.get(url_path_for(get_files.__name__))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await registered_client.get(url_path_for(get_files.__name__))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_registered_client(
        registered_client: AsyncClient,
        user_one_token: str,
        url_path_for: Callable,
        create_files: Callable,
        project_path: str
) -> None:
    response = await registered_client.get(
        url_path_for(get_files.__name__),
        headers={'Authorization': f'Bearer {user_one_token}'}
    )
    files = response.json().get('files')
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('account_id') == str(RegisteredUserOne.id)
    assert isinstance(files, list)
    assert len(files) == 3
    assert files[0] == {
        'id': 'ffff0101-22ba-4327-b711-db8502bcfc27',
        'name': 'file_1_1.txt',
        'created_at': '2023-03-01T12:01:00',
        'path': '/user_1/file_1_1.txt',
        'size': 1,
    }
