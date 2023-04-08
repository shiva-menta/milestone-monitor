# syntax=docker/dockerfile:1

FROM python:3.10-buster
ENV PYTHONUNBUFFERED 1
RUN mkdir /code

WORKDIR /code

RUN pip install pipenv
# COPY requirements.txt /code/
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system

COPY . ./

CMD python manage.py runserver