#!/usr/bin/env python3
"""In-process browser execution shim for Algo Studio single-file HTML mode.

Runs inside Pyodide WebAssembly (or standard CPython 3 for local unit tests)
without spawning OS subprocesses or starting an HTTP server. Routes API calls
directly into server.AlgoStudioHandler._handle_post_route and syncs progress
back to the browser's localStorage.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from typing import Any

os.environ["ALGO_STUDIO_OFFLINE_TESTS"] = "1"

import curated_lists as cl
import server

_PATCHED = False
_ORIGINAL_SUBPROCESS_RUN = subprocess.run


class _AlgoTimeLimitExceeded(BaseException):
    """Raised by the line tracer when user code exceeds the browser timeout."""


def _inprocess_python_run(cmd: list[str], timeout: float | None = 4.0) -> subprocess.CompletedProcess[str]:
    script = cmd[2]
    max_sec = min(float(timeout or 4.0), 4.0)
    deadline = time.monotonic() + max_sec
    state = {"steps": 0}
    real_settrace = sys.settrace

    def _deadline_only_tracer(frame: Any, event: str, arg: Any) -> Any:
        state["steps"] += 1
        if (state["steps"] & 1023) == 0 and time.monotonic() > deadline:
            raise _AlgoTimeLimitExceeded()
        return _deadline_only_tracer

    def _make_wrapped_tracer(inner_fn: Any) -> Any:
        def _wrapped(frame: Any, event: str, arg: Any) -> Any:
            state["steps"] += 1
            if (state["steps"] & 511) == 0 and time.monotonic() > deadline:
                raise _AlgoTimeLimitExceeded()
            nxt = inner_fn(frame, event, arg)
            return _wrapped if nxt is not None else _deadline_only_tracer

        return _wrapped

    def _guarded_settrace(fn: Any) -> None:
        if fn is None:
            real_settrace(_deadline_only_tracer)
        else:
            real_settrace(_make_wrapped_tracer(fn))

    out_buf = io.StringIO()
    err_buf = io.StringIO()
    prev_stdout = sys.stdout
    prev_stderr = sys.stderr
    returncode = 0
    runner_ns: dict[str, Any] = {"__name__": "__main__"}

    try:
        sys.stdout = out_buf
        sys.stderr = err_buf
        sys.settrace = _guarded_settrace
        real_settrace(_deadline_only_tracer)
        compiled = compile(script, "<algo_runner>", "exec")
        exec(compiled, runner_ns)
    except SystemExit as exc:
        if exc.code is None:
            returncode = 0
        elif isinstance(exc.code, int):
            returncode = exc.code
        else:
            err_buf.write(str(exc.code) + "\n")
            returncode = 1
    except _AlgoTimeLimitExceeded:
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=max_sec)
    except Exception as exc:
        err_buf.write(f"{type(exc).__name__}: {exc}\n")
        returncode = 1
    finally:
        sys.settrace = real_settrace
        real_settrace(None)
        sys.stdout = prev_stdout
        sys.stderr = prev_stderr

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=returncode,
        stdout=out_buf.getvalue(),
        stderr=err_buf.getvalue(),
    )


def _patched_subprocess_run(
    cmd: Any,
    *args: Any,
    timeout: float | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    if isinstance(cmd, (list, tuple)) and len(cmd) >= 3 and str(cmd[1]) == "-c":
        exe = os.path.basename(str(cmd[0])).lower()
        if "python" in exe or str(cmd[0]) in (server.PYTHON_BIN, cl.PYTHON_BIN, sys.executable):
            return _inprocess_python_run([str(x) for x in cmd], timeout=timeout)
    return subprocess.CompletedProcess(
        args=cmd,
        returncode=1,
        stdout="",
        stderr="External process execution is disabled in single-file browser mode.",
    )


def _browser_run_typescript(func_name: str, code: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import js  # type: ignore[import-not-found]

        runner = getattr(js.window, "__algoRunTsTestCases", None)
        if runner is not None:
            raw_json = str(runner(func_name, code, json.dumps(test_cases)))
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                return parsed
    except Exception as exc:
        return {"ok": False, "error": f"Browser TypeScript runner error: {exc}"}
    return {
        "ok": False,
        "error": "TypeScript browser bridge is unavailable in this environment.",
    }


def _browser_run_go(func_name: str, code: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": False,
        "error": (
            "Go compilation requires a local Go toolchain. Python 3, TypeScript, and SQL 50 "
            "run directly in Chrome in this single-file app; use the local launcher from the "
            "repository when practising Go."
        ),
    }


def install_browser_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    subprocess.run = _patched_subprocess_run  # type: ignore[assignment]
    server._run_typescript = _browser_run_typescript
    server._run_go = _browser_run_go
    _PATCHED = True


class _CaptureHandler:
    """Minimal stand-in for AlgoStudioHandler that captures JSON responses in memory."""

    def __init__(self) -> None:
        self.status = 200
        self.response: dict[str, Any] = {"ok": False, "error": "No response produced"}

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        self.status = status
        self.response = payload


def dispatch_api(route: str, payload_json: str, progress_json: str = "") -> str:
    """Dispatch an Algo Studio POST API route in-process and return JSON string."""
    install_browser_patches()

    if progress_json:
        try:
            incoming_prog = json.loads(progress_json)
            if isinstance(incoming_prog, dict):
                base = server._default_progress()
                base.update(incoming_prog)
                server.save_progress(base)
        except Exception:
            pass

    try:
        body = json.loads(payload_json) if payload_json else {}
        if not isinstance(body, dict):
            body = {}
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Invalid JSON payload: {exc}"})

    handler = _CaptureHandler()
    try:
        server.AlgoStudioHandler._handle_post_route(handler, route, body)  # type: ignore[arg-type]
    except (ValueError, TypeError) as exc:
        handler.response = {"ok": False, "error": f"Invalid request: {exc}"}
    except Exception as exc:
        handler.response = {"ok": False, "error": f"Execution error: {exc}"}

    if isinstance(handler.response, dict):
        try:
            handler.response["_syncedProgress"] = server.load_progress(auto_advance=False)
        except Exception:
            pass

    return json.dumps(handler.response, ensure_ascii=False)
