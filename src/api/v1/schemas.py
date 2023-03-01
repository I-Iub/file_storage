from pydantic import BaseModel


class Ping(BaseModel):
    db: int
    cache: int


class User(BaseModel):
    username: str


class UserAuth(User):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class FilePath(BaseModel):
    path: str


class FileInfo(BaseModel):
    id: str
    name: str
    created_ad: str
    path: str
    size: int
    is_downloadable: bool
