"""Проверка туннеля: t.me должен открываться через локальный HTTP-прокси Xray."""

import sys
import urllib.request

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"https": "http://127.0.0.1:8118"})
)
try:
    opener.open("https://t.me", timeout=10)
except OSError as e:
    print(f"t.me недоступен через прокси: {e}", file=sys.stderr)
    sys.exit(1)
