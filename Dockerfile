FROM alpine:3.11

ENV DRONE_CLI=https://github.com/drone/drone-cli/releases/latest/download/drone_linux_amd64.tar.gz

RUN apk add --update \
    python3 \
    sqlite \
    curl \
    && rm -rf /var/cache/apk/*

RUN curl -L $DRONE_CLI | tar zx && install -t /usr/local/bin drone

VOLUME /data

ADD globalize.py /globalize.py
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT /entrypoint.sh
