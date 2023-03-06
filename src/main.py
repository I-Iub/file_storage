from logging import config as logging_config

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.v1 import auth, base, register
from src.core.config import settings
from src.core.logger import LOGGING

PREFIX = '/api/v1'

logging_config.dictConfig(LOGGING)
app = FastAPI(
    title=settings.project_name,
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
        host=settings.project_host,
        port=settings.project_port,
    )
