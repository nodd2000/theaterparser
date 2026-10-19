import json

import pytest

from theaterparser.vpn.xray_config import (
    HTTP_PORT,
    SOCKS_PORT,
    XrayLinkError,
    build_config,
    main,
)

UUID = "1b0c2a4e-5f6d-4e3a-9b8c-7d6e5f4a3b2c"

REALITY = (
    f"vless://{UUID}@vpn.example.com:443?type=tcp&security=reality&pbk=PUBKEY"
    "&fp=chrome&sni=www.microsoft.com&sid=ab12&spx=%2F&flow=xtls-rprx-vision"
    "&encryption=none#my-server"
)


def test_vless_reality() -> None:
    config = build_config(REALITY)
    proxy = config["outbounds"][0]
    assert proxy["protocol"] == "vless"
    assert proxy["settings"]["vnext"] == [
        {
            "address": "vpn.example.com",
            "port": 443,
            "users": [{"id": UUID, "encryption": "none", "flow": "xtls-rprx-vision"}],
        }
    ]
    assert proxy["streamSettings"] == {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
            "serverName": "www.microsoft.com",
            "fingerprint": "chrome",
            "publicKey": "PUBKEY",
            "shortId": "ab12",
            "spiderX": "/",
        },
    }
    ports = {inbound["protocol"]: inbound["port"] for inbound in config["inbounds"]}
    assert ports == {"socks": SOCKS_PORT, "http": HTTP_PORT}


def test_vless_ws_tls() -> None:
    link = (
        f"vless://{UUID}@1.2.3.4:8443?type=ws&security=tls&sni=cdn.example.com"
        "&host=cdn.example.com&path=%2Fws&alpn=h2,http/1.1"
    )
    stream = build_config(link)["outbounds"][0]["streamSettings"]
    assert stream["wsSettings"] == {"path": "/ws", "host": "cdn.example.com"}
    assert stream["tlsSettings"] == {"serverName": "cdn.example.com", "alpn": ["h2", "http/1.1"]}


def test_trojan_grpc() -> None:
    link = (
        "trojan://p%40ss@t.example.com:443?type=grpc&serviceName=svc&security=tls&sni=t.example.com"
    )
    proxy = build_config(link)["outbounds"][0]
    assert proxy["settings"]["servers"][0]["password"] == "p@ss"
    assert proxy["streamSettings"]["grpcSettings"] == {"serviceName": "svc", "multiMode": False}


@pytest.mark.parametrize(
    "link",
    [
        "vmess://abc",
        f"vless://{UUID}@host?security=none",
        f"vless://{UUID}@host:443?security=reality",
        f"vless://{UUID}@host:443?type=quic",
    ],
)
def test_invalid_links(link: str) -> None:
    with pytest.raises(XrayLinkError):
        build_config(link)


def test_main_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["xray_config.py", REALITY]) == 0
    assert json.loads(capsys.readouterr().out)["outbounds"][1]["protocol"] == "freedom"
