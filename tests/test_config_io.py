# -*- coding: utf-8 -*-
"""`.env` handling: parsing, atomic writes, backups, permissions, masking."""

import os
import stat
import sys

import pytest

from mido import config_io


class TestParse:
    def test_comments_blank_lines_and_export(self):
        text = (
            "# comment\n"
            "\n"
            "APP_ID=123\n"
            "export API_HASH='abc def'\n"
            'TG_BOT_TOKEN="quoted-token"\n'
            "not a valid line\n"
            "DB_URI=sqlite:///./x.db?mode=rw\n"
        )
        values = config_io.parse_env_text(text)
        assert values["APP_ID"] == "123"
        assert values["API_HASH"] == "abc def"
        assert values["TG_BOT_TOKEN"] == "quoted-token"
        assert values["DB_URI"] == "sqlite:///./x.db?mode=rw"
        assert len(values) == 4

    def test_read_missing_file_returns_empty(self, tmp_path):
        assert config_io.read_env_file(tmp_path / "missing.env") == {}


class TestWrite:
    def test_creates_new_file_without_backup(self, project):
        path, backup = config_io.write_env_file({"APP_ID": "42"})
        assert path == project / ".env"
        assert backup is None
        assert "APP_ID=42" in path.read_text(encoding="utf-8")

    def test_updates_existing_key_in_place_and_appends_new(self, project):
        (project / ".env").write_text(
            "# header\nAPP_ID=1\nTG_BOT_TOKEN=old\n", encoding="utf-8"
        )
        path, backup = config_io.write_env_file({"APP_ID": "2", "ALIVE_NAME": "Mido"})
        content = path.read_text(encoding="utf-8")
        assert "# header" in content  # comments survive
        assert "APP_ID=2" in content and "APP_ID=1" not in content
        assert "TG_BOT_TOKEN=old" in content  # untouched key kept
        assert "ALIVE_NAME=Mido" in content
        assert backup is not None
        assert "APP_ID=1" in backup.read_text(encoding="utf-8")

    def test_unknown_keys_are_appended_in_sorted_order(self, project):
        path, _ = config_io.write_env_file({"ZZZ_KEY": "1", "AAA_KEY": "2"})
        content = path.read_text(encoding="utf-8")
        assert content.index("AAA_KEY") < content.index("ZZZ_KEY")

    def test_file_is_private_on_posix(self, project):
        if sys.platform == "win32":
            pytest.skip("POSIX permissions")
        path, _ = config_io.write_env_file({"APP_ID": "1"})
        mode = stat.S_IMODE(os.stat(path).st_mode)
        assert mode == 0o600

    def test_harden_missing_file(self, tmp_path):
        assert config_io.harden_file(tmp_path / "nope") == "missing"


class TestMask:
    def test_none_and_empty(self):
        assert "غير مضبوط" in config_io.mask(None)
        assert "فارغ" in config_io.mask("")

    def test_short_values_are_fully_hidden(self):
        assert config_io.mask("abc") == "•••"

    def test_long_value_shows_edges_only(self):
        masked = config_io.mask("1234567890abcdef", keep=4)
        assert masked.startswith("1234")
        assert "cdef" in masked
        assert "567890ab" not in masked


class TestSensitiveFiles:
    def test_report_lists_env_and_sessions(self, project):
        entries = dict(config_io.describe_sensitive_files(project))
        assert any(str(project / ".env") == key for key in entries)
        assert any("sessions" in key for key in entries)
