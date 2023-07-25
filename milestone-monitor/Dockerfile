FROM python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /code

WORKDIR /code

RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "backend.wsgi"]