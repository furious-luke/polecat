FROM python:3.7-alpine3.7

LABEL maintainer="furious.luke@gmail.com"
LABEL description="Development Polecat image."

ENV TZ=Australia/Melbourne

RUN    apk add --no-cache --update \
	bash git postgresql-libs tzdata \
    && pip install pipenv \
    && rm -rf /var/lib/apt/lists/* /root/.cache \
    && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && mkdir -p /app

ADD setup.py /app/
ADD polecat /app/polecat
WORKDIR /app

RUN     apk add --no-cache --virtual .build-deps postgresql-dev \
    && python setup.py install \
    && apk --purge del .build-deps \
    && rm -rf /var/lib/apt/lists/* /root/.cache

EXPOSE 8000
