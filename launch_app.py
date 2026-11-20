#!/usr/bin/env python3
"""Cross-platform standalone desktop app launcher for Algo Studio.

Works completely offline on Chromebook (ChromeOS Linux), Windows, macOS, and Linux:
1. Starts the local Python 3 stdlib server on 127.0.0.1:8788 (or reuses an active instance).
2. Opens Algo Studio in a frameless standalone app window (Chrome/Edge --app mode)
   or launches the ChromeOS / default system browser automatically.
3. Keeps your progress saved locally in data/progress.json (or ALGO_STUDIO_DATA_DIR).
"""

from __future__ import annotations

import argparse
import http.client
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import server


def _is_algo_studio_running(host: str, port: int) -> bool:
    try:
        conn = http.client.HTTPConnection(host, port, timeout=1.0)
        try:
            conn.request("GET", "/api/health")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8", errors="ignore")
            return resp.status == 200 and '"algo-studio"' in body
        finally:
            conn.close()
    except OSError:
        return False


def _pick_available_port(host: str, preferred: int) -> int:
    for port in (preferred, *range(preferred + 1, preferred + 25)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def _is_chromeos_crostini() -> bool:
    return Path("/dev/.cros_milestone").exists() or shutil.which("garcon-url-handler") is not None


def _find_chromium_app_browser() -> str | None:
    system = platform.system().lower()
    if system == "darwin":
        for app_bin in (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ):
            if os.path.isfile(app_bin):
                return app_bin
        return None

    if system == "windows":
        program_files = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        rel_paths = (
            r"Google\Chrome\Application\chrome.exe",
            r"Microsoft\Edge\Application\msedge.exe",
            r"BraveSoftware\Brave-Browser\Application\brave.exe",
        )
        for base in program_files:
            if not base:
                continue
            for rel in rel_paths:
                cand = os.path.join(base, rel)
                if os.path.isfile(cand):
                    return cand
        for cmd in ("chrome", "msedge", "brave"):
            found = shutil.which(cmd)
            if found:
                return found
        return None

    for cmd in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "brave-browser"):
        found = shutil.which(cmd)
        if found:
            return found
    return None


def _open_app_window(url: str) -> subprocess.Popen | None:
    if _is_chromeos_crostini():
        garcon = shutil.which("garcon-url-handler")
        if garcon:
            try:
                subprocess.Popen([garcon, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return None
            except OSError:
                pass
        webbrowser.open(url)
        return None

    browser_bin = _find_chromium_app_browser()
    if browser_bin:
        try:
            return subprocess.Popen(
                [browser_bin, f"--app={url}", "--window-size=1320,880"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass

    webbrowser.open(url)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Algo Studio as an offline desktop app.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT") or "8788"), help="Preferred port")
    parser.add_argument("--no-browser", action="store_true", help="Start the offline server without opening a window")
    args = parser.parse_args()

    if _is_algo_studio_running(args.host, args.port):
        url = f"http://{args.host}:{args.port}"
        print(f"Algo Studio is already running at {url}", flush=True)
        if not args.no_browser:
            _open_app_window(url)
        return

    port = _pick_available_port(args.host, args.port)
    url = f"http://{args.host}:{port}"
    httpd = server._ReusableThreadingHTTPServer((args.host, port), server.AlgoStudioHandler)
    srv_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    srv_thread.start()

    print(f"Algo Studio offline workbench ready at {url}", flush=True)
    print("Tip: In Chrome or ChromeOS, click the Install icon in the address bar to pin Algo Studio as a standalone app.", flush=True)
    print("Press Ctrl+C in this window to stop the local server.", flush=True)

    app_proc = None
    if not args.no_browser:
        time.sleep(0.25)
        app_proc = _open_app_window(url)

    try:
        if app_proc is not None and platform.system().lower() != "darwin":
            # Keep running while the standalone app window stays open; if Chrome handed off to an existing process, stay alive until Ctrl+C.
            time.sleep(1.5)
            if app_proc.poll() is None:
                app_proc.wait()
            else:
                while srv_thread.is_alive():
                    time.sleep(0.5)
        else:
            while srv_thread.is_alive():
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping Algo Studio...", flush=True)
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
