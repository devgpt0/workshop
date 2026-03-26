from pathlib import Path
import subprocess
import sys


def streamlit_app_path() -> Path:
    return Path(__file__).resolve().parents[1] / "ui" / "web" / "streamlit_app.py"


def launch_web_ui() -> int:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(streamlit_app_path())],
            check=False,
        )
    except OSError as exc:
        print(f"Error launching Streamlit: {exc}")
        return 1
    return int(result.returncode)


def main() -> int:
    return launch_web_ui()
