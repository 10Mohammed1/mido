#requires -Version 5.1
<#
.SYNOPSIS
    Mido One-Click bootstrap for Windows/RDP.
.DESCRIPTION
    One entry point: downloads the latest official Mido-RDP-Install.ps1 and runs
    its full Install workflow.  A public repository is fetched anonymously; only
    when that fails (private repository / blocked connection) is a GitHub token
    requested.  Secrets are never written to disk by this bootstrap.
#>
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'interactive one-click bootstrap: the console is the user interface')]
[CmdletBinding()]
param(
    [string]$RepoDir = (Join-Path $env:USERPROFILE "Mido")
)

$ErrorActionPreference = "Stop"
$repo = "10Mohammed1/mido"
$branch = "main"
$installerUrl = "https://raw.githubusercontent.com/$repo/$branch/Mido-RDP-Install.ps1"
$tempInstaller = Join-Path ([IO.Path]::GetTempPath()) ("Mido-RDP-Install-" + [guid]::NewGuid().ToString("N") + ".ps1")
$oldToken = $env:MIDO_GITHUB_TOKEN
$token = $oldToken
$exitCode = 1

function Write-Title([string]$Message) {
    Write-Host ""
    Write-Host ("=== " + $Message + " ===") -ForegroundColor Cyan
}

try {
    Write-Title "Mido — تشغيل وتثبيت تلقائي"
    Write-Host "سيتم تجهيز Python/Git والمكتبات وإعداد تيليجرام وفحص المشروع."
    Write-Host "لن يتم رفع ملف الجلسة أو بيانات الدخول إلى GitHub."

    Write-Title "تنزيل أحدث مثبّت رسمي"
    $downloaded = $false
    try {
        # a public repository needs no credentials at all
        Invoke-WebRequest -Uri $installerUrl -OutFile $tempInstaller -UseBasicParsing
        if ((Test-Path -LiteralPath $tempInstaller -PathType Leaf) -and (Get-Item -LiteralPath $tempInstaller).Length -ge 1000) {
            Write-Host "تم التنزيل مباشرة بدون مصادقة." -ForegroundColor Green
            $downloaded = $true
        }
    } catch {
        $downloaded = $false
    }

    if (-not $downloaded) {
        Write-Host "المستودع يبدو خاصًا (أو الاتصال محجوب) — سنستخدم توكن GitHub." -ForegroundColor Yellow
        if ([string]::IsNullOrWhiteSpace($token) -and (Get-Command gh -ErrorAction SilentlyContinue)) {
            try {
                $candidate = (& gh auth token --hostname github.com 2>$null | Select-Object -First 1)
                if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace([string]$candidate)) {
                    $token = ([string]$candidate).Trim()
                    Write-Host "تم العثور على تسجيل دخول GitHub CLI." -ForegroundColor Green
                }
            } catch {
                $token = $null
            }
        }

        if ([string]::IsNullOrWhiteSpace($token)) {
            Write-Host ""
            Write-Host "أدخل GitHub Personal Access Token بصلاحية قراءة محتويات المستودع (Contents: Read)." -ForegroundColor Yellow
            Write-Host "لن تظهر الأحرف أثناء الكتابة. لا ترسل هذا التوكن لأي شخص."
            $secureToken = Read-Host "GitHub token" -AsSecureString
            if ($null -eq $secureToken -or $secureToken.Length -eq 0) {
                throw "لم يتم إدخال توكن GitHub."
            }
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
            try {
                $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
            } finally {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
                $secureToken.Dispose()
            }
        }

        if ([string]::IsNullOrWhiteSpace($token)) {
            throw "تعذّر الحصول على توكن GitHub."
        }

        $env:MIDO_GITHUB_TOKEN = $token
        $headers = @{ Authorization = "token $token"; "User-Agent" = "Mido-OneClick" }
        Invoke-WebRequest -Uri $installerUrl -Headers $headers -OutFile $tempInstaller -UseBasicParsing
    }

    if (-not (Test-Path -LiteralPath $tempInstaller -PathType Leaf) -or (Get-Item -LiteralPath $tempInstaller).Length -lt 1000) {
        throw "ملف المثبّت الذي تم تنزيله غير مكتمل."
    }

    Write-Title "بدء التثبيت الكامل"
    Write-Host ("مجلد المشروع: " + $RepoDir)
    # resolve the Windows PowerShell host explicitly: under PowerShell 7 $PSHOME
    # points at the pwsh folder, where powershell.exe does not exist
    $shell = Join-Path $PSHOME "powershell.exe"
    if (-not (Test-Path -LiteralPath $shell)) {
        $cmd = Get-Command powershell.exe -ErrorAction SilentlyContinue
        if ($null -ne $cmd) { $shell = $cmd.Source } else { $shell = (Get-Process -Id $PID).Path }
    }
    & $shell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $tempInstaller -Mode Install -RepoDir $RepoDir
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }

    if ($exitCode -eq 0) {
        Write-Title "انتهى المثبّت"
        Write-Host "لو اكتمل الإعداد بنجاح، يمكنك تشغيل Mido من المجلد:" -ForegroundColor Green
        Write-Host $RepoDir
        Write-Host "قد يطلب منك الإعداد APP_ID وAPI_HASH ورقم الهاتف وكود تيليجرام وكلمة مرور 2FA عند الحاجة."
    } else {
        Write-Host ""
        Write-Host ("انتهى المثبّت بكود خطأ: " + $exitCode) -ForegroundColor Red
        Write-Host "افحص سجل المثبّت: $env:TEMP\mido-install.log"
    }
} catch {
    Write-Host ""
    Write-Host ("فشل Mido One-Click: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "تأكد من اتصال الإنترنت وصلاحية التوكن للوصول إلى المستودع الخاص."
    Write-Host "إذا استمر الخطأ، أرسل نص الخطأ فقط، وليس التوكن أو ملف الجلسة."
    $exitCode = 1
} finally {
    if (Test-Path -LiteralPath $tempInstaller) {
        Remove-Item -LiteralPath $tempInstaller -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $oldToken) {
        $env:MIDO_GITHUB_TOKEN = $oldToken
    } else {
        Remove-Item Env:\MIDO_GITHUB_TOKEN -ErrorAction SilentlyContinue
    }
    $token = $null
    $headers = $null
}

Write-Host ""
if ($exitCode -ne 0) {
    Write-Host "لم يكتمل التثبيت. لم يتم حذف ملفات المشروع أو الجلسات الموجودة." -ForegroundColor Yellow
}
exit [int]$exitCode
