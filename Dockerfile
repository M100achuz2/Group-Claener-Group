FROM python:3.7-slim as base

RUN pip install pyrogram tgcrypto aiojobs async_timeout

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "main.py"]
