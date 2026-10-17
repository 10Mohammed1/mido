# Mido على ويندوز / RDP — دليل التشغيل الكامل

هذا الدليل مخصّص لتركيب **Mido** على سيرفر ويندوز جديد (Windows Server 2019/2022/2025 أو
Windows 10/11) بحيث يعمل البوت بالكامل: المكتبات → جلسة تيليجرام → توكن البوت → التشغيل.

> كل الأوامر أدناه تُنفَّذ في **PowerShell** داخل مجلد المشروع (مثال: `C:\Users\Administrator\Mido`).

---

## 1) التثبيت السريع

### الطريقة صفر) سطر واحد يُلصق في PowerShell (الأسرع — بلا تنزيل ملفات)

انسخ السطر التالي والصقه في PowerShell على السيرفر (سيطلب منك توكن GitHub مرة واحدة):

```powershell
$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $s=Read-Host 'GitHub token' -AsSecureString; $t=[System.Net.NetworkCredential]::new('',$s).Password; $h=@{Authorization="token $t";'User-Agent'='Mido'}; $p="$env:TEMP\Mido-OneClick.ps1"; Invoke-WebRequest 'https://raw.githubusercontent.com/10Mohammed1/mido/main/Mido-OneClick.ps1' -Headers $h -OutFile $p -UseBasicParsing; $env:MIDO_GITHUB_TOKEN=$t; powershell -NoProfile -ExecutionPolicy Bypass -File $p; Remove-Item Env:\MIDO_GITHUB_TOKEN -ErrorAction SilentlyContinue
```

> المستودع خاص، لذلك التوكن (صلاحية `repo`) ضروري لتنزيل الملف. السطر لا يطبع التوكن
> ولا يكتبه على القرص، ويمرّره للمثبّت عبر متغيّر بيئة فقط (لا في الأمر نفسه).

### الطريقة أ) ملف واحد فقط — `Mido-OneClick.ps1` (الأسهل)

1. نزّل **`Mido-OneClick.ps1`** (من المستودع أو من صفحة Releases).
2. شغّل سطرًا واحدًا يتعامل مع مكان الملف أيًّا كان (تنزيلات المتصفح تذهب عادةً إلى
   `Downloads`، وقد يتغير اسم الملف):

```powershell
cd $env:USERPROFILE\Downloads; $f=(Get-ChildItem -Filter 'Mido-OneClick*.ps1' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; if (-not $f) { Write-Host 'Mido-OneClick.ps1 غير موجود في Downloads — استخدم الطريقة صفر أو انسخ الملف إلى هذا المجلد' } else { Unblock-File $f -ErrorAction SilentlyContinue; powershell -NoProfile -ExecutionPolicy Bypass -File $f }
```

> إن كان الملف في نفس المجلد الذي أنت فيه الآن: `powershell -ExecutionPolicy Bypass -File .\Mido-OneClick.ps1`
> (علامة `.\` تعني «في المجلد الحالي» — لهذا يفشل الأمر من مجلد آخر).

يسألك عن توكن GitHub (أو يستخدم `gh` إن كان مسجّلًا للدخول)، ثم **ينزّل أحدث نسخة من
المشروع** إلى `%USERPROFILE%\Mido` ويشغّل التثبيت الكامل تلقائيًا. ملف واحد يكفي.

### الطريقة ب) المجلد كامل — بدون توكن GitHub إطلاقًا

انسخ مجلد المشروع كما هو (أو فُكّ ضغط `Mido-Windows-Bundle.zip`) إلى السيرفر، ثم من
داخل المجلد:

```powershell
powershell -ExecutionPolicy Bypass -File .\Mido-RDP-Install.ps1 -Mode Install
```

> الطريقة (ب) لا تتصل بـ GitHub نهائيًا (المثبّت يكتشف أنها نسخة منقولة بدون `.git`
> ويستخدمها كما هي). تحتاج إنترنت فقط لتنزيل Python/Git والمكتبات.

**التشغيل بعد انتهاء التثبيت:**

```powershell
.\Mido-Start.cmd
```

### ماذا سيسألك الإعداد (في الطريقتين)

| المطلوب | ماذا تفعل |
| --- | --- |
| `APP_ID` / `API_HASH` | من <https://my.telegram.org> → API development tools |
| رقم الهاتف | بصيغة دولية مثل `+201234567890` (يُرسل عليه كود تيليجرام) |
| الكود | يصلك في تطبيق تيليجرام → أدخله في نفس النافذة |
| كلمة مرور التحقق بخطوتين | فقط إن كانت مفعّلة على حسابك (لن تظهر على الشاشة) |
| توكن البوت | من [@BotFather](https://t.me/BotFather) → `/newbot` (يُتحقق منه فعليًا قبل حفظه) |

بعد انتهاء الإعداد يُنشأ `.env` بصلاحيات مقيّدة، ويُحفظ ملف الجلسة في
`data\sessions\Mido.session`، ثم يُشغَّل فحص نهائي `python mido_setup.py check`.

---

## 2) أوضاع المثبّت

| الوضع | الأمر | ماذا يفعل بالضبط |
| --- | --- | --- |
| Install | `.\Mido-RDP-Install.ps1 -Mode Install` | تثبيت المتطلبات + نسخ المستودع + venv + المكتبات + الإعداد + الفحص. آمن للتكرار (يتحوّل تلقائيًا إلى تحديث إن كان المشروع موجودًا). |
| Update | `.\Mido-RDP-Install.ps1 -Mode Update` | `git pull --ff-only` + تحديث المكتبات + فحص. **لا يلمس** `.env` ولا الجلسات ولا قواعد البيانات. |
| Setup | `.\Mido-RDP-Install.ps1 -Mode Setup` | (إعادة) تشغيل تسجيل الدخول/التوكن فقط + تأمين الملفات + فحص. |
| Check | `.\Mido-RDP-Install.ps1 -Mode Check` | فحص فقط بدون أي تعديل (كود الخروج 1 عند وجود مشكلة). |
| Repair | `.\Mido-RDP-Install.ps1 -Mode Repair` | إعادة بناء venv التالف + إعادة تثبيت المكتبات + تأمين الملفات + فحص. لا يحذف أي جلسة أو قاعدة بيانات. |
| Start | `.\Mido-RDP-Install.ps1 -Mode Start` | تشغيل البوت من داخل البيئة الافتراضية. |

معاملات مفيدة:

```powershell
-RepositoryDir "D:\Mido"     # مكان المشروع (الافتراضي %USERPROFILE%\Mido)
-RepoUrl "https://github.com/10Mohammed1/mido.git"
-Branch "main"
-SessionFile "C:\path\to\old_pc.session"   # استيراد جلسة من جهاز آخر قبل الدخول
-PythonVersion "3.13"                      # لو احتجت نسخة محددة
-SkipDeps                                  # تخطي pip (للتحديث السريع)
-NoStart                                   # عدم السؤال عن التشغيل في النهاية
-NonInteractive                            # بدون أي أسئلة (يحتاج MIDO_SETUP_* أو جلسة جاهزة)
```

---

## 3) الجلسات: تسجيل دخول جديد أو استيراد جلسة قديمة

**أ) تسجيل دخول جديد:** اترك الإعداد يسألك عن الرقم والكود (كما في الجدول أعلاه).

**ب) استيراد جلسة من جهازك القديم** (بدون كود جديد):

```powershell
# انسخ الملف القديم إلى السيرفر أولًا، ثم:
.\Mido-RDP-Install.ps1 -Mode Setup -SessionFile "C:\Upload\account.session"
```

سيتحقّق Mido من الملف **باتصال حقيقي بتيليجرام** قبل اعتماده:

* جلسة سليمة → تُنسخ إلى `data\sessions\Mido.session` (الملف الأصلي يبقى كما هو).
* جلسة ملغاة/منتهية/تالفة → يُخبرك بذلك صراحةً ولن يستبدل شيئًا، ويمكنك المتابعة بتسجيل دخول جديد.

في الحالتين، إن كانت هناك جلسة سابقة في `data\sessions\Mido.session` يتم عمل نسخة احتياطية
`Mido.session.bak-YYYYMMDD-HHMMSS` قبل أي استبدال. لا يُحذف أي ملف جلسة أبدًا.

**ج) ترتيب مصادر الجلسة** (متغيّر `SESSION_SOURCE` في `.env`):

1. `auto` (الافتراضي): ملف الجلسة في `data\sessions\` إن وُجد → وإلا `STRING_SESSION` → وإلا جلسة جديدة.
2. ملف جلسة صالح **مهمّ** على النص، لأن الجلسة النصية أسهل في التسريب وأصعب في الإدارة.
3. الجلسات القديمة في جذر المشروع (مثل `ZedTgbot.session`) تُستخدم تلقائيًا للحفاظ على
   تشغيلاتك السابقة بدون إعادة تسجيل دخول.

**د) لا تشغّل نسختين من البوت على نفس الجلسة.** Mido يحمي نفسه بقفل
`data\sessions\<اسم الجلسة>.session.lock`؛ إن وُجدت نسخة تعمل سترى:
`نسخة أخرى تعمل الآن على نفس الجلسة (pid …)`.
(يمكن تجاوز القفل مؤقتًا بـ `MIDO_IGNORE_SESSION_LOCK=1` — لا تفعل ذلك إلا وأنت تعرف السبب.)

---

## 4) التشغيل الدائم

تشغيل يدوي: `.\Mido-Start.cmd` أو:

```powershell
& "$env:USERPROFILE\Mido\.venv\Scripts\python.exe" -m zira
```

تشغيل تلقائي عند الدخول (Task Scheduler):

```powershell
$python  = "$env:USERPROFILE\Mido\.venv\Scripts\python.exe"
$action  = New-ScheduledTaskAction -Execute $python -Argument "-m zira" -WorkingDirectory "$env:USERPROFILE\Mido"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "Mido" -Action $action -Trigger $trigger -RunLevel Highest -Force
Start-ScheduledTask -TaskName "Mido"
```

إيقاف/حذف المهمة:

```powershell
Stop-ScheduledTask  -TaskName "Mido"
Unregister-ScheduledTask -TaskName "Mido" -Confirm:$false
```

---

## 5) الأمان (اقرأ هذا)

| الملف | الحماية |
| --- | --- |
| `.env` | خارج git (`.gitignore`) + صلاحيات NTFS للمستخدم الحالي فقط (`icacls`) |
| `*.session` | نفس الحماية + نسخ احتياطية قبل الاستبدال + لا تُحذف تلقائيًا |
| `data\sessions\` | مجلد مُدار ومقيّد الصلاحيات |
| توكن البوت | يُتحقق منه باتصال حقيقي، يُحفظ في `.env` فقط، ويُطبع دائمًا مقنّعًا (`1234…oken`) |
| توكن GitHub | يُمرَّر عبر متغيّر بيئة + `GIT_ASKPASS` — لا يظهر في سطر الأوامر ولا داخل رابط `remote` |
| السجل `%TEMP%\mido-install.log` | تُقنَّع فيه كل الأسرار قبل الكتابة |

قواعد ذهبية: لا ترفع `.env` أو `*.session` إلى أي مستودع. لو تسرّبت جلسة، ألغِها من
إعدادات تيليجرام (Devices) فورًا ثم `-Mode Setup` من جديد.

---

## 6) عند حدوث مشاكل

| الأعراض | السبب المرجّح | الحل |
| --- | --- | --- |
| `git clone` يفشل بكود 128 | توكن GitHub ناقص/منتهي | `$env:MIDO_GITHUB_TOKEN` جديد بصلاحية `repo`، أو `gh auth login` ثم أعد المحاولة |
| `لا توجد جلسة صالحة` | لم يكتمل تسجيل الدخول | `-Mode Setup` (أو `-SessionFile` لجلسة قديمة) |
| `الجلسة ملغاة` | أُنهيت من تيليجرام → الأجهزة | `-Mode Setup` لتسجيل دخول جديد |
| `توكن البوت غير صالح` | نسخ ناقص من BotFather | أعد `-Mode Setup` والصق التوكن كاملًا |
| البوت يخرج فورًا ويذكّر بقفل | نسخة أخرى تعمل | أوقف النسخة القديمة (`Stop-ScheduledTask` أو Ctrl+C في نافذتها) |
| `ModuleNotFoundError` بعد تحديث | مكتبات قديمة | `-Mode Repair` |
| رسائل عربية مشوّشة في نافذة قديمة | ترميز الكونسول | شغّل من `Mido-Start.cmd` أو `chcp 65001` |
| فشل تنزيل Python/Git | لا winget على السيرفر | المثبّت ينزّل الحِزم الرسمية تلقائيًا؛ لو فشل، ثبّتهما يدويًا من python.org و git-scm.com ثم أعد `-Mode Install` |

فحص شامل بدون تعديل:

```powershell
.\Mido-RDP-Install.ps1 -Mode Check
& "$env:USERPROFILE\Mido\.venv\Scripts\python.exe" mido_setup.py sessions   # الجلسات المكتشفة
```

### المكتبات: لماذا ملفان؟

`requirements.txt` قابل للتثبيت مباشرة (`pip install -r requirements.txt`)، لكن حزمتين
تُثبَّتان بعده بـ `--no-deps` من `requirements-nodeps.txt` لأن تثبيتهما العادي مستحيل:

| الحزمة | سبب الاستثناء |
| --- | --- |
| `googletrans==4.0.0rc1` | آخر إصدار بواجهة `translate()` **المتزامنة** التي تستخدمها الملحقات (4.0.2 صارت async وتكسرها)، ويصرّح بحاجة قديمة `httpx==0.13.3` تتعارض مع `youtube-search-python` |
| `search-engine-parser==0.6.8` | يصرّح بـ `lxml<5` بينما `cinemagoer` يحتاج `lxml>=6.1.1`؛ القيد قديم والحزمة تعمل طبيعيًا مع lxml 6 (تستخدم BeautifulSoup) |

المثبّت و GitHub Actions ينفّذان الخطوتين تلقائيًا:

```powershell
pip install -r requirements.txt
pip install --no-deps -r requirements-nodeps.txt
```

---

## 7) ملفات مهمة

| المسار | الوصف |
| --- | --- |
| `.env` | الإعدادات والأسرار (محمي، خارج git) |
| `config.py` | الطريقة القديمة للإعداد — إن وُجد يأخذ الأولوية على `.env` عند قراءة القيم من البيئة |
| `data\sessions\Mido.session` | جلسة المستخدم (telethon) |
| `data\sessions\ZedTgbot.session` | جلسة البوت المساعدة |
| `Mido.db`, `zthon.db` | قواعد بيانات البوت (لا تُحذف عند التحديث) |
| `%TEMP%\mido-install.log` | سجل المثبّت (أسراره مقنّعة) |

---

## 8) قيود معروفة (بصراحة)

* سكربت `Mido-RDP-Install.ps1` كُتب لـ PowerShell 5.1+ على ويندوز. ما تحقّقنا منه فعليًا:
  * فحص ثابت بـ **PSScriptAnalyzer 1.25** (كل القواعد Error/Warning): **لا ملاحظات**،
    وقاعدة التوافق `PSUseCompatibleSyntax` مع **PowerShell 5.1**: **لا ملاحظات**.
  * دوال السكربت النقية (تحديد روابط Python من python.org، اختيار حزمة Git، تقنيع الأسرار)
    **تُنفَّذ فعليًا** في `tests/test_installer_assets.py` عبر PowerShell حقيقي.
  * مسار Python/المكتبات/الإعداد مغطّى بنفس الاختبارات على Linux.
  * **ما لم يتحقّق بعد:** تشغيل المثبّت كاملًا على سيرفر ويندوز حقيقي. ملف
    `.github/workflows/Tests.yml` جاهز لتشغيل الاختبارات على `windows-latest`، لكن
    **GitHub Actions معطّل حاليًا على مستوى الحساب** (`Actions has been disabled for this user`)،
    لذلك لم تظهر نتائج ويندوز من CI بعد. أول تشغيل حقيقي على RDP هو اختبارك، والسجل
    `%TEMP%\mido-install.log` سيحدّد أي مشكلة بدقة.

  للتحقق على أي جهاز ويندوز بعد التثبيت:

  ```powershell
  .\.venv\Scripts\python.exe -m pip install pytest
  .\.venv\Scripts\python.exe -m pytest tests -q          # المتوقع: 127 اختبارًا ناجحًا
  .\Mido-RDP-Install.ps1 -Mode Check                     # فحص شامل بدون أي تعديل
  ```

* مشغّل المجموعات الصوتية (`vcplayer`) غير مدعوم على ويندوز (مكتباته Linux-only) ويُستثنى تلقائيًا.
* `selenium` مثبّت لكنه يحتاج Chrome/Chromedriver على السيرفر (اختياري لأوامر الفحص).
* ملفان للمكتبات: `requirements.txt` ثم `requirements-nodeps.txt` (بـ `--no-deps`) — التفصيل في
  قسم "المكتبات: لماذا ملفان؟" أعلاه.
