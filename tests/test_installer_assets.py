# -*- coding: utf-8 -*-
"""Installer & packaging assets.

The Windows installer is a PowerShell script, so it is verified in two ways:

* **static** — secret-handling invariants that must never regress (token via
  ``GIT_ASKPASS``, no plain-text transcripts, session import through the
  environment instead of the command line),
* **behavioural** — the pure helper functions (python.org parsing, Git for
  Windows asset selection, secret masking) are dot-sourced and executed with
  real PowerShell when it is available (GitHub's ubuntu/windows runners ship
  ``pwsh``, so CI always exercises this path).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PS1 = ROOT / "Mido-RDP-Install.ps1"
CMD = ROOT / "Mido-Start.cmd"
DOCS = ROOT / "deploy" / "WINDOWS-RDP.md"
WORKFLOW = ROOT / ".github" / "workflows" / "Tests.yml"
LOCK = ROOT / "requirements.lock.txt"

PWSH = shutil.which("pwsh") or shutil.which("powershell")


def test_deliverables_exist():
    for path in (PS1, CMD, DOCS, WORKFLOW, LOCK, ROOT / ".env.example", ROOT / "mido_setup.py"):
        assert path.is_file(), f"missing deliverable: {path.relative_to(ROOT)}"


def test_installer_modes_are_complete():
    text = PS1.read_text(encoding="utf-8")
    marker = 'ValidateSet("Install", "Update", "Setup", "Check", "Start", "Repair")'
    assert marker in text
    for mode in ("Install", "Update", "Setup", "Check", "Start", "Repair"):
        assert f'"{mode}"' in text


def test_hand_copied_folder_needs_no_github_credentials():
    """A project folder uploaded to the RDP box (no .git) must install without
    GitHub: no clone, no token prompt — it is used exactly as it is."""
    text = PS1.read_text(encoding="utf-8")
    assert "$isGitCheckout" in text
    assert "بدون .git" in text
    # the only code that can ask for a GitHub token is Ensure-Repository, and it
    # is reachable *only* from the "not a git checkout" branch
    branch = text.split("$isGitCheckout = ")[1].split("$venvPython = Ensure-Venv")[0]
    assert "Update-Repository" in branch
    assert "Ensure-Repository | Out-Null" in branch
    assert "else {" in branch


class TestSecretHandling:
    def test_token_never_reaches_the_command_line(self):
        text = PS1.read_text(encoding="utf-8")
        assert "GIT_ASKPASS" in text, "git auth must go through GIT_ASKPASS"
        assert "MIDO_GIT_TOKEN" in text
        # the token must never be interpolated into a URL/argument
        assert "$Token@" not in text
        assert "x-access-token:$" not in text
        assert "-c http.extraheader" not in text

    def test_no_transcript_can_capture_typed_secrets(self):
        text = PS1.read_text(encoding="utf-8")
        assert "Start-Transcript" not in text

    def test_session_import_uses_the_environment_not_argv(self):
        text = PS1.read_text(encoding="utf-8")
        assert "MIDO_SETUP_SESSION_FILE" in text
        # the .session path must not be appended to the python argument list
        assert '"--session-file"' not in text

    def test_files_are_hardened_with_icacls(self):
        text = PS1.read_text(encoding="utf-8")
        assert "icacls" in text
        assert "/inheritance:r" in text

    def test_repair_never_deletes_sessions_or_databases(self):
        text = PS1.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "Remove-Item" in line:
                assert ".session" not in line, line
                assert ".db" not in line, line
                assert "data\\sessions" not in line, line

    def test_script_is_utf8_with_bom(self):
        # Windows PowerShell 5.1 reads scripts as ANSI without a BOM, which
        # would garble every Arabic message and the confirmation regex.
        assert PS1.read_bytes().startswith(b"\xef\xbb\xbf"), "Mido-RDP-Install.ps1 must be UTF-8 with BOM"


class TestRequirementsSplit:
    def test_googletrans_is_installed_without_dependencies(self):
        main = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        no_deps = (ROOT / "requirements-nodeps.txt").read_text(encoding="utf-8")
        assert "googletrans==4.0.0rc1" not in main
        assert "googletrans==4.0.0rc1" in no_deps

    def test_installer_and_ci_install_both_files(self):
        ps1 = PS1.read_text(encoding="utf-8")
        assert "requirements-nodeps.txt" in ps1
        assert '"--no-deps"' in ps1
        workflow = WORKFLOW.read_text(encoding="utf-8")
        assert "requirements-nodeps.txt" in workflow
        assert "--no-deps" in workflow

    def test_lock_file_points_at_the_no_deps_file(self):
        text = LOCK.read_text(encoding="utf-8")
        assert "requirements-nodeps.txt" in text
        # the lock itself must stay resolvable by pip: no file:// artefacts
        assert "@ file://" not in text
        active = [
            line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
        ]
        assert not any(line.startswith("googletrans") for line in active)


class TestEnvExample:
    def test_contains_every_key_the_setup_writes(self):
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        for key in (
            "APP_ID",
            "API_HASH",
            "TG_BOT_TOKEN",
            "SESSION_DIR",
            "SESSION_NAME",
            "BOT_SESSION_NAME",
            "SESSION_SOURCE",
            "NO_LOAD",
        ):
            assert f"{key}=" in example, key

    def test_example_has_no_values_that_look_like_real_secrets(self):
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            if key in ("API_HASH", "TG_BOT_TOKEN", "STRING_SESSION", "HEROKU_API_KEY"):
                assert value == "", f"{key} must stay empty in the example"


class TestGitignore:
    def test_covers_every_secret_artifact(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (".env", "*.session", "*.session.lock", "data/sessions/", "*.db"):
            assert pattern in text, pattern


def test_workflow_runs_the_suite_on_windows_and_linux():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ubuntu-latest" in text and "windows-latest" in text
    assert "pytest" in text
    assert "mido_setup.py" in text  # offline smoke test of the setup CLI


def test_docs_cover_the_official_commands():
    text = DOCS.read_text(encoding="utf-8")
    for needle in ("Mido-RDP-Install.ps1 -Mode Install", "-Mode Update", "-Mode Repair", "Mido-Start.cmd"):
        assert needle in text, needle


# ── real PowerShell execution ────────────────────────────────────────────────
PARSE_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile('{ps1}', [ref]$null, [ref]$errors)
ConvertTo-Json -InputObject @{{ parseErrors = @($errors | ForEach-Object {{ $_.Message }}) }} -Compress -Depth 5
"""

BEHAVIOUR_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
if (-not $env:USERPROFILE) {{ $env:USERPROFILE = [System.IO.Path]::GetTempPath() }}
if (-not $env:TEMP) {{ $env:TEMP = [System.IO.Path]::GetTempPath() }}

. '{ps1}'

$html = @'
<html><body>
<a href="2.7.18/">2.7.18/</a>
<a href="3.9.9/">3.9.9/</a>
<a href="3.10.11/">3.10.11/</a>
<a href="3.12.10/">3.12.10/</a>
<a href="3.13.12/">3.13.12/</a>
<a href="3.14.2/">3.14.2/</a>
<a href="3.12.15/">3.12.15/</a>
</body></html>
'@
$pythonUrls = @(Get-PythonDownloadCandidates -Html $html)

$json = @'
{{ "tag_name": "v2.56.0.windows.2", "assets": [
  {{ "name": "PortableGit-2.56.0.2-64-bit.7z.exe", "browser_download_url": "https://example.invalid/PortableGit-2.56.0.2-64-bit.7z.exe" }},
  {{ "name": "Git-2.56.0.2-32-bit.exe", "browser_download_url": "https://example.invalid/Git-2.56.0.2-32-bit.exe" }},
  {{ "name": "Git-2.56.0.2-64-bit.exe", "browser_download_url": "https://example.invalid/Git-2.56.0.2-64-bit.exe" }},
  {{ "name": "Git-2.56.0.2-64-bit.tar.bz2", "browser_download_url": "https://example.invalid/Git-2.56.0.2-64-bit.tar.bz2" }}
] }}
'@
$gitUrl = Select-GitForWindowsAssetUrl -Json $json

Register-Secret 'SENTINEL-TOKEN-123456'
$masked = Protect-Secrets 'before SENTINEL-TOKEN-123456 after'

ConvertTo-Json -InputObject @{{
  pythonUrls = $pythonUrls
  gitUrl     = $gitUrl
  masked     = $masked
}} -Compress -Depth 5
"""


def _run_pwsh(tmp_path: Path, name: str, script: str) -> dict:
    path = tmp_path / name
    path.write_text(script.format(ps1=str(PS1).replace("'", "''")), encoding="utf-8")
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(path)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(PWSH is None, reason="PowerShell is not installed (CI runners have it)")
def test_installer_parses_with_real_powershell(tmp_path):
    payload = _run_pwsh(tmp_path, "parse.ps1", PARSE_SCRIPT)
    assert payload["parseErrors"] == []


@pytest.mark.skipif(PWSH is None, reason="PowerShell is not installed (CI runners have it)")
def test_powershell_assets_behave_as_expected(tmp_path):
    payload = _run_pwsh(tmp_path, "behaviour.ps1", BEHAVIOUR_SCRIPT)

    # 1. python.org listing → newest Windows installers first, old ones dropped
    urls = payload["pythonUrls"]
    assert urls[0].endswith("python-3.14.2-amd64.exe")
    assert any(url.endswith("python-3.12.15-amd64.exe") for url in urls)
    assert len(urls) == 5
    assert not any("3.9.9" in url or "2.7.18" in url for url in urls)

    # 2. Git for Windows asset selection (64-bit, not portable, not 32-bit)
    assert payload["gitUrl"].endswith("/Git-2.56.0.2-64-bit.exe")

    # 3. registered secrets are masked
    assert payload["masked"] == "before *** after"
