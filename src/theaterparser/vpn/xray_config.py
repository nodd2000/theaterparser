"""Сборка клиентского конфига Xray из ссылки-ключа.

Поддерживаются ссылки vless:// и trojan:// с транспортами tcp, ws, grpc, xhttp и
шифрованием none / tls / reality. Конфиг поднимает внутри docker-сети SOCKS5- и
HTTP-прокси, весь трафик через них уходит на сервер из ключа.

Запуск: python -m theaterparser.vpn.xray_config "<ссылка>" > config.json
"""

import json
import sys
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

SOCKS_PORT = 1080
HTTP_PORT = 8118

SUPPORTED_SCHEMES = ("vless", "trojan")
SUPPORTED_NETWORKS = ("tcp", "raw", "ws", "grpc", "xhttp", "splithttp")


class XrayLinkError(ValueError):
    pass


def _params(query: str) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(query).items()}


def _stream_settings(params: dict[str, str]) -> dict[str, Any]:
    network = params.get("type", "tcp")
    if network not in SUPPORTED_NETWORKS:
        raise XrayLinkError(f"Транспорт {network!r} не поддерживается")
    if network == "splithttp":
        network = "xhttp"
    if network == "raw":
        network = "tcp"

    security = params.get("security", "none")
    stream: dict[str, Any] = {"network": network, "security": security}

    if security == "tls":
        tls: dict[str, Any] = {"serverName": params.get("sni", "")}
        if fp := params.get("fp"):
            tls["fingerprint"] = fp
        if alpn := params.get("alpn"):
            tls["alpn"] = alpn.split(",")
        if params.get("allowInsecure") in ("1", "true"):
            tls["allowInsecure"] = True
        stream["tlsSettings"] = tls
    elif security == "reality":
        if not params.get("pbk"):
            raise XrayLinkError("Для reality нужен параметр pbk (публичный ключ)")
        stream["realitySettings"] = {
            "serverName": params.get("sni", ""),
            "fingerprint": params.get("fp", "chrome"),
            "publicKey": params["pbk"],
            "shortId": params.get("sid", ""),
            "spiderX": params.get("spx", ""),
        }
    elif security != "none":
        raise XrayLinkError(f"Шифрование {security!r} не поддерживается")

    host = params.get("host", "")
    path = params.get("path", "/")
    if network == "ws":
        stream["wsSettings"] = {"path": path, "host": host}
    elif network == "grpc":
        stream["grpcSettings"] = {
            "serviceName": params.get("serviceName", ""),
            "multiMode": params.get("mode") == "multi",
        }
    elif network == "xhttp":
        stream["xhttpSettings"] = {"path": path, "host": host, "mode": params.get("mode", "auto")}
    elif network == "tcp" and params.get("headerType") == "http":
        raise XrayLinkError("tcp с headerType=http не поддерживается — используйте config.json")

    return stream


def outbound_from_link(link: str) -> dict[str, Any]:
    parts = urlsplit(link.strip())
    if parts.scheme not in SUPPORTED_SCHEMES:
        supported = ", ".join(SUPPORTED_SCHEMES)
        raise XrayLinkError(f"Схема {parts.scheme!r} не поддерживается, нужна одна из: {supported}")
    if not parts.username or not parts.hostname or not parts.port:
        raise XrayLinkError("В ссылке должны быть идентификатор, адрес и порт сервера")

    params = _params(parts.query)
    secret = unquote(parts.username)

    settings: dict[str, Any]
    if parts.scheme == "vless":
        user: dict[str, Any] = {"id": secret, "encryption": params.get("encryption", "none")}
        if flow := params.get("flow"):
            user["flow"] = flow
        settings = {"vnext": [{"address": parts.hostname, "port": parts.port, "users": [user]}]}
    else:
        settings = {
            "servers": [{"address": parts.hostname, "port": parts.port, "password": secret}]
        }

    return {
        "tag": "proxy",
        "protocol": parts.scheme,
        "settings": settings,
        "streamSettings": _stream_settings(params),
    }


def build_config(link: str) -> dict[str, Any]:
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "tag": "socks",
                "listen": "0.0.0.0",
                "port": SOCKS_PORT,
                "protocol": "socks",
                "settings": {"udp": True},
            },
            {"tag": "http", "listen": "0.0.0.0", "port": HTTP_PORT, "protocol": "http"},
        ],
        "outbounds": [outbound_from_link(link), {"tag": "direct", "protocol": "freedom"}],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Использование: xray_config.py <vless://...|trojan://...>", file=sys.stderr)
        return 2
    try:
        config = build_config(argv[1])
    except XrayLinkError as e:
        print(f"Ошибка в ключе: {e}", file=sys.stderr)
        return 1
    json.dump(config, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
