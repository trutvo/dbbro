import pymysql

from dbbro.db.connection import connect
from dbbro.db.models import DatabaseConfig


class _FakeConnection:
    def __init__(self):
        self.cursorclass = None


def test_connect_returns_a_connection_for_valid_config(monkeypatch):
    fake_conn = _FakeConnection()
    monkeypatch.setattr(pymysql, "connect", lambda **kwargs: fake_conn)
    config = DatabaseConfig(host="h", name="n", user="u", password="p")

    result = connect(config)

    assert result is fake_conn


def test_connect_uses_default_port_when_none_given(monkeypatch):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return _FakeConnection()

    monkeypatch.setattr(pymysql, "connect", fake_connect)
    config = DatabaseConfig(host="h", name="n", user="u", password="p")

    connect(config)

    assert captured["port"] == 3306


def test_connect_uses_given_port(monkeypatch):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return _FakeConnection()

    monkeypatch.setattr(pymysql, "connect", fake_connect)
    config = DatabaseConfig(host="h", name="n", user="u", password="p", port=1234)

    connect(config)

    assert captured["port"] == 1234
