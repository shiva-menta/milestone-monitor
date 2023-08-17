# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /code

WORKDIR /code

RUN apt-get update && apt-get install -y \
  libpq-dev \
  gcc \
  && rm -rf /var/lib/apt/lists/* 

RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install

COPY . .

# Development
# CMD ["sh", "-c", "pipenv run gunicorn --bind 0.0.0.0:8000 -w 1 backend.wsgi"]

# Production
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]