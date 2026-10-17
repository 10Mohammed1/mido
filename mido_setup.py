#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mido · setup & diagnostics entry point.

Usage (the same commands also work as ``python -m zira <command>``)::

    python mido_setup.py check                 # فحص البيئة والإعدادات والجلسات
    python mido_setup.py check --online        # + تحقق فعلي من تيليجرام
    python mido_setup.py setup                 # الإعداد الأولي (جلسة + توكن + .env)
    python mido_setup.py import-session PATH   # استيراد ملف .session جاهز
    python mido_setup.py sessions              # عرض الجلسات الموجودة
    python mido_setup.py repair                # تسجيل دخول جديد لجلسة ملغاة

Importing this file has no side effects (it never starts a Telegram client).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mido.setup_cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
