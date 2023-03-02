import datetime
from uuid import UUID

from pydantic import BaseModel


class Ping(BaseModel):
    db: int
    cache: int


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
