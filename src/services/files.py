import datetime
import os
from pathlib import Path
from uuid import uuid4

from aioshutil import copyfileobj
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import File
from src.api.v1.schemas import FileInfo
from src.core.config import STORAGE_ROOT_DIR

FIRST_LEVEL_SLICE = slice(0, 2)
SECOND_LEVEL_SLICE = slice(2, 4)
THIRD_LEVEL_SLICE = slice(4, None)


async def upload_file(
        file: UploadFile, path: str, user_uuid: str, session: AsyncSession
) -> FileInfo:
    user_file_path: Path = make_user_path(user_uuid, path, file.filename)
    created_ts = await write_to_file_system(file, user_file_path)
    file_info = FileInfo(
        id=uuid4(),
        name=file.filename,
        created_at=datetime.datetime.fromtimestamp(created_ts),
        path=str(user_file_path),
        size=file.size
    )
    await write_to_database(file_info, user_uuid, session)
    return file_info


def make_user_path(user_uuid: str, path: str, file_name: str) -> Path:
    if not path.startswith('/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Путь до файла должен начинаться со слэша.')
    if str(path).endswith('/'):
        folder = path
    else:
        path_obj = Path(path)
        folder = path_obj.parent
        file_name = path_obj.name
    file_path = Path(folder).joinpath(file_name)

    user_base_dir = '/'.join(
        (user_uuid[FIRST_LEVEL_SLICE],
         user_uuid[SECOND_LEVEL_SLICE],
         user_uuid[THIRD_LEVEL_SLICE])
    )
    return Path(STORAGE_ROOT_DIR + user_base_dir + str(file_path))


async def write_to_file_system(file: UploadFile, path: Path) -> float:
    check_path(path)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'wb') as file_obj:
        await copyfileobj(file.file, file_obj)
    created_ts: float = os.path.getctime(path)
    return created_ts


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
