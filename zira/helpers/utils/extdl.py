import sys
from subprocess import PIPE, Popen


def install_pip(pipfile):
    print(f"installing {pipfile}")
    # use the interpreter that is actually running the bot - a bare `pip`
    # binary does not exist on every system (only `pip3`).
    pip_cmd = [sys.executable, "-m", "pip", "install", f"{pipfile}"]
    process = Popen(pip_cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout
