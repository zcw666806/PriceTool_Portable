from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REQUIRED_MODULES = ("streamlit", "pandas", "openpyxl", "pdfplumber", "rapidfuzz")


def main() -> int:
    config_path = BASE_DIR / "config" / "app_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "startup.log"
    pid_path = logs_dir / "price_tool.pid"
    app_path = BASE_DIR / "app" / "streamlit_app.py"

    print("========================================")
    print("UK Order 价格查询工具")
    print("========================================")

    if not app_path.exists():
        message = f"未找到页面文件：{app_path}"
        print(message)
        log_path.write_text(message + "\n", encoding="utf-8")
        return 1

    host = config.get("host", "127.0.0.1")
    port = int(config.get("port", 8501))
    url = f"http://{host}:{port}"

    missing = missing_modules()
    if missing:
        print("依赖不完整，工具暂时无法启动。")
        print("缺少模块：" + ", ".join(missing))
        print("请先安装 requirements-portable.txt 中的依赖。")
        return 1

    existing_pid = read_pid(pid_path)
    if existing_pid and is_pid_running(existing_pid):
        print("工具已经在运行中，正在打开页面。")
        webbrowser.open(url)
        return 0

    if is_port_open(host, port):
        print(f"检测到端口 {port} 已经被占用。")
        print("如果页面可以打开，说明工具可能已经在运行。")
        print("正在尝试打开页面。")
        webbrowser.open(url)
        return 0

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

    print("正在启动本地服务，请稍候...")
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n========================================\n")
        log.write("Starting Price Tool\n")
        log.write(f"Base dir: {BASE_DIR}\n")
        log.write(" ".join(command) + "\n")
        process = subprocess.Popen(
            command,
            cwd=BASE_DIR,
            stdout=log,
            stderr=log,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    pid_path.write_text(str(process.pid), encoding="utf-8")

    if wait_for_port(host, port, timeout=20):
        print("启动成功。")
        print(f"页面地址：{url}")
        if config.get("open_browser_on_start", True):
            print("正在打开浏览器...")
            webbrowser.open(url)
        print("可以关闭这个窗口，工具会继续在后台运行。")
        return 0

    print("启动命令已经执行，但页面暂时没有响应。")
    print(f"请稍后手动打开：{url}")
    print(f"如果仍无法访问，请查看日志：{log_path}")
    return 1


def missing_modules() -> list[str]:
    missing = []
    for module in REQUIRED_MODULES:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    return missing


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_port(host: str, port: int, timeout: int = 20) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


def read_pid(pid_path: Path) -> int | None:
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def open_page() -> int:
    config_path = BASE_DIR / "config" / "app_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    host = config.get("host", "127.0.0.1")
    port = int(config.get("port", 8501))
    url = f"http://{host}:{port}"
    if is_port_open(host, port):
        webbrowser.open(f"http://{host}:{port}")
        print(f"已打开页面：{url}")
        return 0
    print("工具当前似乎没有运行，请先启动工具。")
    print(f"页面地址：{url}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--open":
        raise SystemExit(open_page())
    raise SystemExit(main())
