from __future__ import annotations

import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def main() -> int:
    config_path = BASE_DIR / "config" / "app_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "startup.log"
    app_path = BASE_DIR / "app" / "streamlit_app.py"
    if not app_path.exists():
        log_path.write_text(f"Missing app file: {app_path}\n", encoding="utf-8")
        return 1

    host = config.get("host", "127.0.0.1")
    port = int(config.get("port", 8501))
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]

    with log_path.open("a", encoding="utf-8") as log:
        log.write("\nStarting Price Tool\n")
        log.write(" ".join(command) + "\n")
        process = subprocess.Popen(command, cwd=BASE_DIR, stdout=log, stderr=log)

    if config.get("open_browser_on_start", True):
        time.sleep(3)
        webbrowser.open(f"http://{host}:{port}")

    return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
