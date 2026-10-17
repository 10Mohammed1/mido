# -*- coding: utf-8 -*-
"""Mido · shared helper package.

Everything in ``mido/`` is deliberately **import-safe**: importing these
modules must never start a Telegram client, read credential *values*, connect
to the network or mutate global state.  That is what makes it possible to run
``python -m zira setup`` / ``python mido_setup.py check`` on a fresh machine
(before any session exists) and to unit-test the session logic without
touching a real account.

The userbot itself lives in ``zira/`` and imports from here.
"""

__version__ = "1.0.0"
