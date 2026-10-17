# -*- coding: utf-8 -*-
"""Process-level entry points.

These run the real scripts in a subprocess, which is the only way to prove
that ``python -m zira <command>`` routes to the setup CLI *before* importing
the userbot package (and therefore before any Telegram client is created).
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Values that must never show up in any output.
SENTINELS = {
    "APP_ID": "424242",
    "API_HASH": "SENTINEL-HASH-VALUE-9876543210",
    "TG_BOT_TOKEN": "1234567890:SENTINEL-BOT-TOKEN",
    "STRING_SESSION": "SETINEL-STRING-SESSION-VALUE",
}


def run(*args, env_extra=None, timeout=120):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(SENTINELS)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def combined(proc) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


def test_importing_mido_has_no_side_effects():
    proc = run("-c", "import mido, mido.session, mido.config_io, mido.auth, mido.setup_cli; print('clean')")
    assert proc.returncode == 0, combined(proc)
    assert "clean" in proc.stdout


def test_version_command():
    proc = run(str(ROOT / "mido_setup.py"), "version")
    assert proc.returncode == 0, combined(proc)
    assert "Mido helpers" in proc.stdout


def test_help_is_available():
    proc = run(str(ROOT / "mido_setup.py"), "--help")
    assert proc.returncode == 0
    for command in ("setup", "check", "import-session", "sessions", "repair"):
        assert command in proc.stdout


def test_check_masks_every_secret():
    proc = run(str(ROOT / "mido_setup.py"), "check")
    output = combined(proc)
    for key in ("API_HASH", "TG_BOT_TOKEN", "STRING_SESSION"):
        assert SENTINELS[key] not in output, f"{key} leaked into the output"
    # APP_ID is not a secret and stays visible for diagnostics
    assert SENTINELS["APP_ID"] in output
    # and the check itself is meaningful
    assert "البيئة" in output and "الجلسات" in output


def test_python_m_zira_routes_cli_before_starting_the_bot(tmp_path):
    # Point the session dir at an empty folder: importing the userbot package
    # would create `Mido.session` there (Telethon creates the SQLite file on
    # construction) and a lock file.  Seeing neither proves the CLI was routed
    # before `zira.core.session` was ever imported.
    session_dir = tmp_path / "sessions"
    extra = {"SESSION_SOURCE": "file", "SESSION_DIR": str(session_dir)}
    proc = run("-m", "zira", "version", env_extra=extra)
    assert proc.returncode == 0, combined(proc)
    assert "Mido helpers" in proc.stdout
    # the userbot banner must NOT have been printed
    assert "تنصيـب" not in proc.stdout and "Mido Source" not in proc.stdout
    assert "Connecting" not in proc.stdout
    assert not session_dir.exists(), "the userbot package was imported"


def test_python_m_zira_check_is_offline_safe(tmp_path):
    session_dir = tmp_path / "sessions"
    extra = {"SESSION_SOURCE": "file", "SESSION_DIR": str(session_dir)}
    proc = run("-m", "zira", "check", env_extra=extra)
    output = combined(proc)
    for key in ("API_HASH", "TG_BOT_TOKEN", "STRING_SESSION"):
        assert SENTINELS[key] not in output
    assert "البيئة" in output and "الجلسات" in output
    assert not session_dir.exists(), "the userbot package was imported"


def test_ordinary_scripts_are_not_hijacked():
    """`import zira` inside a script named like a CLI command must not route."""
    script = ROOT / "tests" / "_probe_script.py"
    script.write_text(
        "import sys, zira  # noqa: F401\n"
        "print('REAL_IMPORT', sys.argv)\n",
        encoding="utf-8",
    )
    try:
        proc = run("-c", f"import runpy, sys; sys.argv = ['check']; runpy.run_path({str(script)!r}, run_name='__main__')")
    finally:
        script.unlink()
    output = combined(proc)
    # it must either really import zira (and then fail to connect in this test
    # environment) - NEVER print the CLI version banner
    assert "Mido helpers" not in output
