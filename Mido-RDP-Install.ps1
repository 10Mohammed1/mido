<#
.SYNOPSIS
    Mido — مثبّت ويندوز / RDP (تثبيت، تحديث، إعداد، فحص، إصلاح، تشغيل).

.DESCRIPTION
    A single, idempotent installer for a fresh Windows Server / RDP machine:

      * installs the prerequisites (Git + Python) through winget, or downloads
        the official installers directly when winget is unavailable,
      * clones the (private) repository — the token never touches the command
        line or the git remote URL: it is passed through GIT_ASKPASS,
      * creates the project virtual environment and installs requirements.txt,
      * creates `.env` and runs the interactive Python setup
        (`python mido_setup.py setup`) for the Telegram login, 2FA, session
        import and bot-token validation,
      * hardens the ACLs of `.env`, `*.session` and the session folder so other
        users on the same machine cannot read the credentials,
      * verifies everything with `python mido_setup.py check`.

    Nothing is ever deleted: existing sessions, databases and `.env` files are
    kept (`.env` gets a timestamped backup before it is rewritten).

.PARAMETER Mode
    Install (default)  full pipeline, safe to re-run (becomes an update)
    Update             git pull + dependencies + check (config/session untouched)
    Setup              (re)run the Telegram/login setup and file hardening
    Check              diagnostics only, exit code 1 when something is wrong
    Start              launch the userbot from the project virtual environment
    Repair             rebuild a broken venv, re-install dependencies, re-harden

.PARAMETER RepoUrl
    Clone URL of the repository (default: the private Mido repository).

.PARAMETER RepoDir
    Where the repository lives (default: %USERPROFILE%\Mido).

.PARAMETER Token
    GitHub personal access token with `repo` scope.  Prefer the environment
    variable MIDO_GITHUB_TOKEN / GH_TOKEN over this parameter: parameters can
    end up in the PowerShell history.

.PARAMETER SessionFile
    Optional path to an existing `*.session` file (from another PC) that should
    be imported and verified before the login prompt.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Mido-RDP-Install.ps1 -Mode Install

.EXAMPLE
    $env:MIDO_GITHUB_TOKEN = "github_pat_..."      # never on the command line
    .\Mido-RDP-Install.ps1 -Mode Update

.NOTES
    Log file: %TEMP%\mido-install.log (secrets are masked before they reach it).
    Exit codes: 0 = success, 1 = failure, 2 = wrong environment / usage.
#>
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'read by the helper functions through the script scope')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'interactive installer: the console is the user interface')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification = 'the private helpers follow the project wording (Ensure/Protect), not the cmdlet convention')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'private helpers, not public cmdlets')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'a one-shot installer: every action is already announced to the user')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidOverwritingBuiltInCmdlets', '', Justification = 'Write-Log is a private helper; the installer never loads the module that ships it')]
[CmdletBinding()]
param(
    [ValidateSet("Install", "Update", "Setup", "Check", "Start", "Repair")]
    [string]$Mode = "Install",
    [string]$RepoUrl = "https://github.com/10Mohammed1/mido.git",
    [string]$RepoDir = $(if ($env:USERPROFILE) { Join-Path $env:USERPROFILE "Mido" } else { Join-Path (Get-Location).Path "Mido" }),
    [string]$Branch = "main",
    [string]$Token,
    [string]$SessionFile,
    [string]$PythonVersion,
    [switch]$SkipDeps,
    [switch]$NoStart,
    [switch]$Force,
    [switch]$NonInteractive,
    # Advanced: lets the helper functions run on a non-Windows host (self-test).
    [switch]$AllowNonWindows
)

# ══════════════════════════════════════════════════════════════════════════════
#  constants
# ══════════════════════════════════════════════════════════════════════════════
$script:MidoInstallerVersion = "1.0.0"
$script:MinPython = [version]"3.10.0"
$script:LogFile = Join-Path ([System.IO.Path]::GetTempPath()) "mido-install.log"
$script:AskPassFile = $null
$script:Secrets = New-Object System.Collections.Generic.List[string]
$script:StartTime = Get-Date

# ══════════════════════════════════════════════════════════════════════════════
#  output + logging (never prints or stores a registered secret)
# ══════════════════════════════════════════════════════════════════════════════
function Write-Log {
    param([string]$Text)
    try {
        $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Add-Content -LiteralPath $script:LogFile -Value "[$stamp] $Text" -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {
        Write-Verbose "mido: log file not writable: $($_.Exception.Message)"
    }
}

function Write-Head {
    param([string]$Text)
    Write-Host ""
    Write-Host ("== " + $Text + " " + ("=" * [Math]::Max(0, 60 - $Text.Length))) -ForegroundColor Cyan
    Write-Log "## $Text"
}

function Write-Step {
    param([string]$Text)
    Write-Host "  - $Text" -ForegroundColor White
    Write-Log "  * $Text"
}

function Write-Ok {
    param([string]$Text)
    Write-Host "  [OK] $Text" -ForegroundColor Green
    Write-Log "  OK $Text"
}

function Write-Info2 {
    param([string]$Text)
    Write-Host "  [i] $Text" -ForegroundColor Gray
    Write-Log "  i $Text"
}

function Write-Warn2 {
    param([string]$Text)
    Write-Host "  [!] $Text" -ForegroundColor Yellow
    Write-Log "  WARN $Text"
}

function Write-Err2 {
    param([string]$Text)
    Write-Host "  [x] $Text" -ForegroundColor Red
    Write-Log "  ERROR $Text"
}

function Register-Secret {
    param([string]$Value)
    if ($Value -and $Value.Length -ge 6 -and -not $script:Secrets.Contains($Value)) {
        [void]$script:Secrets.Add($Value)
    }
}

function Protect-Secrets {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    foreach ($secret in $script:Secrets) {
        if ($secret) { $Text = $Text.Replace($secret, "***") }
    }
    return $Text
}

# ══════════════════════════════════════════════════════════════════════════════
#  process helpers
# ══════════════════════════════════════════════════════════════════════════════
function Invoke-Native {
    <#
        Runs an external program, echoes its output to the console and the log
        (with secrets masked) and returns its exit code.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )
    Write-Log ("+ " + $FilePath + " " + ($Arguments -join " "))
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $code = 1
    try {
        & $FilePath @Arguments 2>&1 | ForEach-Object {
            $line = Protect-Secrets ([string]$_)
            if ($line.Trim().Length -gt 0) {
                Write-Host "      $line" -ForegroundColor DarkGray
                Write-Log "    | $line"
            }
        }
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
    } catch {
        $line = Protect-Secrets ([string]$_)
        Write-Err2 $line
        Write-Log "    ! $line"
        $code = 1
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0 -and -not $AllowFailure) {
        throw ("فشل تنفيذ الأمر: {0} {1} (كود {2})" -f $FilePath, ($Arguments -join " "), $code)
    }
    return [int]$code
}

function Invoke-InRepo {
    <#  Runs a command with the project folder as the working directory
        (the setup CLI resolves `config.py` and `.env` relative to it). #>
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure
    )
    Push-Location -LiteralPath $RepoDir
    try {
        return (Invoke-Native -FilePath $FilePath -Arguments $Arguments -AllowFailure:$AllowFailure)
    } finally {
        Pop-Location
    }
}

function Update-SessionPath {
    # winget installers only update the *stored* PATH — reload it for this run.
    try {
        $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $user = [Environment]::GetEnvironmentVariable("Path", "User")
        $parts = @()
        if ($machine) { $parts += $machine }
        if ($user) { $parts += $user }
        if ($parts.Count -gt 0) { $env:Path = ($parts -join ";") }
    } catch {
        Write-Warn2 "تعذّر تحديث PATH مؤقتًا: $($_.Exception.Message)"
    }
}

function Get-PythonLauncher {
    <#
        Returns @{ Exe; Prefix; Version } for the newest usable Python >= 3.10,
        or $null.  Only the *installed* interpreters are considered.
    #>
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) { $candidates += , @("py", "-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += , @("python") }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { $candidates += , @("python3") }

    $probe = "import sys; print('%d.%d.%d' % sys.version_info[:3])"
    foreach ($candidate in $candidates) {
        $exe = [string]$candidate[0]
        $prefix = @()
        if ($candidate.Count -gt 1) { $prefix = @($candidate[1..($candidate.Count - 1)]) }
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $output = & $exe @prefix -c $probe 2>$null
            $code = $LASTEXITCODE
        } catch {
            $code = 1; $output = $null
        } finally {
            $ErrorActionPreference = $previous
        }
        if ($code -eq 0 -and $output) {
            $raw = ([string]($output | Select-Object -First 1)).Trim()
            try { $version = [version]$raw } catch { $version = $null }
            if ($version -and $version -ge $script:MinPython) {
                return @{ Exe = $exe; Prefix = $prefix; Version = $version }
            }
        }
    }
    return $null
}

# ══════════════════════════════════════════════════════════════════════════════
#  prerequisite installation (winget first, official installers as fallback)
# ══════════════════════════════════════════════════════════════════════════════
function Get-PythonDownloadCandidates {
    <#
        Pure helper: parses the python.org FTP index and returns the newest
        Windows amd64 installer URLs first.  Testable without network access.
    #>
    param([Parameter(Mandatory = $true)][string]$Html)
    $versions = New-Object System.Collections.Generic.List[version]
    foreach ($match in [regex]::Matches($Html, 'href="(3\.(\d+)\.(\d+))/"')) {
        $minor = [int]$match.Groups[2].Value
        $patch = [int]$match.Groups[3].Value
        if ($minor -ge 10 -and $minor -le 14) {
            $versions.Add([version]("3.$minor.$patch"))
        }
    }
    $ordered = $versions | Sort-Object -Descending -Unique
    $urls = New-Object System.Collections.Generic.List[string]
    foreach ($version in $ordered) {
        $v = $version.ToString()
        $urls.Add("https://www.python.org/ftp/python/$v/python-$v-amd64.exe")
    }
    return $urls
}

function Select-GitForWindowsAssetUrl {
    <#
        Pure helper: picks the `Git-*-64-bit.exe` asset out of a GitHub
        releases/latest JSON payload (the asset name contains the version, so it
        cannot be hardcoded).
    #>
    param([Parameter(Mandatory = $true)][string]$Json)
    $found = [regex]::Matches($Json, '"browser_download_url"\s*:\s*"(?<url>[^"]+/(?<name>Git-[0-9][^"/]*-64-bit\.exe))"')
    if ($found.Count -eq 0) { return $null }
    $best = $found | Select-Object -First 1
    return [string]$best.Groups["url"].Value
}

function Install-PythonWithWinget {
    param([string]$PreferredVersion)
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    $ids = New-Object System.Collections.Generic.List[string]
    if ($PreferredVersion -and $PreferredVersion -match '^3\.\d+$') { $ids.Add("Python.Python.$PreferredVersion") }
    foreach ($fallback in @("Python.Python.3.13", "Python.Python.3.12")) {
        if (-not $ids.Contains($fallback)) { $ids.Add($fallback) }
    }
    foreach ($id in $ids) {
        Write-Step "winget install $id"
        $code = Invoke-Native -FilePath "winget" -Arguments @(
            "install", "--id", $id, "-e", "--source", "winget",
            "--accept-package-agreements", "--accept-source-agreements",
            "--silent"
        ) -AllowFailure
        if ($code -eq 0) {
            Update-SessionPath
            $launcher = Get-PythonLauncher
            if ($launcher) { return $true }
        }
        Write-Warn2 "لم ينجح تثبيت $id عبر winget (كود $code)."
    }
    return $false
}

function Install-PythonFromWeb {
    param([string]$PreferredVersion)
    Write-Step "تنزيل مثبّت Python الرسمي من python.org…"
    $candidates = @()
    if ($PreferredVersion) {
        $candidates += "https://www.python.org/ftp/python/$PreferredVersion/python-$PreferredVersion-amd64.exe"
    }
    $candidates += "https://www.python.org/ftp/python/3.13.12/python-3.13.12-amd64.exe"
    $candidates += "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
    try {
        $listing = (Invoke-WebRequest -Uri "https://www.python.org/ftp/python/" -UseBasicParsing -TimeoutSec 60).Content
        $candidates += (Get-PythonDownloadCandidates -Html ([string]$listing) | Select-Object -First 8)
    } catch {
        Write-Warn2 "تعذّر قراءة قائمة python.org: $($_.Exception.Message)"
    }
    $installer = $null
    foreach ($url in ($candidates | Select-Object -Unique)) {
        try {
            $head = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 45
            if ($head.StatusCode -eq 200) { $installer = $url; break }
        } catch {
            Write-Verbose "mido: no installer at $url"
        }
    }
    if (-not $installer) {
        throw "تعذّر العثور على مثبّت Python مناسب — ثبّت Python 3.12+ يدويًا من python.org ثم أعد التشغيل."
    }
    $target = Join-Path $env:TEMP (Split-Path -Leaf $installer)
    Write-Step "تنزيل $(Split-Path -Leaf $installer)…"
    Invoke-WebRequest -Uri $installer -OutFile $target -UseBasicParsing -TimeoutSec 900 | Out-Null
    Write-Step "تثبيت Python صامتًا (للمستخدم الحالي، مع إضافته إلى PATH)…"
    $code = Invoke-Native -FilePath $target -Arguments @(
        "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1",
        "Include_test=0", "Include_doc=0", "AssociateFiles=0", "Shortcuts=0"
    ) -AllowFailure
    Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
    Update-SessionPath
    if (-not (Get-PythonLauncher)) {
        throw "تم تشغيل مثبّت Python (كود $code) لكن لم يتم العثور عليه — افتح نافذة PowerShell جديدة وأعد المحاولة."
    }
    return $true
}

function Install-GitWithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    Write-Step "winget install Git.Git"
    $code = Invoke-Native -FilePath "winget" -Arguments @(
        "install", "--id", "Git.Git", "-e", "--source", "winget",
        "--accept-package-agreements", "--accept-source-agreements", "--silent"
    ) -AllowFailure
    if ($code -eq 0) {
        Update-SessionPath
        if (Get-Command git -ErrorAction SilentlyContinue) { return $true }
    }
    Write-Warn2 "لم ينجح تثبيت Git عبر winget (كود $code)."
    return $false
}

function Install-GitFromWeb {
    Write-Step "تنزيل Git for Windows…"
    $url = $null
    try {
        $json = (Invoke-WebRequest -Uri "https://api.github.com/repos/git-for-windows/git/releases/latest" -UseBasicParsing -TimeoutSec 60 -Headers @{ "User-Agent" = "Mido-Installer" }).Content
        $url = Select-GitForWindowsAssetUrl -Json ([string]$json)
    } catch {
        Write-Warn2 "تعذّر استعلام GitHub: $($_.Exception.Message)"
    }
    if (-not $url) {
        $url = "https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.2/Git-2.56.0.2-64-bit.exe"
        $head = $null
        try { $head = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 45 } catch {
            Write-Verbose "mido: fallback Git URL did not respond: $($_.Exception.Message)"
        }
        if (-not $head -or $head.StatusCode -ne 200) {
            throw "تعذّر تحديد رابط Git for Windows — ثبّت Git يدويًا من git-scm.com ثم أعد التشغيل."
        }
    }
    $target = Join-Path $env:TEMP (Split-Path -Leaf $url)
    Write-Step "تنزيل $(Split-Path -Leaf $url)…"
    Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing -TimeoutSec 900 | Out-Null
    Write-Step "تثبيت Git صامتًا…"
    $code = Invoke-Native -FilePath $target -Arguments @(
        "/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"
    ) -AllowFailure
    Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
    Update-SessionPath
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "تم تشغيل مثبّت Git (كود $code) لكن لم يتم العثور عليه — افتح نافذة PowerShell جديدة وأعد المحاولة."
    }
    return $true
}

function Ensure-Prerequisites {
    Write-Head "المتطلبات الأساسية"
    $needWork = $false

    $launcher = Get-PythonLauncher
    if ($launcher) {
        Write-Ok "Python $($launcher.Version) متاح ($($launcher.Exe) $($launcher.Prefix -join ' '))"
    } else {
        $needWork = $true
        if (-not (Install-PythonWithWinget -PreferredVersion $PythonVersion)) {
            Install-PythonFromWeb -PreferredVersion $PythonVersion | Out-Null
        }
        $launcher = Get-PythonLauncher
        if (-not $launcher) { throw "Python $($script:MinPython)+ مطلوب ولم يكتمل تثبيته." }
        Write-Ok "تم تثبيت Python $($launcher.Version)"
    }

    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitVersion = (& git --version 2>$null) -join ""
        Write-Ok "$gitVersion متاح"
    } else {
        $needWork = $true
        if (-not (Install-GitWithWinget)) {
            Install-GitFromWeb | Out-Null
        }
        Write-Ok "تم تثبيت Git"
    }

    if ($needWork) { Update-SessionPath }

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Info2 "winget غير متاح على هذا النظام — تم استخدام المثبّتات الرسمية."
    }
    return $launcher
}

# ══════════════════════════════════════════════════════════════════════════════
#  git (private repository, token never on the command line)
# ══════════════════════════════════════════════════════════════════════════════
function New-AskPassScript {
    if (-not $env:MIDO_GIT_TOKEN) { return $null }
    $path = Join-Path $env:TEMP ("mido-askpass-" + [guid]::NewGuid().ToString("N") + ".cmd")
    @(
        "@echo off",
        "setlocal",
        "set `"PROMPT=%~1`"",
        "echo %PROMPT% | findstr /I /C:`"Username`" >nul",
        "if errorlevel 1 (echo %MIDO_GIT_TOKEN%) else (echo %MIDO_GIT_USER%)"
    ) | Set-Content -LiteralPath $path -Encoding ASCII
    $script:AskPassFile = $path
    return $path
}

function Remove-AskPassScript {
    if ($script:AskPassFile) {
        Remove-Item -LiteralPath $script:AskPassFile -Force -ErrorAction SilentlyContinue
        $script:AskPassFile = $null
    }
    Remove-Item Env:\MIDO_GIT_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:\MIDO_GIT_USER -ErrorAction SilentlyContinue
    Remove-Item Env:\GIT_ASKPASS -ErrorAction SilentlyContinue
}

function Enable-GitAuth {
    <#
        Prepares git authentication for the private repository:

          1. an already-authenticated `gh` CLI (`gh auth setup-git`) — nothing
             secret to handle,
          2. a token from -Token / $env:MIDO_GITHUB_TOKEN / $env:GH_TOKEN —
             handed to git through GIT_ASKPASS so it never appears in the
             process command line,
          3. a secure prompt (interactive runs only).
    #>
    New-AskPassScript | Out-Null   # creates the script only when a token exists

    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $ghOk = $false
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & gh auth status *> $null
            $ghOk = ($LASTEXITCODE -eq 0)
        } catch { $ghOk = $false } finally { $ErrorActionPreference = $previous }
        if ($ghOk) {
            Write-Info2 "GitHub CLI مسجّل الدخول — سيتم استخدامه لمصادقة git."
            Invoke-Native -FilePath "gh" -Arguments @("auth", "setup-git") -AllowFailure | Out-Null
            return $true
        }
    }

    if ($env:MIDO_GIT_TOKEN) { return $true }

    if ($NonInteractive) { return $false }

    Write-Host ""
    Write-Info2 "المستودع خاص (private) — نحتاج صلاحية GitHub لتنزيله."
    Write-Info2 "أنشئ توكنًا من: https://github.com/settings/tokens (صلاحية repo)"
    Write-Info2 "أو سجّل الدخول بـ: gh auth login"
    $secure = Read-Host "  الصق توكن GitHub (لن يظهر على الشاشة)" -AsSecureString
    $plain = [System.Net.NetworkCredential]::new("", $secure).Password
    if (-not $plain) { return $false }
    $env:MIDO_GIT_TOKEN = $plain
    Register-Secret $plain
    New-AskPassScript | Out-Null
    return $true
}

function Invoke-MidoGit {
    param([string[]]$Arguments)
    $env:GIT_TERMINAL_PROMPT = "0"
    $env:MIDO_GIT_USER = "x-access-token"
    return Invoke-Native -FilePath "git" -Arguments $Arguments
}

function Ensure-Repository {
    Write-Head "المستودع"
    $gitDir = Join-Path $RepoDir ".git"
    if ((Test-Path -LiteralPath $gitDir) -and (Test-Path -LiteralPath (Join-Path $RepoDir "mido_setup.py"))) {
        Write-Ok "المستودع موجود: $RepoDir"
        if ($Mode -eq "Install" -and -not $Force) {
            Write-Info2 "سيتم تحديث المستودع الموجود (بدون أي حذف)."
        }
        return $true
    }
    if ((Test-Path -LiteralPath $RepoDir) -and -not (Test-Path -LiteralPath $gitDir)) {
        if (-not $Force) {
            throw "$RepoDir موجود لكنه ليس مستودع git — انقل المجلد أو استخدم -RepoDir آخر أو -Force."
        }
    }

    if (-not (Test-Path -LiteralPath $RepoDir)) {
        New-Item -ItemType Directory -Path $RepoDir -Force | Out-Null
    }

    if (-not (Enable-GitAuth)) {
        throw 'لا توجد مصادقة GitHub.  صدّر $env:MIDO_GITHUB_TOKEN أو استخدم gh auth login أو شغّل بدون -NonInteractive.'
    }

    Write-Step "git clone ($Branch)…"
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $staging = Join-Path (Split-Path -Parent $RepoDir) ("Mido.clone-" + $stamp)
    $cloneOk = $false
    try {
        Invoke-MidoGit -Arguments @("clone", "--branch", $Branch, "--origin", "origin", $RepoUrl, $staging) | Out-Null
        if (-not (Test-Path -LiteralPath (Join-Path $staging "mido_setup.py"))) {
            throw "المستودع المُنزَّل لا يحتوي على mido_setup.py — تحقّق من الرابط والفرع ($Branch)."
        }
        if (Test-Path -LiteralPath $RepoDir) {
            $items = @(Get-ChildItem -LiteralPath $RepoDir -Force)
            if ($items.Count -gt 0) {
                throw "$RepoDir ليس فارغًا - لن يتم حذف أي شيء. انقل محتواه أو استخدم -RepoDir آخر."
            }
            Remove-Item -LiteralPath $RepoDir -Force
        }
        Move-Item -LiteralPath $staging -Destination $RepoDir
        $cloneOk = $true
    } catch {
        Write-Warn2 "تعذّر الاستنساخ: $(Protect-Secrets $_.Exception.Message)"
    } finally {
        if (Test-Path -LiteralPath $staging) {
            # only our own, never-completed clone is removed - user data is never touched
            Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    if (-not $cloneOk) {
        throw "فشل git clone من $RepoUrl — تحقّق من التوكن والاتصال بالإنترنت."
    }
    Write-Ok "تم استنساخ المستودع في $RepoDir"
    return $true
}

function Update-Repository {
    Write-Head "تحديث المستودع"
    if (-not (Test-Path -LiteralPath (Join-Path $RepoDir ".git"))) {
        throw "$RepoDir ليس مستودع git — شغّل -Mode Install أولًا."
    }
    if (-not (Enable-GitAuth)) {
        Write-Warn2 "بدون مصادقة GitHub — سيُجرّب التحديث كما هو."
    }
    Invoke-MidoGit -Arguments @("-C", $RepoDir, "fetch", "origin", $Branch) | Out-Null
    $before = (& git -C $RepoDir rev-parse --short HEAD 2>$null) -join ""
    Invoke-MidoGit -Arguments @("-C", $RepoDir, "pull", "--ff-only", "origin", $Branch) | Out-Null
    $after = (& git -C $RepoDir rev-parse --short HEAD 2>$null) -join ""
    if ($before -eq $after) {
        Write-Ok "المستودع محدّث بالفعل ($after)"
    } else {
        Write-Ok "تم التحديث: $before → $after"
    }
    return $true
}

# ══════════════════════════════════════════════════════════════════════════════
#  python environment
# ══════════════════════════════════════════════════════════════════════════════
function Get-VenvPython {
    $candidates = @(
        (Join-Path $RepoDir ".venv\Scripts\python.exe"),
        (Join-Path $RepoDir ".venv\Scripts\python"),
        (Join-Path $RepoDir ".venv/bin/python")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Ensure-Venv {
    param([hashtable]$Launcher)
    Write-Head "البيئة الافتراضية (venv)"
    $venvPython = Get-VenvPython
    if ($venvPython) {
        $probeOk = $false
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & $venvPython -c "import sys; print(sys.version_info[0])" *> $null
            $probeOk = ($LASTEXITCODE -eq 0)
        } catch { $probeOk = $false } finally { $ErrorActionPreference = $previous }
        if ($probeOk) {
            Write-Ok "venv سليم: $venvPython"
            return $venvPython
        }
        Write-Warn2 "venv موجود لكنه غير قابل للاستخدام — سيُعاد إنشاؤه (بدون لمس الجلسات أو قاعدة البيانات)."
        $broken = Join-Path $RepoDir (".venv.broken-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
        Move-Item -LiteralPath (Join-Path $RepoDir ".venv") -Destination $broken -Force
        Write-Info2 "تم الاحتفاظ بالبيئة القديمة في $broken (يمكنك حذفها لاحقًا)."
    }

    Write-Step "إنشاء .venv جديد…"
    Invoke-Native -FilePath $Launcher.Exe -Arguments ($Launcher.Prefix + @("-m", "venv", (Join-Path $RepoDir ".venv"))) | Out-Null
    $venvPython = Get-VenvPython
    if (-not $venvPython) { throw "تعذّر إنشاء البيئة الافتراضية في $RepoDir\.venv" }
    Write-Ok "تم إنشاء venv"
    return $venvPython
}

function Install-Dependencies {
    param([string]$VenvPython)
    Write-Head "المكتبات"
    if ($SkipDeps) {
        Write-Info2 "تم تخطي تثبيت المكتبات (-SkipDeps)."
        return $true
    }
    $requirements = Join-Path $RepoDir "requirements.txt"
    if (-not (Test-Path -LiteralPath $requirements)) { throw "requirements.txt غير موجود في $RepoDir" }
    Invoke-Native -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "wheel") | Out-Null
    Write-Step "pip install -r requirements.txt (قد يستغرق بضع دقائق)…"
    Invoke-Native -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--no-input", "-r", $requirements) | Out-Null
    $noDeps = Join-Path $RepoDir "requirements-nodeps.txt"
    if (Test-Path -LiteralPath $noDeps) {
        # googletrans pins a stale httpx that conflicts with youtube-search-python
        Write-Step "pip install --no-deps -r requirements-nodeps.txt…"
        Invoke-Native -FilePath $VenvPython -Arguments @("-m", "pip", "install", "--no-input", "--no-deps", "-r", $noDeps) | Out-Null
    }
    Write-Ok "تم تثبيت المكتبات"
    return $true
}

# ══════════════════════════════════════════════════════════════════════════════
#  configuration, setup, hardening, verification
# ══════════════════════════════════════════════════════════════════════════════
function Ensure-EnvFile {
    $envPath = Join-Path $RepoDir ".env"
    if (Test-Path -LiteralPath $envPath) {
        Write-Ok ".env موجود (لن يُستبدل؛ سيُؤخذ منه ما هو مطلوب)."
        return $envPath
    }
    $example = Join-Path $RepoDir ".env.example"
    if (Test-Path -LiteralPath $example) {
        Copy-Item -LiteralPath $example -Destination $envPath -Force
        Write-Ok "تم إنشاء .env من .env.example"
    } else {
        New-Item -ItemType File -Path $envPath -Force | Out-Null
        Write-Warn2 ".env.example غير موجود — تم إنشاء .env فارغ."
    }
    return $envPath
}

function Invoke-MidoSetup {
    param([string]$VenvPython)
    Write-Head "الإعداد وتسجيل الدخول"
    if ($SessionFile) {
        if (-not (Test-Path -LiteralPath $SessionFile)) {
            throw "ملف الجلسة غير موجود: $SessionFile"
        }
        $env:MIDO_SETUP_SESSION_FILE = (Resolve-Path -LiteralPath $SessionFile).Path
        Write-Info2 "سيتم استيراد الجلسة من: $SessionFile"
    }
    $arguments = @("mido_setup.py", "setup")
    if ($NonInteractive) { $arguments += "--non-interactive" }
    $code = Invoke-InRepo -FilePath $VenvPython -Arguments $arguments -AllowFailure
    if ($code -ne 0) {
        throw "لم يكتمل الإعداد (كود $code) — راجع الرسائل أعلاه ثم أعد المحاولة."
    }
    Write-Ok "اكتمل الإعداد"
    return $true
}

function Invoke-MidoCheck {
    param([string]$VenvPython, [switch]$AllowProblems)
    Write-Head "الفحص النهائي"
    $code = Invoke-InRepo -FilePath $VenvPython -Arguments @("mido_setup.py", "check") -AllowFailure
    if ($code -ne 0 -and -not $AllowProblems) {
        throw "الفحص وجد مشاكل (كود $code) — راجع النقاط أعلاه، ثم شغّل -Mode Repair أو أعد -Mode Setup."
    }
    if ($code -eq 0) { Write-Ok "كل الفحوصات ناجحة" }
    return [int]$code
}

function Protect-Files {
    Write-Head "تأمين الملفات الحساسة (ACLs)"
    $icacls = Get-Command icacls -ErrorAction SilentlyContinue
    if (-not $icacls) {
        Write-Warn2 "icacls غير متاح — لم يتم ضبط الصلاحيات. تأكد يدويًا أن .env ومجلد الجلسات لا يقرأهما غيرك."
        return $true
    }
    $user = "$env:USERDOMAIN\$env:USERNAME"
    $targets = New-Object System.Collections.Generic.List[string]
    foreach ($name in @(".env", "config.py", "Mido.db", "zthon.db", "cinemagoer.db")) {
        $path = Join-Path $RepoDir $name
        if (Test-Path -LiteralPath $path) { $targets.Add($path) }
    }
    foreach ($file in (Get-ChildItem -LiteralPath $RepoDir -Filter "*.session" -File -ErrorAction SilentlyContinue)) {
        $targets.Add($file.FullName)
    }
    $sessionDir = Join-Path $RepoDir "data\sessions"
    if (-not (Test-Path -LiteralPath $sessionDir)) {
        New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null
    }
    $targets.Add($sessionDir)
    foreach ($file in (Get-ChildItem -LiteralPath $sessionDir -File -ErrorAction SilentlyContinue)) {
        $targets.Add($file.FullName)
    }

    foreach ($target in $targets) {
        $isDir = Test-Path -LiteralPath $target -PathType Container
        $grant = $(if ($isDir) { "${user}:(OI)(CI)(F)" } else { "${user}:(F)" })
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & icacls $target /inheritance:r *> $null
            & icacls $target /grant:r $grant *> $null
            $code = $LASTEXITCODE
        } catch { $code = 1 } finally { $ErrorActionPreference = $previous }
        if ($code -eq 0) {
            Write-Ok ((Protect-Secrets $target) + " → للمستخدم $user فقط")
        } else {
            Write-Warn2 "تعذّر ضبط صلاحيات $target (كود $code)"
        }
    }
    return $true
}

function Start-Mido {
    param([string]$VenvPython)
    Write-Head "تشغيل Mido"
    if (-not $VenvPython) { $VenvPython = Get-VenvPython }
    if (-not $VenvPython) { throw "لا توجد بيئة افتراضية — شغّل -Mode Install أولًا." }
    Write-Info2 "لإيقاف البوت: Ctrl+C"
    Write-Info2 "للتشغيل التلقائي عند الدخول راجع deploy\WINDOWS-RDP.md (Task Scheduler)."
    Push-Location -LiteralPath $RepoDir
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $VenvPython -m zira
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
        Pop-Location
    }
    if ($null -eq $code) { $code = 0 }
    return [int]$code
}

# ══════════════════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════════════════
function Test-IsWindows {
    if ($AllowNonWindows) { return $true }
    if ($PSVersionTable.PSVersion.Major -ge 6) { return [bool]$IsWindows }
    return [bool]($env:OS -eq "Windows_NT")
}

function Invoke-MidoMain {
    $exitCode = 0
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {
        Write-Verbose "mido: console encoding left untouched: $($_.Exception.Message)"
    }
    Write-Host ""
    Write-Host "  Mido - Windows/RDP installer - mode: $Mode (installer $($script:MidoInstallerVersion))" -ForegroundColor Magenta
    Write-Host "  Log: $($script:LogFile)" -ForegroundColor DarkGray
    Write-Log "=== Mido installer $($script:MidoInstallerVersion) · mode=$Mode · repo=$RepoDir · ps=$($PSVersionTable.PSVersion) ==="

    $ProgressPreference = "SilentlyContinue"   # much faster downloads
    if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }
    $ErrorActionPreference = "Stop"

    if (-not (Test-IsWindows)) {
        Write-Err2 "هذا المثبّت مخصص لويندوز (Windows Server / RDP)."
        return 2
    }

    # token precedence: parameter → environment (never logged, never on argv)
    if (-not $Token) { $Token = $env:MIDO_GITHUB_TOKEN }
    if (-not $Token) { $Token = $env:GH_TOKEN }
    if ($Token) {
        Register-Secret $Token
        $env:MIDO_GIT_TOKEN = $Token
    }
    if ($SessionFile) { Register-Secret (Split-Path -Leaf $SessionFile) }

    try {
        switch ($Mode) {
            "Start" {
                return (Start-Mido -VenvPython (Get-VenvPython))
            }
            "Check" {
                if (-not (Test-Path -LiteralPath (Join-Path $RepoDir "mido_setup.py"))) {
                    Write-Err2 "لم يتم العثور على المشروع في $RepoDir — شغّل -Mode Install أولًا."
                    return 2
                }
                $venvPython = Get-VenvPython
                if (-not $venvPython) {
                    Write-Err2 "لا توجد بيئة افتراضية — شغّل -Mode Install أو -Mode Repair."
                    return 2
                }
                return (Invoke-MidoCheck -VenvPython $venvPython -AllowProblems)
            }
            "Repair" {
                $launcher = Ensure-Prerequisites
                if (-not (Test-Path -LiteralPath (Join-Path $RepoDir "mido_setup.py"))) {
                    Write-Warn2 "المشروع غير موجود — سيتم تثبيته بالكامل."
                    Ensure-Repository | Out-Null
                }
                $venvPython = Ensure-Venv -Launcher $launcher
                if (-not $SkipDeps) { Install-Dependencies -VenvPython $venvPython | Out-Null }
                Protect-Files | Out-Null
                $code = Invoke-MidoCheck -VenvPython $venvPython -AllowProblems
                if ($code -ne 0) {
                    Write-Warn2 "ما زالت هناك مشاكل — راجع التفاصيل أعلاه (لا يتم حذف أي جلسة أو قاعدة بيانات تلقائيًا)."
                }
                return $code
            }
            "Setup" {
                if (-not (Test-Path -LiteralPath (Join-Path $RepoDir "mido_setup.py"))) {
                    Write-Err2 "لم يتم العثور على المشروع في $RepoDir — شغّل -Mode Install أولًا."
                    return 2
                }
                $venvPython = Get-VenvPython
                if (-not $venvPython) {
                    Write-Warn2 "لا توجد بيئة افتراضية — سيتم إنشاؤها."
                    $launcher = Get-PythonLauncher
                    if (-not $launcher) { $launcher = Ensure-Prerequisites }
                    $venvPython = Ensure-Venv -Launcher $launcher
                    if (-not $SkipDeps) { Install-Dependencies -VenvPython $venvPython | Out-Null }
                }
                Ensure-EnvFile | Out-Null
                Invoke-MidoSetup -VenvPython $venvPython | Out-Null
                Protect-Files | Out-Null
                $code = Invoke-MidoCheck -VenvPython $venvPython -AllowProblems
                if (-not $NoStart -and -not $NonInteractive) {
                    $answer = Read-Host "  هل تريد تشغيل البوت الآن؟ (y/N)"
                    if ($answer -match '^(y|yes|نعم)$') { return (Start-Mido -VenvPython $venvPython) }
                }
                return $code
            }
            default {
                # Install / Update
                $launcher = Ensure-Prerequisites
                $repoExisted = Test-Path -LiteralPath (Join-Path $RepoDir "mido_setup.py")
                if ($repoExisted) {
                    if ($Mode -eq "Update") {
                        Update-Repository | Out-Null
                    } else {
                        try { Update-Repository | Out-Null } catch { Write-Warn2 "تعذّر التحديث: $(Protect-Secrets $_.Exception.Message)" }
                    }
                } else {
                    Ensure-Repository | Out-Null
                }
                $venvPython = Ensure-Venv -Launcher $launcher
                Install-Dependencies -VenvPython $venvPython | Out-Null
                Ensure-EnvFile | Out-Null
                Invoke-MidoSetup -VenvPython $venvPython | Out-Null
                Protect-Files | Out-Null
                $exitCode = Invoke-MidoCheck -VenvPython $venvPython -AllowProblems
                if ($exitCode -ne 0) {
                    Write-Warn2 "الفحص النهائي أبلغ عن مشاكل — راجع التفاصيل أعلاه."
                    return $exitCode
                }
                Write-Host ""
                Write-Ok "اكتمل التثبيت بنجاح."
                Write-Info2 "للتشغيل لاحقًا: $RepoDir\Mido-Start.cmd أو: `"$venvPython`" -m zira"
                if (-not $NoStart -and -not $NonInteractive) {
                    $answer = Read-Host "  هل تريد تشغيل البوت الآن؟ (y/N)"
                    if ($answer -match '^(y|yes|نعم)$') { return (Start-Mido -VenvPython $venvPython) }
                }
                return 0
            }
        }
    } catch {
        $message = Protect-Secrets ([string]$_.Exception.Message)
        Write-Host ""
        Write-Err2 "توقّف التنفيذ: $message"
        Write-Info2 "السجل الكامل: $($script:LogFile)"
        Write-Log "FATAL $message"
        return 1
    } finally {
        Remove-AskPassScript
    }
    return $exitCode
}

# Allow dot-sourcing for tests (`Get-PythonDownloadCandidates`, `Select-GitForWindowsAssetUrl`, …)
if ($MyInvocation.InvocationName -ne ".") {
    exit (Invoke-MidoMain)
}
