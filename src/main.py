from logging import config as logging_config

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.v1 import auth, base, register
from src.core import config
from src.core.logger import LOGGING

PREFIX = '/api/v1'

logging_config.dictConfig(LOGGING)
app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)
app.include_router(register.router, prefix=PREFIX)
app.include_router(auth.router, prefix=PREFIX)
app.include_router(base.router, prefix=PREFIX)


if __name__ == '__main__':
    uvicorn.run(
        'src.main:app',
        host=config.PROJECT_HOST,
        port=config.PROJECT_PORT,
    )
