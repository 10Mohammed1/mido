# -*- coding: utf-8 -*-
"""Dependency files: installability, the two-step no-deps packages, and proof
that the installed modules really work with the modern stack.

Background: a single `pip install -r requirements.txt` used to be impossible.

* ``googletrans 4.0.0rc1`` pins ``httpx==0.13.3`` while
  ``youtube-search-python`` needs ``httpx>=0.14.2``;
* ``search-engine-parser 0.6.8`` pins ``lxml<5`` while ``cinemagoer`` needs
  ``lxml>=6.1.1``.

Both pins are obsolete, so those two packages are installed with ``--no-deps``
(``requirements-nodeps.txt``) — exactly how the production environment runs
today.  These tests keep that split honest.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
NO_DEPS = ROOT / "requirements-nodeps.txt"
LOCK = ROOT / "requirements.lock.txt"

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?\s*(==|>=|<=|~=|!=|<|>|;|$)")


def active_lines(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):  # pip option line
            yield line
            continue
        yield line


def test_requirement_lines_are_well_formed():
    for path in (REQUIREMENTS, NO_DEPS):
        for line in active_lines(path):
            if line.startswith("-"):
                continue
            assert NAME_RE.match(line), f"{path.name}: suspicious requirement {line!r}"


def test_conflicting_packages_live_in_the_no_deps_file():
    def names(path):
        found = []
        for line in active_lines(path):
            if line.startswith("-"):
                continue
            found.append(line.split("==")[0].split(">=")[0].split("<")[0].split(" ")[0].strip())
        return found

    main = names(REQUIREMENTS)
    no_deps = names(NO_DEPS)
    for package in ("googletrans", "search-engine-parser"):
        assert package not in main, f"{package} must not be in requirements.txt"
        assert package in no_deps, f"{package} must be in requirements-nodeps.txt"


def test_linux_only_packages_are_marked():
    text = REQUIREMENTS.read_text(encoding="utf-8")
    for name in ("py-tgcalls", "pyrofork", "mautrix"):
        lines = [line for line in text.splitlines() if line.startswith(name)]
        assert lines and 'sys_platform == "linux"' in lines[0], name


def test_lock_file_has_no_uninstallable_file_entries():
    text = LOCK.read_text(encoding="utf-8")
    assert "@ file://" not in text
    assert "requirements-nodeps.txt" in text
    active = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    assert active, "the lock file looks empty"
    for line in active:
        assert "==" in line, line


def test_no_deps_modules_are_importable_and_keep_the_expected_api():
    """The --no-deps install must produce the API the plugins were written for."""
    googletrans = pytest.importorskip("googletrans")
    import inspect

    from googletrans import LANGUAGES, Translator

    assert len(LANGUAGES) > 100
    # the plugins call translate() synchronously (zira/helpers/functions/functions.py)
    assert inspect.iscoroutinefunction(Translator.translate) is False, (
        "googletrans must stay on the synchronous 4.0.0rc1 API"
    )

    search_engine_parser = pytest.importorskip("search_engine_parser")
    from bs4 import BeautifulSoup
    from search_engine_parser.core.engines.google import Search

    engine = Search()
    html = '<div class="Gx5Zad fP1Qef xpd EtOod pkphOe"><a href="https://example.test"><h3>t</h3></a></div>'
    soup = BeautifulSoup(html, "lxml")  # bs4 + modern lxml (>=6)
    assert len(engine.parse_soup(soup)) == 1
