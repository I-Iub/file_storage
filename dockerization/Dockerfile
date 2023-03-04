FROM python:3.10-slim

WORKDIR /code

COPY ../requirements.txt .

RUN pip3 install --upgrade pip \
    && pip3 install -r requirements.txt

COPY ../src ./src/
COPY ../migrations ./migrations
COPY ../alembic.ini .
