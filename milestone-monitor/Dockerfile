ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
# COPY Pipfile Pipfile.lock /code/
# RUN pipenv install --deploy --system
COPY . /code

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "backend.wsgi"]
