# -*- coding: utf-8 -*-
"""Mido · session store.

Single source of truth for:

* **where** the Telethon sessions live (``data/sessions/`` by default, with a
  transparent fall-back to the old in-repo location so an already running
  deployment keeps working after an upgrade),
* **which source** is used when both a file session and ``STRING_SESSION``
  are configured (documented precedence, see :func:`session_source`),
* **how** two processes are stopped from writing the same session file at the
  same time (:class:`SessionLock`),
* import / validation / backup helpers for ``.session`` files.

This module never touches Telegram: it only reasons about files.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_SESSION_DIR = "data/sessions"
DEFAULT_SESSION_NAME = "Mido"
DEFAULT_BOT_SESSION_NAME = "ZedTgbot"
SESSION_EXTENSION = ".session"
SIDECAR_SUFFIXES = ("-journal", "-wal", "-shm")
SQLITE_MAGIC = b"SQLite format 3\x00"


# ── locations ────────────────────────────────────────────────────────────────
def project_root() -> Path:
    """Directory that contains ``zira/``, ``mido/`` and ``mido_setup.py``."""
    return Path(__file__).resolve().parent.parent


def resolve_session_dir(explicit: Optional[str] = None) -> Path:
    """Return the configured session directory as an absolute path."""
    raw = explicit or os.environ.get("SESSION_DIR") or DEFAULT_SESSION_DIR
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = project_root() / path
    return path


def session_name(kind: str = "user") -> str:
    """Session base name (without ``.session``) for the user or bot client."""
    if kind == "bot":
        return os.environ.get("BOT_SESSION_NAME") or DEFAULT_BOT_SESSION_NAME
    return os.environ.get("SESSION_NAME") or DEFAULT_SESSION_NAME


@dataclass(frozen=True)
class SessionLocation:
    """A resolved session file (never contains session *contents*)."""

    name: str
    stem: Path
    legacy: bool = False

    @property
    def file(self) -> Path:
        return self.stem.parent / (self.stem.name + SESSION_EXTENSION)

    @property
    def exists(self) -> bool:
        return self.file.is_file()

    @property
    def size(self) -> int:
        try:
            return self.file.stat().st_size
        except OSError:
            return 0

    def sidecars(self) -> List[Path]:
        return [self.file.with_name(self.file.name + suffix) for suffix in SIDECAR_SUFFIXES]

    def describe(self) -> str:
        where = "legacy" if self.legacy else "managed"
        present = "exists" if self.exists else "missing"
        return f"{self.name}: {self.file} ({where}, {present})"


def locate_session(
    name: str,
    *,
    directory: Optional[Path] = None,
    legacy_roots: Optional[Iterable[Path]] = None,
) -> SessionLocation:
    """Resolve *name* to a :class:`SessionLocation`.

    Resolution order:

    1. ``<SESSION_DIR>/<name>.session``  (the managed, documented location)
    2. ``<project root>/<name>.session`` (the legacy location used before
       sessions were moved into ``data/sessions``)
    3. ``<current working directory>/<name>.session`` (legacy, exotic setups)

    When nothing exists yet the managed path is returned so that a fresh
    login writes there.
    """
    base_dir = Path(directory) if directory is not None else resolve_session_dir()
    primary = base_dir / name
    if (primary.parent / (primary.name + SESSION_EXTENSION)).is_file():
        return SessionLocation(name, primary)
    if legacy_roots is None:
        legacy_roots = (project_root(), Path.cwd())
    for root in legacy_roots:
        candidate = Path(root) / name
        if (candidate.parent / (candidate.name + SESSION_EXTENSION)).is_file():
            return SessionLocation(name, candidate, legacy=True)
    return SessionLocation(name, primary)


def session_source(
    string_session: Optional[str],
    *,
    prefer: Optional[str] = None,
    file_exists: bool = False,
) -> str:
    """Decide whether the user client runs on ``"file"`` or ``"string"``.

    Precedence (``SESSION_SOURCE`` environment variable, default ``auto``):

    * ``file``   → always use the on-disk Telethon session,
    * ``string`` → always use ``STRING_SESSION`` when it is set,
    * ``auto``   → use the file session **when one exists**, otherwise fall
      back to ``STRING_SESSION`` and finally to a (to-be-created) file
      session.  ``auto`` never deletes or rewrites anything.
    """
    mode = (prefer or os.environ.get("SESSION_SOURCE") or "auto").strip().lower()
    if mode not in ("auto", "file", "string"):
        mode = "auto"
    if mode == "file":
        return "file"
    if mode == "string":
        return "string" if string_session else "file"
    if file_exists:
        return "file"
    if string_session:
        return "string"
    return "file"


# ── single-instance lock ─────────────────────────────────────────────────────
class SessionLockedError(RuntimeError):
    """Another live process already owns this session."""


class SessionImportError(RuntimeError):
    """The supplied ``.session`` file cannot be used."""


def _proc_start_time() -> Optional[float]:
    try:
        import psutil  # type: ignore

        return psutil.Process(os.getpid()).create_time()
    except Exception:
        return None


def _pid_alive(pid: int, started: Optional[float] = None) -> bool:
    """Best-effort liveness check that also survives pid re-use."""
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        import psutil  # type: ignore

        proc = psutil.Process(pid)
        if started is not None:
            with_started = proc.create_time()
            if abs(with_started - float(started)) > 2.0:
                return False
        return proc.is_running() and proc.status() != "zombie"
    except Exception:
        pass
    try:  # POSIX fall-back
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_lock(path: Path) -> Dict[str, object]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@dataclass
class SessionLock:
    """Handle returned by :func:`acquire_session_lock`."""

    path: Path
    pid: int
    acquired: bool = True
    _released: bool = field(default=False, repr=False)

    def release(self) -> None:
        if not self.acquired or self._released:
            return
        self._released = True
        try:
            holder = _read_lock(self.path)
            if holder.get("pid") in (None, self.pid):
                self.path.unlink()
        except OSError:
            pass


def session_lock_status(location: SessionLocation) -> Dict[str, object]:
    """Describe the lock of *location* without touching it."""
    lock_path = _lock_path(location)
    holder = _read_lock(lock_path) if lock_path.exists() else {}
    pid = int(holder.get("pid") or 0)
    alive = bool(pid) and _pid_alive(pid, holder.get("started"))
    return {
        "lock_file": str(lock_path),
        "pid": pid or None,
        "running": alive,
        "stale": bool(holder) and not alive,
    }


def _lock_path(location: SessionLocation) -> Path:
    return location.file.with_name(location.file.name + ".lock")


def acquire_session_lock(
    location: SessionLocation,
    *,
    wait_seconds: float = 0.0,
    env_override: str = "MIDO_IGNORE_SESSION_LOCK",
) -> SessionLock:
    """Take an exclusive lock next to the session file.

    A lock whose owning pid is gone (crash, kill, reboot) is treated as stale
    and replaced automatically, so the supervisor can always restart the bot.
    """
    lock_path = _lock_path(location)
    if os.environ.get(env_override):
        return SessionLock(lock_path, os.getpid(), acquired=False)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0.0, float(wait_seconds))
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            holder = _read_lock(lock_path)
            pid = int(holder.get("pid") or 0)
            if pid and _pid_alive(pid, holder.get("started")):
                if time.time() < deadline:
                    time.sleep(0.5)
                    continue
                raise SessionLockedError(
                    "الجلسة مستخدمة بالفعل من نسخة أخرى تعمل الآن "
                    f"(pid {pid}). أغلق النسخة الأخرى ثم أعد المحاولة، "
                    f"أو استخدم {env_override}=1 إذا كنت متأكدًا."
                )
            try:
                lock_path.unlink()
            except OSError:
                pass
            continue
        except OSError as exc:  # e.g. read-only volume
            raise SessionLockedError(
                f"لا يمكن إنشاء ملف القفل {lock_path}: {exc}. "
                "تأكد من صلاحيات الكتابة على مجلد الجلسات."
            ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "pid": os.getpid(),
                    "started": _proc_start_time(),
                    "host": socket.gethostname(),
                    "cwd": str(Path.cwd()),
                    "argv": sys.argv[1:],
                    "created": time.time(),
                },
                handle,
            )
        return SessionLock(lock_path, os.getpid())


# ── validation / import ──────────────────────────────────────────────────────
def validate_session_file(path: Path) -> Tuple[bool, str]:
    """Cheap structural validation of a Telethon SQLite session file."""
    path = Path(path).expanduser()
    if not path.is_file():
        return False, f"الملف غير موجود: {path}"
    if path.stat().st_size <= 0:
        return False, f"الملف فارغ: {path}"
    try:
        with open(path, "rb") as handle:
            header = handle.read(len(SQLITE_MAGIC))
    except OSError as exc:
        return False, f"لا يمكن قراءة الملف {path}: {exc}"
    if header != SQLITE_MAGIC:
        return False, (
            f"الملف {path} ليس ملف جلسة Telethon صالح "
            "(قاعدة SQLite غير معروفة). تأكد أنك اخترت الملف الصحيح."
        )
    try:
        uri = f"file:{path}?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True, timeout=2) as conn:
            conn.execute("select count(*) from sqlite_master").fetchone()
    except Exception as exc:
        return False, f"ملف الجلسة تالف أو غير قابل للقراءة: {path} ({exc})"
    return True, "ok"


def backup_session(location: SessionLocation, *, suffix: Optional[str] = None) -> Optional[Path]:
    """Back up an existing session file (never deletes the original)."""
    if not location.exists:
        return None
    stamp = suffix or time.strftime("%Y%m%d-%H%M%S")
    backup = location.file.with_name(location.file.name + f".bak-{stamp}")
    shutil.copy2(location.file, backup)
    return backup


def import_session_file(
    source,
    *,
    name: Optional[str] = None,
    directory: Optional[Path] = None,
    force: bool = False,
) -> Tuple[SessionLocation, Optional[Path]]:
    """Validate *source* and copy it into the managed session directory.

    Returns ``(location, backup)`` where *backup* is the previous session that
    was preserved when ``force=True`` overwrote one.

    Refuses (without ``force``) to overwrite an existing session, and never
    overwrites a *different* valid session silently.
    """
    source = Path(source).expanduser().resolve()
    ok, message = validate_session_file(source)
    if not ok:
        raise SessionImportError(message)

    location = locate_session(name or session_name("user"), directory=directory)
    target = location.file
    if source == target.resolve():
        return location, None

    backup: Optional[Path] = None
    if target.exists():
        if not force:
            raise SessionImportError(
                f"توجد جلسة بالفعل في {target}. "
                "استخدم --force لعمل نسخة احتياطية منها ثم استبدالها "
                "(لن يتم حذف الجلسة القديمة)."
            )
        ok_existing, _ = validate_session_file(target)
        if ok_existing:
            backup = backup_session(location)

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    shutil.copy2(source, tmp)
    for suffix in SIDECAR_SUFFIXES:
        sidecar = source.with_name(source.name + suffix)
        if sidecar.exists():
            shutil.copy2(sidecar, tmp.with_name(tmp.name + suffix))
    os.replace(tmp, target)
    for suffix in SIDECAR_SUFFIXES:
        tmp_side = tmp.with_name(tmp.name + suffix)
        if tmp_side.exists():
            os.replace(tmp_side, target.with_name(target.name + suffix))
    return locate_session(location.name, directory=location.stem.parent), backup


def cleanup_partial_session(location: SessionLocation) -> List[str]:
    """Remove the files of a *failed* fresh login (used right after errors)."""
    removed: List[str] = []
    for path in [location.file, *location.sidecars(), _lock_path(location)]:
        try:
            if path.exists():
                path.unlink()
                removed.append(str(path))
        except OSError:
            continue
    return removed


def list_session_files(directory: Optional[Path] = None) -> List[Dict[str, object]]:
    """Inventory of ``*.session`` files (metadata only, no secrets)."""
    base = Path(directory) if directory is not None else resolve_session_dir()
    entries: List[Dict[str, object]] = []
    candidates = []
    if base.is_dir():
        candidates.extend(sorted(base.glob("*.session")))
    for legacy_root in (project_root(), Path.cwd()):
        legacy = legacy_root / (session_name("user") + SESSION_EXTENSION)
        if legacy.is_file() and legacy not in candidates:
            candidates.append(legacy)
    for path in candidates:
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append(
            {
                "file": str(path),
                "size": stat.st_size,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "valid": validate_session_file(path)[0],
                "lock": session_lock_status(SessionLocation(path.stem, path.with_name(path.stem))),
            }
        )
    return entries
