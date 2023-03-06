import os

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, PostgresDsn

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    project_name: str = Field('File storage', env='PROJECT_NAME')
    project_host: str = Field('127.0.0.1', env='PROJECT_HOST')
    project_port: int = Field(8080, env='PROJECT_PORT')
    dsn: PostgresDsn
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = Field(30,
                                             env='ACCESS_TOKEN_EXPIRE_MINUTES')
    storage_root_dir: str

    class Config:
        env_file = BASE_DIR + '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
