import os
import shutil
from pathlib import Path
from typing import Callable

import pytest
from fastapi import status
from httpx import AsyncClient

from src.api.v1.base import download_files
from src.services.files import get_user_dir
from src.tests.conftest import RegisteredUserOne


async def test_unauthorized_client(
        client: AsyncClient,
        registered_client: AsyncClient,
        url_path_for: Callable
) -> None:
    response = await client.get(url_path_for(download_files.__name__))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await registered_client.get(
        url_path_for(download_files.__name__)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


class Test:
    project_path = os.path.dirname(__file__)
    user_dir = get_user_dir(str(RegisteredUserOne.id))

    @classmethod
    def setup_class(cls) -> None:
        content_path = cls.project_path + '/content/user_1/file_1_1.txt'
        os.makedirs(cls.user_dir + '/user_1', exist_ok=True)
        shutil.copyfile(content_path, cls.user_dir + '/user_1/file_1_1.txt')

    @classmethod
    def teardown_class(cls) -> None:
        root_test_dir = os.getenv('STORAGE_ROOT_DIR')
        for file_path in Path(root_test_dir).iterdir():
            shutil.rmtree(file_path)

    async def test_authorized_client_get(
            self,
            registered_client: AsyncClient,
            user_one_token: str,
            url_path_for: Callable,
            create_files: Callable
    ) -> None:
        response = await registered_client.get(
            url_path_for(download_files.__name__),
            headers={'Authorization': f'Bearer {user_one_token}'},
            params={'path': 'ffff0101-22ba-4327-b711-db8502bcfc27'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b'user_1\n'

    @pytest.mark.parametrize('params', ['tar', 'zip', ])
    async def test__authorized_client_get_2(
            self,
            params: dict[str, str],
            registered_client: AsyncClient,
            user_one_token: str,
            url_path_for: Callable,
            create_files: Callable
    ) -> None:
        response = await registered_client.get(
            url_path_for(download_files.__name__),
            headers={'Authorization': f'Bearer {user_one_token}'},
            params={'path': 'ffff0101-22ba-4327-b711-db8502bcfc27',
                    'compression': params}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0
