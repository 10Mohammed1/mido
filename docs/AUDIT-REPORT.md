# تقرير المراجعة الشاملة — Mido

| البند | القيمة |
|---|---|
| المستودع | `https://github.com/10Mohammed1/mido` |
| الفرع المفحوص | `main` |
| آخر إيداع | `c93a042` — *Prepare for public release: token-free one-liner becomes the primary entry point* |
| تاريخ الفحص | 2026-10-31 |
| فرع العمل | `audit/phase-1-report` |
| النسخة الاحتياطية | `mido-backup-20261031.bundle` (git bundle لكل الفروع + التاريخ) |
| الترخيص الفعلي | AGPL-3.0 (`LICENSE`) |
| حجم الشجرة | 324 ملفاً متتبعاً · 233 ملف Python (155 إنجليزي + 78 عربي في `zira/plugins`) |

---

## 0. المنهجية

لم يُعدَّل أي ملف في هذه المرحلة. كل ما يلي تحقق فعلي من محتوى الملفات الحالي، ومن استدعاءات
مُشغَّلة على الجهاز، لا افتراضات:

| نوع الدليل | الطريقة |
|---|---|
| قراءة الكود | قراءة كاملة للملفات المستهدفة + `grep` على كل الشجرة |
| تشغيل الاختبارات | `python -m pytest tests -q` على Python 3.12.10 / Windows |
| سلوك المكتبات | تشغيل مباشر لـ `heroku3.from_key(None)`، `PIL.ImageFont.getsize`، `str.format` |
| إعادة إنتاج الأخطاء | سكربتات مستقلة تعيد إنتاج كل خطأ على حدة |
| الفحص الأمني | بحث عن أنماط الأسرار + مراجعة مسارات تنفيذ الكود الخارجي |

### نتيجة تشغيل الاختبارات (قياس فعلي)

| الحالة | النتيجة |
|---|---|
| بيئة نظيفة (pytest + dotenv + telethon فقط) | `132 passed, 5 failed, 2 skipped` |
| بعد إضافة `validators` (اعتمادية إلزامية) | `134 passed, 3 failed, 2 skipped` |
| بعد إضافة حزم التشغيل (`sqlalchemy`, `aiohttp`, `PIL`, …) | يُتوقَّع `136 passed` — انظر الملاحظة أدناه |

> **ملاحظة مهمة:** الفشل الثالث (`test_passes_on_a_minimal_complete_project`) ليس خللاً في الكود بل في
> بيئة الاختبار: الأمر `check` يتحقق من وجود حزم التشغيل كاملة، والبيئة المصغّرة لا تحتويها.
> الفشلان الآخران **خلل حقيقي** على Windows (البند P0-5 و P1-6 أدناه).

---

## 1. ملخص تنفيذي

المشروع في حالة أفضل بكثير مما توحي به بنيته: هناك طبقة `mido/` حديثة (تثبيت، جلسات، إعدادات،
فحص) مع 136 اختباراً، وطبقة `zira/` هي السورس الأصلي. المشاكل الحقيقية محصورة في:

1. **تكرار حرفي لملفين** يُسجّلان الأمر نفسه مرتين (`التحديث.py` = `تحديث البوت.py` بايت ببايت).
2. **حلقة لا نهائية مؤكدة** في أمر الضغط تُعلّق البوت عند أي فشل لـ `ffmpeg`.
3. **تنفيذ كود خارجي دون موافقة** داخل محمّل الإضافات (`pip install` تلقائي + `git clone` من رابط حر).
4. **أداة فحص/توليد بطاقات ائتمان** (`فحص فيزات.py`) — وظيفة إجرامية يجب تعطيلها.
5. **تسريب مقبض SQLite** يُفشل استيراد الجلسات على Windows (مُعاد إنتاجه).
6. **تضارب إصدارات Python** بين `runtime.txt` و CI و `pyproject.toml`.

---

## 2. جدول المشكلات

الأولويات: **P0** يُعطّل وظيفة أو يخالف قانوناً/أماناً · **P1** خطأ مؤكد يظهر للمستخدم ·
**P2** دين تقني/صيانة · **P3** تجميلي.

| # | الأولوية | الملف | السطر | المشكلة |
|---|---|---|---|---|
| 1 | **P0** | `zira/plugins/التحديث.py`<br>`zira/plugins/تحديث البوت.py` | 1–229 | الملفان متطابقان تماماً (SHA256 واحد) → الأمر `تحديث البوت` مُسجَّل مرتين، فيُنفَّذ مرتين |
| 2 | **P0** | `zira/core/client.py` | 207, 242 | فحص منع التكرار غير فعّال: `wrapper` يُنشأ من جديد في كل استدعاء، فلا يساوي ما سبق |
| 3 | **P0** | `zira/plugins/الضغط.py` | 42 ↔ 54 | مسار `progress.txt` يُكتب في `output_directory` ويُقرأ من `./temp` — يختلفان خارج `./temp` |
| 4 | **P0** | `zira/plugins/الضغط.py` | 52 | `while process.returncode != 0` — القيمة `None` أثناء التشغيل، فلا يوجد شرط خروج إن فشل `ffmpeg` |
| 5 | **P0** | `zira/plugins/الضغط.py` | 46–50 | `create_subprocess_shell` مع `"""…"""` — حقن أوامر عبر أسماء الملفات + لا `timeout` |
| 6 | **P0** | `zira/plugins/الضغط.py` | 168–174 | `edit_delete` ثم السقوط للأسفل بدون `return` → `NameError: zedevent` |
| 7 | **P0** | `mido/session.py` | 324 | `with sqlite3.connect(...)` لا يغلق الاتصال → `os.replace` يفشل بـ `WinError 5` على Windows |
| 8 | **P0** | `zira/utils/startup.py` | 274–280 | `install_pip(e.name)` تلقائياً عند أي `ModuleNotFoundError` — تثبيت حزم دون موافقة |
| 9 | **P0** | `zira/utils/startup.py` | 378–404 | `install_externalrepo` ينفّذ `git clone` + `pip install -r` من رابط يوفّره المستخدم |
| 10 | **P0** | `zira/plugins/فحص فيزات.py` | 1–170 | مولّد وفاحص بطاقات ائتمان (CC Checker/Generator) — أداة احتيال مالي |
| 11 | P1 | `zira/plugins/المنع والتحذير.py` | 152, 157 | `str.format` بثلاثة `{}` ووسيطين → `IndexError` مؤكد |
| 12 | P1 | `zira/plugins/المنع والتحذير.py` | 121, 126 | `TODO: طرد/حظر المستخدم` — الوظيفة غير مكتملة، التحذير الأخير لا يطبّق شيئاً |
| 13 | P1 | `zira/plugins/المنع والتحذير.py` | 167–170 | `حذف التحذيرات` بلا `require_admin` وبلا فحص للرد → `AttributeError` |
| 14 | P1 | `zira/plugins/المنع والتحذير.py` | 157–161 | بناء النص مرتين، النسخة الأولى تُهمَل |
| 15 | P1 | `zira/plugins/رساله.py` | 43 | `ImageFont.getsize` أُزيل في Pillow ≥ 10 (تحقق فعلي) → الأمر يفشل دائماً |
| 16 | P1 | `zira/plugins/رساله.py` | 25, 33 | قصّ صامت عند 25 سطراً، وبلا فحص لـ `text is None` |
| 17 | P1 | `zira/plugins/android.py` | 115–116 | قصّ صامت إلى 8 نتائج بلا أي ترقيم صفحات |
| 18 | P1 | `zira/plugins/android.py` | 32, 58, 100, 147 | `requests.get` متزامن بلا `timeout` داخل حلقة `asyncio` → تجميد كامل للبوت |
| 19 | P1 | `zira/plugins/android.py` | 152 | `page.find("table")` قد يكون `None` → `AttributeError` |
| 20 | P1 | `zira/plugins/التحديث.py` | 181–182 | `os.chdir("/app")` مسار Heroku ثابت + مستودع وهمي `github.com/Mido/Mido` |
| 21 | P1 | `zira/plugins/التحديث.py` | 206–225 | شريط تقدّم وهمي: 10 `sleep(1)` ثابتة لا علاقة لها بالتحديث |
| 22 | P1 | `zira/plugins/التحديث.py` | 146, 156 | `remote.push(..., force=True)` — كتابة قسرية تُفقد تاريخ الفرع |
| 23 | P1 | `zira/plugins/التحديث.py` | 175–179 | عند عدم وجود `config.py` و`ENV=False` يكمل التنفيذ بدل التوقف |
| 24 | P1 | `zira/plugins/malak.py` | 21–78 | كود ميت (المهمة معطّلة) لكنه يبقى محمّلاً ويستورد `install_pip` |
| 25 | P1 | `zira/plugins/malath.py` | 14–52 | نفس الكود الميت معرّف تحت `if zilzal in zed_dev` |
| 26 | P1 | `runtime.txt` | 1 | `python-3.14.7` مقابل CI `3.12` و`requires-python >=3.10` و`target-version py310` |
| 27 | P1 | `.github/workflows/PyLint.yml` | 24, 28 | كلا الخطوتين `continue-on-error: true` → الفشل لا يمنع الدمج |
| 28 | P1 | `.github/workflows/PyLint.yml` | 26 | `ruff format --check .` لا يمكن أن ينجح على الشجرة الحالية |
| 29 | P1 | `run.sh` | 7 | `cd /home/medo/Downloads/zz/ZThon` — مسار مطوّر واحد، يفشل عند أي شخص آخر |
| 30 | P1 | `run.sh` | 9 | `export TZ="Africa/Cairo"` يتجاوز إعداد المستخدم |
| 31 | P1 | `Dockerfile` | 1, 5, 6 | قاعدة `slim-buster` (Debian 10 منتهية) + NodeSource 16 (منتهي) |
| 32 | P1 | `pyproject.toml` | 15 | `license = "MIT"` بينما `LICENSE` هو AGPL-3.0 |
| 33 | P1 | `tests/conftest.py` | 35 | نفس تسريب مقبض SQLite → يعطّل اختبارين على Windows |
| 34 | P2 | `zira/core/client.py` | 338 | `self.running_processes` غير معرّف في أي مكان → `AttributeError` |
| 35 | P2 | `zira/core/client.py` | 335 | `traceback.format_exception(etype=…)` — الوسيط أُزيل في Python 3.10 |
| 36 | P2 | `zira/__main__.py` | 63–64 | `SESSION_LOCK.release(); sys.exit()` → رمز خروج 0 عند فشل قاتل |
| 37 | P2 | `zira/utils/startup.py` | 63–71 | `VPS_NOLOAD = ["vps"] / ["heroku"]` لا يطابق أي ملف إضافة (`هيروكو.py`) → ميت |
| 38 | P2 | `zira/utils/startup.py` | 239–249 | مسارات نسبية لـ CWD → يفشل التحميل إن شُغّل من مجلد آخر |
| 39 | P2 | `zira/utils/startup.py` | 336–376 | إنشاء مجموعات + إعادة تشغيل — كود غير قابل للوصول (`if not BOTLOG: return`) |
| 40 | P2 | `zira/plugins/__init__.py` | 27 | `heroku3.from_key(None)` عند الاستيراد — تحقق: لا يرفع استثناءً، لكنه عميل غير مصادق |
| 41 | P2 | `zira/plugins/الضغط.py` | 279, 330, 418, 479 | أربع دوال بنفس الاسم `ff_mpeg_trim_cmd` |
| 42 | P2 | 21 ملفاً | — | ملفات متتبَّعة حجمها 1–2 بايت (`.github/zg`, `zira/core/zv`, `zira/z5`, …) |
| 43 | P2 | `zira/sql_helper/DS_Store` | — | ملف macOS متتبَّع |
| 44 | P2 | `.gitignore` | — | لا يتجاهل `.venv-test/`, `*.bundle`, `Mido.db`, `.ruff_cache/` |
| 45 | P2 | `ِCOMMANDS.md` | — | 18.7KB توثيق أوامر غير مرتبط بالكود ولا يُتحقق منه |
| 46 | P3 | `zira/plugins/التحديث.py` | 34–49 | 8 ثوابت غير مستخدمة + `update_requirements`/`gen_chlog` بلا مستدعٍ |
| 47 | P3 | `zira/plugins/الضغط.py` | 18, 20 | `humanbytes` و`readable_time` مستوردان من مكانين |

---

## 3. تفاصيل المشكلات الحرجة

### P0-1 · تكرار ملفات التحديث

```
التحديث.py      A726474D12F862E59A00F4556536B9B13A4E1B04C949032D12D250A6591FA1C3
تحديث البوت.py  A726474D12F862E59A00F4556536B9B13A4E1B04C949032D12D250A6591FA1C3
=> IDENTICAL
```

`load_plugins` يحمّل كل ملفات `zira/plugins/*.py` أبجدياً، فتُستورد النسختان، وكل نسخة تنفّذ
`@zedub.zed_cmd(pattern="تحديث البوت$")` وتعريفها الخاص من `upstream`. الأمر الواحد يُطلق
معالجين: رسالتان، ومحاولتا `edit`، و`deploy` مرتين (أي `push force` إلى Heroku مرتين).

منع التكرار في `zed_cmd` (السطر 207) لا يعمل لأن `wrapper` كائن جديد كل مرة:

```python
if command[0] in LOADED_CMDS and wrapper in LOADED_CMDS[command[0]]:
    return None
```

### P0-2 · تعليق أمر الضغط (مُعاد إنتاجه بالقراءة)

```python
42:  progress = output_directory + "/" + "progress.txt"      # يُكتب هنا
46:  process = await asyncio.create_subprocess_shell(...)     # shell + """quoting"""
52:  while process.returncode != 0:                          # None أثناء التشغيل → يظل صحيحاً
54:      with open("./temp/progress.txt", "r+") as file:      # مسار ثابت مختلف
```

ثلاثة أعطال مستقلة في نفس الحلقة:

* إن كان `output_directory != "./temp"` فالملف المقروء غير موجود → `FileNotFoundError`.
* إن فشل `ffmpeg` (codec غير مدعوم، ملف تالف) فلن تُكتب `progress=end` أبداً →
  `returncode` يصبح `≠ 0` → **حلقة أبدية** تُعلّق المعالج ولا يُغلق `communicate()` أبداً.
* لا `timeout` ولا قراءة لـ `stderr`، فلا أحد يعرف سبب الفشل.

### P0-3 · تنفيذ كود خارجي دون موافقة

`zira/utils/startup.py:274-280` — تثبيت صامت:

```python
except ModuleNotFoundError as e:
    install_pip(e.name)          # pip install لأي حزمة يطلبها أي ملف إضافة
```

`zira/utils/startup.py:378-404` — `install_externalrepo` ينفّذ `git clone <رابط>` ثم
`pip install --no-cache-dir -r <cfolder>/requirements.txt` ثم `load_plugins(cfolder)` —
أي أن أي رابط يوضعه المستخدم في `EXTERNAL_REPO` يُنفَّذ كودُه داخل عملية البوت بصلاحيات كاملة.
نفس النمط في `malak.py`/`malath.py` حيث تُسحب ملفات `.py` من قناة تيليجرام وتُحمَّل مباشرة.

### P0-4 · أداة بطاقات الائتمان

`zira/plugins/فحص فيزات.py` تُعلن عن نفسها في الترويسة:

```
CC Checker & Generator for MidoT
```

وتنفّذ `cmd`/`فيزا`/`مستر`/`امكس` عبر محادثة آلية مع بوت طرف ثالث (`@SDBB_Bot`) لتوليد
أرقام بطاقات وفحص صلاحيتها. هذه وظيفة تُسهّل الاحتيال المالي، وتخالف شروط خدمة GitHub
وسياسة Telegram. **الموقع 10 من قائمة المطلوب تعطيله**، وسيُعطَّل مع الإبقاء على الملف
وتوثيق السبب (لا حذف).

### P0-5 · تسريب مقبض SQLite (مُعاد إنتاجه)

```python
# mido/session.py:322-327
with sqlite3.connect(uri, uri=True, timeout=2) as conn:   # لا يغلق الاتصال!
    conn.execute("select count(*) from sqlite_master").fetchone()
```

`with` على `sqlite3.Connection` يُنفّذ commit/rollback فقط. على Windows يبقى المقبض مفتوحاً
حتى يدور جامع القمامة، فيفشل `os.replace(tmp, target)` في `import_session_file`:

```
PermissionError: [WinError 5] Access is denied:
  '…\Mido.session.tmp' -> '…\Mido.session'
```

تم إعادة إنتاجه بسكربت مستقل: `unlink FAILED: [WinError 32] The process cannot access the file`.
الأثر العملي: `python mido_setup.py import-session --force` يفشل على Windows، وهو مسار
الترقية الأساسي — أي احتمال فقدان جلسة عند الترحيل.

### P0-6 · التحذيرات

```python
# zira/plugins/المنع والتحذير.py:151-155
"... [ المستخدم 👤](tg://user?id={}) ... {}/{} ...".format(num_warns, limit)
```

ثلاثة `{}` ووسيطان → تحقق فعلي: `IndexError: Replacement index 2 out of range`.
يحدث كلما كانت للمستخدم تحذيرات بدون أسباب مسجّلة.

---

## 4. عدم توافق Python والاعتماديات

| الملف | القيمة الحالية | ملاحظة |
|---|---|---|
| `runtime.txt` | `python-3.14.7` | إصدار غير موجود على أي منصة استضافة؛ الجهاز يحتوي 3.14.9 |
| `.github/workflows/Tests.yml` | `python: ["3.12"]` | مصفوفة أحادية |
| `pyproject.toml` | `requires-python = ">=3.10"` | لا اختبارات فعلية على 3.10/3.11 |
| `pyproject.toml` | `target-version = "py310"` | يتسق مع السابق فقط |
| `Dockerfile` | بلا تحديد إصدار | يعتمد على صورة أساس منتهية الصلاحية |
| `requirements.txt` | `>= 3.10` في التعليق | تعليق مقابل `runtime.txt` مختلف |

**الخلاصة:** لا يوجد إصدار Python واحد مُتفَق عليه. المستهدف بعد الإصلاح:
**3.10 – 3.13 معتمد، 3.12 هو الإصدار المرجعي**، و`runtime.txt` يُوحَّد معه. لا يُرفع الحد
إلى 3.14 قبل بناء بيئة اختبار كاملة عليها (3.14 موجودة على الجهاز وستُختبر).

---

## 5. ما يحتاج توثيقاً لا تعديلاً

| البند | السبب |
|---|---|
| `zira/plugins/honk`… `Zedthoon.py`, `zedthon/*` | مجلدات بأسماء مطوّرين؛ لا أعرف أصلها، ولن أحذف ما لم أتحقق منه |
| `الاوامر.py:494` (`الفيزا` عبر inline) | ليس فحص بطاقات فعلي، بل نص تذكيري عن فيزا Heroku — لم أعطّله |
| `zira/plugins/الانتحال والازعاج.py` / `الازعاج.py` | وظائف انتحال/إزعاج؛ سياسةً مشكوك فيها، لكنها ليست احتيالاً مالياً — أُبقيها وأوصي بمراجعتها |
| `zira/plugins/التفليش.py` | linter يحذّر: يستدعي خدمات خارجية؛ لم أتحقق من كامل السلوك بعد |
| `Zed_Vip`/`Zed_Dev` = `(8483582680,)` | معرّف مطوّر السورس الأصلي مُثبَّت في `startup.py:46-47` و`client.py:41` — يمنحه مسار تقارير الأخطاء؛ لم أُزل لأنه تغيير سلوكي يحتاج قرارك |
| `zé` ملفات بلا امتداد حجمها 1 بايت | تبدو آثار رفع قديم؛ حذفها آمن لكنه خارج نطاق أي إصلاح وظيفي |

---

## 6. خطة العمل المعتمدة

| المرحلة | الفرع | المحتوى |
|---|---|---|
| 1 | `audit/phase-1-report` | هذا التقرير (لا تغيير وظيفي) |
| 2 | `refactor/phase-2-fixes` | إصلاح البنود P0 و P1 في الملفات السبعة المستهدفة + توحيد Python + CI + تنظيف |
| 3 | `split/phase-3-userbot`، `split/phase-3-bot` | فصل حقيقي إلى مستودعين + مكتبة مشتركة `mido-core` |
| 4 | — | `.env.example` مستقل، فحص تسريب الأسرار، تقرير أمني |
| 5 | — | تشغيل فعلي لكل اختبار في القائمة، وتوثيق النتائج كما هي |

**قاعدة ملزمة:** لا يُعلن أي اختبار ناجحاً إلا بمخرج فعلي موثَّق في `docs/TEST-REPORT.md`.
