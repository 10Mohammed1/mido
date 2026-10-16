# طرق تشغيل Mido (بدائل `run.sh`)

`run.sh` بيشتغل كـ supervisor بسيط: لو البوت وقع بيرجّعه بعد 20 ثانية.
الملفات اللي هنا بتقدّم طريقة أنضف وأقوى (systemd) اختيارية — مش لازم تستخدمها.

---

## الطريقة 1: `run.sh` (الأسهل، شغالة حاليًا)

```bash
cd /home/medo/Downloads/zz/ZThon
setsid nohup ./run.sh >/dev/null 2>&1 &
```

- بيتكتب لوج واحد: `/tmp/opencode/zthon_run3.log`
- بيتصفّر اللوج في كل مرة الـsupervisor يقوم.
- **عيب:** لو الجهاز عمل reboot، مش هيرجع لوحده.

---

## الطريقة 2: systemd (يشتغل تلقائي بعد الـreboot) — يحتاج `sudo`

```bash
cd /home/medo/Downloads/zz/ZThon
mkdir -p logs
sudo cp deploy/mido.service /etc/systemd/system/mido.service
sudo systemctl daemon-reload
sudo systemctl enable --now mido
```

أوامر المتابعة:

```bash
systemctl status mido      # البوت شغال؟
systemctl restart mido     # إعادة تشغيل
systemctl stop mido        # إيقاف
tail -f logs/mido.log      # اللوج
```

---

## الطريقة 3: systemd للمستخدم (بدون `sudo`)

```bash
cd /home/medo/Downloads/zz/ZThon
mkdir -p logs ~/.config/systemd/user
cp deploy/mido-user.service ~/.config/systemd/user/mido.service
systemctl --user daemon-reload
systemctl --user enable --now mido

# عشان يفضل شغال بعد تسجيل الخروج:
loginctl enable-linger "$USER"
```

---

## دوران السجلات (logrotate) — يحتاج `sudo`

```bash
sudo cp deploy/logrotate.conf /etc/logrotate.d/mido
sudo logrotate -d /etc/logrotate.d/mido    # تجربة بدون تنفيذ
```

من غير `sudo`، اقدر تفضّي اللوج بنفسك:

```bash
: > /home/medo/Downloads/zz/ZThon/logs/mido.log
```

---

## ملاحظات مهمة

1. **متشغلش أكتر من نسخة في نفس الوقت** بنفس `STRING_SESSION` — ده بيفصل الجلسة.
2. السشن بينحفظ في `ZedTgbot.session` — **متمسحهوش**.
3. لو نقلت المشروع لمجلد تاني، عدّل المسارات في:
   - `deploy/mido.service`
   - `deploy/mido-user.service`
   - `deploy/logrotate.conf`
4. الأسرار كلها تتقرأ من البيئة، وممكن تحطها في `.env` (شوف `.env.example`).
