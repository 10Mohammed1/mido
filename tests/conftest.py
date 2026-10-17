# -*- coding: utf-8 -*-
"""Shared pytest fixtures.

The tests never touch the real repository state: every path is redirected to a
temporary directory, every environment variable that can leak in is cleaned up
and no test ever connects to Telegram (Telethon is mocked where needed).
"""

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))


def make_sqlite_session(
    path: Path,
    *,
    dc_id: int = 2,
    server: str = "149.154.167.51",
    port: int = 443,
    auth_key: bytes = b"\x01" * 256,
) -> Path:
    """Create a structurally valid (but fake) Telethon session file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("create table version (version integer primary key)")
        conn.execute("insert into version values (8)")
        conn.execute(
            "create table sessions (dc_id integer primary key, server_address text, "
            "port integer, auth_key blob, takeout_id integer, tmp_auth_key blob)"
        )
        conn.execute(
            "insert into sessions values (?, ?, ?, ?, NULL, NULL)",
            (dc_id, server, port, auth_key),
        )
    return path


@pytest.fixture()
def project(tmp_path, monkeypatch):
    """An isolated project root.

    ``mido.session.project_root`` and ``mido.config_io._project_root`` are
    redirected to the temporary directory and the working directory follows,
    so legacy-path handling is exercised too.
    """
    root = tmp_path / "project"
    (root / "data" / "sessions").mkdir(parents=True)
    monkeypatch.setenv("SESSION_DIR", "data/sessions")
    for key in (
        "SESSION_NAME",
        "BOT_SESSION_NAME",
        "SESSION_SOURCE",
        "MIDO_IGNORE_SESSION_LOCK",
        "STRING_SESSION",
        "APP_ID",
        "API_HASH",
        "TG_BOT_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("mido.session.project_root", lambda: root)
    monkeypatch.setattr("mido.config_io._project_root", lambda: root)
    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def session_factory():
    return make_sqlite_session


@pytest.fixture()
def stub_conversion(monkeypatch):
    """Replace ``auth.write_file_session_from_string`` with a file writer."""
    from fakes import write_fake_session_file

    monkeypatch.setattr("mido.auth.write_file_session_from_string", write_fake_session_file)
    return write_fake_session_file
