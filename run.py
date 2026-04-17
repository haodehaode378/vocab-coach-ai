import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "apps" / "api"
WEB_DIR = ROOT / "apps" / "web"


def npm_command() -> str:
    if os.name == "nt":
        return "npm.cmd"
    return "npm"


def spawn_api(host: str, port: int, reload_enabled: bool) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload_enabled:
        cmd.append("--reload")
    return subprocess.Popen(cmd, cwd=API_DIR)


def spawn_web(host: str, port: int) -> subprocess.Popen:
    npm_bin = shutil.which(npm_command()) or npm_command()
    cmd = [npm_bin, "run", "dev", "--", "--host", host, "--port", str(port)]
    return subprocess.Popen(cmd, cwd=WEB_DIR)


def stop_processes(procs: list[subprocess.Popen]) -> None:
    for p in procs:
        if p.poll() is None:
            p.terminate()
    for p in procs:
        if p.poll() is None:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI Vocab Agent")
    parser.add_argument("--target", choices=["all", "api", "web"], default="all")
    parser.add_argument("--api-host", default="127.0.0.1")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-host", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=5173)
    parser.add_argument("--no-reload", action="store_true", help="Disable API auto reload")
    parser.add_argument("--no-open", action="store_true", help="Disable auto open browser")
    args = parser.parse_args()

    if not API_DIR.exists():
        print(f"API directory not found: {API_DIR}")
        return 1
    if args.target in ("all", "web") and not WEB_DIR.exists():
        print(f"Web directory not found: {WEB_DIR}")
        return 1

    procs: list[subprocess.Popen] = []

    def handle_stop(_sig, _frame):
        stop_processes(procs)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    try:
        if args.target in ("all", "api"):
            procs.append(spawn_api(args.api_host, args.api_port, not args.no_reload))
            print(f"API running at http://{args.api_host}:{args.api_port}")

        if args.target in ("all", "web"):
            procs.append(spawn_web(args.web_host, args.web_port))
            print(f"Web running at http://{args.web_host}:{args.web_port}")

        if not args.no_open:
            if args.target in ("all", "web"):
                time.sleep(1)
                webbrowser.open(f"http://{args.web_host}:{args.web_port}")
            elif args.target == "api":
                time.sleep(1)
                webbrowser.open(f"http://{args.api_host}:{args.api_port}/healthz")

        if not procs:
            return 1

        while True:
            for p in procs:
                code = p.poll()
                if code is not None:
                    stop_processes([x for x in procs if x is not p])
                    return code
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_processes(procs)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
