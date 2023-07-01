# syntax=docker/dockerfile:1

FROM python:3.10-buster
ENV PYTHONUNBUFFERED 1
RUN mkdir /code

WORKDIR /code

RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system

COPY . ./

CMD python manage.py runserver & python -m celery -A backend beat -l info --logfile=celery.beat.log --detach & python -m celery -A backend worker -l info --logfile=celery.worker.log --detach --concurrency 4