import asyncio
import datetime
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Generator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    create_async_engine)
from sqlalchemy.sql.expression import update

from src.api.v1.auth import login_for_access_token
from src.api.v1.register import register
from src.db.database import Base, get_session
from src.main import app
from src.models.base import File, User

load_dotenv()


@pytest.fixture(scope='session')
def event_loop() -> Generator[Any, None, None]:
    """
    Creates an instance of the default event loop for the test session.
    """
    if sys.platform.startswith("win") and sys.version_info[:2] >= (3, 8):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing
        # down tests https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def _database_url() -> str:
    return os.getenv('DSN_TEST')


@pytest.fixture(scope='session')
def init_database() -> Any:
    return Base.metadata.create_all


@pytest_asyncio.fixture(scope='session')
async def test_engine(_database_url: str) -> AsyncEngine:
    return create_async_engine(_database_url, echo=True)


@pytest_asyncio.fixture
async def test_app(db_session: AsyncSession) -> FastAPI:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_db
    return app


@pytest_asyncio.fixture
async def url_path_for(test_app: FastAPI) -> Callable:
    return test_app.url_path_for


@pytest_asyncio.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=test_app,
                           base_url='http://test.te') as async_client:
        yield async_client


@dataclass
class RegisteredUserOne:
    id = uuid.UUID('11111111-22ba-4327-b711-db8502bcfc27')
    username = 'test_user_one'
    password = 'test_user_one_password'


@dataclass
class RegisteredUserTwo:
    id = uuid.UUID('22222222-22ba-4327-b711-db8502bcfc27')
    username = 'test_user_two'
    password = 'test_user_two_password'


@pytest_asyncio.fixture
async def registered_client(
        test_app: Callable,
        url_path_for: Callable,
        db_session: AsyncSession
) -> AsyncGenerator[list[AsyncClient], None]:
    async with AsyncClient(app=test_app,
                           base_url='http://test.te') as async_client:
        await async_client.post(url_path_for(
            register.__name__),
            json={'username': RegisteredUserOne.username,
                  'password': RegisteredUserOne.password}
        )
        statement = (
            update(User).where(User.username == RegisteredUserOne.username)
            .values(id=RegisteredUserOne.id)
        )
        await db_session.execute(statement)
        yield async_client


@pytest_asyncio.fixture
async def user_one_token(url_path_for: Callable,
                         registered_client: AsyncClient) -> str:
    response = await registered_client.post(
        url_path_for(login_for_access_token.__name__),
        data={'username': RegisteredUserOne.username,
              'password': RegisteredUserOne.password}
    )
    return response.json().get('access_token')


@pytest_asyncio.fixture
async def registered_client_two(
        test_app: Callable,
        url_path_for: Callable,
        db_session: AsyncSession
) -> AsyncGenerator[list[AsyncClient], None]:
    async with AsyncClient(app=test_app,
                           base_url='http://test.te') as async_client:
        await async_client.post(url_path_for(
            register.__name__),
            json={'username': RegisteredUserTwo.username,
                  'password': RegisteredUserTwo.password}
        )
        statement = (
            update(User).where(User.username == RegisteredUserTwo.username)
            .values(id=RegisteredUserTwo.id)
        )
        await db_session.execute(statement)
        yield async_client


@pytest_asyncio.fixture
async def project_path() -> str:
    return os.path.dirname(__file__)


@pytest_asyncio.fixture
async def create_files(registered_client: AsyncClient,
                       registered_client_two: AsyncClient,
                       db_session: AsyncSession,
                       project_path: str) -> None:
    file_infos = [
        {'id': uuid.UUID('ffff0101-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_1_1.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 1),
         'path': '/user_1/file_1_1.txt',
         'size': 1,
         'user_id': RegisteredUserOne.id},
        {'id': uuid.UUID('ffff0102-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_1_2.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 2),
         'path': '/user_1/file_1_2.txt',
         'size': 1,
         'user_id': RegisteredUserOne.id},
        {'id': uuid.UUID('ffff0103-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_1_3.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 3),
         'path': '/user_1/file_1_3.txt',
         'size': 1,
         'user_id': RegisteredUserOne.id},

        {'id': uuid.UUID('ffff0201-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_2_1.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 1),
         'path': '/user_2/file_2_1.txt',
         'size': 1,
         'user_id': RegisteredUserTwo.id},
        {'id': uuid.UUID('ffff0202-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_2_2.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 2),
         'path': '/user_2/file_2_2.txt',
         'size': 1,
         'user_id': RegisteredUserTwo.id},
        {'id': uuid.UUID('ffff0203-22ba-4327-b711-db8502bcfc27'),
         'name': 'file_2_3.txt',
         'created_at': datetime.datetime(2023, 3, 1, 12, 3),
         'path': '/user_2/file_2_3.txt',
         'size': 1,
         'user_id': RegisteredUserTwo.id}
    ]
    await db_session.execute(insert(File).values(file_infos))
    await db_session.commit()
