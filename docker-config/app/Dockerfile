FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt .

RUN apk add --no-cache postgresql-libs zlib && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev zlib-dev python3-dev jpeg-dev linux-headers && \
    apk add --no-cache --virtual libssldev libressl --repository=http://dl-cdn.alpinelinux.org/alpine/edge/main && \
    pip install --no-cache-dir -r requirements.txt && \
    apk --purge del .build-deps && \
    addgroup -g 1000 docker_user && \
    adduser --disabled-password -u 1000 -G docker_user docker_user && \
    chown docker_user:docker_user .

USER docker_user

COPY docker-config/app/uwsgi.ini .
COPY docker-config/app/entrypoint.sh .
COPY . .

EXPOSE 80

CMD ["sh", "entrypoint.sh"]
