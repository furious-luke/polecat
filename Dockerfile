FROM python:3.7-alpine3.7

LABEL maintainer="furious.luke@gmail.com"
LABEL description="Development Polecat image."

ENV TZ=Australia/Melbourne

RUN    apk add --no-cache --update \
	bash postgresql-libs tzdata \
    && pip install pipenv \
    && rm -rf /var/lib/apt/lists/* /root/.cache \
    && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && mkdir -p /app

ADD setup.py /app/
ADD Pipfile /app/
ADD Pipfile.lock /app/
WORKDIR /app

RUN    apk add --no-cache --virtual .build-deps \
        postgresql-dev gcc git musl-dev \
    && pipenv install -d --three \
    && apk --purge del .build-deps \
    && rm -rf /var/lib/apt/lists/* /root/.cache

ADD polecat /app/polecat
ADD tests /app/tests
ADD scripts /app/scripts

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8000
CMD pipenv run pytest
