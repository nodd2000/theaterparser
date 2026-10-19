#!/bin/sh
# Готовый конфиг в docker/vpn/custom/config.json имеет приоритет над ссылкой XRAY_LINK.
set -eu

CUSTOM=/etc/xray/custom/config.json
GENERATED=/tmp/xray-config.json

if [ -f "$CUSTOM" ]; then
    CONFIG="$CUSTOM"
elif [ -n "${XRAY_LINK:-}" ]; then
    python3 /opt/xray_config.py "$XRAY_LINK" > "$GENERATED"
    CONFIG="$GENERATED"
else
    echo "Не задан ключ: укажите XRAY_LINK в .env или положите docker/vpn/custom/config.json" >&2
    exit 1
fi

exec xray run -c "$CONFIG"
