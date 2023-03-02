from typing import Any

from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import FileInfo, Ping, UserInDB
from src.db.database import get_session
from src.services.files import upload_file
from src.services.auth import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@router.get('/ping',
            response_model=Ping,
            status_code=status.HTTP_200_OK,
            summary='Статус активности связанных сервисов.',
            description='Получить информацию о времени доступа ко всем '
                        'связанным сервисам')
async def ping(current_user: UserInDB = Depends(get_current_user)) -> Any:
    return Ping(db=1, cache=2)


@router.get('/files',
            status_code=status.HTTP_200_OK,
            summary='Информация о загруженных файлах.',
            description='Вернуть информацию о ранее загруженных файлах.')
async def get_files(current_user: UserInDB = Depends(get_current_user)):
    pass


@router.post('/files/upload',
             response_model=FileInfo,
             status_code=status.HTTP_201_CREATED,
             summary='Загрузить файл в хранилище.',
             description='Метод загрузки файла в хранилище. Для загрузки '
                         'заполняется полный путь до файла, в который будет '
                         'загружен/переписан загружаемый файл. Если нужные '
                         'директории не существуют, то они должны быть '
                         'созданы автоматически. Так же, есть возможность '
                         'указать только путь до директории. В этом случае '
                         'имя создаваемого файла будет создано в соответствии '
                         'с передаваемым именем файла. Если путь заканчивается'
                         'на слэш ("/"), то он считается путём до директории, '
                         'если не заканчивается на слэш, то путём до файла.')
async def upload_files(file: UploadFile,
                       path: str = Form(),
                       current_user: UserInDB = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)) -> Any:
    file_info = await upload_file(file, path, current_user.uuid, session)
    return file_info


@router.get('/files/download',
            status_code=status.HTTP_201_CREATED,
            summary='Скачать загруженный файл.',
            description='Скачивание ранее загруженного файла. Возможность '
                        'скачивания есть как по переданному пути до файла, '
                        'так и по идентификатору.')
async def download_files(current_user: UserInDB = Depends(get_current_user)):
    pass
