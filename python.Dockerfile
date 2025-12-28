FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

