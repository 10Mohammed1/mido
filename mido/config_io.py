# -*- coding: utf-8 -*-
"""Mido · configuration & secret storage helpers.

Only two things live on disk and both are handled here:

``.env``
    the runtime configuration file (git-ignored).  It is written atomically,
    backed up before every change and locked down as much as the platform
    allows (``chmod 600`` on POSIX, ``icacls`` on Windows).

``config.py``
    optional legacy file (git-ignored as well).  It is **never** rewritten by
    the setup — when it exists the values it contains keep working and a
    warning is printed so the user knows which file is authoritative.

Secret *values* are never logged, printed in full or passed on a command
line; use :func:`mask` whenever a value has to be mentioned.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ENV_FILENAME = ".env"
CONFIG_PY = "config.py"

#: Keys the setup knows about.  Order matters: it is the order used when
#: appending missing keys to an existing ``.env``.
KNOWN_KEYS: Tuple[str, ...] = (
    "APP_ID",
    "API_HASH",
    "TG_BOT_TOKEN",
    "TG_BOT_USERNAME",
    "OWNER_ID",
    "ALIVE_NAME",
    "DB_URI",
    "SESSION_DIR",
    "SESSION_NAME",
    "BOT_SESSION_NAME",
    "SESSION_SOURCE",
    "STRING_SESSION",
    "PRIVATE_GROUP_BOT_API_ID",
    "PM_LOGGER_GROUP_ID",
    "HEROKU_API_KEY",
    "HEROKU_APP_NAME",
    "COMMAND_HAND_LER",
    "SUDO_COMMAND_HAND_LER",
    "TZ",
    "NO_LOAD",
)

_LINE_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


def env_path(root: Optional[Path] = None) -> Path:
    return Path(root) / ENV_FILENAME if root is not None else _project_root() / ENV_FILENAME


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def mask(value: Optional[str], *, keep: int = 4) -> str:
    """Render a secret for logs / reports without revealing it."""
    if value is None:
        return "(غير مضبوط)"
    text = str(value)
    if not text:
        return "(فارغ)"
    if len(text) <= keep * 2:
        return "•" * len(text)
    return f"{text[:keep]}…{text[-keep:]} ({len(text)} حرف)"


def load_dotenv_if_available(path: Optional[Path] = None, *, override: bool = False) -> bool:
    """Call ``python-dotenv`` when it is installed.

    ``override=False`` keeps real environment variables winning over the file
    (the same behaviour the project always had).
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return False
    target = path if path is not None else _project_root() / ENV_FILENAME
    try:
        return bool(load_dotenv(dotenv_path=str(target), override=override))
    except Exception:
        return False


def parse_env_text(text: str) -> Dict[str, str]:
    """Parse ``KEY=VALUE`` lines (comments / blank lines ignored)."""
    values: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE_RE.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def read_env_file(path: Optional[Path] = None) -> Dict[str, str]:
    target = path if path is not None else env_path()
    try:
        return parse_env_text(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except OSError:
        return {}


def write_env_file(
    updates: Dict[str, str],
    *,
    path: Optional[Path] = None,
    backup: bool = True,
    harden: bool = True,
) -> Tuple[Path, Optional[Path]]:
    """Merge *updates* into ``.env`` atomically (existing keys stay in place).

    Returns ``(path, backup_path)``.  The previous file is copied aside before
    any change, so a bad value can always be recovered.
    """
    target = path if path is not None else env_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    backup_path: Optional[Path] = None
    if existed and backup:
        backup_path = target.with_name(target.name + f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(target, backup_path)

    lines: List[str] = []
    if existed:
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except OSError:
            lines = []

    seen = set()
    remaining = dict(updates)
    for index, raw_line in enumerate(lines):
        match = _LINE_RE.match(raw_line.strip())
        if not match:
            continue
        key = match.group(1)
        if key in remaining:
            lines[index] = f"{key}={remaining.pop(key)}"
            seen.add(key)

    if remaining:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# ── Mido setup ──────────────────────────────────────────────")
        for key in KNOWN_KEYS:
            if key in remaining:
                lines.append(f"{key}={remaining.pop(key)}")
                seen.add(key)
        for key in sorted(remaining):  # anything not in KNOWN_KEYS
            lines.append(f"{key}={remaining[key]}")
            seen.add(key)

    content = "\n".join(lines).rstrip("\n") + "\n"
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, target)
    if harden:
        harden_file(target)
    return target, backup_path


def harden_file(path: Path) -> str:
    """Restrict *path* to the current user as far as the platform allows."""
    path = Path(path)
    if not path.exists():
        return "missing"
    if platform.system() == "Windows":
        return _harden_windows(path)
    try:
        os.chmod(path, 0o600)
        return "chmod 600"
    except OSError:
        return "unsupported"


def _harden_windows(path: Path) -> str:
    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if not user:
        return "unsupported"
    account = user if "\\" in user else f"{os.environ.get('USERDOMAIN', '')}\\{user}".lstrip("\\")
    try:
        result = subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{account}:(F)"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return "unsupported"
    if result.returncode == 0:
        return f"icacls {account}:(F)"
    return f"icacls failed ({result.returncode})"


def config_py_present(root: Optional[Path] = None) -> bool:
    base = Path(root) if root is not None else _project_root()
    return (base / CONFIG_PY).is_file()


def describe_sensitive_files(root: Optional[Path] = None) -> List[Tuple[str, str]]:
    """Files that must never be committed or shared."""
    base = Path(root) if root is not None else _project_root()
    return [
        (str(base / ENV_FILENAME), "بيانات الدخول والإعدادات السرية"),
        (str(base / CONFIG_PY), "إعدادات محلية (تحتوي المفاتيح في بعض النسخ)"),
        (str(base / "data" / "sessions"), "ملفات جلسات تيليثون (وصول كامل للحساب)"),
        (str(base / "Mido.db"), "قاعدة بيانات البوت"),
        (str(base / "zthon.db"), "قاعدة بيانات البوت"),
    ]


def iter_secret_keys() -> Iterable[str]:
    return ("API_HASH", "TG_BOT_TOKEN", "STRING_SESSION", "HEROKU_API_KEY")
