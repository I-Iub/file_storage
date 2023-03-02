import datetime
import os
from pathlib import Path
from typing import BinaryIO, TextIO
from uuid import UUID, uuid4

from aioshutil import copyfileobj
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from src.models.base import File
from src.api.v1.schemas import FileInfo
from src.core.config import STORAGE_ROOT_DIR

FIRST_LEVEL_SLICE = slice(0, 2)
SECOND_LEVEL_SLICE = slice(2, 4)
THIRD_LEVEL_SLICE = slice(4, None)


async def upload_file(
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
    uuid_string = is_valid_uuid(file_path_or_id)
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


def is_valid_uuid(string):
    try:
        return str(UUID(string, version=4))
    except ValueError:
        return


def iter_file(file_path: Path) -> BinaryIO | TextIO:
    with open(file_path, mode='rb') as file_like:
        yield from file_like
