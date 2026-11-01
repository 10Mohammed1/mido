# تقرير فحص مشروع Mido — المرحلة الأولى

- **تاريخ الفحص:** 2026-11-01
- **ال-commit المفحوص:** `c93a042` (Prepare for public release…)
- **طريقة الفحص:** قراءة فعلية لكل ملف مذكور، تشغيل فعلي للاختبارات وRuff، فحص md5 للتوافقات، فحص نصي للسرّيات.
- **خط أساس الاختبارات (مُشغَّل فعليًا):**
  `.venv-test/bin/python -m pytest tests -q` → **1 failed, 133 passed, 5 skipped**
  (Python 3.12.3، والقفزات الخمس = اختبارات PowerShell غير متاحة على Linux)
- **حالة فحص الأسرار:** نظيف — لا توجد API_HASH أو Bot Token أو STRING_SESSION داخل المستودع.

**مفتاح الأولويات:**

| الرمز | المعنى |
|---|---|
| 🔴 P1 | حرج: يمنع التشغيل أو يفشل الاختبار أو كسر وظيفة بالكامل |
| 🟠 P2 | مهم: سلوك خاطئ، خطر أمان، أو تناقض يُضلّل المستخدم |
| 🟡 P3 | تحسين/تنظيف/توثيق |

---

## 1. مشاكل حرجة (P1)

### 1.1 كسر googletrans مع المكتبات الحديثة 🔴 P1
- **الملف:** `zira/helpers/functions/functions.py:8` (`from googletrans import Translator`)
- **الحقيقة:** حزمة `googletrans==4.0.0rc1` (في `requirements-nodeps.txt:26`) تفشل **عند الاستيراد** مع `httpcore` الحديث:
  `AttributeError: module 'httpcore' has no attribute 'SyncHTTPTransport'` (‏`googletrans/client.py:62`).
- **الدليل الفعلي:** هذا بالضبط الاختبار الفاشل الوحيد في خط الأساس:
  `tests/test_requirements.py::test_no_deps_modules_are_importable_and_keep_the_expected_api`.
- **ملاحظة:** التعليقات في `requirements-nodeps.txt:11-17` و`requirements.lock.txt:127` تزعم أن googletrans تعمل مع httpx الحديث — **الزعم مُفكَّك بالاختبار الفعلي**. حتى حقن السمة يدويًا يُفشل لاحقًا `Translator()` بـ `ImportError: ... 'h2' package is not installed`.
- **الأثر:** أي وحدة تستورد `functions.py` لا تُحمَّل → خطوة تشغيل البوت تتعطل.

### 1.2 واجهات Pillow المحذوفة (Pillow 10+) 🔴 P1
- `zira/helpers/functions/functions.py:274` — `Image.ANTIALIAS` (حُذفت في Pillow 10؛ المثبّت Pillow 12.x)
- `zira/helpers/functions/functions.py:287` — `draw.textsize()` (حُذفت)
- `zira/helpers/functions/functions.py:332` و`:361` — `font.getsize()` (حُذفت)
- `zira/plugins/رساله.py:43` — `font.getsize("hg")`
- **الأثر:** استدعاء هذه الدوال يرمي `AttributeError` فوريًا.

### 1.3 حتمية تعليق/انهيار `الضغط.py` 🔴 P1
- `zira/plugins/الضغط.py:42` مقابل `:54` — التقدُّم **يُكتب** في `output_directory/progress.txt` ويُقرأ من `./temp/progress.txt` (مساران مختلفان).
- `zira/plugins/الضغط.py:52` — `while process.returncode != 0:` مع `communicate()` **بعد** الحلقة: مع خروج процесс بفشل دائم تدور الحلقة إلى ما لا نهاية (تعليق دائم)، ومع حجم أنبوب كبير يمتلئ الـpipe فيتعطل ffmpeg (deadlock).
- لا يوجد `timeout` لأي أمر ffmpeg، ولا فحص لـ `returncode` بعد الانتهاء (يُعلن النجاح حتى عند الفشل).
- `create_subprocess_shell` مع f-string (السطران `:46` و`:118`) — خطر حقن مسارات/أسماء ملفات.
- أربع دوال تحمل الاسم نفسه `ff_mpeg_trim_cmd` (السطور `271, 330, 418, 479`) — خطأ F811 يصعّب الصيانة.

## 2. ملفات التحديث (P2)

- **تكرار كامل:** `zira/plugins/التحديث.py` و`zira/plugins/تحديث البوت.py` **متطابقان بايتًا ببايت** (md5 `c16c387b…` لكليهما)، وكلاهما يسجّل نفس الـ handler `pattern="تحديث البوت$"` (السطر `167` في كلٍّ منهما) → تسجيل مكرر وتحميل مزدوج.
- `التحديث.py:181` — `off_repo = "https://github.com/Mido/Mido"` — مسار upstream **خاطئ** (المشروع `10Mohammed1/mido`) → أي فحص تحديث سيلتمم مستودعًا آخر.
- `التحديث.py:182` — `os.chdir("/app")` — مسار Heroku مطلق، يفشل على كل منصّة أخرى.
- **سلبي مُؤكَّد جيدًا:** `update_bot` معطّل عمداً منذ سابق (بدون `git reset --hard`) مع تعليق تفسيري — سيُحتفظ به ويُطوَّر.
- `.تحديث` = أمر إعادة تشغيل فعلي في `zira/plugins/النظام.py:233`، بينما نص المساعدة (`zira/plugins/الاوامر.py:101,191`) يصفه بأنه «البحث عن تحديثات وتحديث البوت» — تناقض نصي/سلوكي.
- `.تحديث الان` مذكور في نص المساعدة (`الاوامر.py:101,191`، `المساعده.py:541`، ورسالة داخل `التحديث.py:178`) لكن **لا يوجد handler ينفّذه**.

## 3. عرض النتائج (P2)

- `zira/plugins/android.py:116` — `results = results[:8]`: قصّ للقوائم الطويلة **دون Pagination ودون طريقة عرض الباقي** → النتائج تُحذف من العرض ولا يمكن الوصول إليها.

## 4. المنع والتحذير (P2)

- `zira/plugins/المنع والتحذير.py:121` و`:126` — عند بلوغ حد التحذيرات يُسجَّل فقط `logger.info("TODO: طرد المستخدم")` / `("TODO: حظر المستخدم")` — **الإجراء غير منفَّذ**.
- يجب تنفيذ الطرد/الحظر مع التحقق من صلاحية المشرف، ومنع الحظر الخاطئ، وتسجيل العمليات والأخطاء. (يُفحص بالكامل عند مرحلة الإصلاح؛ الملف يحوي فحوصات صلاحيات جزئية موجودة بالفعل.)

## 5. إدارة الإضافات (P2)

- `zira/utils/startup.py:275` — عند `ModuleNotFoundError` أثناء تحميل إضافة يُستدعى `install_pip(e.name)` — **تثبيت اعتمادية تلقائيًا دون موافقة** (خطورة سلسلة إمداد + تعارض صريح مع قواعد المشروع).
- `zira/utils/pluginmanager.py:20` (`load_module`) — لا يوجد حماية ضد تحميل الإضافة نفسها مرتين.
- `NO_LOAD`/`VPS_NOLOAD` موجودان ويجب الحفاظ عليهما (`startup.py:64-71,259-260`).
- `malak.py` (الجذر) و`zira/plugins/malak.py` **مختلفان** (md5 مختلف: `a65a15ae` مقابل `65e537d7`) — نسخة الجذر ليست محمّلة لكنها تُضلّل؛ إضافة المستخدمات الخارجية (`malak.py`/`malath.py` في الإضافات) **معطّلة عمداً بتعليقات** وسيُبقَى تعطيلها.

## 6. Python والاعتماديات (P1/P2)

- `runtime.txt` = `python-3.14.7`، بينما CI يختبر `3.12` فقط، و`pyproject.toml:14` يقول `>=3.10`، و`pyproject.toml:63` (pylint) يقول `3.10`.
- **الحد الفعلي المُثبَت بالاعتماديات:** `numpy==2.5.3` يتطلب `>=3.12`، و`SQLAlchemy 2.1.4` يتطلب `>=3.11`، و`fonttools`/`markdown`/`lyricsgenius` `>=3.11` → **الحد الأدنى الحقيقي 3.12**، أي أن `requires-python >=3.10` غير صادق، وأن `3.14.7` غير مُختبَر في CI إطلاقًا.
- `requirements-nodeps.txt:26` — googletrans كسرة كما في البند 1.1.

## 7. GitHub Actions (P2)

- `.github/workflows/Tests.yml:20-22` — المصفوفة ممتازة (‎ubuntu+windows‎) لكن إصدار Python واحد `3.12` فقط.
- `.github/workflows/PyLint.yml:26,30` — `continue-on-error: true` على خطوتَي Ruff → فشل اللِنت لا يمنع الإطلاق أبدًا.
- **حالة Ruff الحالية (مُشغَّلة فعليًا، ruff 0.17.3):** نحو 2034 خطأ، منها ~1154 قابلة للإصلاح تلقائيًا، أبرزها `F811` (إعادة تعريف دوال — أسلوب handler مكرر) و`F821` (‏`tgbot`/`edit_or_reply`/`borg` غير معرّفة في `zira/assistant/zedhack.py` وغيرها) — معظم F821 أسماء **يحقنها `load_module` ديناميكيًا** ولا يراها Ruff.

## 8. تثبيت Windows وRDP (P2)

- `deploy/WINDOWS-RDP.md:86` يستخدم `-RepositoryDir` بينما اسم المعامل الفعلي في السكربت هو `-RepoDir` (`Mido-RDP-Install.ps1:34,68`) → الأمر الموثّق يفشل فعليًا.
- `Mido-RDP-Install.ps1` — `MinPython = 3.10` بينما الحد الأدنى الحقيقي 3.12 (بند 6) → التثبيت يقبل Python لا تعمل عليه الاعتماديات.
- `Mido-OneClick.ps1` وميثاق الاختبارات موجودان؛ اختبارات PowerShell تُتخطّى على Linux (لا يوجد PowerShell هنا) — توثيقها كقيد بيئي.

## 9. ملفات التشغيل والنشر (P2/P3)

- `run.sh:6` — `cd /home/medo/Downloads/zz/ZThon` — مسار شخصي مطلق لا يعمل خارج جهاز صاحب المشروع.
- `deploy/mido.service:26` و`deploy/mido-user.service:26` — نفس المسار الشخصي في `WorkingDirectory`.
- `Dockerfile:1,7` — صورة قديمة `zilzalll/zthon:slim-buster` (‏Debian buster EOL) + Node 16 EOL (`nodesource setup_16.x`) — غير صالحة للاستخدام الحديث.

## 10. ملفات قمامة (P3)

ستة ملفات بحجم 1 بايت لا تؤدي شيئًا: `.github/zg`، `zedthon/zzz`، `zira/Config/zb`، `zira/assistant/zt`، `zira/core/zv`، `zira/z5`.

## 11. الأمان (P1 سياسة)

- `zira/plugins/فحص فيزات.py` — أوامر تخصّ بطاقات الدفع/الفيزا (`cc`, `كومبو`, `توليد`, `فيزا`, `ماستر` … السطور `31,55,79,103,127…`) تُفوّض لبوت خارجي `@SDBB_Bot` وتفتح `unblock` عليه — **تُعطَّل** في مرحلة الأمان (تسهّل إساءة استخدام).
- `install_pip` التلقائي (بند 5) — يُعطَّل/يُقيَّد بموافقة.
- `malak`/`malath` لتنزيل إضافات خارجية — يُبقَى معطّلًا مع توثيق السبب.
- فحص السرّيات: نظيف ✓ (يُحوَّل إلى اختبار دائم في مرحلة الأمان).

---

## ملخص الأولويات

| # | المشكلة | المسار:السطر | الأولوية |
|---|---|---|---|
| 1 | googletrans غير قابل للاستيراد | functions.py:8 + requirements-nodeps.txt:26 | 🔴 P1 |
| 2 | Pillow API محذوف (4 مواضع + رساله.py) | functions.py:274,287,332,361 · رساله.py:43 | 🔴 P1 |
| 3 | الضغط.py تعليق/مسارات/timeout | الضغط.py:42,52,54,46,118,271+ | 🔴 P1 |
| 4 | تحديث مكرر + upstream خاطئ + ‎chdir‎ مطلق | التحديث.py:167,181,182 ≡ تحديث البوت.py | 🟠 P2 |
| 5 | android.py قصّ بلا Pagination | android.py:116 | 🟠 P2 |
| 6 | TODOs طرد/حظر غير منفّذة | المنع والتحذير.py:121,126 | 🟠 P2 |
| 7 | تثبيت تلقائي للإضافات | startup.py:275 · extdl.py:5 | 🟠 P2 |
| 8 | Python 3.10/3.14/3.12 متناقضة | runtime.txt · pyproject:14,63 | 🟠 P2 |
| 9 | continue-on-error + CI بإصدار واحد | PyLint.yml:26,30 · Tests.yml:22 | 🟠 P2 |
| 10 | ‎-RepositoryDir‎ vs ‎-RepoDir‎ | WINDOWS-RDP.md:86 · RDP-Install.ps1:68 | 🟠 P2 |
| 11 | مسارات شخصية | run.sh:6 · deploy/*.service:26 | 🟠 P2 |
| 12 | Dockerfile قديمة | Dockerfile:1,7 | 🟡 P3 |
| 13 | ملفات قمامة 1 بايت (6 ملفات) | انظر بند 10 | 🟡 P3 |
| 14 | فحص فيزات.py (بطاقات) | فحص فيزات.py:31+ | 🔴 P1 سياسة |
| 15 | نص مساعدة `.تحديث` و`.تحديث الان` لا يطابق الواقع | الاوامر.py:101,191 · لا handler | 🟡 P3 |

**حدود الفحص:** اختبارات PowerShell وWindows الحقيقية غير قابلة للتشغيل في بيئة Linux هذه (5 اختبارات مُتخطّاة) — توثّق كقيد بيئي ولا تُعلَّم كنجاح.
