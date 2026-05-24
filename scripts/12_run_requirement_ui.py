from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "apps" / "requirement_collection_ui.py"


def main() -> None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(APP_PATH)], cwd=str(PROJECT_ROOT), check=True)


if __name__ == "__main__":
    main()
