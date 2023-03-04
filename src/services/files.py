import datetime
import contextlib
import os
import tarfile
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, TextIO
from uuid import UUID, uuid4

import psycopg2
from aioshutil import copyfileobj
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from src.models.base import File
from src.api.v1.schemas import COMPRESSION_TYPE, FileInfo
from src.core.config import DSN, STORAGE_ROOT_DIR

FIRST_LEVEL_SLICE = slice(0, 2)
SECOND_LEVEL_SLICE = slice(2, 4)
THIRD_LEVEL_SLICE = slice(4, None)


async def ping_connections() -> dict[str, float]:
    db_state = ping_database()
    return dict(db='N/A' if db_state is None else db_state)


def ping_database() -> float | None:
    sync_dsn = DSN.replace('asyncpg', 'psycopg2', 1)
    sync_engine = create_engine(sync_dsn)
    try:
        start = time.monotonic()
        with contextlib.closing(sync_engine.raw_connection()) as conn:
            if sync_engine.dialect.do_ping(conn):
                return round(time.monotonic() - start, ndigits=6)
    except psycopg2.OperationalError:
        return


async def retrieve_files(
        user_uuid: str, session: AsyncSession
) -> dict[str, str | list[FileInfo]]:
    statement = select(File).where(File.user_id == user_uuid)
    result = await session.execute(statement)
    files = [file.as_dict() for file, in result.all()]
    return dict(account_id=user_uuid, files=files)


async def upload(
        file: UploadFile, user_path: str, user_uuid: str, session: AsyncSession
) -> FileInfo:
    full_path, path_tail = make_full_path(file.filename, user_path, user_uuid)
    created_ts = await write_to_file_system(file, full_path)
    file_info = FileInfo(
        id=uuid4(),
        name=file.filename,
        created_at=datetime.datetime.fromtimestamp(created_ts),
        path=str(path_tail),
        size=file.size
    )
    await write_to_database(file_info, user_uuid, session)
    return file_info


async def write_to_file_system(file: UploadFile, full_path: Path) -> float:
    check_path(full_path)
    os.makedirs(full_path.parent, exist_ok=True)
    with open(full_path, 'wb') as file_obj:
        await copyfileobj(file.file, file_obj)
    created_ts: float = os.path.getctime(full_path)
    return created_ts


def make_full_path(
        file_name: str, user_path: str, user_uuid: str
) -> tuple[Path, Path]:
    if not user_path.startswith('/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Путь до файла должен начинаться со слэша.')
    if str(user_path).endswith('/'):
        folder = user_path
    else:
        path_obj = Path(user_path)
        folder = path_obj.parent
        file_name = path_obj.name
    path_tail = Path(folder).joinpath(file_name)
    user_dir = get_user_dir(user_uuid)
    full_path = Path(user_dir + str(path_tail))
    return full_path, path_tail


def get_user_dir(user_uuid: str) -> str:
    user_base_dir = '/'.join(
        (user_uuid[FIRST_LEVEL_SLICE],
         user_uuid[SECOND_LEVEL_SLICE],
         user_uuid[THIRD_LEVEL_SLICE])
    )
    return STORAGE_ROOT_DIR + user_base_dir


def check_path(path: Path) -> None:
    if path.is_file():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='По указанному пути файл с таким именем '
                                   'уже загружен.')
    if path.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='По указанному пути имя файла совпадает с '
                                   'существующей директорией.')
    if Path(path.parent).is_file():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='По указанному пути имя конечной папки '
                                   'совпадает с именем существующего файла.')


async def write_to_database(
        file_info: FileInfo, user_uuid: str, session: AsyncSession
) -> None:
    record = File(user_id=user_uuid, **file_info.dict())
    session.add(record)
    await session.commit()


async def get_file_path(
        file_path_or_id: str, user_uuid: str, session: AsyncSession
) -> Path:
    uuid_string = get_valid_uuid(file_path_or_id)
    if uuid_string is None:
        file_path = file_path_or_id
        statement = select(File).where(File.path == file_path)
    else:
        statement = select(File).where(File.id == uuid_string)
    result = await session.execute(statement)
    file = result.scalar()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Файл не найден.')
    user_dir = get_user_dir(user_uuid)
    full_path = Path(user_dir + file.path)
    return full_path


def get_valid_uuid(string):
    try:
        return str(UUID(string, version=4))
    except ValueError:
        return


def iter_file(file_path: Path) -> BinaryIO | TextIO:
    with open(file_path, mode='rb') as file_like:
        yield from file_like


async def get_archive(path_or_id: str,
                      compression_type: COMPRESSION_TYPE,
                      user_uuid: str,
                      session: AsyncSession) -> tuple[BytesIO, str]:
    not_found_exception = HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail='Путь не найден.')
    uuid_string = get_valid_uuid(path_or_id)
    if uuid_string is None:
        path = path_or_id
    else:
        statement = select(File.path).where(File.id == uuid_string)
        result = await session.execute(statement)
        path = result.scalar()
        if path is None:
            raise not_found_exception
    user_dir = get_user_dir(user_uuid)
    full_path = Path(user_dir + path)
    if not full_path.exists():
        raise not_found_exception
    if full_path.is_file():
        paths = [full_path]
    else:
        paths = [path for path in full_path.iterdir() if path.is_file()]

    if compression_type == 'tar':
        return tar_files(paths, user_dir)
    elif compression_type == 'zip':
        return zip_files(paths, user_dir)


def tar_files(paths: list[Path], user_dir: str) -> tuple[BytesIO, str]:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as file_obj:
        for path in paths:
            file_obj.add(
                path,
                arcname=str(path).replace(user_dir, '')
            )
    return buffer, 'application/x-gtar'


def zip_files(paths: list[Path], user_dir: str) -> tuple[BytesIO, str]:
    buffer = BytesIO()
    with zipfile.ZipFile(
            buffer, mode='w', compression=zipfile.ZIP_DEFLATED
    ) as file_obj:
        for path in paths:
            file_obj.write(
                path,
                arcname=str(path).replace(user_dir, '')
            )
    return buffer, 'application/x-zip-compressed'
