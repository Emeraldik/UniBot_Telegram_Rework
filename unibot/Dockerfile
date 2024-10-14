FROM python:3.11-buster AS builder

RUN pip install poetry==1.8.0

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /code

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --without dev

FROM python:3.11-slim-buster AS runtime

RUN pip install poetry==1.8.0

ENV VIRTUAL_ENV=/code/.venv \
    PATH="/code/.venv/bin:$PATH"

WORKDIR /code

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY pyproject.toml poetry.lock ./
COPY project ./project

CMD [ "poetry", "run", "python", "project" ]