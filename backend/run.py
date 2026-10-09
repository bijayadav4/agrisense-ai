import os
import sys

# Auto-detect and switch to project virtualenv if running with system python
venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "../venv/bin/python"))
if os.path.exists(venv_python) and sys.executable != venv_python and not os.environ.get("_AGRISENSE_VENV_ACTIVATED"):
    os.environ["_AGRISENSE_VENV_ACTIVATED"] = "1"
    os.execv(venv_python, [venv_python] + sys.argv)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
