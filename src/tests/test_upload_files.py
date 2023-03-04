import datetime
import os
import shutil
import uuid
from pathlib import Path
from typing import Callable

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from src.api.v1.base import upload_files
from src.models.base import File
from src.services.files import get_user_dir
from src.tests.conftest import RegisteredUserOne


async def test_unauthorized_client(
        client: AsyncClient,
        registered_client: AsyncClient,
        url_path_for: Callable
) -> None:
    response = await client.post(url_path_for(upload_files.__name__))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await registered_client.post(
        url_path_for(upload_files.__name__)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpload:
    # @classmethod
    # def setup_class(cls):
    #     """ setup any state specific to the execution of the given class
    #     (which usually contains tests).
    #     """

    @classmethod
    def teardown_class(cls) -> None:
        root_test_dir = os.getenv('STORAGE_ROOT_DIR')
        for file_path in Path(root_test_dir).iterdir():
            shutil.rmtree(file_path)

    async def test_post_correct_data_response(
            self,
            registered_client: AsyncClient,
            url_path_for: Callable,
            user_one_token: str,
            project_path: str
    ) -> None:
        file = open(project_path + '/content/user_1/file_1_1.txt', 'rb')
        response = await registered_client.post(
            url_path_for(upload_files.__name__),
            headers={'Authorization': f'Bearer {user_one_token}'},
            files={'file': file},
            data={'path': '/user_1/path/'}
        )
        try:
            uuid.UUID(response.json().get('id'))
        except ValueError:
            assert False

        try:
            datetime.datetime.strptime(
                response.json().get('created_at'), '%Y-%m-%dT%H:%M:%S.%f'
            )
        except ValueError:
            assert False

        assert response.json().get('name') == 'file_1_1.txt'
        assert response.json().get('path') == '/user_1/path/file_1_1.txt'
        assert isinstance(response.json().get('size'), int)

    async def test_db_record_creates(
            self,
            registered_client: AsyncClient,
            url_path_for: Callable,
            user_one_token: str,
            project_path: str,
            db_session: AsyncSession
    ) -> None:
        file = open(project_path + '/content/user_1/file_1_2.txt', 'rb')
        await registered_client.post(
            url_path_for(upload_files.__name__),
            headers={'Authorization': f'Bearer {user_one_token}'},
            files={'file': file},
            data={'path': '/user_1/path/'}
        )
        statement = (
            select(File).where(File.path == '/user_1/path/file_1_2.txt')
        )
        result = await db_session.execute(statement)
        file = result.scalar()
        assert file is not None
        assert file.name == 'file_1_2.txt'
        assert file.user_id == RegisteredUserOne.id

        try:
            uuid.UUID(str(file.id))
        except ValueError:
            assert False

        try:
            datetime.datetime.strftime(file.created_at, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            assert False

    async def test_file_creates(
            self,
            registered_client: AsyncClient,
            url_path_for: Callable,
            user_one_token: str,
            project_path: str,
            db_session: AsyncSession
    ) -> None:
        file = open(project_path + '/content/user_1/file_1_3.txt', 'rb')
        await registered_client.post(
            url_path_for(upload_files.__name__),
            headers={'Authorization': f'Bearer {user_one_token}'},
            files={'file': file},
            data={'path': '/user_1/path/'}
        )
        user_dir = get_user_dir(str(RegisteredUserOne.id))
        assert Path(user_dir + '/user_1/path/file_1_3.txt').is_file()
