FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN python -m pip install .

COPY src src