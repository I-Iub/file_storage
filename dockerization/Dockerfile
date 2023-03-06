FROM python:3.10-slim

WORKDIR /code

COPY ../requirements.txt .

RUN pip3 install --upgrade pip \
    && pip3 install -r requirements.txt --no-cache-dir

COPY ../src ./src/
COPY ../migrations ./migrations
COPY ../alembic.ini .

EXPOSE 8000

ENTRYPOINT ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "src.main:app"]
