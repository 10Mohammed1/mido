"""Portable process restart.

The restart command (``.بنك`` / ``.تحديث``) and the logger-group bootstrap both
need to relaunch ``python -m zira`` in place.

* POSIX: ``os.execv`` really replaces the process (same pid, same stdio).
* Windows: ``os.exec*`` semantics are surprising (and the old code also
  escaped spaces with a backslash, which is a *shell* trick that corrupts the
  path when passed to the exec family).  A detached child is spawned and the
  current process exits cleanly instead.
"""

import os
import subprocess
import sys

__all__ = ["restart_process"]


def restart_process(extra_argv=("-m", "zira")) -> None:
    """Replace (POSIX) or re-spawn (Windows) the current interpreter."""
    argv = [sys.executable, *extra_argv]
    if os.name == "nt":
        # cwd/console are inherited; the supervisor (if any) still sees the
        # exit code of *this* process.
        subprocess.Popen(argv, cwd=os.getcwd(), env=os.environ.copy(), close_fds=True)
        os._exit(0)
    os.execv(sys.executable, argv)
