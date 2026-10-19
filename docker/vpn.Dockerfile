FROM python:3.12-alpine

ARG XRAY_VERSION=26.7.28

RUN apk add --no-cache ca-certificates \
    && wget -q -O /tmp/xray.zip \
       "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" \
    && mkdir -p /usr/local/share/xray \
    && unzip -q /tmp/xray.zip -d /tmp/xray \
    && install -m 755 /tmp/xray/xray /usr/local/bin/xray \
    && mv /tmp/xray/*.dat /usr/local/share/xray/ \
    && rm -rf /tmp/xray /tmp/xray.zip

COPY src/theaterparser/vpn/xray_config.py /opt/xray_config.py
COPY docker/vpn/entrypoint.sh /entrypoint.sh
COPY docker/vpn/healthcheck.py /healthcheck.py

EXPOSE 1080 8118
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
