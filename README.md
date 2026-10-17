
**〔 سـورس Mido 〕**

**افضـل سـورسـات يـوزر بـوت العربيـة**

**› عربـي بالكـامل › تحديثـات متواصـله › فـارات تلقـائيـه بسهولـه〔 حصريـاً 〕** 

#**By:** https://t.me/Mido

---

## تشغيل سريع على ويندوز / RDP

**الطريقة الأسهل — ملف واحد فقط:**

```powershell
# ارفع Mido-OneClick.ps1 إلى السيرفر ثم:
powershell -ExecutionPolicy Bypass -File .\Mido-OneClick.ps1
```

ينزّل أحدث نسخة من المشروع (توكن GitHub مرة واحدة) ويكمل التثبيت والإعداد تلقائيًا.

**أو — المجلد كامل بدون GitHub (لا توكن):**

```powershell
powershell -ExecutionPolicy Bypass -File .\Mido-RDP-Install.ps1 -Mode Install
.\Mido-Start.cmd
```

المثبّت يتكفّل بـ: Python + Git (عبر winget أو المثبّتات الرسمية) → نسخ المشروع → venv →
`requirements.txt` → إنشاء `.env` → تسجيل دخول تيليجرام (أو استيراد جلسة قديمة
`-SessionFile`) → التحقق من توكن البوت → تأمين الصلاحيات (ACLs) → فحص شامل.

* نقطة البداية المكتوبة لأي مشغّل: [`START-HERE-WINDOWS.txt`](START-HERE-WINDOWS.txt)

* الأوضاع: `Install` · `Update` · `Setup` · `Check` · `Repair` · `Start`
* لم تُحذف أي جلسة أو قاعدة بيانات عند التحديث، و`.env` يُعمل له نسخة احتياطية قبل أي تعديل.
* الدليل الكامل والمشاكل الشائعة: [`deploy/WINDOWS-RDP.md`](deploy/WINDOWS-RDP.md)
* أدوات الإعداد/الفحص بدون تشغيل البوت:

```bash
python mido_setup.py check              # فحص البيئة والجلسات (مقنّع للأسرار)
python mido_setup.py sessions           # الجلسات المكتشفة ومصدرها
python mido_setup.py setup              # الإعداد التفاعلي
python mido_setup.py import-session X.session   # استيراد جلسة والتحقق منها
```

* الاختبارات: `python -m pytest tests -q` (تعمل على Linux وWindows) — ملف سير العمل جاهز في
  `.github/workflows/Tests.yml` لتشغيلها تلقائيًا على `ubuntu-latest` و`windows-latest`
  (يتطلّب تفعيل GitHub Actions للحساب)، ويمكن تشغيلها محليًا على أي نظام.

