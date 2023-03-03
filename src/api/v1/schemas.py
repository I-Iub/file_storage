import datetime
import typing
from uuid import UUID

from pydantic import BaseModel

COMPRESSION_TYPE = typing.Literal['tar', 'zip']


class Ping(BaseModel):
    db: float | typing.Literal['N/A']


class User(BaseModel):
    username: str


class UserAuth(User):
    password: str


class UserInDB(UserAuth):
    uuid: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class FileInfo(BaseModel):
    id: UUID
    name: str
    created_at: datetime.datetime
    path: str
    size: int


class UserFiles(BaseModel):
    account_id: str
    files: list[FileInfo]
