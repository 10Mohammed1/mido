"""Central event-loop helper.

Modern replacement for the old ``asyncio.get_event_loop()`` pattern that was
deprecated in Python 3.12+ and raises inside 3.14 when no loop is set.

``get_loop()`` mirrors the behaviour of the old ``zedub.loop`` property: it
returns the loop that is currently running (the correct answer inside
coroutines and callbacks) and otherwise reuses the loop that is already
installed.  That matters because Telethon starts the assistant bot during
import and installs its own loop - creating a second, uninstalled loop here
makes the clients disagree and Telethon raises
``The asyncio event loop must not change after connection``.
"""

import asyncio
import warnings
from typing import Optional

_loop: Optional[asyncio.AbstractEventLoop] = None


def get_loop() -> asyncio.AbstractEventLoop:
    """Return the running loop, else the installed one, else create one."""
    global _loop
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        pass
    if _loop is not None and not _loop.is_closed():
        return _loop
    with warnings.catch_warnings():
        # Old interpreters warn here, new ones raise when no loop is set;
        # both cases are handled by the branches below.
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Python 3.12+ stopped creating a loop on demand.
            loop = None
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _loop = loop
    return loop


def install_loop() -> asyncio.AbstractEventLoop:
    """Force-install the loop used by the process (used once at start-up)."""
    loop = get_loop()
    asyncio.set_event_loop(loop)
    return loop


def close_loop() -> None:
    """Close the loop we adopted/created (clean shutdown)."""
    global _loop
    if _loop is not None and not _loop.is_closed():
        _loop.close()
    _loop = None
