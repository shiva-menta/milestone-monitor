# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster
ENV PYTHONUNBUFFERED 1
RUN mkdir /code

WORKDIR /code

RUN pip install pipenv
# COPY requirements.txt /code/
COPY Pipfile Pipfile.lock ./
RUN pipenv install

COPY . .

CMD python manage.py runserver