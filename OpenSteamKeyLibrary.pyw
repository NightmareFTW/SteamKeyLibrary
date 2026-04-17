import sys
import os
import subprocess

# Bootstrap: if a .venv exists next to this script, re-launch with its Python
# so that all optional dependencies (e.g. cryptography) are available.
_script_dir = os.path.dirname(os.path.abspath(__file__))
_venv_python = os.path.join(_script_dir, ".venv", "Scripts", "pythonw.exe")
if os.path.isfile(_venv_python) and os.path.abspath(sys.executable) != os.path.abspath(_venv_python):
    subprocess.Popen([_venv_python, __file__] + sys.argv[1:])
    sys.exit()

from steamkeylibrary import SteamKeyApp


if __name__ == "__main__":
    app = SteamKeyApp()
    app.mainloop()