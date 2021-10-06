# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_ENV=development

CMD ["python3", "-m", "flask", "run", "--host=127.0.0.1"]