# -*- coding: utf-8 -*-
"""Windows-portability guards.

Two kinds of checks:

* **static** — the startup path must not contain Linux-only imports, shell
  escapes or `os.execle` (which behaves differently on Windows),
* **behavioural** — the restart helper must spawn a child on Windows and use
  ``execv`` on POSIX.
"""

import importlib.util
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = (
    (r'\.replace\(\s*" "\s*,\s*"\\\\ "\s*\)', "shell-style space escaping in a subprocess argv"),
    (r"\bos\.execle\(", "os.execle is not portable"),
    (r"^[ \t]*import[ \t]+(fcntl|pty|termios|resource|pwd|grp|crypt)\b", "Linux-only module import"),
    (r"^[ \t]*from[ \t]+(fcntl|pty|termios|resource|pwd|grp|crypt)[ \t]+import", "Linux-only module import"),
)


def runtime_files():
    for base in ("zira", "mido"):
        for path in sorted((ROOT / base).rglob("*.py")):
            if "__pycache__" not in path.parts:
                yield path
    yield ROOT / "mido_setup.py"


@pytest.mark.parametrize("pattern,reason", FORBIDDEN)
def test_forbidden_patterns_are_absent(pattern, reason):
    regex = re.compile(pattern, re.MULTILINE)
    hits = []
    for path in runtime_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in regex.finditer(text):
            line = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(ROOT)}:{line} {match.group(0).strip()}")
    assert hits == [], f"{reason}: {hits}"


def test_setup_module_never_imports_the_userbot_package():
    """Importing the setup CLI must not start any Telegram client."""
    files = [ROOT / "mido_setup.py", *sorted((ROOT / "mido").glob("*.py"))]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^[ \t]*(import[ \t]+zira|from[ \t]+zira)\b", text, re.MULTILINE), path


def test_main_dispatches_cli_before_importing_the_package():
    """`python -m zira <cmd>` must route before the clients are created.

    runpy imports the package before ``__main__.py``, so the effective guard
    lives in ``zira/__init__.py`` and must precede the client imports.  The
    dispatch in ``__main__.py`` is kept for direct script runs.
    """
    package = (ROOT / "zira" / "__init__.py").read_text(encoding="utf-8")
    assert "_CLI_COMMANDS" in package
    assert package.index("_is_cli_invocation") < package.index("from .core.session import zedub")
    for command in ('"setup"', '"check"', '"import-session"', '"sessions"', '"repair"', '"version"'):
        assert command in package

    main_text = (ROOT / "zira" / "__main__.py").read_text(encoding="utf-8")
    assert main_text.index("CLI_COMMANDS") < main_text.index("import zira")


def test_main_reconfigures_the_console_encoding():
    text = (ROOT / "zira" / "__main__.py").read_text(encoding="utf-8")
    assert 'reconfigure(encoding="utf-8", errors="replace")' in text


def test_main_releases_the_session_lock_on_shutdown():
    text = (ROOT / "zira" / "__main__.py").read_text(encoding="utf-8")
    assert "SESSION_LOCK.release()" in text
    assert "def _shutdown()" in text


def test_session_layer_is_used_by_the_bot():
    text = (ROOT / "zira" / "core" / "session.py").read_text(encoding="utf-8")
    assert "acquire_session_lock" in text
    assert "locate_session" in text
    assert "session_source" in text


def test_sample_config_exposes_session_settings():
    text = (ROOT / "sample_config.py").read_text(encoding="utf-8")
    for key in ("SESSION_DIR", "SESSION_NAME", "BOT_SESSION_NAME", "SESSION_SOURCE"):
        assert key in text


def test_noload_accepts_commas_and_spaces(monkeypatch):
    import importlib

    import sample_config

    monkeypatch.setenv("NO_LOAD", "alpha, beta gamma")
    reloaded = importlib.reload(sample_config)
    assert reloaded.Config.NO_LOAD == ["alpha", "beta", "gamma"]
    monkeypatch.delenv("NO_LOAD", raising=False)
    importlib.reload(sample_config)


def test_vps_noload_always_defaults():
    """A fresh clone has no config.py — the plugin loader must not crash."""
    text = (ROOT / "zira" / "utils" / "startup.py").read_text(encoding="utf-8")
    assert text.count("VPS_NOLOAD = [") == 3


def test_requirements_splits_linux_only_packages():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for name in ("py-tgcalls", "pyrofork", "mautrix"):
        lines = [line for line in text.splitlines() if line.startswith(name)]
        assert lines and 'sys_platform == "linux"' in lines[0], name
    assert "GitPython" in text  # needed by the update plugins on every OS


# ── restart helper behaviour ─────────────────────────────────────────────────
def load_restart_module():
    spec = importlib.util.spec_from_file_location(
        "mido_restart_under_test", ROOT / "zira" / "core" / "restart.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_restart_uses_execv_on_posix(monkeypatch):
    module = load_restart_module()
    captured = {}

    def fake_execv(path, argv):
        captured["path"] = path
        captured["argv"] = list(argv)
        raise SystemExit(0)

    monkeypatch.setattr(module.os, "name", "posix")
    monkeypatch.setattr(module.os, "execv", fake_execv)
    with pytest.raises(SystemExit):
        module.restart_process()
    assert captured["path"] == sys.executable
    assert captured["argv"] == [sys.executable, "-m", "zira"]


def test_restart_spawns_a_child_on_windows(monkeypatch):
    module = load_restart_module()
    captured = {}

    class FakePopen:
        def __init__(self, argv, **kwargs):
            captured["argv"] = list(argv)
            captured["kwargs"] = kwargs

    def fake_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(module.os, "name", "nt")
    monkeypatch.setattr(module.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(module.os, "_exit", fake_exit)
    with pytest.raises(SystemExit):
        module.restart_process()
    assert captured["argv"] == [sys.executable, "-m", "zira"]
    assert captured["kwargs"]["close_fds"] is True
    assert captured["kwargs"]["cwd"] == os.getcwd()
