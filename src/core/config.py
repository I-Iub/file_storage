import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = os.getenv('PROJECT_NAME', 'File storage')
PROJECT_HOST = os.getenv('PROJECT_HOST', '127.0.0.1')
PROJECT_PORT = int(os.getenv('PROJECT_PORT', '8080'))


DSN = os.getenv(
    'DSN', 'postgresql+asyncpg://postgres:postgres@localhost:5432/storage'
)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

STORAGE_ROOT_DIR = str(os.getenv('STORAGE_ROOT_DIR'))
