# config values will be loaded from here

import os
from pathlib import Path

# The `mido` helpers / local `config.py` live in the repository root.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

# `.env` must work even when there is no local `config.py` (fresh clone,
# Windows install, …).  `override=False` keeps real environment variables
# (Heroku / systemd / the installer) authoritative.
try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=str(ROOT / ".env"), override=False)
except Exception:
    pass

ENV = bool(os.environ.get("ENV", False))


def _local_config_available() -> bool:
    return Path("config.py").is_file() or (ROOT / "config.py").is_file()


if ENV:
    from sample_config import Config  # noqa
elif _local_config_available():
    try:
        from config import Development as Config  # noqa
    except Exception:  # a broken local config must not brick the bot
        from sample_config import Config  # noqa
else:
    from sample_config import Config  # noqa
