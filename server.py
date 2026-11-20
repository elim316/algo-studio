#!/usr/bin/env python3
"""Offline-first local HTTP server for Algo Studio.

Runs completely offline using only the Python 3 standard library (zero pip or
npm dependencies required).
Features:
- Course selector covering the 120-Day SWE/FDE Plan, LeetCode Top 150,
  Grind 75, Grind 70 (Core), NeetCode 150 Skill-Tree, and SQL 50.
- Local multi-language execution (Python 3, SQLite 3, plus optional Node.js
  TypeScript and Go when installed).
- Line-level failure debugger, Python Tutor step-by-step memory tracer,
  20-check rubric scorer, Pressure Recall Drills, and Mock/OA simulators.
- Built-in offline AST coding mentor with optional GEMINI_API_KEY support.
"""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import curriculum_data as cd
import curated_lists as cl

PUBLIC_DIR = ROOT_DIR / "public"
DATA_DIR = Path(os.environ.get("ALGO_STUDIO_DATA_DIR") or (ROOT_DIR / "data"))
PROGRESS_PATH = DATA_DIR / "progress.json"


def _detect_node_bin() -> str:
    found = shutil.which("node")
    if found:
        return found
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.is_dir():
        candidates = sorted(nvm_root.glob("*/bin/node"), reverse=True)
        if candidates:
            return str(candidates[0])
    for candidate in ("/opt/homebrew/bin/node", "/usr/local/bin/node"):
        if os.path.isfile(candidate):
            return candidate
    return "node"


NODE_BIN = _detect_node_bin()
GO_BIN = shutil.which("go") or ("/usr/bin/go" if os.path.isfile("/usr/bin/go") else "go")
PYTHON_BIN = sys.executable or shutil.which("python3") or "python3"


_PROGRESS_LOCK = threading.RLock()

_LC_NUM_RE = re.compile(r"(\d+)")
_DAY_TO_LC_NUM: dict[int, int] = {}
_LC_NUM_TO_DAYS: dict[int, list[int]] = {}
for _p in cd.PROBLEMS:
    _lcid = str(_p.get("leetcodeId", ""))
    if _lcid.upper().startswith("LC"):
        _m = _LC_NUM_RE.search(_lcid)
        if _m:
            _lc_n = int(_m.group(1))
            _day_n = int(_p["day"])
            _DAY_TO_LC_NUM[_day_n] = _lc_n
            _LC_NUM_TO_DAYS.setdefault(_lc_n, []).append(_day_n)


def _day_to_lc_num(day: int) -> int | None:
    return _DAY_TO_LC_NUM.get(int(day))


def _lc_num_to_days(lc_num: int) -> list[int]:
    return list(_LC_NUM_TO_DAYS.get(int(lc_num), ()))


_ALLOWED_COURSES = frozenset({
    "schedule-120",
    "leetcode-150",
    "grind-75",
    "grind-70",
    "neetcode-150",
    "sql-50",
})


def _ordered_course_problem_ids(course_id: str) -> list[str]:
    sheet_id = "grind-75" if course_id == "grind-70" else course_id
    sheet = next((s for s in cl.SHEETS if s.get("id") == sheet_id), None)
    if not sheet:
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for grp in sheet.get("groups") or []:
        for pid in grp.get("problemIds") or []:
            if pid in seen:
                continue
            prob = cl.get_problem(pid)
            if not prob:
                continue
            if course_id == "grind-70":
                meta = (prob.get("sheetMeta") or {}).get("grind-75") or {}
                if meta.get("isCore70") is False:
                    continue
            seen.add(pid)
            ordered.append(pid)
    return ordered


def _next_unsolved_curated_id(
    course_id: str,
    solved_lc_ids: dict[str, Any],
    after_pid: str | None = None,
) -> str | None:
    ordered = _ordered_course_problem_ids(course_id)
    if not ordered:
        return after_pid
    start_idx = 0
    if after_pid and after_pid in ordered:
        start_idx = ordered.index(after_pid)
    n = len(ordered)
    for offset in range(1, n + 1):
        cand = ordered[(start_idx + offset) % n]
        prob = cl.get_problem(cand)
        lc_n = prob.get("lcNum") if prob else None
        if lc_n is None or str(lc_n) not in solved_lc_ids:
            return cand
    return ordered[(start_idx + 1) % n]


def _default_progress() -> dict[str, Any]:
    return {
        "currentDay": 1,
        "activeCourse": "schedule-120",
        "coursePositions": {},
        "solvedDays": {},
        "solvedLcIds": {},
        "bookmarks": [],
        "pressureScores": {},
        "interviewHistory": [],
        "oaHistory": [],
        "drafts": {},
        "notes": {},
        "chatHistory": {},
        "layoutSizes": {},
        "revealedHiddenDays": {},
        "lastActiveDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "streak": 1,
    }


def _next_unsolved_day(solved_days: dict[str, Any] | list[Any] | set[Any], after_day: int = 0) -> int:
    raw_items = solved_days.keys() if isinstance(solved_days, dict) else solved_days
    solved_set = {int(k) for k in raw_items if str(k).isdigit()}
    total_days = len(cd.PROBLEMS) or 120
    for offset in range(1, total_days + 1):
        candidate = ((after_day + offset - 1) % total_days) + 1
        if candidate not in solved_set:
            return candidate
    return min(total_days, max(1, after_day))


def load_progress(auto_advance: bool = True) -> dict[str, Any]:
    with _PROGRESS_LOCK:
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not PROGRESS_PATH.is_file():
            prog = _default_progress()
            save_progress(prog)
            return prog
        try:
            data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            base = _default_progress()
            base.update(data)
            if base.get("activeCourse") not in _ALLOWED_COURSES:
                base["activeCourse"] = "schedule-120"
            if not isinstance(base.get("coursePositions"), dict):
                base["coursePositions"] = {}
            solved = base.get("solvedDays") or {}
            solved_lc = base.setdefault("solvedLcIds", {})
            mirrored = False
            for d_str, info in solved.items():
                if str(d_str).isdigit():
                    lc_n = _day_to_lc_num(int(d_str))
                    if lc_n is not None and str(lc_n) not in solved_lc:
                        solved_lc[str(lc_n)] = info
                        mirrored = True
            cur = int(base.get("currentDay") or 1)
            if auto_advance and str(cur) in solved and len(solved) < len(cd.PROBLEMS):
                base["currentDay"] = _next_unsolved_day(solved, after_day=cur)
                mirrored = True
            if mirrored:
                save_progress(base)
            return base
        except Exception:
            return _default_progress()


def save_progress(prog: dict[str, Any]) -> None:
    with _PROGRESS_LOCK:
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(prog, indent=2, ensure_ascii=False) + "\n"
        tmp_path = PROGRESS_PATH.parent / f".{PROGRESS_PATH.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        tmp_path.write_text(payload, encoding="utf-8")
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass
        os.replace(tmp_path, PROGRESS_PATH)


def compute_tag_stats(solved_days: dict[str, Any]) -> list[dict[str, Any]]:
    solved_set = {int(k) for k in solved_days.keys() if str(k).isdigit()}
    counts: dict[str, dict[str, int]] = {}
    for t in cd.ALL_TAGS:
        counts[t["name"]] = {"total": 0, "solved": 0}
    for p in cd.PROBLEMS:
        d = p["day"]
        for tag_name in p["tags"]:
            if tag_name not in counts:
                counts[tag_name] = {"total": 0, "solved": 0}
            counts[tag_name]["total"] += 1
            if d in solved_set:
                counts[tag_name]["solved"] += 1
    out: list[dict[str, Any]] = []
    for t in cd.ALL_TAGS:
        c = counts.get(t["name"], {"total": 0, "solved": 0})
        out.append({
            **t,
            "curriculumTotal": c["total"],
            "curriculumSolved": c["solved"],
        })
    return out


def compute_spaced_repetition_insights(prog: dict[str, Any]) -> dict[str, Any]:
    """Compute Due-for-Review queue and Weak-Topic Radar from spaced-repetition ratings and failed attempts."""
    solved_days = prog.get("solvedDays") or {}
    failed_by_day = prog.get("failedAttemptsByDay") or {}
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    due_review_days: list[dict[str, Any]] = []
    weak_tag_scores: dict[str, dict[str, Any]] = {}

    def _bump_weak_tags(day_num: int, weight: int, reason: str) -> None:
        prob = cd.PROBLEMS_BY_DAY.get(day_num)
        if not prob:
            return
        for tag_name in prob.get("tags", [])[:3]:
            entry = weak_tag_scores.setdefault(tag_name, {"name": tag_name, "score": 0, "days": [], "reasons": []})
            entry["score"] += weight
            if day_num not in entry["days"]:
                entry["days"].append(day_num)
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)

    for d_str, info in solved_days.items():
        if not str(d_str).isdigit():
            continue
        d_int = int(d_str)
        prob = cd.PROBLEMS_BY_DAY.get(d_int)
        if not prob:
            continue
        rating = str(info.get("rating", "Good"))
        next_rev = str(info.get("nextReviewDate", today_str))
        is_due_date = next_rev <= today_str
        is_struggled = rating in ("Again", "Hard")
        if is_due_date or is_struggled:
            due_review_days.append({
                "day": d_int,
                "title": prob["title"],
                "leetcodeId": prob["leetcodeId"],
                "difficulty": prob["difficulty"],
                "rating": rating,
                "nextReviewDate": next_rev,
                "reason": "Rated " + rating if is_struggled else "Review date reached",
            })
        if rating == "Again":
            _bump_weak_tags(d_int, 3, f"Day {d_int} rated Again")
        elif rating == "Hard":
            _bump_weak_tags(d_int, 2, f"Day {d_int} rated Hard")

    for d_str, fail_cnt in failed_by_day.items():
        if str(d_str).isdigit() and int(fail_cnt) > 0:
            d_int = int(d_str)
            _bump_weak_tags(d_int, min(3, int(fail_cnt)), f"Day {d_str} ({fail_cnt} failed test runs)")
            if int(fail_cnt) >= 2 and d_str not in solved_days:
                prob = cd.PROBLEMS_BY_DAY.get(d_int)
                if prob:
                    due_review_days.append({
                        "day": d_int,
                        "title": prob["title"],
                        "leetcodeId": prob["leetcodeId"],
                        "difficulty": prob["difficulty"],
                        "rating": "Retry",
                        "nextReviewDate": today_str,
                        "reason": f"{fail_cnt} failed test runs",
                    })

    due_review_days.sort(key=lambda x: (0 if x["rating"] in ("Again", "Retry") else 1 if x["rating"] == "Hard" else 2, x["nextReviewDate"], x["day"]))
    raw_weak = sorted(weak_tag_scores.values(), key=lambda x: (-x["score"], x["name"]))[:8]
    weak_topics = [
        {"tag": w["name"], "name": w["name"], "weakScore": w["score"], "score": w["score"], "days": w["days"], "reasons": w["reasons"]}
        for w in raw_weak
    ]
    return {
        "dueCount": len(due_review_days),
        "dueReviewDays": due_review_days,
        "weakTopics": weak_topics,
    }


def _strip_typescript_types(ts_code: str) -> str:
    """Line-preserving TypeScript-to-JavaScript transformer so line numbers stay 1:1."""
    out_lines: list[str] = []
    for line in ts_code.splitlines():
        if re.match(r"^\s*type\s+\w+\s*=[^;]+;\s*$", line):
            out_lines.append("// " + line)
            continue
        s = line
        # Remove generic type arguments on Map, Set, Array: new Map<string, number>() -> new Map()
        s = re.sub(r"\b(Map|Set|Array)\s*<[^>;()]+>\s*\(", r"\1(", s)
        # Remove non-null assertions like .get(k)! or .pop()!
        s = re.sub(r"(\)|\w|\])\s*!(?=[.;,\)\]\s])", r"\1", s)
        # Remove variable type annotations: const x: Record<string, any> = ...
        s = re.sub(r"\b(const|let|var)\s+(\w+)\s*:\s*[^=;]+\s*=", r"\1 \2 =", s)
        # Remove function return type annotations: ): number[] { or ): void =>
        s = re.sub(r"\)\s*:\s*[A-Za-z0-9_<>\[\]\|\s]+(?=\s*(\{|=>))", ")", s)

        def clean_params(match: re.Match[str]) -> str:
            inner = match.group(1)
            if "?" in inner:
                return match.group(0)
            parts = []
            for p in inner.split(","):
                p_clean = re.sub(r":\s*[A-Za-z0-9_<>\[\]\|\s]+", "", p)
                parts.append(p_clean)
            return "(" + ", ".join(parts) + ")"

        s = re.sub(r"\(([^()?]*:\s*[A-Za-z0-9_<>\[\]\|]+[^()?]*)\)", clean_params, s)
        out_lines.append(s)
    return "\n".join(out_lines)


def _compute_expected_via_reference_python(prob: dict[str, Any], custom_args: list[Any]) -> Any:
    """Compute ground-truth expected output for a custom test case using the problem's reference Python solution."""
    ref_code = prob.get("solutionCode", {}).get("python", "")
    func_name = prob["funcName"]
    if not ref_code:
        return None
    try:
        ns: dict[str, Any] = {}
        exec(compile(ref_code, "<ref>", "exec"), ns)
        fn = ns.get(func_name)
        if callable(fn):
            import copy
            return fn(*copy.deepcopy(custom_args))
    except Exception:
        return None
    return None


def execute_user_code(
    day: int,
    language: str,
    code: str,
    custom_test_args: list[Any] | None = None,
) -> dict[str, Any]:
    """Execute user solution in Python, Go, or TypeScript with line-level debug tracing and optional custom test input."""
    prob = cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown problem day {day}"}

    func_name = prob["funcName"]
    test_cases = list(prob["testCases"])
    if custom_test_args is not None and isinstance(custom_test_args, list):
        expected_val = _compute_expected_via_reference_python(prob, custom_test_args)
        custom_tc = {
            "label": "Custom Input",
            "args": custom_test_args,
            "expected": expected_val,
        }
        test_cases = test_cases + [custom_tc]

    if language == "python":
        res = _run_python(func_name, code, test_cases)
    elif language == "typescript":
        res = _run_typescript(func_name, code, test_cases)
    elif language == "go":
        res = _run_go(func_name, code, test_cases)
    else:
        return {"ok": False, "error": f"Unsupported language: {language}"}

    if isinstance(res.get("results"), list):
        vis_passed = 0
        vis_total = 0
        hid_passed = 0
        hid_total = 0
        for idx, tc_res in enumerate(res["results"]):
            src_tc = test_cases[idx] if idx < len(test_cases) else {}
            is_hidden = bool(src_tc.get("hidden", False))
            tc_res["hidden"] = is_hidden
            tc_res["category"] = str(src_tc.get("category", ""))
            tc_res["edgeReason"] = str(src_tc.get("edgeReason", ""))
            if is_hidden:
                hid_total += 1
                if tc_res.get("passed"):
                    hid_passed += 1
            else:
                vis_total += 1
                if tc_res.get("passed"):
                    vis_passed += 1
        res["visiblePassed"] = vis_passed
        res["visibleTotal"] = vis_total
        res["hiddenPassed"] = hid_passed
        res["hiddenTotal"] = hid_total
    res["tracedCode"] = code
    res["tracedLanguage"] = language
    return res


def trace_optimal_solution(day: int, tc_idx: int = 0) -> dict[str, Any]:
    """Run the reference Python solution on one test case to produce real Python Tutor frames."""
    prob = cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown problem day {day}"}
    opt_code = prob.get("solutionCode", {}).get("python", "")
    if not opt_code:
        return {"ok": False, "error": f"No Python optimal solution found for Day {day}"}
    test_cases = prob.get("testCases", [])
    if not test_cases:
        return {"ok": False, "error": f"No test cases found for Day {day}"}
    safe_idx = max(0, min(len(test_cases) - 1, int(tc_idx)))
    tc = test_cases[safe_idx]
    res = _run_python(prob["funcName"], opt_code, [tc])
    if not res.get("ok"):
        return res
    first_res = (res.get("results") or [{}])[0]
    frames = first_res.get("frames") or res.get("executionFrames") or []
    return {
        "ok": True,
        "day": day,
        "tcIdx": safe_idx,
        "language": "python",
        "code": opt_code,
        "input": tc.get("args", []),
        "expected": tc.get("expected"),
        "frames": frames,
    }


def _build_partial_executable_python(code: str) -> tuple[str | None, dict[int, dict[str, str]]]:
    """Python Tutor-style partial AST recovery: replaces lines containing SyntaxErrors with runtime
    `_raise_syntax_error(line, src, msg)` calls at the same indentation so valid lines before the
    error execute step-by-step under `sys.settrace` right up until the offending syntax line."""
    orig_lines = code.splitlines()
    patched_lines = list(orig_lines)
    syntax_errors_by_line: dict[int, dict[str, str]] = {}

    for _ in range(12):
        candidate = "\n".join(patched_lines)
        try:
            ast.parse(candidate, filename="<user_code>")
            return candidate, syntax_errors_by_line
        except SyntaxError as syn_err:
            ln = syn_err.lineno or 1
            idx = max(0, min(len(patched_lines) - 1, ln - 1))
            if (idx + 1) in syntax_errors_by_line:
                # Already patched this line and still failing (e.g. unclosed multiline token or broken def header)
                return None, syntax_errors_by_line
            raw_orig = orig_lines[idx] if idx < len(orig_lines) else ""
            stripped_orig = raw_orig.strip()
            if stripped_orig.startswith("def "):
                return None, syntax_errors_by_line
            syntax_errors_by_line[idx + 1] = {
                "msg": syn_err.msg or "invalid syntax",
                "src": raw_orig,
            }
            indent_match = re.match(r"^(\s*)", raw_orig)
            indent = indent_match.group(1) if indent_match else ""

            # Check if the next non-empty line is indented deeper (meaning this line opens a suite)
            opens_suite = False
            for next_idx in range(idx + 1, len(orig_lines)):
                nxt = orig_lines[next_idx]
                if not nxt.strip() or nxt.strip().startswith("#"):
                    continue
                nxt_indent = len(re.match(r"^(\s*)", nxt).group(1))
                if nxt_indent > len(indent):
                    opens_suite = True
                break

            call_expr = f"_raise_syntax_error({idx + 1}, {json.dumps(stripped_orig)}, {json.dumps(syn_err.msg or 'invalid syntax')})"
            if opens_suite:
                if stripped_orig.startswith("elif "):
                    patched_lines[idx] = f"{indent}elif {call_expr}:"
                else:
                    patched_lines[idx] = f"{indent}if {call_expr}:"
            else:
                patched_lines[idx] = f"{indent}{call_expr}"

    return None, syntax_errors_by_line


def _run_python(func_name: str, code: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    # Pre-check syntax: if there is a SyntaxError inside the function body, recover a partial
    # executable AST so we can run and trace every valid step right up to the offending line!
    code_lines = code.splitlines()
    exec_code = code
    first_syn_err: tuple[int, str, str] | None = None
    try:
        ast.parse(code, filename="<user_code>")
    except SyntaxError as syn_err:
        lineno = syn_err.lineno or 1
        src_line = code_lines[lineno - 1] if 1 <= lineno <= len(code_lines) else ""
        first_syn_err = (lineno, syn_err.msg or "invalid syntax", src_line)
        recovered_code, _ = _build_partial_executable_python(code)
        if not recovered_code:
            return {
                "ok": False,
                "errorType": "SyntaxError",
                "error": f"SyntaxError on Line {lineno}: {syn_err.msg}",
                "errorLine": lineno,
                "errorSourceLine": src_line,
            }
        exec_code = recovered_code

    harness = (
        "import copy, inspect, io, json, sys, time, traceback\n\n"
        f"RAW_USER_CODE = {json.dumps(code)}\n"
        f"EXEC_USER_CODE = {json.dumps(exec_code)}\n"
        "USER_LINES = RAW_USER_CODE.splitlines()\n"
        "def _raise_syntax_error(ln, src, msg):\n"
        "    err = SyntaxError(f'{msg}')\n"
        "    err.lineno = ln\n"
        "    err.text = src\n"
        "    raise err\n\n"
        "ns = {'__name__': '__user__', '_raise_syntax_error': _raise_syntax_error}\n"
        "try:\n"
        "    exec(compile(EXEC_USER_CODE, '<user_code>', 'exec'), ns)\n"
        "except Exception as exc:\n"
        "    tb = traceback.extract_tb(exc.__traceback__)\n"
        "    u_frames = [f for f in tb if f.filename == '<user_code>']\n"
        "    _raw_ln = getattr(exc, 'lineno', None)\n"
        "    ln = _raw_ln if isinstance(_raw_ln, int) and not isinstance(_raw_ln, bool) else (u_frames[-1].lineno if u_frames else 1)\n"
        "    src = USER_LINES[ln - 1] if 1 <= ln <= len(USER_LINES) else ''\n"
        "    print('__ALGO_RESULT__' + json.dumps({\n"
        "        'ok': False,\n"
        "        'errorType': type(exc).__name__,\n"
        "        'error': f'{type(exc).__name__} on Line {ln}: {exc}',\n"
        "        'errorLine': ln,\n"
        "        'errorSourceLine': src,\n"
        "    }))\n"
        "    sys.exit(0)\n\n"
        "def _safe_repr(val):\n"
        "    try:\n"
        "        s = repr(val)\n"
        "        return s if len(s) <= 120 else s[:117] + '...'\n"
        "    except Exception:\n"
        "        return '<unprintable>'\n\n"
        "def _json_val(val, depth=0):\n"
        "    if depth > 2:\n"
        "        return _safe_repr(val)\n"
        "    if val is None or isinstance(val, (bool, int, float)):\n"
        "        return val\n"
        "    if isinstance(val, str):\n"
        "        return val if len(val) <= 80 else val[:77] + '...'\n"
        "    if isinstance(val, (list, tuple)):\n"
        "        return [_json_val(x, depth + 1) for x in list(val)[:16]]\n"
        "    if isinstance(val, set):\n"
        "        return [_json_val(x, depth + 1) for x in list(val)[:16]]\n"
        "    if isinstance(val, dict):\n"
        "        return {str(k): _json_val(v, depth + 1) for k, v in list(val.items())[:16]}\n"
        "    if hasattr(val, '__iter__') and type(val).__name__ == 'deque':\n"
        "        return [_json_val(x, depth + 1) for x in list(val)[:16]]\n"
        "    return _safe_repr(val)\n\n"
        "def _build_pt_snapshot(func_name, sig_params, args_copy, live_frame, event, ret_arg):\n"
        "    heap_objects = []\n"
        "    heap_by_id = {}\n"
        "    func_sig = f\"{func_name}({', '.join(sig_params)})\"\n"
        "    heap_objects.append({'id': 'heap_func', 'type': 'function', 'label': func_sig})\n"
        "    def _encode_val(v, depth=0):\n"
        "        if v is None or isinstance(v, (bool, int, float, str)):\n"
        "            val_out = _safe_repr(v) if isinstance(v, float) and (v != v or abs(v) == float('inf')) else v\n"
        "            return {'kind': 'primitive', 'type': type(v).__name__, 'value': val_out}\n"
        "        oid = id(v)\n"
        "        if oid not in heap_by_id:\n"
        "            hid = f'heap_{len(heap_objects)}'\n"
        "            heap_by_id[oid] = hid\n"
        "            if isinstance(v, dict):\n"
        "                entries = [[_json_val(k), _json_val(val)] for k, val in list(v.items())[:16]]\n"
        "                heap_objects.append({'id': hid, 'type': 'dict', 'entries': entries})\n"
        "            elif isinstance(v, (list, tuple, set)) or (hasattr(v, '__iter__') and type(v).__name__ == 'deque'):\n"
        "                tname = type(v).__name__\n"
        "                els = [_json_val(x) for x in list(v)[:16]]\n"
        "                heap_objects.append({'id': hid, 'type': tname, 'elements': els})\n"
        "            elif hasattr(v, '__dict__') and depth < 4:\n"
        "                placeholder = {'id': hid, 'type': 'instance', 'className': type(v).__name__, 'fields': []}\n"
        "                heap_objects.append(placeholder)\n"
        "                fields = []\n"
        "                for fk, fv in list(vars(v).items())[:10]:\n"
        "                    if not fk.startswith('_'):\n"
        "                        fields.append({'name': fk, **_encode_val(fv, depth + 1)})\n"
        "                placeholder['fields'] = fields\n"
        "            else:\n"
        "                heap_objects.append({'id': hid, 'type': type(v).__name__, 'label': _safe_repr(v)})\n"
        "        return {'kind': 'ref', 'refId': heap_by_id[oid], 'type': type(v).__name__}\n"
        "    global_vars = [{'name': func_name, 'kind': 'ref', 'refId': 'heap_func', 'type': 'function'}]\n"
        "    for p_idx, p_name in enumerate(sig_params):\n"
        "        if p_idx < len(args_copy):\n"
        "            enc = _encode_val(args_copy[p_idx])\n"
        "            global_vars.append({'name': p_name, **enc})\n"
        "    # Walk the call stack inside <user_code> to capture all recursive / helper frames!\n"
        "    raw_stack = []\n"
        "    cur_f = live_frame\n"
        "    while cur_f is not None and len(raw_stack) < 12:\n"
        "        if cur_f.f_code.co_filename == '<user_code>' and cur_f.f_code.co_name != '<module>':\n"
        "            raw_stack.append(cur_f)\n"
        "        cur_f = cur_f.f_back\n"
        "    raw_stack.reverse()\n"
        "    if not raw_stack:\n"
        "        raw_stack = [live_frame]\n"
        "    call_frames = []\n"
        "    for f_idx, cf in enumerate(raw_stack):\n"
        "        floc = cf.f_locals\n"
        "        f_keys = [p for p in sig_params if p in floc] + [k for k in floc.keys() if k not in sig_params]\n"
        "        f_vars = []\n"
        "        for k in f_keys:\n"
        "            v = floc[k]\n"
        "            if not k.startswith('_') and not callable(v):\n"
        "                f_vars.append({'name': k, **_encode_val(v)})\n"
        "        call_frames.append({\n"
        "            'funcName': cf.f_code.co_name,\n"
        "            'line': cf.f_lineno,\n"
        "            'depth': f_idx + 1,\n"
        "            'isHighlighted': f_idx == len(raw_stack) - 1,\n"
        "            'vars': f_vars,\n"
        "        })\n"
        "    frame_vars = call_frames[-1]['vars'] if call_frames else []\n"
        "    ret_enc = _encode_val(ret_arg) if event == 'return' else None\n"
        "    return {\n"
        "        'funcName': call_frames[-1]['funcName'] if call_frames else func_name,\n"
        "        'funcSignature': func_sig,\n"
        "        'globalVars': global_vars,\n"
        "        'frameVars': frame_vars,\n"
        "        'callFrames': call_frames,\n"
        "        'returnValueEncoded': ret_enc,\n"
        "        'heapObjects': heap_objects,\n"
        "    }\n\n"
        "def _run_suite():\n"
        f"    cases = json.loads({json.dumps(json.dumps(test_cases))})\n"
        f"    func_name_str = {json.dumps(func_name)}\n"
        "    fn = ns.get(func_name_str)\n"
        "    if not callable(fn):\n"
        "        print('__ALGO_RESULT__' + json.dumps({'ok': False, 'error': 'Function ' + func_name_str + ' not found in editor.'}))\n"
        "        return\n"
        "    try:\n"
        "        sig_params = list(inspect.signature(fn).parameters.keys())\n"
        "    except Exception:\n"
        "        sig_params = []\n"
        "    results = []\n"
        "    passed = 0\n"
        "    first_error_line = None\n"
        "    primary_frames = []\n"
        "    for idx, tc in enumerate(cases):\n"
        "        buf = io.StringIO()\n"
        "        old_stdout = sys.stdout\n"
        "        args_copy = copy.deepcopy(tc['args'])\n"
        "        trace_state = {'last_line': None, 'return_line': None, 'locals': {}, 'frames': []}\n"
        "        def _tracer(frame, event, arg):\n"
        "            if frame.f_code.co_filename == '<user_code>':\n"
        "                ln = frame.f_lineno\n"
        "                prev_ln = trace_state['last_line']\n"
        "                trace_state['last_line'] = ln\n"
        "                snap = {}\n"
        "                structured = {}\n"
        "                for k, v in frame.f_locals.items():\n"
        "                    if not k.startswith('_') and not callable(v):\n"
        "                        snap[k] = _safe_repr(v)\n"
        "                        structured[k] = _json_val(v)\n"
        "                trace_state['locals'] = snap\n"
        "                if event == 'return':\n"
        "                    trace_state['return_line'] = ln\n"
        "                if event in ('line', 'return') and len(trace_state['frames']) < 80:\n"
        "                    src_ln = USER_LINES[ln - 1].strip() if (1 <= ln <= len(USER_LINES)) else ''\n"
        "                    pt_snap = _build_pt_snapshot(func_name_str, sig_params, args_copy, frame, event, arg)\n"
        "                    trace_state['frames'].append({\n"
        "                        'step': len(trace_state['frames']) + 1,\n"
        "                        'line': ln,\n"
        "                        'prevLine': prev_ln,\n"
        "                        'source': src_ln,\n"
        "                        'event': event,\n"
        "                        'locals': structured,\n"
        "                        'returnValue': _json_val(arg) if event == 'return' else None,\n"
        "                        **pt_snap,\n"
        "                    })\n"
        "            return _tracer\n"
        "        t0 = time.perf_counter()\n"
        "        try:\n"
        "            sys.stdout = buf\n"
        "            sys.settrace(_tracer)\n"
        "            try:\n"
        "                actual = fn(*args_copy)\n"
        "            finally:\n"
        "                sys.settrace(None)\n"
        "                sys.stdout = old_stdout\n"
        "            dt_ms = round((time.perf_counter() - t0) * 1000, 2)\n"
        "            exp = tc['expected']\n"
        "            if isinstance(exp, list) and exp and isinstance(exp[0], float):\n"
        "                ok = isinstance(actual, list) and len(actual) == len(exp) and all(abs(a - b) < 1e-5 for a, b in zip(actual, exp))\n"
        "            else:\n"
        "                ok = (actual == exp)\n"
        "            if ok:\n"
        "                passed += 1\n"
        "            ret_ln = trace_state['return_line'] or trace_state['last_line']\n"
        "            ret_src = USER_LINES[ret_ln - 1].strip() if (ret_ln and 1 <= ret_ln <= len(USER_LINES)) else ''\n"
        "            if not ok and first_error_line is None and ret_ln:\n"
        "                first_error_line = ret_ln\n"
        "                primary_frames = trace_state['frames']\n"
        "            elif idx == 0 and not primary_frames:\n"
        "                primary_frames = trace_state['frames']\n"
        "            results.append({\n"
        "                'index': idx + 1,\n"
        "                'label': tc.get('label', ''),\n"
        "                'input': tc['args'],\n"
        "                'expected': exp,\n"
        "                'actual': actual,\n"
        "                'passed': ok,\n"
        "                'runtimeMs': dt_ms,\n"
        "                'stdout': buf.getvalue().strip(),\n"
        "                'suspectLine': ret_ln if not ok else None,\n"
        "                'suspectSource': ret_src if not ok else '',\n"
        "                'localsSnapshot': trace_state['locals'] if not ok else {},\n"
        "                'frames': trace_state['frames'],\n"
        "            })\n"
        "        except Exception as exc:\n"
        "            sys.settrace(None)\n"
        "            sys.stdout = old_stdout\n"
        "            dt_ms = round((time.perf_counter() - t0) * 1000, 2)\n"
        "            tb = traceback.extract_tb(exc.__traceback__)\n"
        "            u_frames = [f for f in tb if f.filename == '<user_code>']\n"
        "            _raw_ln = getattr(exc, 'lineno', None)\n"
        "            err_ln = _raw_ln if isinstance(_raw_ln, int) and not isinstance(_raw_ln, bool) else (u_frames[-1].lineno if u_frames else (trace_state['last_line'] or 1))\n"
        "            err_src = USER_LINES[err_ln - 1].strip() if (err_ln and 1 <= err_ln <= len(USER_LINES)) else ''\n"
        "            if trace_state['frames']:\n"
        "                trace_state['frames'][-1]['event'] = 'exception'\n"
        "                trace_state['frames'][-1]['error'] = f'{type(exc).__name__} on Line {err_ln}: {exc}'\n"
        "            if first_error_line is None:\n"
        "                first_error_line = err_ln\n"
        "                primary_frames = trace_state['frames']\n"
        "            results.append({\n"
        "                'index': idx + 1,\n"
        "                'label': tc.get('label', ''),\n"
        "                'input': tc['args'],\n"
        "                'expected': tc['expected'],\n"
        "                'actual': None,\n"
        "                'error': f'{type(exc).__name__} on Line {err_ln}: {exc}',\n"
        "                'errorLine': err_ln,\n"
        "                'suspectLine': err_ln,\n"
        "                'suspectSource': err_src,\n"
        "                'localsSnapshot': trace_state['locals'],\n"
        "                'stdout': buf.getvalue().strip(),\n"
        "                'passed': False,\n"
        "                'runtimeMs': dt_ms,\n"
        "                'frames': trace_state['frames'],\n"
        "            })\n"
        "    print('__ALGO_RESULT__' + json.dumps({\n"
        "        'ok': True,\n"
        "        'passed': passed,\n"
        "        'total': len(cases),\n"
        "        'allPassed': passed == len(cases),\n"
        "        'highlightLine': first_error_line,\n"
        "        'executionFrames': primary_frames,\n"
        "        'results': results,\n"
        "    }))\n"
        "if __name__ == '__main__':\n"
        "    _run_suite()\n"
    )
    res = _exec_subprocess([PYTHON_BIN, "-c", harness], timeout=4.5)
    if first_syn_err and res.get("ok"):
        syn_ln, syn_msg, syn_src = first_syn_err
        # If the syntax-error line was never reached or if it raised SyntaxError during execution,
        # ensure the test run reports not-allPassed and highlights the syntax error while preserving executionFrames!
        res["allPassed"] = False
        res["syntaxErrorPartialRun"] = True
        if not res.get("highlightLine"):
            res["highlightLine"] = syn_ln
        res["errorLine"] = syn_ln
        res["errorSourceLine"] = syn_src
        res["errorType"] = "SyntaxError"
        res["error"] = f"SyntaxError on Line {syn_ln}: {syn_msg}"
    return res


def _run_typescript(func_name: str, code: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    js_code = _strip_typescript_types(code)
    user_lines = code.splitlines()
    # Find return lines in user code for wrong-answer suspect line reporting
    return_lines = [i + 1 for i, ln in enumerate(user_lines) if re.search(r"\breturn\b", ln)]
    default_ret_line = return_lines[-1] if return_lines else len(user_lines)

    harness = (
        "const vm = require('vm');\n"
        f"const USER_CODE_RAW = {json.dumps(code)};\n"
        f"const JS_CODE = {json.dumps(js_code)};\n"
        "const USER_LINES = USER_CODE_RAW.split('\\n');\n"
        f"const DEFAULT_RET_LINE = {default_ret_line};\n"
        f"const cases = {json.dumps(test_cases)};\n"
        "let logs = [];\n"
        "const customConsole = {\n"
        "  log: (...args) => logs.push(args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')),\n"
        "  error: (...args) => logs.push(args.map(a => String(a)).join(' ')),\n"
        "  warn: (...args) => logs.push(args.map(a => String(a)).join(' ')),\n"
        "};\n"
        "const sandbox = { console: customConsole, Map, Set, Array, Int32Array, Float64Array, Math, Number, String, Boolean, Object, JSON, Infinity, NaN, parseInt, parseFloat, isNaN };\n"
        "vm.createContext(sandbox);\n"
        "function extractLine(err) {\n"
        "  const st = String(err && err.stack ? err.stack : err);\n"
        "  const m = st.match(/user_code\\.js:(\\d+)(?::(\\d+))?/);\n"
        "  return m ? Number(m[1]) : null;\n"
        "}\n"
        "try {\n"
        "  const script = new vm.Script(JS_CODE, { filename: 'user_code.js' });\n"
        "  script.runInContext(sandbox, { timeout: 2500 });\n"
        "} catch (err) {\n"
        "  const ln = extractLine(err) || 1;\n"
        "  const src = USER_LINES[ln - 1] ? USER_LINES[ln - 1].trim() : '';\n"
        "  console.log('__ALGO_RESULT__' + JSON.stringify({\n"
        "    ok: false,\n"
        "    error: `${err.name || 'Error'} on Line ${ln}: ${err.message || err}`,\n"
        "    errorLine: ln,\n"
        "    errorSourceLine: src,\n"
        "  }));\n"
        "  process.exit(0);\n"
        "}\n"
        f"const fn = sandbox[{json.dumps(func_name)}];\n"
        "if (typeof fn !== 'function') {\n"
        f"  console.log('__ALGO_RESULT__' + JSON.stringify({{ok: false, error: 'Function {func_name} not found'}}));\n"
        "  process.exit(0);\n"
        "}\n"
        "const results = [];\n"
        "let passed = 0;\n"
        "let firstErrorLine = null;\n"
        "for (let i = 0; i < cases.length; i++) {\n"
        "  const tc = cases[i];\n"
        "  logs = [];\n"
        "  const t0 = performance.now();\n"
        "  try {\n"
        "    const argsCopy = JSON.parse(JSON.stringify(tc.args));\n"
        "    const actual = fn(...argsCopy);\n"
        "    const dtMs = Math.round((performance.now() - t0) * 100) / 100;\n"
        "    const ok = JSON.stringify(actual) === JSON.stringify(tc.expected);\n"
        "    if (ok) passed++;\n"
        "    else if (firstErrorLine === null) firstErrorLine = DEFAULT_RET_LINE;\n"
        "    const src = !ok && USER_LINES[DEFAULT_RET_LINE - 1] ? USER_LINES[DEFAULT_RET_LINE - 1].trim() : '';\n"
        "    results.push({\n"
        "      index: i + 1,\n"
        "      label: tc.label || '',\n"
        "      input: tc.args,\n"
        "      expected: tc.expected,\n"
        "      actual: actual ?? null,\n"
        "      passed: ok,\n"
        "      runtimeMs: dtMs,\n"
        "      stdout: logs.join('\\n'),\n"
        "      suspectLine: !ok ? DEFAULT_RET_LINE : null,\n"
        "      suspectSource: src,\n"
        "    });\n"
        "  } catch (err) {\n"
        "    const dtMs = Math.round((performance.now() - t0) * 100) / 100;\n"
        "    const ln = extractLine(err) || DEFAULT_RET_LINE;\n"
        "    if (firstErrorLine === null) firstErrorLine = ln;\n"
        "    const src = USER_LINES[ln - 1] ? USER_LINES[ln - 1].trim() : '';\n"
        "    results.push({\n"
        "      index: i + 1,\n"
        "      label: tc.label || '',\n"
        "      input: tc.args,\n"
        "      expected: tc.expected,\n"
        "      actual: null,\n"
        "      error: `${err.name || 'Error'} on Line ${ln}: ${err.message || err}`,\n"
        "      errorLine: ln,\n"
        "      suspectLine: ln,\n"
        "      suspectSource: src,\n"
        "      stdout: logs.join('\\n'),\n"
        "      passed: false,\n"
        "      runtimeMs: dtMs,\n"
        "    });\n"
        "  }\n"
        "}\n"
        "console.log('__ALGO_RESULT__' + JSON.stringify({ok: true, passed, total: cases.length, allPassed: passed === cases.length, highlightLine: firstErrorLine, results}));\n"
    )
    return _exec_subprocess([NODE_BIN, "-e", harness], timeout=4.5)


def _go_literal(val: Any, go_type: str) -> str:
    go_type = go_type.strip()
    if go_type == "int":
        return str(int(val))
    if go_type == "float64":
        return repr(float(val))
    if go_type == "string":
        return json.dumps(str(val))
    if go_type == "bool":
        return "true" if val else "false"
    if go_type == "[][]any":
        rows = []
        for row in val:
            elems = [json.dumps(x) if isinstance(x, str) else repr(float(x)) for x in row]
            rows.append("[]any{" + ", ".join(elems) + "}")
        return "[][]any{" + ", ".join(rows) + "}"
    if go_type.startswith("[]"):
        inner = go_type[2:]
        return f"{go_type}{{" + ", ".join(_go_literal(x, inner) for x in val) + "}"
    return json.dumps(val)


def _run_go(func_name: str, code: str, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
    sig_match = re.search(rf"func\s+{re.escape(func_name)}\s*\(([^)]*)\)\s*([^{{\n]+)", code)
    if not sig_match:
        return {"ok": False, "error": f"Could not find `func {func_name}(...)` signature in Go code.", "errorLine": 1}
    params_raw = sig_match.group(1).strip()
    ret_type = sig_match.group(2).strip()

    param_types: list[str] = []
    if params_raw:
        parts = [p.strip() for p in params_raw.split(",")]
        for p in parts:
            tokens = p.split()
            if len(tokens) >= 2:
                param_types.append(" ".join(tokens[1:]))
            else:
                param_types.append("")
        for i in range(len(param_types) - 2, -1, -1):
            if not param_types[i]:
                param_types[i] = param_types[i + 1]

    user_lines = code.splitlines()
    return_lines = [i + 1 for i, ln in enumerate(user_lines) if re.search(r"\breturn\b", ln)]
    default_ret_line = return_lines[-1] if return_lines else len(user_lines)
    default_ret_src = user_lines[default_ret_line - 1].strip() if (1 <= default_ret_line <= len(user_lines)) else ""

    body_lines = []
    user_line_map: dict[int, int] = {}
    in_import_block = False
    needed_imports = {"encoding/json", "fmt", "time"}
    for orig_idx, line in enumerate(user_lines, start=1):
        stripped = line.strip()
        if stripped.startswith("package "):
            continue
        if stripped.startswith("import ("):
            in_import_block = True
            continue
        if in_import_block:
            if stripped == ")":
                in_import_block = False
            else:
                imp = stripped.strip('"')
                if imp:
                    needed_imports.add(imp)
            continue
        if stripped.startswith("import "):
            imp = stripped.replace("import", "").strip().strip('"')
            if imp:
                needed_imports.add(imp)
            continue
        body_lines.append(line)
        user_line_map[len(body_lines)] = orig_idx

    imports_list = sorted(needed_imports)
    header_line_count = 4 + len(imports_list)  # package + import ( + imports + ) + blank

    calls_code = []
    for idx, tc in enumerate(test_cases):
        arg_lits = [_go_literal(arg, param_types[j]) for j, arg in enumerate(tc["args"])]
        exp_lit = _go_literal(tc["expected"], ret_type)
        calls_code.append(
            f"\t{{\n"
            f"\t\tt0 := time.Now()\n"
            f"\t\tactual := {func_name}({', '.join(arg_lits)})\n"
            f"\t\tdtMs := float64(time.Since(t0).Microseconds()) / 1000.0\n"
            f"\t\texp := {exp_lit}\n"
            f"\t\tab, _ := json.Marshal(actual)\n"
            f"\t\teb, _ := json.Marshal(exp)\n"
            f"\t\tok := string(ab) == string(eb)\n"
            f"\t\tif ok {{ passed++ }}\n"
            f"\t\tsuspect := 0\n"
            f"\t\tsrc := \"\"\n"
            f"\t\tif !ok {{ suspect = {default_ret_line}; src = {json.dumps(default_ret_src)} }}\n"
            f"\t\tresults = append(results, map[string]any{{\n"
            f"\t\t\t\"index\": {idx + 1},\n"
            f"\t\t\t\"label\": {json.dumps(tc.get('label', ''))},\n"
            f"\t\t\t\"input\": json.RawMessage({json.dumps(json.dumps(tc['args']))}),\n"
            f"\t\t\t\"expected\": exp,\n"
            f"\t\t\t\"actual\": actual,\n"
            f"\t\t\t\"passed\": ok,\n"
            f"\t\t\t\"runtimeMs\": dtMs,\n"
            f"\t\t\t\"suspectLine\": suspect,\n"
            f"\t\t\t\"suspectSource\": src,\n"
            f"\t\t}})\n"
            f"\t}}"
        )

    imports_str = "\n".join(f'\t"{imp}"' for imp in imports_list)
    go_src = (
        f"package main\n\nimport (\n{imports_str}\n)\n\n"
        + "\n".join(body_lines)
        + "\n\nfunc main() {\n"
        "\tpassed := 0\n"
        "\tresults := []map[string]any{}\n"
        + "\n".join(calls_code)
        + f"\n\ttotal := {len(test_cases)}\n"
        "\tout, _ := json.Marshal(map[string]any{\n"
        "\t\t\"ok\": true,\n"
        "\t\t\"passed\": passed,\n"
        "\t\t\"total\": total,\n"
        "\t\t\"allPassed\": passed == total,\n"
        f"\t\t\"highlightLine\": {default_ret_line},\n"
        "\t\t\"results\": results,\n"
        "\t})\n"
        "\tfmt.Println(\"__ALGO_RESULT__\" + string(out))\n"
        "}\n"
    )
    with tempfile.TemporaryDirectory(prefix="algo_go_") as tmpd:
        go_file = Path(tmpd) / "main.go"
        go_file.write_text(go_src, encoding="utf-8")
        res = _exec_subprocess([GO_BIN, "run", str(go_file)], timeout=12.0)
        if not res.get("ok") and res.get("error"):
            m = re.search(r"main\.go:(\d+):", res["error"])
            if m:
                gen_ln = int(m.group(1))
                body_idx = gen_ln - header_line_count
                orig_ln = user_line_map.get(body_idx, max(1, min(len(user_lines), body_idx)))
                res["errorLine"] = orig_ln
                res["errorSourceLine"] = user_lines[orig_ln - 1].strip() if 1 <= orig_ln <= len(user_lines) else ""
                res["error"] = f"Compiler Error on Line {orig_ln}: " + res["error"].split(f"main.go:{gen_ln}:")[-1].strip()
        return res


def _exec_subprocess(cmd: list[str], timeout: float) -> dict[str, Any]:
    go_base = Path(tempfile.gettempdir()) / f"algo-studio-go-{os.getuid()}"
    go_cache = go_base / "build-cache"
    go_path = go_base / "gopath"
    try:
        go_cache.mkdir(parents=True, exist_ok=True)
        go_path.mkdir(parents=True, exist_ok=True)
        os.chmod(go_base, 0o700)
    except OSError:
        pass
    env = cl.safe_subprocess_env({
        "GOCACHE": str(go_cache),
        "GOPATH": str(go_path),
        "GO111MODULE": "off",
    })
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"Time Limit Exceeded ({timeout:.1f}s). Check for infinite `while` loops or pointer updates that never advance.",
        }
    except Exception as exc:
        return {"ok": False, "error": f"Execution error: {exc}"}

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    marker = "__ALGO_RESULT__"
    if marker in stdout:
        user_stdout, payload_raw = stdout.split(marker, 1)
        try:
            payload = json.loads(payload_raw.strip().splitlines()[0])
            if user_stdout.strip() and payload.get("results"):
                # Attach global stdout (such as Go fmt.Println) to test results if per-test stdout is empty
                for r in payload["results"]:
                    if not r.get("stdout"):
                        r["stdout"] = user_stdout.strip()
            payload["stdout"] = user_stdout.strip()
            payload["stderr"] = stderr.strip()
            return payload
        except Exception as exc:
            return {"ok": False, "error": f"Failed to parse runner output: {exc}", "stdout": stdout, "stderr": stderr}

    err_msg = (stderr.strip() or stdout.strip() or f"Process exited with code {proc.returncode}")
    return {"ok": False, "error": err_msg, "stdout": stdout.strip(), "stderr": stderr.strip()}


def _sanitise_mentor_reply(text: str) -> str:
    """Enforce British English, zero bold markers (**), and zero em/en dashes or middle dots."""
    if not text:
        return ""
    cleaned = text.replace("**", "").replace("__", "")
    cleaned = cleaned.replace("\u2014", ", ").replace("\u2013", " to ").replace("\u00b7", " | ")
    cleaned = re.sub(r" -- ", ", ", cleaned)
    for pattern, repl in (
        (r"\bvisualize\b", "visualise"),
        (r"\bVisualize\b", "Visualise"),
        (r"\bvisualizer\b", "visualiser"),
        (r"\bVisualizer\b", "Visualiser"),
        (r"\boptimize\b", "optimise"),
        (r"\boptimized\b", "optimised"),
        (r"\boptimizing\b", "optimising"),
        (r"\banalyze\b", "analyse"),
        (r"\banalyzing\b", "analysing"),
        (r"\bbehavior\b", "behaviour"),
        (r"\bcolor\b", "colour"),
    ):
        cleaned = re.sub(pattern, repl, cleaned)
    return cleaned.strip()


def _summarize_cross_session_memory(active_day: int) -> str:
    """Build a compact cross-session memory summary of solved problems and saved code drafts across days."""
    try:
        prog = load_progress()
        solved = prog.get("solvedDays") or {}
        drafts = prog.get("drafts") or {}
        solved_labels = []
        for d_str in sorted(solved.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
            p = cd.PROBLEMS_BY_DAY.get(int(d_str)) if str(d_str).isdigit() else None
            if p:
                solved_labels.append(f"Day {d_str} ({p['title']})")
        other_drafts = []
        for k, v in list(drafts.items())[-6:]:
            if not v or not str(v).strip():
                continue
            parts = str(k).split(":")
            d_num = int(parts[0]) if parts and parts[0].isdigit() else 0
            if d_num and d_num != active_day:
                p = cd.PROBLEMS_BY_DAY.get(d_num)
                title = p["title"] if p else f"Day {d_num}"
                snippet = " | ".join(ln.strip() for ln in str(v).splitlines() if ln.strip())[:140]
                other_drafts.append(f"Day {d_num} ({title}, {parts[-1]}): {snippet}")
        lines = [
            f"Completed problems ({len(solved_labels)}/120): {', '.join(solved_labels[:10]) if solved_labels else 'None yet'}",
        ]
        if other_drafts:
            lines.append("Recent saved code drafts from other days: " + " ; ".join(other_drafts[:3]))
        return "\n".join(lines)
    except Exception:
        return "Completed problems: tracked in persistent workspace memory."


def _call_gemini_coach(
    prob: dict[str, Any],
    language: str,
    code: str,
    user_message: str,
    run_res: dict[str, Any],
    analysis: dict[str, Any],
    history: list[dict[str, Any]],
    model_mode: str,
) -> str | None:
    """Optionally call the public Gemini API when GEMINI_API_KEY is configured; offline by default."""
    if os.environ.get("ALGO_STUDIO_OFFLINE_TESTS") == "1":
        return None
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    numbered_code = "\n".join(f"{idx + 1}: {ln}" for idx, ln in enumerate(code.splitlines()))
    err_info = ""
    if run_res.get("error"):
        err_info = (
            f"Error on Line {run_res.get('errorLine')}: {run_res.get('error')}\n"
            f"Offending source line: {run_res.get('errorSourceLine', '')}"
        )
    else:
        for tc in run_res.get("results", []):
            if not tc.get("passed"):
                hidden_tag = " [Hidden Edge Case]" if tc.get("hidden") else ""
                err_info = (
                    f"Failing Test {tc.get('index')}{hidden_tag} ({tc.get('label', '')}): "
                    f"input={tc.get('input')}, expected={tc.get('expected')}, actual={tc.get('actual') or tc.get('error')}, "
                    f"line={tc.get('suspectLine')}, locals={tc.get('localsSnapshot')}"
                )
                break

    cross_memory = _summarize_cross_session_memory(int(prob["day"]))
    sys_prompt = (
        "You are a warm, sharp, conversational coding mentor inside Algo Studio coaching a candidate "
        "for Software Engineer (SWE) and Forward Deployed Engineer (FDE) technical interviews.\n"
        "Strict Mentoring Rules:\n"
        "- Directly answer the user's exact question first in natural British English (visualise, colour, analyse, optimise, behaviour).\n"
        "- Never ignore the user's question to complain about an unfinished line at the bottom of their editor. Answer what they asked first, referencing their actual variable names and lines in the editor.\n"
        "- Never use bold markdown (**), em dashes, en dashes, middle dots, or robotic headers. Wrap inline code and variable names in single backticks `...`.\n"
        "- Keep the reply concise (2 to 4 short paragraphs or bullet points) and end with a helpful next step or Socratic question unless they ask for the full solution.\n\n"
        f"Active Problem: {prob.get('leetcodeId', '')} ({prob.get('title', '')})\n"
        f"Tags: {', '.join(prob.get('tags', []))}\n"
        f"Optimal Mental Pivot: {prob['mentalModel']['optimalPivot']}\n"
        f"Target Complexity: {prob['complexity']['optimalTime']} time, {prob['complexity']['optimalSpace']} space\n"
        f"Cross-Session Coding Memory:\n{cross_memory}\n\n"
        f"User's Current {language} Code (with line numbers):\n{numbered_code}\n\n"
        f"Execution Status: passed={run_res.get('passed', 0)}/{run_res.get('total', 5)}, allPassed={run_res.get('allPassed')}\n"
        f"Diagnostic / Error Details: {err_info or 'None'}"
    )

    import urllib.request

    model_id = "gemini-2.5-pro" if model_mode == "pro" else "gemini-2.5-flash"
    contents: list[dict[str, Any]] = []
    for h in history[-6:]:
        role = "user" if h.get("role") == "user" else "model"
        text = str(h.get("text", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": sys_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.45, "maxOutputTokens": 420},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            out_text = "".join(p.get("text", "") for p in parts).strip()
            if out_text:
                return _sanitise_mentor_reply(out_text)
    except Exception:
        return None
    return None


def _diagnose_specific_line_issue(language: str, err_ln: int | None, err_src: str, err_msg: str, code: str) -> str:
    """Inspect the exact tokens on the offending line so syntax & runtime explanations feel human and specific."""
    s = err_src.strip()
    # 1. Curly braces used for indexing: e.g. seen{complement} or nums{i}
    curly_idx = re.search(r"\b([A-Za-z_]\w*)\s*\{([^}]*)\}", s)
    if curly_idx:
        var_name, inner_expr = curly_idx.group(1), curly_idx.group(2).strip()
        fixed_expr = f"{var_name}[{inner_expr}]" if inner_expr else f"{var_name}[key]"
        fixed_line = s[:curly_idx.start()] + fixed_expr + s[curly_idx.end():]
        return (
            f"Looking at Line {err_ln} (`{s}`), the syntax issue is `{curly_idx.group(0)}`. "
            f"In Python, curly braces `{{}}` only create a new dictionary or set literal (`seen = {{}}`), "
            f"whereas looking up a key inside `{var_name}` requires square brackets: `{fixed_expr}`.\n\n"
            f"Try changing Line {err_ln} to:\n`{fixed_line}`\n\n"
            f"Notice in the Animator below that your loop already ran cleanly right up to Line {err_ln} and found the matching complement in `{var_name}`!"
        )

    # 2. Single `=` inside an `if` or `while` condition: e.g. `if complement =` or `if a = b:`
    if re.match(r"^(if|elif|while)\b", s) and re.search(r"(?<![=!<>])=(?!=)", s):
        return (
            f"On Line {err_ln} (`{s}`), there is a single equals sign `=` inside your condition. "
            f"In {language.capitalize()}, a single `=` is for variable assignment, while `==` checks equality "
            f"(or `if complement in seen:` checks whether a key exists in your hash map).\n\n"
            + (
                f"Also make sure the condition ends with a colon `:`, for example:\n`if complement in seen:`"
                if language == "python" and not s.endswith(":")
                else f"Replace `=` with `==` or an `in` check on Line {err_ln} and re-run."
            )
        )

    # 3. Missing colon at end of Python block header
    if language == "python" and re.match(r"^(if|elif|else|for|while|def)\b", s) and not s.endswith(":"):
        return (
            f"On Line {err_ln} (`{s}`), Python expects a colon `:` at the end of every `{s.split()[0]}` header "
            f"before the indented block.\n\nTry changing Line {err_ln} to:\n`{s}:`"
        )

    # 4. Unbalanced brackets / parentheses
    if s.count("(") != s.count(")") or s.count("[") != s.count("]") or s.count("{") != s.count("}"):
        return (
            f"Line {err_ln} (`{s}`) has mismatched brackets or parentheses (`(` vs `)`, `[` vs `]`, or `{{` vs `}}`). "
            f"Check that every opening bracket on Line {err_ln} has a matching closing bracket of the same type."
        )

    # 5. Shadowing iterable variable in `for i, nums in enumerate(nums):`
    shadow_m = re.search(r"for\s+\w+\s*,\s*(\w+)\s+in\s+enumerate\(\1\)", code)
    if shadow_m:
        arr_var = shadow_m.group(1)
        return (
            f"On Line {err_ln} (`{s}`), Python reported `{err_msg}`. Also watch out for a subtle bug in your loop header: "
            f"`for i, {arr_var} in enumerate({arr_var}):` overwrites the list `{arr_var}` with the current element on the first iteration! "
            f"Use a singular variable name like `for i, num in enumerate({arr_var}):` so `{arr_var}` stays intact."
        )

    return (
        f"Your code ran step-by-step up to Line {err_ln} (`{s}`) before stopping with `{err_msg}`. "
        f"Check the syntax and variable names on Line {err_ln}, fix that expression, and click `Run Tests` to continue."
    )


def _answer_specific_coding_question(
    prob: dict[str, Any],
    language: str,
    code: str,
    user_message: str,
) -> tuple[str | None, int | None]:
    """Answer concrete coding/implementation questions directly using the user's live variable names and lines."""
    q = user_message.lower().strip()
    code_lines = code.splitlines()

    # Detect user's dictionary / map variable name (default 'seen' or 'counts')
    dict_match = re.search(r"\b([A-Za-z_]\w*)\s*=\s*(?:\{\}|dict\s*\(\))", code)
    dict_var = dict_match.group(1) if dict_match else "seen"

    # Detect user's first loop variable and iterable: e.g. `for i in s:`
    loop_match = re.search(r"for\s+([A-Za-z_]\w*)\s+in\s+([A-Za-z_]\w*)\s*:", code)
    loop_var = loop_match.group(1) if loop_match else "ch"
    iter_var = loop_match.group(2) if loop_match else "s"

    # Check if the user accidentally inverted dictionary indexing (e.g. `i["s"] = seen`)
    inverted_ln: int | None = None
    inverted_src = ""
    for idx, raw_ln in enumerate(code_lines, start=1):
        stripped_ln = raw_ln.strip()
        if re.search(rf"\b{re.escape(loop_var)}\s*\[.*\]\s*=\s*{re.escape(dict_var)}\b", stripped_ln):
            inverted_ln = idx
            inverted_src = stripped_ln
            break

    # 1. Counting / adding frequency / dictionary increments
    if any(
        k in q
        for k in (
            "frequency",
            "count",
            "add the",
            "increment",
            "letters i've seen",
            "letters ive seen",
            "characters i've seen",
            "how do i add",
            "how to add",
            "store in dict",
            "update dict",
            "in seen",
        )
    ):
        parts: list[str] = []
        if inverted_ln:
            parts.append(
                f"In your loop `for {loop_var} in {iter_var}:`, `{dict_var}` is your dictionary and `{loop_var}` is the current letter. "
                f"On Line {inverted_ln} (`{inverted_src}`), the indexing is flipped around: `{dict_var}[{loop_var}]` looks up the count for letter `{loop_var}` inside `{dict_var}`."
            )
        else:
            parts.append(
                f"Inside your loop `for {loop_var} in {iter_var}:`, use the letter `{loop_var}` as the key inside `{dict_var}` and store its integer count as the value."
            )

        if language == "python":
            parts.append(
                f"With your `if / else` structure, increment the count by `1` when `{loop_var}` is already in `{dict_var}`, and initialise it to `1` in the `else` branch:\n"
                f"`if {loop_var} in {dict_var}:`\n"
                f"`    {dict_var}[{loop_var}] += 1`\n"
                f"`else:`\n"
                f"`    {dict_var}[{loop_var}] = 1`\n\n"
                f"Or as a clean one-liner using `.get()`:\n"
                f"`{dict_var}[{loop_var}] = {dict_var}.get({loop_var}, 0) + 1`"
            )
            if "for j in t" in code or "anagram" in prob["title"].lower():
                parts.append(
                    f"Then in your second loop `for j in t:`, check `if j not in {dict_var} or {dict_var}[j] == 0: return False`, "
                    f"subtract `1` via `{dict_var}[j] -= 1`, and `return len(s) == len(t)` at the end."
                )
        elif language == "go":
            parts.append(
                f"In Go, missing map keys default to `0`, so you can increment the frequency in one line:\n"
                f"`{dict_var}[{loop_var}]++`"
            )
        else:
            parts.append(
                f"In TypeScript/JavaScript, read the current count with `?? 0` and add `1`:\n"
                f"`{dict_var}.set({loop_var}, ({dict_var}.get({loop_var}) ?? 0) + 1);`"
            )
        return "\n\n".join(parts), inverted_ln

    # 2. Decrementing / checking second string or complement
    if any(k in q for k in ("decrement", "subtract", "second loop", "for j in", "compare", "match")):
        return (
            f"Once `{dict_var}` holds the frequency of every character from `{iter_var}`, loop over the second input and decrement each character's count:\n"
            f"- If the character is missing (`if j not in {dict_var} or {dict_var}[j] == 0:`), return `False` immediately.\n"
            f"- Otherwise subtract one: `{dict_var}[j] -= 1`.\n"
            f"- If you also check `if len(s) != len(t): return False` at the very top, surviving the second loop guarantees every count returned to `0`, so you can `return True`.",
            inverted_ln,
        )

    # 3. General "how do I" / "can I" / "what should I" implementation questions
    if q.startswith(("how ", "can i", "should i", "what should", "where do", "do i ", "is there")) or (
        "?" in q and not any(w in q for w in ("syntax", "error", "crash", "fail", "wrong", "issue", "bug", "contrast", "complex", "visual", "animat", "explain", "propose", "hint", "nudge"))
    ):
        return (
            f"To implement that step for {prob['title']}:\n"
            f"- Core invariant: {prob['mentalModel']['optimalPivot']}\n"
            f"- In your `{language}` code: {prob['walkthrough']}\n"
            + (
                f"- Also note on Line {inverted_ln} (`{inverted_src}`): update `{dict_var}[{loop_var}] = {dict_var}.get({loop_var}, 0) + 1` so `{dict_var}` maps each character to its count."
                if inverted_ln
                else "- Try updating your loop body with that step and click `Run Tests` to see the live variable trace."
            ),
            inverted_ln,
        )

    return None, None


def diagnose_in_chat(
    day: int,
    language: str,
    code: str,
    user_message: str,
    model_mode: str = "flash",
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Right-hand AI Co-Pilot that acts like a conversational Gemini mentor with live AST & trace awareness."""
    prob = cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown problem day {day}"}

    prog = load_progress()
    if history is not None:
        hist = list(history)
    else:
        hist = prog.setdefault("chatHistory", {}).setdefault(str(day), [])

    analysis = analyse_user_code(day, language, code)
    run_res = analysis.get("runResult", {})
    mm = prob["mentalModel"]
    sig = analysis.get("structuralSignals", {})
    depth = sig.get("maxLoopDepth", 0)
    uses_hash = sig.get("usesHash", False)
    q_lower = user_message.lower().strip()

    model_labels = {
        "flash": "Local AST Mentor (Flash)",
        "pro": "5-Axis Rubric Coach (Pro)",
    }
    model_used_label = model_labels.get(model_mode, model_labels["flash"])

    # Identify the first failing test case and its line / variable state
    failing_tc = None
    for tc in run_res.get("results", []):
        if not tc.get("passed"):
            failing_tc = tc
            break

    asks_about_syntax_or_error = any(
        k in q_lower
        for k in (
            "syntax",
            "error",
            "crash",
            "exception",
            "traceback",
            "colon",
            "bracket",
            "indent",
            "what's the issue",
            "whats the issue",
            "what is the issue",
            "what's wrong",
            "whats wrong",
            "what is wrong",
            "why is it failing",
            "why did it fail",
            "why is my test",
            "why did my test",
            "diagnose",
            "bug",
        )
    )

    specific_q_reply, specific_q_line = _answer_specific_coding_question(
        prob=prob,
        language=language,
        code=code,
        user_message=user_message,
    )

    highlight_line = (
        (run_res.get("errorLine") if asks_about_syntax_or_error or not run_res.get("syntaxErrorPartialRun") else None)
        or specific_q_line
        or (failing_tc.get("suspectLine") if failing_tc else None)
    )
    exec_frames = run_res.get("executionFrames") or []
    visual_widget: dict[str, Any] = {
        "type": "execution_animator",
        "title": f"Live Step-by-Step Visual Trace ({len(exec_frames)} frames)" if exec_frames else "Interactive Dry-Run Visualiser",
        "mode": "user" if exec_frames else "optimal",
        "loopDepth": depth,
        "usesHash": uses_hash,
        "bruteTime": prob["complexity"]["bruteTime"],
        "optimalTime": prob["complexity"]["optimalTime"],
        "optimalSpace": prob["complexity"]["optimalSpace"],
    }

    if any(k in q_lower for k in ("contrast", "complex", "big o", "time", "space", "fast", "slow", "brute")):
        visual_widget = {
            "type": "complexity_contrast",
            "title": "Brute-Force vs Optimal Operations Visualiser",
            "loopDepth": depth,
            "usesHash": uses_hash,
            "bruteTime": prob["complexity"]["bruteTime"],
            "bruteSpace": prob["complexity"]["bruteSpace"],
            "optimalTime": prob["complexity"]["optimalTime"],
            "optimalSpace": prob["complexity"]["optimalSpace"],
        }
    elif any(k in q_lower for k in ("propose", "mental", "think", "approach", "start", "stuck", "hint", "nudge")):
        visual_widget = {
            "type": "invariant_diagram",
            "title": "Visual Mental Pivot: Trap vs Invariant",
            "trap": mm["instinctiveTrap"],
            "pivot": mm["optimalPivot"],
            "bruteTime": prob["complexity"]["bruteTime"],
            "optimalTime": prob["complexity"]["optimalTime"],
        }

    # 1. Try optional Gemini API (if GEMINI_API_KEY is configured and online); otherwise use built-in offline mentor
    gemini_reply = _call_gemini_coach(
        prob=prob,
        language=language,
        code=code,
        user_message=user_message,
        run_res=run_res,
        analysis=analysis,
        history=hist,
        model_mode=model_mode,
    )

    reply_parts: list[str] = []
    if gemini_reply:
        reply_parts.append(gemini_reply)
    else:
        # 2. Conversational Socratic & Line-Aware Mentor (offline / sandbox fallback)
        has_syntax_or_crash = (not run_res.get("ok")) or bool(run_res.get("syntaxErrorPartialRun")) or bool(run_res.get("errorLine"))
        err_ln = run_res.get("errorLine") or (failing_tc.get("errorLine") if failing_tc else None)
        err_src = run_res.get("errorSourceLine") or (failing_tc.get("suspectSource") if failing_tc else "") or ""
        err_msg = run_res.get("error") or (failing_tc.get("error") if failing_tc else "") or "Syntax / Runtime Error"

        # Count how many assistant turns already exist in this problem's conversation so we vary our angle
        assistant_turns = [m.get("text", "") for m in hist if m.get("role") == "assistant"]
        turn_idx = len(assistant_turns)

        if specific_q_reply and not asks_about_syntax_or_error:
            reply_parts.append(specific_q_reply)

        elif has_syntax_or_crash and asks_about_syntax_or_error:
            highlight_line = err_ln
            specific_diag = _diagnose_specific_line_issue(language, err_ln, err_src, err_msg, code)
            if assistant_turns and specific_diag in assistant_turns[-1]:
                # User asked a follow-up on the same error — give the concrete corrected snippet and explain the trace!
                last_locals = (exec_frames[-1].get("locals") if exec_frames else None) or (failing_tc.get("localsSnapshot") if failing_tc else {})
                locals_summary = ", ".join(f"{k}={v}" for k, v in list(last_locals.items())[:5]) if last_locals else "initial state"
                reply_parts.append(
                    f"Let's walk through what happened right before Line {err_ln}:\n"
                    f"- Your code executed `{len(exec_frames)}` steps cleanly and reached Line {err_ln} with `{locals_summary}`.\n"
                    f"- Your algorithm logic (storing seen values and checking `complement = target - num`) is already spot on! "
                    f"Only the bracket syntax on Line {err_ln} (`{err_src.strip()}`) is blocking execution.\n"
                    f"- Replace `{err_src.strip()}` with square-bracket indexing (e.g. `return [seen[complement], i]`) and click `Run Tests`."
                )
            else:
                reply_parts.append(specific_diag)

        elif any(k in q_lower for k in ("visual", "animat", "draw", "diagram", "step-by-step", "trace")):
            if exec_frames:
                reply_parts.append(
                    f"I have traced `{len(exec_frames)}` live execution steps from your `{language}` code on Test Case 1.\n"
                    f"- Notice how the Animator below steps through each line up to Line {exec_frames[-1].get('line')} "
                    f"while updating your local variables (`{', '.join(list((exec_frames[-1].get('locals') or {}).keys())[:5])}`).\n"
                    f"- Use the `Play`, `Prev`, and `Next` controls under the console to scrub through each iteration."
                )
            else:
                reply_parts.append(
                    f"I have loaded the `{len(prob.get('traceSteps', []))}`-step visual invariant trace for `{prob['title']}` in the Animator.\n"
                    f"- Watch how `{prob['tags'][0]}` updates memory in a single pass without redundant inner-loop scans."
                )

        elif any(k in q_lower for k in ("contrast", "complex", "big o", "time", "space", "fast", "slow", "brute")):
            is_suboptimal_nested = depth >= 2 and "O(N)" in prob["complexity"]["optimalTime"] and not sig.get("usesStackQueue")
            reply_parts.append(
                f"Comparing Brute-Force (`{prob['complexity']['bruteTime']}`) vs Optimal (`{prob['complexity']['optimalTime']}`):\n"
                f"- Your current code has loop nesting depth `{depth}` and hash/set usage `{uses_hash}`.\n"
                + (
                    f"- Right now your outer and inner loops test pairs in `{prob['complexity']['bruteTime']}` time. "
                    f"By recording seen values in a hash map (`seen[x] = i`), each element only needs one `O(1)` lookup (`target - x`), "
                    f"bringing total runtime down to `{prob['complexity']['optimalTime']}`.\n"
                    if is_suboptimal_nested
                    else f"- Your single-pass structure avoids the `{prob['complexity']['bruteTime']}` nested scan and targets `{prob['complexity']['optimalTime']}` time with `{prob['complexity']['optimalSpace']}` space.\n"
                )
                + f"- Why optimal holds: {prob['complexity']['derivation']}"
            )

        elif any(k in q_lower for k in ("explain", "hash", "optimal", "walkthrough", "how to solve", "solution")):
            reply_parts.append(
                f"Here is how the optimal `{prob['tags'][0]}` approach works for {prob['title']}:\n"
                f"- Core Invariant: {mm['optimalPivot']}\n"
                f"- Step-by-Step Walkthrough: {prob['walkthrough']}\n"
                f"- Want to try coding this invariant yourself first, or would you like me to check a specific line of your implementation?"
            )

        elif any(k in q_lower for k in ("propose", "mental", "think", "approach", "start", "stuck", "hint", "nudge")):
            hints = prob.get("hints", [])
            hint_idx = min(len(hints) - 1, turn_idx % max(1, len(hints))) if hints else 0
            selected_hint = hints[hint_idx] if hints else mm["optimalPivot"]
            is_suboptimal_pass = bool(run_res.get("allPassed")) and depth >= 2 and "O(N)" in prob["complexity"]["optimalTime"]
            if is_suboptimal_pass:
                reply_parts.append(
                    f"Your nested loop baseline passes all `{run_res.get('total', 3)}` test cases! To optimise it from `{prob['complexity']['bruteTime']}` to `{prob['complexity']['optimalTime']}`:\n"
                    f"- Ask yourself: what is your inner loop searching for on each iteration?\n"
                    f"- Instead of scanning forward with a second pointer, store each visited value in a dictionary `seen = {{}}` so you can check for the complement in `O(1)` time."
                )
            else:
                reply_parts.append(
                    f"Here is a Socratic nudge for {prob['title']} (Hint Tier {hint_idx + 1}):\n"
                    f"- {selected_hint}\n"
                    f"- Mental pivot to keep in mind: {mm['optimalPivot']}\n"
                    f"- What data structure lets you maintain that invariant in `O(1)` per step?"
                )

        elif failing_tc:
            ln = failing_tc.get("suspectLine")
            src = failing_tc.get("suspectSource", "")
            snap = failing_tc.get("localsSnapshot") or {}
            snap_str = ", ".join(f"{k}={v}" for k, v in list(snap.items())[:6]) if snap else "none captured"
            reply_parts.append(
                f"On Test {failing_tc['index']} (`{failing_tc.get('label', '')}`), with input `{json.dumps(failing_tc['input'])}`, "
                f"expected `{json.dumps(failing_tc['expected'])}` but your code returned `{json.dumps(failing_tc.get('actual'))}`"
                + (f" at Line {ln} (`{src}`)." if ln else ".") + "\n"
                + (f"- Live variables at Line {ln}: `{snap_str}`\n" if snap else "")
                + f"- Guiding question: {mm['optimalPivot']}"
            )

        elif run_res.get("allPassed"):
            is_suboptimal_nested = depth >= 2 and "O(N)" in prob["complexity"]["optimalTime"] and not sig.get("usesStackQueue")
            if is_suboptimal_nested:
                reply_parts.append(
                    f"Your baseline passes all `{run_res.get('passed')}/{run_res.get('total')}` tests (`{analysis.get('totalScore')}/100` on the SWE & FDE rubric), "
                    f"but uses nested loops (`depth = {depth}`, `{prob['complexity']['bruteTime']}`).\n"
                    f"- How could you replace the inner loop with `O(1)` auxiliary memory so the whole function runs in `{prob['complexity']['optimalTime']}`?"
                )
            else:
                reply_parts.append(
                    f"All `{run_res.get('total', 0)}` test cases pass with optimal `{prob['complexity']['optimalTime']}` structure (`{analysis.get('totalScore')}/100` rubric score)!\n"
                    f"- You can click `Submit & Next →` in the editor toolbar to mark Day {day} solved and move to the next question, or try this interviewer follow-up first:\n"
                    f"- {prob['interviewFollowUp']['question']}"
                )
        elif has_syntax_or_crash:
            highlight_line = err_ln
            reply_parts.append(_diagnose_specific_line_issue(language, err_ln, err_src, err_msg, code))
        else:
            reply_parts.append(
                f"{analysis.get('diagnosis', '')}\n\n"
                f"Key Invariant: {mm['optimalPivot']}"
            )

    if model_mode == "pro":
        rubric_summary = " | ".join(f"{r['axis'].split('(')[0].strip()}: `{r['score']}/{r['max']}`" for r in analysis.get("rubric", []))
        top_gains = analysis.get("improvementPlan", [])[:3]
        pro_lines = [
            f"Pro 5-Axis Rubric Breakdown (`{analysis.get('totalScore', 0)}/100`):",
            f"- {rubric_summary}",
        ]
        if top_gains:
            pro_lines.append("Fastest path to 100/100:")
            for item in top_gains:
                pro_lines.append(f"- `+{item['gain']} pts` ({item['axis']}): {item['howToImprove']}")
        reply_parts.append("\n".join(pro_lines))

    reply_text = "\n\n".join(reply_parts)

    with _PROGRESS_LOCK:
        prog = load_progress(auto_advance=False)
        if history is None:
            hist = prog.setdefault("chatHistory", {}).setdefault(str(day), [])
        hist.append({"role": "user", "text": user_message, "model": model_mode})
        hist.append({
            "role": "assistant",
            "text": reply_text,
            "highlightLine": highlight_line,
            "modelUsed": model_used_label,
            "visualWidget": visual_widget,
        })
        prog.setdefault("chatHistory", {})[str(day)] = hist[-20:]
        save_progress(prog)
        saved_hist = prog["chatHistory"][str(day)]

    return {
        "ok": True,
        "reply": reply_text,
        "modelUsed": model_used_label,
        "highlightLine": highlight_line,
        "visualWidget": visual_widget,
        "executionFrames": exec_frames,
        "runResult": run_res,
        "analysis": analysis,
        "history": saved_hist,
    }


_PY_BUILTIN_NAMES = {
    "list", "dict", "set", "str", "int", "sum", "max", "min", "len",
    "map", "filter", "type", "id", "input", "open", "tuple",
}

_RE_USES_HASH = re.compile(r"\b(dict|set|defaultdict|Counter|Map|Set|make\(map)\b|\{\}|map\[")
_RE_USES_HEAP = re.compile(r"\b(heapq|heappush|heappop|container/heap|MinHeap|MaxHeap)\b")
_RE_USES_STACK_QUEUE = re.compile(r"\b(deque|popleft|stack|queue|lifo|fifo)\b|\.pop\(\)|\.shift\(\)")
_RE_USES_SORT = re.compile(r"\.sort\(|\b(?:sorted|sort\.Ints|sort\.Slice|sort\.Strings)\b")
_RE_USES_BSEARCH = re.compile(r"\b(mid|bisect|lo\s*<\s*hi|left\s*<=\s*right|l\s*<\s*r|>>\s*1)\b")
_RE_USES_TWO_PTR = re.compile(r"\b(left|right|lo|hi|slow|fast|start|end|l,\s*r)\b")
_RE_WORD_L = re.compile(r"\bl\b")
_RE_WORD_R = re.compile(r"\br\b")
_RE_USES_DP = re.compile(r"\b(dp|memo|cache|lru_cache|prefix|running|lps|bit|out|prev|curr|freq|count|counts|parent|indeg|dist)\b")
_RE_USES_FREQ_ARR = re.compile(r"\[0\]\s*\*\s*26|\bord\(|charCodeAt|\[26\]int|Array\(26\)")
_RE_USES_BIT_OPS = re.compile(r"&\s*-\w+|\^=|<<|>>|\bbitmask\b")
_RE_EDGE_GUARD = re.compile(
    r"\bif\s+(not\s+\w+|len\([^)]+\)\s*(==|!=|<|<=)|n\s*(==|!=|<|<=)\s*[0-2]\b|\w+\.length\s*(===|!==|<|<=)|capacity\s*<=)"
)
_RE_HARDCODED_RET = re.compile(r"if\s+\w+\s*==\s*\[[^\]]+\]")
_RE_LOOP_KW = re.compile(r"\b(for|while)\b")
_RE_CTRL_KW = re.compile(r"\b(for|while|if|switch)\b")
_RE_RETURN_KW = re.compile(r"\breturn\b")
_RE_PRINT_CALL = re.compile(r"\bprint\s*\(")
_RE_PY_IDIOM = re.compile(
    r"\b(enumerate|zip|defaultdict|Counter|deque|heapq|all|any|ord|sorted|bisect|math\.gcd|min|max)\s*\("
    r"|\.(get|setdefault|items|values|keys|append|pop|sort)\s*\("
    r"|\[[^\]]+\s+for\s+\w+\s+in\s+"
    r"|\[[^\]]+\]\s*\*\s*\w"
    r"|\w+\[[^:\]]*:[^\]]*\]"
    r"|range\([^,]+,\s*-1,\s*-1\)"
)
_RE_PY_MULTI_ASSIGN = re.compile(r"^\s*[A-Za-z_]\w*\s*,\s*[A-Za-z_]\w*\s*=", re.MULTILINE)
_RE_PY_RANGE_LEN = re.compile(r"for\s+\w+\s+in\s+range\s*\(\s*len\(")
_RE_TS_CONSOLE = re.compile(r"\bconsole\.(log|debug|warn)\s*\(")
_RE_GO_PRINT = re.compile(r"\bfmt\.Print(ln|f)?\s*\(")
_RE_TS_VAR = re.compile(r"\bvar\s+\w+")
_RE_TS_IDIOM = re.compile(r"\b(const|let|Map|Set|Math\.|\?\?|=>|for\s*\(\s*(?:const|let)\b)")
_RE_GO_IDIOM = re.compile(r":=|\brange\b|\bmake\(|,\s*ok\s*:=")
_RE_NESTED_C_FOR = re.compile(r"for\s*\([^;]*;[^;]*;[^)]*\)\s*\{[\s\S]*?for\s*\(")
_RE_DECL_VAR = re.compile(r"\b(?:let|const|var)\s+(\w+)|(\w+)\s*:=")


def _compute_code_metrics(language: str, code: str, func_name: str) -> dict[str, Any]:
    """Extract accurate static AST and structural metrics across Python, TypeScript, and Go."""
    raw_lines = code.splitlines()
    non_empty_lines = [
        ln for ln in raw_lines
        if ln.strip() and not ln.strip().startswith(("#", "//"))
    ]
    max_loop_depth = 0
    max_control_depth = 0
    has_nested_for_for_range = False
    has_hidden_linear_scan_in_loop = False
    has_func_def = False
    has_type_annotations = False
    has_return_stmt = False
    has_bare_except = False
    has_global_stmt = False
    has_hardcoded_return = False
    body_statements_count = 0
    helper_count = 0
    declared_vars: list[str] = []
    container_vars: list[str] = []
    shadowed_builtins: list[str] = []
    shadowed_iterables: list[str] = []
    debug_print_lines: list[int] = []
    syntax_parse_ok = True

    uses_hash = bool(_RE_USES_HASH.search(code))
    uses_heap = bool(_RE_USES_HEAP.search(code))
    uses_stack_queue = bool(_RE_USES_STACK_QUEUE.search(code))
    uses_sort = bool(_RE_USES_SORT.search(code))
    uses_binary_search = bool(_RE_USES_BSEARCH.search(code))
    uses_two_pointers = bool(
        _RE_USES_TWO_PTR.search(code)
        or (_RE_WORD_L.search(code) and _RE_WORD_R.search(code))
    )
    uses_dp_prefix = bool(_RE_USES_DP.search(code))
    uses_freq_array = bool(_RE_USES_FREQ_ARR.search(code))
    uses_bit_ops = bool(_RE_USES_BIT_OPS.search(code))
    uses_recursion_or_helper = False

    has_edge_guard = bool(_RE_EDGE_GUARD.search(code))
    if _RE_HARDCODED_RET.search(code):
        has_hardcoded_return = True

    if language == "python":
        try:
            tree = ast.parse(code)
            fn_node: ast.FunctionDef | None = None
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name == func_name:
                        fn_node = node
                    else:
                        helper_count += 1
                elif isinstance(node, ast.ClassDef):
                    helper_count += 1

            has_func_def = fn_node is not None
            if fn_node is not None:
                args = fn_node.args.args
                has_type_annotations = (fn_node.returns is not None) and all(
                    a.annotation is not None for a in args
                )
                body_statements_count = len(fn_node.body)
                param_names = {a.arg for a in args}
                for sub in ast.walk(fn_node):
                    if isinstance(sub, ast.Return):
                        has_return_stmt = True
                    elif isinstance(sub, ast.ExceptHandler) and sub.type is None:
                        has_bare_except = True
                    elif isinstance(sub, ast.Global):
                        has_global_stmt = True
                    elif isinstance(sub, ast.FunctionDef) and sub is not fn_node:
                        helper_count += 1
                    elif isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name):
                            if sub.func.id == "print":
                                debug_print_lines.append(getattr(sub, "lineno", 1))
                            elif sub.func.id == func_name:
                                uses_recursion_or_helper = True
                    elif isinstance(sub, ast.Assign):
                        is_container_rhs = isinstance(sub.value, (ast.Dict, ast.List, ast.Set)) or (
                            isinstance(sub.value, ast.Call)
                            and isinstance(sub.value.func, ast.Name)
                            and sub.value.func.id in ("dict", "set", "list", "defaultdict", "Counter", "deque")
                        )
                        if is_container_rhs:
                            for tgt in sub.targets:
                                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                                    if tgt.id not in container_vars:
                                        container_vars.append(tgt.id)
                    elif isinstance(sub, ast.For):
                        # Detect shadowing iterable variable: e.g. `for i, nums in enumerate(nums):`
                        iter_names: set[str] = set()
                        if isinstance(sub.iter, ast.Name):
                            iter_names.add(sub.iter.id)
                        elif isinstance(sub.iter, ast.Call):
                            for a in sub.iter.args:
                                if isinstance(a, ast.Name):
                                    iter_names.add(a.id)
                        tgt_names = {
                            t.id for t in ast.walk(sub.target) if isinstance(t, ast.Name)
                        }
                        for ov in sorted(iter_names & tgt_names):
                            if ov not in shadowed_iterables:
                                shadowed_iterables.append(ov)

                # Detect hidden O(N) list membership / .index() / .count() on list input inside a loop
                def _scan_loop_linear(node: ast.AST, in_loop: bool = False) -> bool:
                    now_in_loop = in_loop or isinstance(node, (ast.For, ast.While))
                    if in_loop:
                        if isinstance(node, ast.Compare) and any(
                            isinstance(op, (ast.In, ast.NotIn)) for op in node.ops
                        ):
                            for comp in node.comparators:
                                if isinstance(comp, ast.Name) and comp.id in param_names:
                                    return True
                                if (
                                    isinstance(comp, ast.Subscript)
                                    and isinstance(comp.value, ast.Name)
                                    and comp.value.id in param_names
                                ):
                                    return True
                        elif (
                            isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and node.func.attr in ("index", "count")
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id in param_names
                        ):
                            return True
                    return any(_scan_loop_linear(child, now_in_loop) for child in ast.iter_child_nodes(node))

                has_hidden_linear_scan_in_loop = _scan_loop_linear(fn_node)

            if helper_count > 0:
                uses_recursion_or_helper = True

            def _walk_loop_depth(node: ast.AST, depth: int = 0) -> int:
                best = depth
                for child in ast.iter_child_nodes(node):
                    nd = depth + (1 if isinstance(child, (ast.For, ast.While)) else 0)
                    best = max(best, _walk_loop_depth(child, nd))
                return best

            def _walk_ctrl_depth(node: ast.AST, depth: int = 0) -> int:
                best = depth
                for child in ast.iter_child_nodes(node):
                    nd = depth + (1 if isinstance(child, (ast.For, ast.While, ast.If, ast.Try)) else 0)
                    best = max(best, _walk_ctrl_depth(child, nd))
                return best

            def _is_range_loop(node: ast.AST) -> bool:
                return (
                    isinstance(node, ast.For)
                    and isinstance(node.iter, ast.Call)
                    and isinstance(node.iter.func, ast.Name)
                    and node.iter.func.id == "range"
                )

            def _detect_nested_for_range(node: ast.AST, in_for_range: bool = False) -> bool:
                cur_range = in_for_range or _is_range_loop(node)
                for child in ast.iter_child_nodes(node):
                    if in_for_range and _is_range_loop(child):
                        return True
                    if _detect_nested_for_range(child, cur_range):
                        return True
                return False

            max_loop_depth = _walk_loop_depth(tree)
            max_control_depth = _walk_ctrl_depth(tree)
            has_nested_for_for_range = _detect_nested_for_range(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if not node.id.startswith("_"):
                        if node.id not in declared_vars:
                            declared_vars.append(node.id)
                        if node.id in _PY_BUILTIN_NAMES and node.id not in shadowed_builtins:
                            shadowed_builtins.append(node.id)
        except SyntaxError:
            syntax_parse_ok = False
            max_loop_depth = 1 if _RE_LOOP_KW.search(code) else 0
            max_control_depth = max_loop_depth
            has_func_def = bool(re.search(rf"\bdef\s+{re.escape(func_name)}\s*\(", code))
            has_type_annotations = bool(re.search(rf"\bdef\s+{re.escape(func_name)}\s*\([^)]*:\s*[^)]+\)\s*->", code))
            has_return_stmt = bool(_RE_RETURN_KW.search(code))
            for idx, ln in enumerate(raw_lines, start=1):
                if _RE_PRINT_CALL.search(ln):
                    debug_print_lines.append(idx)

        uses_idiomatic = bool(
            _RE_PY_IDIOM.search(code)
            or _RE_PY_MULTI_ASSIGN.search(code)
        )
        # Flag verbose `for i in range(len(arr)):` only when no idiomatic Python construct is used
        if not uses_idiomatic and _RE_PY_RANGE_LEN.search(code):
            uses_idiomatic = False
    else:
        cur_loops = 0
        cur_ctrl = 0
        for idx, ln in enumerate(raw_lines, start=1):
            stripped_ln = ln.strip()
            if _RE_LOOP_KW.search(stripped_ln):
                cur_loops += 1
                max_loop_depth = max(max_loop_depth, cur_loops)
            if _RE_CTRL_KW.search(stripped_ln):
                cur_ctrl += 1
                max_control_depth = max(max_control_depth, cur_ctrl)
            if "}" in stripped_ln:
                close_cnt = stripped_ln.count("}")
                cur_loops = max(0, cur_loops - close_cnt)
                cur_ctrl = max(0, cur_ctrl - close_cnt)
            if language == "typescript" and _RE_TS_CONSOLE.search(stripped_ln):
                debug_print_lines.append(idx)
            elif language == "go" and _RE_GO_PRINT.search(stripped_ln):
                debug_print_lines.append(idx)

        if language == "typescript":
            sig_m = re.search(rf"function\s+{re.escape(func_name)}\s*\(([^)]*)\)\s*:\s*[^\s{{]+", code)
            has_func_def = bool(re.search(rf"function\s+{re.escape(func_name)}\s*\(", code))
            has_type_annotations = bool(sig_m) and (
                (not sig_m.group(1).strip()) or (":" in sig_m.group(1))
            )
            uses_idiomatic = (
                not bool(_RE_TS_VAR.search(code))
                and bool(_RE_TS_IDIOM.search(code))
            )
            body_statements_count = max(0, len(non_empty_lines) - 2)
        else:
            has_func_def = bool(re.search(rf"func\s+{re.escape(func_name)}\s*\(", code))
            has_type_annotations = has_func_def
            uses_idiomatic = bool(_RE_GO_IDIOM.search(code))
            body_statements_count = max(0, len(non_empty_lines) - 2)

        has_return_stmt = bool(_RE_RETURN_KW.search(code))
        if max_loop_depth >= 2 and _RE_NESTED_C_FOR.search(code):
            has_nested_for_for_range = True
        for m in _RE_DECL_VAR.finditer(code):
            v = m.group(1) or m.group(2)
            if v and v not in declared_vars:
                declared_vars.append(v)
        uses_recursion_or_helper = (
            len(re.findall(rf"\b{re.escape(func_name)}\s*\(", code)) >= 2
            or bool(re.search(r"\b(dfs|bfs|backtrack|helper|find|union)\s*(?:=\s*\(|\()", code))
        )

    descriptive_vars = [v for v in declared_vars if len(v) >= 2]
    cryptic_containers = [v for v in container_vars if len(v) == 1]

    return {
        "lineCount": len(non_empty_lines),
        "bodyStatements": body_statements_count,
        "maxLoopDepth": max_loop_depth,
        "maxControlDepth": max_control_depth,
        "hasNestedForForRange": has_nested_for_for_range,
        "hasHiddenLinearScanInLoop": has_hidden_linear_scan_in_loop,
        "hasFuncDef": has_func_def,
        "hasTypeAnnotations": has_type_annotations,
        "hasReturnStmt": has_return_stmt,
        "hasEdgeGuard": has_edge_guard,
        "hasBareExcept": has_bare_except,
        "hasGlobalStmt": has_global_stmt,
        "hasHardcodedReturn": has_hardcoded_return,
        "usesIdiomatic": uses_idiomatic,
        "syntaxParseOk": syntax_parse_ok,
        "declaredVars": declared_vars,
        "descriptiveVars": descriptive_vars,
        "crypticContainers": cryptic_containers,
        "shadowedBuiltins": shadowed_builtins,
        "shadowedIterables": shadowed_iterables,
        "debugPrintLines": debug_print_lines,
        "helperCount": helper_count,
        "usesHash": uses_hash,
        "usesHeap": uses_heap,
        "usesStackQueue": uses_stack_queue,
        "usesSort": uses_sort,
        "usesBinarySearch": uses_binary_search,
        "usesTwoPointers": uses_two_pointers,
        "usesDpPrefix": uses_dp_prefix,
        "usesFreqArray": uses_freq_array,
        "usesBitOps": uses_bit_ops,
        "usesRecursionOrHelper": uses_recursion_or_helper,
    }


def _detect_pattern_match(prob: dict[str, Any], metrics: dict[str, Any]) -> tuple[bool, list[str]]:
    """Verify whether the code uses a data structure or algorithmic mechanism matching the problem tags."""
    tags_low = " ".join(prob.get("tags", [])).lower()
    pivot_low = prob.get("mentalModel", {}).get("optimalPivot", "").lower()
    combined = f"{tags_low} {pivot_low}"

    detected_labels: list[str] = []
    if metrics["usesHash"]:
        detected_labels.append("hash map / set")
    if metrics["usesFreqArray"]:
        detected_labels.append("fixed-size frequency array")
    if metrics["usesTwoPointers"]:
        detected_labels.append("two pointers / sliding window")
    if metrics["usesStackQueue"]:
        detected_labels.append("stack / queue")
    if metrics["usesHeap"]:
        detected_labels.append("heap / priority queue")
    if metrics["usesBinarySearch"]:
        detected_labels.append("binary search bounds")
    if metrics["usesSort"]:
        detected_labels.append("sorting")
    if metrics["usesDpPrefix"]:
        detected_labels.append("DP / prefix state table")
    if metrics["usesRecursionOrHelper"]:
        detected_labels.append("helper / recursion")
    if metrics["usesBitOps"]:
        detected_labels.append("bitwise operations")

    expected_checks: list[bool] = []
    if any(k in combined for k in ("hash", "map", "dict", "set", "complement", "counting", "frequency", "anagram", "lru")):
        expected_checks.append(metrics["usesHash"] or metrics["usesFreqArray"])
    if any(k in combined for k in ("two pointers", "sliding window", "window", "inward")):
        expected_checks.append(metrics["usesTwoPointers"] or metrics["usesHash"] or metrics["usesDpPrefix"])
    if any(k in combined for k in ("stack", "monotonic", "queue", "bfs", "breadth-first", "deque", "topological")):
        expected_checks.append(metrics["usesStackQueue"] or metrics["usesDpPrefix"])
    if any(k in combined for k in ("heap", "priority queue", "median")):
        expected_checks.append(metrics["usesHeap"] or metrics["usesSort"])
    if any(k in combined for k in ("binary search", "search space", "bisect")):
        expected_checks.append(metrics["usesBinarySearch"])
    if any(k in combined for k in ("sorting", "sort", "sweep line", "interval")):
        expected_checks.append(metrics["usesSort"] or metrics["usesHeap"])
    if any(k in combined for k in ("dynamic programming", "prefix sum", "memoization", "game theory", "dp")):
        expected_checks.append(metrics["usesDpPrefix"] or metrics["usesHash"] or metrics["usesRecursionOrHelper"])
    if any(k in combined for k in ("depth-first", "tree", "trie", "graph", "union-find", "backtracking", "recursion", "fenwick", "segment tree", "linked list")):
        expected_checks.append(
            metrics["usesRecursionOrHelper"]
            or metrics["usesHash"]
            or metrics["usesStackQueue"]
            or metrics["usesDpPrefix"]
            or metrics["usesBitOps"]
        )
    if any(k in combined for k in ("bit manipulation", "math", "number theory", "geometry", "string matching", "kmp", "rolling hash")):
        expected_checks.append(
            metrics["usesBitOps"]
            or metrics["usesHash"]
            or metrics["usesDpPrefix"]
            or metrics["usesTwoPointers"]
        )

    matched = any(expected_checks) if expected_checks else bool(detected_labels)
    return matched, detected_labels


def _make_criterion(
    label: str,
    earned: int,
    possible: int,
    evidence: str,
    how_to_improve: str = "",
    target_line: int | None = None,
) -> dict[str, Any]:
    earned_clamped = max(0, min(possible, int(earned)))
    status = "met" if earned_clamped >= possible else ("partial" if earned_clamped > 0 else "missed")
    return {
        "label": label,
        "earned": earned_clamped,
        "possible": possible,
        "gap": possible - earned_clamped,
        "status": status,
        "evidence": evidence,
        "howToImprove": "" if status == "met" else how_to_improve,
        "targetLine": target_line if status != "met" else None,
    }


def _build_axis_entry(axis_name: str, criteria: list[dict[str, Any]], full_marks_reason: str) -> dict[str, Any]:
    score = sum(c["earned"] for c in criteria)
    max_score = sum(c["possible"] for c in criteria)
    pts_lost = max_score - score
    missed_or_partial = [c for c in criteria if c["status"] != "met"]

    if pts_lost == 0:
        why_score = f"Earned full marks ({score}/{max_score}): {full_marks_reason}"
        how_to_full = "Full marks achieved on this axis. No changes needed."
        feedback = full_marks_reason
    else:
        deduction_bits = [
            f"{c['label']} ({c['earned']}/{c['possible']})"
            for c in missed_or_partial
        ]
        why_score = (
            f"Awarded {score}/{max_score} ({pts_lost} pt{'s' if pts_lost != 1 else ''} deducted on "
            + ", ".join(deduction_bits)
            + ")."
        )
        top_fix = max(missed_or_partial, key=lambda c: c["gap"])
        how_to_full = (
            f"Complete the {len(missed_or_partial)} remaining check{'s' if len(missed_or_partial) != 1 else ''} "
            f"below to recover +{pts_lost} pt{'s' if pts_lost != 1 else ''}, starting with: {top_fix['howToImprove']}"
        )
        feedback = f"{why_score} Next step: {top_fix['howToImprove']}"

    return {
        "axis": axis_name,
        "score": score,
        "max": max_score,
        "pointsToFullMarks": pts_lost,
        "whyScore": why_score,
        "howToFullMarks": how_to_full,
        "feedback": feedback,
        "criteria": criteria,
    }


def _build_improvement_plan(rubric: list[dict[str, Any]], run_ok: bool = True) -> list[dict[str, Any]]:
    """Build ranked list of actionable improvements from unmet rubric criteria."""
    plan: list[dict[str, Any]] = []
    for ax in rubric:
        for crit in ax["criteria"]:
            if crit["gap"] > 0:
                plan.append({
                    "axis": ax["axis"],
                    "criterion": crit["label"],
                    "gain": crit["gap"],
                    "earned": crit["earned"],
                    "possible": crit["possible"],
                    "status": crit["status"],
                    "why": crit["evidence"],
                    "howToImprove": crit["howToImprove"],
                    "targetLine": crit["targetLine"],
                })
    plan.sort(
        key=lambda item: (
            0 if (not run_ok and item["criterion"] == "Clean compilation & syntax") else 1,
            -item["gain"],
            0 if item["targetLine"] else 1,
            item["axis"],
        )
    )
    return plan


def analyse_user_code(day: int, language: str, code: str) -> dict[str, Any]:
    """Analyse the user's code across the 5 SWE & FDE Interview Rubric Axes with transparent per-criterion scoring."""
    prob = cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown problem day {day}"}

    stripped = code.strip()
    starter_stripped = prob["starterCode"].get(language, "").strip()
    lines = [ln for ln in stripped.splitlines() if ln.strip() and not ln.strip().startswith(("#", "//"))]
    is_skeleton = (
        stripped == starter_stripped
        or len(lines) <= 1
        or ("pass" in stripped and len(lines) <= 3)
    )

    run_res = execute_user_code(day, language, code) if not is_skeleton else {
        "ok": True,
        "passed": 0,
        "total": len(prob["testCases"]),
        "visiblePassed": 0,
        "visibleTotal": len(prob.get("visibleTestCases", [])),
        "hiddenPassed": 0,
        "hiddenTotal": len(prob.get("hiddenTestCases", [])),
        "allPassed": False,
        "results": [],
        "isSkeleton": True,
    }

    func_name = prob["funcName"]
    ref_code = prob.get("solutionCode", {}).get(language, "") or prob.get("solutionCode", {}).get("python", "")
    user_m = _compute_code_metrics(language, code, func_name)
    ref_m = _compute_code_metrics(language, ref_code, func_name)

    run_ok = bool(run_res.get("ok")) and not bool(run_res.get("syntaxErrorPartialRun"))
    all_passed = bool(run_res.get("allPassed")) and run_ok
    passed_cnt = int(run_res.get("passed", 0))
    total_cnt = int(run_res.get("total", len(prob["testCases"])))
    vis_passed = int(run_res.get("visiblePassed", 0))
    vis_total = int(run_res.get("visibleTotal", len(prob.get("visibleTestCases", []))))
    hid_passed = int(run_res.get("hiddenPassed", 0))
    hid_total = int(run_res.get("hiddenTotal", len(prob.get("hiddenTestCases", []))))

    results_list = run_res.get("results") or []
    first_fail_vis = next((r for r in results_list if not r.get("passed") and not r.get("hidden")), None)
    first_fail_hid = next((r for r in results_list if not r.get("passed") and r.get("hidden")), None)
    first_fail_any = first_fail_vis or first_fail_hid
    runtime_errors = [r for r in results_list if r.get("error")]
    max_runtime_ms = max((float(r.get("runtimeMs") or 0.0) for r in results_list), default=0.0)
    none_returns = [
        r for r in results_list
        if (not r.get("passed")) and (r.get("actual") is None) and (not r.get("error"))
    ]

    err_line = run_res.get("errorLine") or (runtime_errors[0].get("errorLine") if runtime_errors else None)
    err_msg = run_res.get("error") or (runtime_errors[0].get("error") if runtime_errors else "")
    fail_line = err_line or (first_fail_any.get("suspectLine") if first_fail_any else None)

    opt_time = prob["complexity"].get("optimalTime", "O(N)")
    opt_space = prob["complexity"].get("optimalSpace", "O(N)")
    brute_time = prob["complexity"].get("bruteTime", "O(N^2)")
    generic_input_tags = {"Array", "String", "Matrix", "Math"}
    craft_keywords = ("Clarification", "Tracing", "Synthesis", "Modularity", "Amortised", "FDE")
    algo_tags = [
        t for t in prob.get("tags", [])
        if t not in generic_input_tags and not any(ck in t for ck in craft_keywords)
    ]
    primary_tag = algo_tags[0] if algo_tags else (prob["tags"][0] if prob.get("tags") else "Core Algorithm")
    mm = prob["mentalModel"]
    checklist_items = prob.get("edgeCaseChecklist") or []
    first_checklist_tip = (
        f"{checklist_items[0].get('trap', 'Edge case')}: {checklist_items[0].get('guard', '')}".strip(": ")
        if checklist_items
        else "Verify empty, duplicate, and boundary inputs."
    )
    followup_q = prob.get("interviewFollowUp", {}).get("question", "Discuss how your design adapts to streaming or high-throughput inputs.")

    ref_loop_depth = max(1, ref_m["maxLoopDepth"])
    is_suboptimal_nested = (
        not is_skeleton
        and user_m["syntaxParseOk"]
        and (
            user_m["maxLoopDepth"] > ref_loop_depth
            or (
                user_m["hasNestedForForRange"]
                and not ref_m["hasNestedForForRange"]
                and "O(N^2)" not in opt_time
                and "O(N^3)" not in opt_time
            )
            or (
                user_m["hasHiddenLinearScanInLoop"]
                and not ref_m["hasHiddenLinearScanInLoop"]
                and "O(N^2)" not in opt_time
            )
        )
    )
    pattern_matched, detected_patterns = _detect_pattern_match(prob, user_m)

    # =========================================================================
    # AXIS 1: Data Structures & Algorithms (20 pts = 6 + 6 + 5 + 3)
    # =========================================================================
    # 1.1 Core correctness on sample tests (6 pts)
    if is_skeleton:
        c1_sample = _make_criterion(
            "Sample test correctness", 0, 6,
            "Starter template has no implementation yet (0 sample tests passing).",
            f"Implement `{func_name}` using the `{primary_tag}` invariant so all {vis_total} visible sample cases pass.",
        )
    elif not run_ok:
        c1_sample = _make_criterion(
            "Sample test correctness", 0, 6,
            f"Execution stopped before passing sample tests (`{err_msg[:110]}`).",
            f"Fix the error on Line {err_line or 1} (`{err_msg[:90]}`) and run tests until all {vis_total} sample tests pass.",
            target_line=err_line,
        )
    elif vis_passed == vis_total and vis_total > 0:
        c1_sample = _make_criterion(
            "Sample test correctness", 6, 6,
            f"Passed all {vis_passed}/{vis_total} visible sample test cases.",
        )
    else:
        pts = max(0, min(5, int(round(6 * vis_passed / max(1, vis_total)))))
        fail_desc = (
            f"Test {first_fail_vis['index']} expected `{json.dumps(first_fail_vis['expected'])}` "
            f"but returned `{json.dumps(first_fail_vis.get('actual'))}`"
            + (f" at Line {first_fail_vis['suspectLine']}" if first_fail_vis.get("suspectLine") else "")
            if first_fail_vis else f"only {vis_passed}/{vis_total} sample cases passed"
        )
        c1_sample = _make_criterion(
            "Sample test correctness", pts, 6,
            f"Passed {vis_passed}/{vis_total} sample tests ({fail_desc}).",
            f"Fix the logic causing {fail_desc} so every sample case matches expected output.",
            target_line=first_fail_vis.get("suspectLine") if first_fail_vis else fail_line,
        )

    # 1.2 Optimal time-complexity structure (6 pts)
    if is_skeleton:
        c1_complex = _make_criterion(
            "Optimal time-complexity structure", 0, 6,
            f"No loop or algorithm body implemented yet (target is `{opt_time}` time, `{opt_space}` space).",
            f"Build your solution around `{opt_time}` time: {mm['optimalPivot']}",
        )
    elif not user_m["syntaxParseOk"]:
        c1_complex = _make_criterion(
            "Optimal time-complexity structure", 0, 6,
            f"Could not verify loop complexity because of a syntax error on Line {err_line or 1}.",
            f"Resolve the syntax error on Line {err_line or 1} so AST complexity analysis can confirm `{opt_time}` structure.",
            target_line=err_line,
        )
    elif is_suboptimal_nested:
        reason_detail = (
            "a hidden O(N) list membership/index scan inside your loop"
            if user_m["hasHiddenLinearScanInLoop"]
            else f"loop nesting depth {user_m['maxLoopDepth']} (exceeding optimal depth {ref_loop_depth})"
        )
        c1_complex = _make_criterion(
            "Optimal time-complexity structure", 2, 6,
            f"Detected {reason_detail}, trending toward `{brute_time}` instead of optimal `{opt_time}`.",
            f"Eliminate the inner scan to reach `{opt_time}` time: {mm['optimalPivot']}",
        )
    elif all_passed:
        c1_complex = _make_criterion(
            "Optimal time-complexity structure", 6, 6,
            f"Loop depth ({user_m['maxLoopDepth']}) matches the optimal `{opt_time}` structure with zero redundant inner rescans.",
        )
    else:
        c1_complex = _make_criterion(
            "Optimal time-complexity structure", 4, 6,
            f"Loop structure (depth {user_m['maxLoopDepth']}) aligns with `{opt_time}`, but full correctness is not yet verified ({passed_cnt}/{total_cnt} passing).",
            f"Fix the remaining failing test cases while keeping loop depth at or below {ref_loop_depth} to confirm `{opt_time}` correctness.",
            target_line=fail_line,
        )

    # 1.3 Target pattern & data structure choice (5 pts)
    if is_skeleton:
        c1_pattern = _make_criterion(
            "Target pattern & data structure", 0, 5,
            f"Starter code does not yet use the `{primary_tag}` pattern.",
            f"Introduce `{primary_tag}` state to maintain the core invariant: {mm['optimalPivot']}",
        )
    elif pattern_matched and not is_suboptimal_nested and all_passed:
        used_str = ", ".join(detected_patterns[:3]) if detected_patterns else primary_tag
        c1_pattern = _make_criterion(
            "Target pattern & data structure", 5, 5,
            f"Detected optimal pattern signals ({used_str}) aligned with `{', '.join(prob['tags'][:2])}`.",
        )
    elif pattern_matched and not is_suboptimal_nested:
        used_str = ", ".join(detected_patterns[:3]) if detected_patterns else primary_tag
        c1_pattern = _make_criterion(
            "Target pattern & data structure", 4, 5,
            f"Detected the right data structure ({used_str}), though some test transitions are still failing.",
            f"Keep your `{used_str}` state and refine the update invariant until all {total_cnt} tests pass.",
            target_line=fail_line,
        )
    elif is_suboptimal_nested:
        c1_pattern = _make_criterion(
            "Target pattern & data structure", 1, 5,
            f"Code relies on repeated scanning rather than `{primary_tag}` auxiliary state.",
            f"Introduce a `{primary_tag}` data structure to cache intermediate state and eliminate the inner scan.",
        )
    else:
        c1_pattern = _make_criterion(
            "Target pattern & data structure", 3 if all_passed else 2, 5,
            f"Expected `{primary_tag}` state structures were not clearly detected ({', '.join(detected_patterns) or 'basic control flow only'}).",
            f"Structure your solution explicitly around `{primary_tag}` ({mm['optimalPivot']}).",
        )

    # 1.4 Full suite algorithmic efficiency (3 pts)
    if is_skeleton or not run_ok:
        c1_eff = _make_criterion(
            "Full-suite scaling efficiency", 0, 3,
            "Efficiency cannot be confirmed until the full visible + hidden suite runs cleanly.",
            "Complete the implementation and pass both visible and hidden stress test cases.",
            target_line=err_line,
        )
    elif all_passed and not is_suboptimal_nested and max_runtime_ms < 250.0:
        c1_eff = _make_criterion(
            "Full-suite scaling efficiency", 3, 3,
            f"All {passed_cnt}/{total_cnt} tests passed rapidly (peak {max_runtime_ms:.2f} ms) under optimal complexity.",
        )
    elif all_passed and is_suboptimal_nested:
        c1_eff = _make_criterion(
            "Full-suite scaling efficiency", 1, 3,
            f"Passed current {total_cnt} tests, but `{brute_time}` scaling will time out on full LeetCode constraint bounds.",
            f"Optimise your nested scan to `{opt_time}` so throughput holds on large inputs.",
        )
    else:
        c1_eff = _make_criterion(
            "Full-suite scaling efficiency", 1 if vis_passed == vis_total and vis_total > 0 else 0, 3,
            f"Passed {passed_cnt}/{total_cnt} total tests (peak {max_runtime_ms:.2f} ms); hidden or scaled inputs are still failing.",
            "Pass all hidden and stress test cases under target complexity bounds.",
            target_line=fail_line,
        )

    axis_dsa = _build_axis_entry(
        "Data Structures & Algorithms",
        [c1_sample, c1_complex, c1_pattern, c1_eff],
        f"All {total_cnt} tests pass using optimal `{opt_time}` structure and `{primary_tag}` state.",
    )

    # =========================================================================
    # AXIS 2: Programming & Language Idioms (20 pts = 5 + 5 + 5 + 5)
    # =========================================================================
    # 2.1 Clean compilation & valid syntax (5 pts)
    if is_skeleton:
        c2_syntax = _make_criterion(
            "Clean compilation & syntax", 2, 5,
            "Starter function header parses cleanly, but the solution body is still a placeholder.",
            f"Replace the starter placeholder inside `{func_name}` with your working logic.",
        )
    elif not run_ok:
        c2_syntax = _make_criterion(
            "Clean compilation & syntax", 0, 5,
            f"Failed with `{err_msg[:110]}` on Line {err_line or 1}.",
            f"Fix the syntax or runtime error on Line {err_line or 1} so the code compiles and runs cleanly.",
            target_line=err_line,
        )
    else:
        c2_syntax = _make_criterion(
            "Clean compilation & syntax", 5, 5,
            f"Compiles and runs cleanly in {language.capitalize()} with zero syntax errors.",
        )

    # 2.2 Type safety & signature discipline (5 pts)
    expected_sig = prob["starterCode"].get(language, "").splitlines()[0].strip() if prob["starterCode"].get(language) else f"def {func_name}(...)"
    if not user_m["hasFuncDef"]:
        c2_types = _make_criterion(
            "Type safety & signature", 0, 5,
            f"Required entry-point function `{func_name}` was not found.",
            f"Define the exact required signature: `{expected_sig}`.",
            target_line=1,
        )
    elif user_m["hasTypeAnnotations"]:
        c2_types = _make_criterion(
            "Type safety & signature", 5, 5,
            f"Preserved `{func_name}` with complete parameter and return type annotations.",
        )
    else:
        c2_types = _make_criterion(
            "Type safety & signature", 3, 5,
            f"`{func_name}` is defined, but parameter or return type annotations are missing.",
            f"Add explicit parameter and return type annotations matching `{expected_sig}`.",
            target_line=1,
        )

    # 2.3 Idiomatic language constructs (5 pts)
    idiom_hints = {
        "python": "Use Pythonic helpers such as `enumerate()`, `.get(key, 0)`, `defaultdict`, `zip()`, or tuple unpacking instead of verbose index boilerplate.",
        "typescript": "Use `const`/`let` (never `var`), `Map`/`Set`, `for (const x of arr)`, and nullish coalescing (`??`).",
        "go": "Use `:=` short declarations, `for i, v := range ...`, `make(...)`, and comma-ok map lookups (`if v, ok := m[k]; ok`).",
    }
    if is_skeleton:
        c2_idioms = _make_criterion(
            "Idiomatic language constructs", 0, 5,
            "No implemented body yet to evaluate language idioms.",
            idiom_hints.get(language, idiom_hints["python"]),
        )
    elif user_m["usesIdiomatic"]:
        c2_idioms = _make_criterion(
            "Idiomatic language constructs", 5, 5,
            f"Uses clean, idiomatic {language.capitalize()} constructs without redundant boilerplate.",
        )
    else:
        c2_idioms = _make_criterion(
            "Idiomatic language constructs", 3, 5,
            f"Code works imperatively, but relies on manual index loops or verbose boilerplate instead of idiomatic {language.capitalize()} patterns.",
            idiom_hints.get(language, idiom_hints["python"]),
        )

    # 2.4 Descriptive naming & zero debug clutter (5 pts)
    if is_skeleton:
        c2_naming = _make_criterion(
            "Descriptive naming & clean output", 0, 5,
            "No state variables declared yet.",
            "Declare descriptive state variables (for example `seen`, `counts`, `left`, `right`, or `res`) and keep output free of debug prints.",
        )
    else:
        naming_pts = 5
        naming_issues: list[str] = []
        naming_fixes: list[str] = []
        naming_line: int | None = None
        if user_m["debugPrintLines"]:
            naming_pts -= 2
            ln_str = ", ".join(str(x) for x in user_m["debugPrintLines"][:3])
            naming_issues.append(f"leftover debug print/log on Line {ln_str}")
            naming_fixes.append(f"remove debug print/log statement on Line {ln_str} before final submission")
            naming_line = user_m["debugPrintLines"][0]
        if user_m["crypticContainers"] and not user_m["descriptiveVars"]:
            naming_pts -= 2
            cnames = ", ".join(f"`{v}`" for v in user_m["crypticContainers"][:3])
            naming_issues.append(f"single-letter container name ({cnames})")
            naming_fixes.append(f"rename {cnames} to a descriptive state name such as `seen`, `counts`, or `groups`")
        elif not user_m["descriptiveVars"] and len(user_m["declaredVars"]) >= 2:
            naming_pts -= 2
            naming_issues.append(f"all state variables are single letters (`{', '.join(user_m['declaredVars'][:4])}`)")
            naming_fixes.append("give key state variables descriptive names so an interviewer can read invariants at a glance")
        if user_m["hasGlobalStmt"]:
            naming_pts -= 2
            naming_issues.append("uses `global` state mutation")
            naming_fixes.append("keep all mutable state local to the function instead of using `global`")

        if not naming_issues:
            tracked = ", ".join(f"`{v}`" for v in user_m["declaredVars"][:5]) if user_m["declaredVars"] else "clean local state"
            c2_naming = _make_criterion(
                "Descriptive naming & clean output", 5, 5,
                f"Clear variable naming ({tracked}) with zero leftover debug prints or global state.",
            )
        else:
            c2_naming = _make_criterion(
                "Descriptive naming & clean output", max(0, naming_pts), 5,
                "Detected " + " and ".join(naming_issues) + ".",
                "To earn full marks here: " + "; ".join(naming_fixes) + ".",
                target_line=naming_line,
            )

    axis_prog = _build_axis_entry(
        "Programming & Language Idioms",
        [c2_syntax, c2_types, c2_idioms, c2_naming],
        f"Clean {language.capitalize()} syntax, typed signature, idiomatic constructs, and readable naming with zero debug clutter.",
    )

    # =========================================================================
    # AXIS 3: Code Comprehension & Edge Cases (20 pts = 8 + 5 + 4 + 3)
    # =========================================================================
    # 3.1 Hidden edge-case test suite (8 pts)
    if is_skeleton:
        c3_hidden = _make_criterion(
            "Hidden edge-case suite", 0, 8,
            f"0/{hid_total} hidden edge cases tested because the function is still a starter skeleton.",
            f"Implement `{func_name}` and verify all {hid_total} hidden edge cases pass (use Reveal Hidden in Problem & Code if stuck).",
        )
    elif not run_ok:
        c3_hidden = _make_criterion(
            "Hidden edge-case suite", 0, 8,
            f"Execution failed before hidden edge cases could pass (`{err_msg[:100]}`).",
            f"Fix Line {err_line or 1} first, then re-run to test all {hid_total} hidden edge cases.",
            target_line=err_line,
        )
    elif hid_passed == hid_total and hid_total > 0:
        c3_hidden = _make_criterion(
            "Hidden edge-case suite", 8, 8,
            f"Passed all {hid_passed}/{hid_total} hidden adversarial edge cases.",
        )
    else:
        pts = max(0, min(7, int(round(8 * hid_passed / max(1, hid_total)))))
        cat = first_fail_hid.get("category") or "Edge Case" if first_fail_hid else "Hidden Edge Case"
        ereason = first_fail_hid.get("edgeReason") or "" if first_fail_hid else ""
        c3_hidden = _make_criterion(
            "Hidden edge-case suite", pts, 8,
            f"Passed {hid_passed}/{hid_total} hidden edge cases; failed on `{cat}`" + (f" ({ereason})." if ereason else "."),
            f"Handle the failing `{cat}` case" + (f" ({ereason})" if ereason else "") + ". Click Reveal Hidden in Problem & Code to inspect the exact failing input.",
            target_line=first_fail_hid.get("suspectLine") if first_fail_hid else fail_line,
        )

    # 3.2 Boundary & empty-input resilience (5 pts)
    if is_skeleton:
        c3_bound = _make_criterion(
            "Boundary & empty-input resilience", 0, 5,
            "No boundary handling implemented yet.",
            "Ensure empty, single-element, and minimal inputs return safely without indexing out of range.",
        )
    elif all_passed:
        guard_note = (
            "Explicit boundary guard detected and verified across all hidden boundary cases."
            if user_m["hasEdgeGuard"]
            else "Loop and return invariants handle minimal and boundary inputs cleanly across all hidden tests."
        )
        c3_bound = _make_criterion("Boundary & empty-input resilience", 5, 5, guard_note)
    elif user_m["hasEdgeGuard"] and run_ok:
        c3_bound = _make_criterion(
            "Boundary & empty-input resilience", 3, 5,
            "Explicit boundary guard detected, but some non-trivial test inputs still fail.",
            "Keep your top-level boundary guard and fix the core loop transition on the failing cases.",
            target_line=fail_line,
        )
    else:
        c3_bound = _make_criterion(
            "Boundary & empty-input resilience", 1 if run_ok and passed_cnt > 0 else 0, 5,
            "No explicit boundary guard detected and edge-case tests are not yet passing.",
            "Add an explicit guard clause for empty, single-element, or mismatched-length inputs before indexing elements.",
            target_line=fail_line,
        )

    # 3.3 Complete return-path coverage (4 pts)
    if is_skeleton or not user_m["hasReturnStmt"]:
        c3_ret = _make_criterion(
            "Complete return-path coverage", 0, 4,
            "No `return` statement found inside the solution body.",
            f"Add explicit `return` statements covering both the match path and the default/empty fallback path.",
        )
    elif none_returns:
        r_tc = none_returns[0]
        c3_ret = _make_criterion(
            "Complete return-path coverage", 1, 4,
            f"Function implicitly returned `None` / `null` on Test {r_tc['index']} (expected `{json.dumps(r_tc['expected'])}`).",
            "Add a fallback `return` statement after your loop so every execution path returns a valid value of the expected type.",
            target_line=r_tc.get("suspectLine"),
        )
    elif all_passed:
        c3_ret = _make_criterion(
            "Complete return-path coverage", 4, 4,
            "Every execution path returns the exact expected type and value across all test cases.",
        )
    else:
        c3_ret = _make_criterion(
            "Complete return-path coverage", 2, 4,
            "`return` path exists, though at least one test case returns an incorrect value.",
            "Verify your return expression and early-exit conditions against the failing test case output.",
            target_line=fail_line,
        )

    # 3.4 Domain-specific trap coverage (3 pts)
    if is_skeleton or not run_ok:
        c3_traps = _make_criterion(
            "Domain-specific edge traps", 0, 3,
            "Problem-specific edge traps have not been verified yet.",
            f"Watch out for `{first_checklist_tip}`.",
            target_line=err_line,
        )
    elif all_passed:
        cats = sorted({r.get("category") for r in results_list if r.get("hidden") and r.get("category")})
        cats_str = ", ".join(cats[:4]) if cats else "all hidden categories"
        c3_traps = _make_criterion(
            "Domain-specific edge traps", 3, 3,
            f"Cleared all domain edge-case categories ({cats_str}).",
        )
    else:
        c3_traps = _make_criterion(
            "Domain-specific edge traps", 1 if vis_passed == vis_total and vis_total > 0 else 0, 3,
            "Sample cases alone do not cover every domain trap for this problem.",
            f"Check this problem's pre-submit trap: {first_checklist_tip}",
            target_line=fail_line,
        )

    axis_comp = _build_axis_entry(
        "Code Comprehension & Edge Cases",
        [c3_hidden, c3_bound, c3_ret, c3_traps],
        f"Passed all {hid_total} hidden edge cases with safe boundary handling and complete return-path coverage.",
    )

    # =========================================================================
    # AXIS 4: Dry-Run & Debugging Readiness (20 pts = 6 + 5 + 5 + 4)
    # =========================================================================
    # 4.1 End-to-end execution reliability (6 pts)
    if is_skeleton:
        c4_exec = _make_criterion(
            "End-to-end execution reliability", 0, 6,
            f"0/{total_cnt} tests executed because the solution is still a starter skeleton.",
            "Implement the solution and click Run Tests (or Visualise Code) to verify execution.",
        )
    elif not run_ok or runtime_errors:
        c4_exec = _make_criterion(
            "End-to-end execution reliability", 0, 6,
            f"Hit a runtime or syntax error on Line {err_line or 1}: `{err_msg[:100]}`.",
            f"Inspect Line {err_line or 1} in the side-by-side Python Tutor visualiser to see the live local variables right before the crash.",
            target_line=err_line,
        )
    elif all_passed:
        c4_exec = _make_criterion(
            "End-to-end execution reliability", 6, 6,
            f"Passed {passed_cnt}/{total_cnt} automated tests with zero runtime errors.",
        )
    else:
        pts = max(1, min(5, int(round(6 * passed_cnt / max(1, total_cnt)))))
        snap = first_fail_any.get("localsSnapshot") if first_fail_any else {}
        snap_str = ", ".join(f"{k}={v}" for k, v in list((snap or {}).items())[:4])
        c4_exec = _make_criterion(
            "End-to-end execution reliability", pts, 6,
            f"Passing {passed_cnt}/{total_cnt} tests" + (f"; diverged at Line {fail_line}" if fail_line else "") + (f" (`{snap_str}`)" if snap_str else "") + ".",
            f"Step through the failing test in the Python Tutor visualiser around Line {fail_line or 1} to inspect where state diverges from expected output.",
            target_line=fail_line,
        )

    # 4.2 Off-by-one & loop-bound safety (5 pts)
    bounds_err = any(
        any(tok in str(r.get("error", "")) for tok in ("IndexError", "KeyError", "RecursionError", "Time Limit"))
        for r in runtime_errors
    ) or any(tok in err_msg for tok in ("IndexError", "KeyError", "RecursionError", "Time Limit"))
    if is_skeleton:
        c4_bounds = _make_criterion(
            "Off-by-one & bound safety", 0, 5,
            "Loop bounds have not been exercised yet.",
            "Write clear loop boundaries (`<` vs `<=`, `0` vs `len - 1`) and test them on minimal inputs.",
        )
    elif bounds_err:
        c4_bounds = _make_criterion(
            "Off-by-one & bound safety", 0, 5,
            f"Triggered a bounds or termination fault (`{err_msg[:100]}`).",
            f"Check loop conditions and index bounds on Line {err_line or 1} (verify `<` vs `<=` and check key existence before indexing).",
            target_line=err_line,
        )
    elif all_passed:
        c4_bounds = _make_criterion(
            "Off-by-one & bound safety", 5, 5,
            "Zero out-of-bounds errors, key faults, or off-by-one mismatches across visible and hidden cases.",
        )
    else:
        c4_bounds = _make_criterion(
            "Off-by-one & bound safety", 2 if run_ok else 0, 5,
            "No index crashes, though incorrect outputs suggest a boundary condition or loop update mismatch.",
            "Trace the first and last loop iterations in the side-by-side visualiser to rule out off-by-one index or pointer updates.",
            target_line=fail_line,
        )

    # 4.3 Traceable state visibility (5 pts)
    if is_skeleton:
        c4_trace = _make_criterion(
            "Traceable state visibility", 0, 5,
            "No intermediate state transitions exist yet for a whiteboard dry-run.",
            "Break the algorithm into clear, line-by-line state transitions so you can narrate a dry-run table smoothly.",
        )
    elif user_m["lineCount"] >= 4 and (user_m["declaredVars"] or user_m["bodyStatements"] >= 2):
        c4_trace = _make_criterion(
            "Traceable state visibility", 5, 5,
            f"Multi-step state flow ({user_m['lineCount']} code lines) makes step-by-step whiteboard dry-running straightforward.",
        )
    else:
        c4_trace = _make_criterion(
            "Traceable state visibility", 3, 5,
            f"Very compact body ({user_m['lineCount']} code lines) compresses intermediate state updates.",
            "Assign key intermediate expressions (such as a complement, midpoint, or window length) to named variables so an interviewer can trace each step.",
        )

    # 4.4 Zero silent state bugs & clean termination (4 pts)
    if is_skeleton:
        c4_clean = _make_criterion(
            "Zero shadowing & silent bugs", 0, 4,
            "Not evaluated on an empty starter template.",
            "Avoid shadowing Python built-ins (`list`, `dict`, `sum`, `max`) or overwriting loop iterables.",
        )
    else:
        clean_pts = 4
        clean_issues: list[str] = []
        clean_fixes: list[str] = []
        if user_m["shadowedBuiltins"]:
            clean_pts -= 2
            s_names = ", ".join(f"`{x}`" for x in user_m["shadowedBuiltins"][:3])
            clean_issues.append(f"shadows built-in {s_names}")
            clean_fixes.append(f"rename {s_names} so you do not shadow built-in functions")
        if user_m["shadowedIterables"]:
            clean_pts -= 2
            it_names = ", ".join(f"`{x}`" for x in user_m["shadowedIterables"][:2])
            clean_issues.append(f"loop variable overwrites iterable {it_names}")
            clean_fixes.append(f"use a distinct singular loop variable name instead of overwriting {it_names}")
        if user_m["hasBareExcept"]:
            clean_pts -= 2
            clean_issues.append("uses a bare `except:` block that hides real bugs")
            clean_fixes.append("catch a specific exception type (for example `except ValueError:`) instead of bare `except:`")
        if "Time Limit" in err_msg:
            clean_pts = 0
            clean_issues.append("hit time limit due to non-terminating loop")
            clean_fixes.append("ensure every `while` loop strictly advances its pointer or shrinks its search space on every branch")

        if not clean_issues:
            c4_clean = _make_criterion(
                "Zero shadowing & silent bugs", 4, 4,
                "Zero built-in shadowing, zero bare exception swallowing, and guaranteed loop termination.",
            )
        else:
            c4_clean = _make_criterion(
                "Zero shadowing & silent bugs", max(0, clean_pts), 4,
                "Detected " + "; ".join(clean_issues) + ".",
                "Fix: " + "; ".join(clean_fixes) + ".",
            )

    axis_debug = _build_axis_entry(
        "Dry-Run & Debugging Readiness",
        [c4_exec, c4_bounds, c4_trace, c4_clean],
        "Zero runtime errors, clean loop boundaries, traceable state steps, and zero silent shadowing bugs.",
    )

    # =========================================================================
    # AXIS 5: FDE Production & Extensibility (20 pts = 6 + 5 + 5 + 4)
    # =========================================================================
    # 5.1 Clean phase separation & controlled nesting (6 pts)
    max_allowed_ctrl = max(4, ref_m["maxControlDepth"])
    if is_skeleton:
        c5_sep = _make_criterion(
            "Clean structure & shallow nesting", 0, 6,
            "No implemented phases (initialisation, invariant loop, return) yet.",
            "Organise your function cleanly into state initialisation, invariant updates, and return formatting.",
        )
    elif user_m["maxControlDepth"] > max_allowed_ctrl:
        c5_sep = _make_criterion(
            "Clean structure & shallow nesting", 3 if all_passed else 2, 6,
            f"Deep control-flow nesting (depth {user_m['maxControlDepth']}, above clean threshold {max_allowed_ctrl}).",
            "Flatten deep nested branches using guard clauses (`continue` / early `return`) or extract a small helper function.",
        )
    elif all_passed:
        c5_sep = _make_criterion(
            "Clean structure & shallow nesting", 6, 6,
            f"Clear separation between state setup, loop invariant updates, and return formatting (nesting depth {user_m['maxControlDepth']}).",
        )
    else:
        c5_sep = _make_criterion(
            "Clean structure & shallow nesting", 4 if run_ok else 2, 6,
            f"Control nesting is controlled (depth {user_m['maxControlDepth']}), though logic is still incomplete ({passed_cnt}/{total_cnt} passing).",
            "Keep this clean phase layout while fixing the failing invariant step.",
            target_line=fail_line,
        )

    # 5.2 Statelessness & side-effect safety (5 pts)
    if is_skeleton:
        c5_side = _make_criterion(
            "Stateless & side-effect safety", 0, 5,
            "Pending implementation.",
            "Keep all state scoped inside the function so repeated calls in a production service never leak state.",
        )
    elif user_m["hasGlobalStmt"]:
        c5_side = _make_criterion(
            "Stateless & side-effect safety", 1, 5,
            "Uses `global` state, which causes race conditions and cross-request contamination in production.",
            "Move all mutable state into local variables or a dedicated class instance.",
        )
    elif not run_ok:
        c5_side = _make_criterion(
            "Stateless & side-effect safety", 3, 5,
            "No global mutation detected, though side-effect safety could not be verified across repeated test calls.",
            f"Fix Line {err_line or 1} so repeated test invocations verify clean isolation.",
            target_line=err_line,
        )
    else:
        c5_side = _make_criterion(
            "Stateless & side-effect safety", 5, 5,
            "Self-contained function with isolated per-call state and zero global side effects across repeated runs.",
        )

    # 5.3 Extensibility for Part 2 / Part 3 follow-ups (5 pts)
    if is_skeleton:
        c5_ext = _make_criterion(
            "Generalisation & follow-up readiness", 0, 5,
            "No general algorithm implemented yet.",
            f"Build a general `{opt_time}` solution ready for the follow-up twist: {followup_q}",
        )
    elif user_m["hasHardcodedReturn"]:
        c5_ext = _make_criterion(
            "Generalisation & follow-up readiness", 0, 5,
            "Detected hardcoded input comparisons instead of general algorithmic logic.",
            "Remove input-specific `if` branches and implement the general invariant across arbitrary inputs.",
        )
    elif all_passed and not is_suboptimal_nested:
        c5_ext = _make_criterion(
            "Generalisation & follow-up readiness", 5, 5,
            f"Generalises cleanly across all {total_cnt} visible and hidden inputs with optimal `{opt_time}` scaling ready for Part 2 extensions.",
        )
    elif all_passed and is_suboptimal_nested:
        c5_ext = _make_criterion(
            "Generalisation & follow-up readiness", 3, 5,
            f"Generalises functionally, but `{brute_time}` complexity will break under production scale or streaming follow-ups.",
            f"Upgrade to `{opt_time}` so the design scales cleanly for follow-up requirements ({followup_q}).",
        )
    else:
        c5_ext = _make_criterion(
            "Generalisation & follow-up readiness", 2 if passed_cnt > 0 else 0, 5,
            f"Currently passes {passed_cnt}/{total_cnt} inputs; edge cases must pass before extending for follow-up twists.",
            f"Pass all {total_cnt} tests first so your core invariant is solid before tackling: {followup_q}",
            target_line=fail_line,
        )

    # 5.4 Production polish & defensive readiness (4 pts)
    if is_skeleton:
        c5_def = _make_criterion(
            "Production polish & defensive readiness", 0, 4,
            "Starter template needs full implementation before production review.",
            "Write clean, debug-free, edge-safe code that handles malformed or boundary inputs gracefully.",
        )
    else:
        def_pts = 4
        def_issues: list[str] = []
        def_fixes: list[str] = []
        def_line: int | None = None
        if not all_passed:
            def_pts -= 2
            def_issues.append(f"{total_cnt - passed_cnt} failing test case{'s' if (total_cnt - passed_cnt) != 1 else ''}")
            def_fixes.append("resolve all failing visible and hidden test cases")
            def_line = fail_line
        if user_m["debugPrintLines"]:
            def_pts -= 1
            def_issues.append(f"console/print logging left on Line {user_m['debugPrintLines'][0]}")
            def_fixes.append(f"strip debug logging on Line {user_m['debugPrintLines'][0]}")
            def_line = def_line or user_m["debugPrintLines"][0]
        if not user_m["hasTypeAnnotations"] or user_m["hasBareExcept"]:
            def_pts -= 1
            if not user_m["hasTypeAnnotations"]:
                def_issues.append("untyped function contract")
                def_fixes.append("keep explicit parameter and return types for a clear API contract")
            if user_m["hasBareExcept"]:
                def_issues.append("bare `except:` swallowing errors")
                def_fixes.append("narrow exception handling to explicit error types")

        if not def_issues:
            c5_def = _make_criterion(
                "Production polish & defensive readiness", 4, 4,
                "Typed contract, zero debug clutter, and verified resilience across all visible and hidden edge cases.",
            )
        else:
            c5_def = _make_criterion(
                "Production polish & defensive readiness", max(0, def_pts), 4,
                "Production gaps found: " + ", ".join(def_issues) + ".",
                "Polish before sign-off: " + "; ".join(def_fixes) + ".",
                target_line=def_line,
            )

    axis_fde = _build_axis_entry(
        "FDE Production & Extensibility",
        [c5_sep, c5_side, c5_ext, c5_def],
        "Clean modular flow, zero side effects, optimal scaling, and production-grade typed contract.",
    )

    rubric = [axis_dsa, axis_prog, axis_comp, axis_debug, axis_fde]
    total_score = sum(a["score"] for a in rubric)
    points_to_full = 100 - total_score

    # Build a ranked, actionable "How to reach 100 / 100" plan across all axes
    improvement_plan = _build_improvement_plan(rubric, run_ok=run_ok)

    if total_score == 100 and all_passed:
        hiring_signal = "Strong Hire (Full Marks: 100 / 100)"
    elif total_score >= 88 and all_passed:
        hiring_signal = "Strong Hire / Hire (Close to Full Marks)"
    elif total_score >= 72:
        hiring_signal = "Leaning Hire (Solid foundation; close the gaps below)"
    elif is_skeleton:
        hiring_signal = "Starter Skeleton (Unfold Step 1 & Step 2 above to begin)"
    else:
        hiring_signal = "In Progress (Fix the priority items below)"

    if is_skeleton:
        diagnosis = (
            f"Score is {total_score}/100 because `{func_name}` is still a starter template (only the typed function header is scored so far). "
            f"Implement the `{primary_tag}` invariant to unlock the remaining +{points_to_full} points."
        )
    elif total_score == 100:
        diagnosis = (
            f"Full marks ({total_score}/100) across all 5 SWE & FDE axes. Every visible and hidden test passes in optimal `{opt_time}` structure "
            "with clean types, readable naming, and zero edge-case gaps. Next challenge: narrate Time/Space complexity aloud and tackle the Follow-Up Twist."
        )
    elif not run_ok:
        diagnosis = (
            f"Score is {total_score}/100 (+{points_to_full} pts available) because execution stopped at Line {err_line or 1} (`{err_msg[:120]}`). "
            "Fixing that single line unlocks correctness, edge-case, and execution points immediately."
        )
    elif not all_passed:
        diagnosis = (
            f"Score is {total_score}/100 (+{points_to_full} pts available). Your code passes {passed_cnt}/{total_cnt} tests "
            f"({vis_passed}/{vis_total} visible, {hid_passed}/{hid_total} hidden). Follow the ranked fixes below to reach 100/100."
        )
    else:
        weakest_axes = [f"{a['axis']} (-{a['pointsToFullMarks']} pts)" for a in rubric if a["pointsToFullMarks"] > 0]
        diagnosis = (
            f"All {total_cnt} tests pass, scoring {total_score}/100 (+{points_to_full} pts to full marks). "
            f"Points were deducted on: {', '.join(weakest_axes)}. Apply the concrete fixes below to hit 100/100."
        )

    socratic_prompt = (
        f"I am working on Day {day} ({prob['leetcodeId']}: {prob['title']}) in {language}.\n\n"
        f"Here is my current code:\n```{language}\n{code.strip()}\n```\n\n"
        f"Test result: {passed_cnt}/{total_cnt} passed. Current 5-Axis Rubric Score: {total_score}/100.\n"
        "Please coach me like a SWE/FDE interviewer: explain why I got this score, show how to fix the remaining rubric gaps to reach 100/100, "
        "and ask me one follow-up twist."
    )

    return {
        "ok": True,
        "day": day,
        "language": language,
        "analysedCode": code,
        "totalScore": total_score,
        "pointsToFullMarks": points_to_full,
        "hiringSignal": hiring_signal,
        "runResult": run_res,
        "diagnosis": diagnosis,
        "followUpStretch": followup_q,
        "improvementPlan": improvement_plan,
        "thinkingShift": {
            "instinctiveTrap": mm["instinctiveTrap"],
            "optimalPivot": mm["optimalPivot"],
            "triggerSignal": mm["triggerSignal"],
        },
        "rubric": rubric,
        "structuralSignals": {
            "maxLoopDepth": user_m["maxLoopDepth"],
            "refLoopDepth": ref_loop_depth,
            "isSuboptimalNested": is_suboptimal_nested,
            "usesHash": user_m["usesHash"],
            "usesHeap": user_m["usesHeap"],
            "usesStackQueue": user_m["usesStackQueue"],
            "usesSort": user_m["usesSort"],
            "usesBinarySearch": user_m["usesBinarySearch"],
            "hasEdgeGuard": user_m["hasEdgeGuard"],
            "hasTypeAnnotations": user_m["hasTypeAnnotations"],
            "debugPrintLines": user_m["debugPrintLines"],
            "declaredVars": user_m["declaredVars"][:8],
        },
        "chatPrompt": socratic_prompt,
    }


def analyse_curated_code(problem_id: str, language: str, code: str) -> dict[str, Any]:
    """Transparent 5-axis 20-check rubric analyser for Grind 75, LC 150, NeetCode 150, and SQL 50 problems."""
    prob = cl.get_problem(problem_id)
    if not prob:
        return {"ok": False, "error": f"Unknown curated problem '{problem_id}'"}

    is_sql = bool(prob.get("isSql")) or str(language).lower() == "sql"
    stripped = code.strip()
    starter = (prob.get("starterCode") or {}).get("sql" if is_sql else "python", "").strip()
    lines = [ln for ln in stripped.splitlines() if ln.strip() and not ln.strip().startswith(("#", "--", "//"))]
    is_skeleton = (
        not lines
        or stripped == starter
        or (not is_sql and ("pass" in stripped and len(lines) <= 4))
        or (is_sql and stripped.rstrip(";").strip().upper() == "SELECT")
    )

    if is_sql:
        run_res = cl.execute_curated_sql(prob, code) if not is_skeleton else {
            "ok": True, "isSql": True, "passed": 0, "total": max(1, len(prob.get("testCases") or [])),
            "allPassed": False, "results": [], "isSkeleton": True,
        }
        all_passed = bool(run_res.get("allPassed"))
        first_err = run_res.get("error") or ""
        sql_up = stripped.upper()
        has_select = "SELECT " in sql_up or "DELETE " in sql_up
        has_from = "FROM " in sql_up
        has_join_or_agg = any(k in sql_up for k in ("JOIN ", "GROUP BY", "OVER(", "OVER (", "WITH ", "UNION", "HAVING", "WHERE "))
        has_explicit_cols = has_select and ("SELECT *" not in sql_up or "DELETE " in sql_up)
        has_null_or_guard = any(k in sql_up for k in ("IS NULL", "IS NOT NULL", "COALESCE", "IFNULL", "CASE ", "WHERE ", "HAVING ", "DISTINCT", "ROUND("))
        followup_q = prob.get("interviewFollowUp", {}).get("question", "How would you index these tables for 100M rows?")

        c1_match = _make_criterion("Query result accuracy", 8 if all_passed else 0, 8, "Output table matches expected rows and columns." if all_passed else (f"SQL error: `{first_err[:100]}`" if first_err else "Returned rows do not match expected result set."), "Compare actual vs expected tables in the Test Console and adjust joins, filters, or aliases.", target_line=1 if not all_passed else None)
        c1_rel = _make_criterion("Relational pattern & clauses", 6 if (all_passed and has_from) else (3 if has_join_or_agg else 0), 6, "Uses appropriate relational clauses (`FROM` / `JOIN` / `GROUP BY` / `WINDOW`)." if has_from else "Missing core relational query structure.", f"Apply the target SQL pattern: {prob['mentalModel']['optimalPivot']}")
        c1_eff = _make_criterion("Set-based efficiency", 6 if all_passed else (2 if has_select else 0), 6, "Set-based SQL executes cleanly in sub-millisecond time." if all_passed else "Query is not yet passing against the seeded dataset.", "Avoid correlated row-by-row subqueries where a single JOIN or window function suffices.")
        ax1 = _build_axis_entry("Data Structures & Algorithms", [c1_match, c1_rel, c1_eff], "Accurate, set-based relational query matching expected results.")

        c2_syn = _make_criterion("Valid SQLite syntax", 7 if (not is_skeleton and not first_err) else (2 if is_skeleton else 0), 7, "Parses and executes with zero SQLite syntax errors." if (not is_skeleton and not first_err) else (first_err or "Starter SQL template has no query yet."), "Fix SQLite syntax and ensure column/table names match the schema.", target_line=1)
        c2_cols = _make_criterion("Explicit column projection", 7 if (not is_skeleton and has_explicit_cols) else (3 if has_select else 0), 7, "Explicitly projects required output columns rather than `SELECT *`." if has_explicit_cols else "Specify explicit output columns and aliases matching expected headers.", "List exact output columns (`AS alias`) instead of `SELECT *`.")
        c2_fmt = _make_criterion("Readable clause formatting", 6 if len(lines) >= 2 else (3 if not is_skeleton else 0), 6, "Clean multi-line SQL formatting." if len(lines) >= 2 else "Compact or empty query.", "Break `SELECT`, `FROM`, `JOIN`, `WHERE`, and `GROUP BY` onto clear lines.")
        ax2 = _build_axis_entry("Programming & Language Idioms", [c2_syn, c2_cols, c2_fmt], "Clean, idiomatic SQL syntax with explicit column projections.")

        c3_null = _make_criterion("NULL & empty-group safety", 10 if all_passed else (4 if has_null_or_guard else 0), 10, "Handles NULL values, zero-division, and missing join matches cleanly." if all_passed else "Check `LEFT JOIN`, `COALESCE`/`IFNULL`, and `IS NOT NULL` filters.", "Ensure outer joins and `NULL` comparisons use `IS NULL` / `COALESCE` instead of `= NULL`.")
        c3_ord = _make_criterion("Aggregation & tie handling", 10 if all_passed else (3 if has_join_or_agg else 0), 10, "Verified exact row grain, duplicates, and rounding." if all_passed else "Verify `GROUP BY` grain, `DISTINCT`, and float division (`* 1.0`).", "Check whether `DISTINCT`, `ROUND(..., 2)`, or `* 1.0` float cast is required.")
        ax3 = _build_axis_entry("Code Comprehension & Edge Cases", [c3_null, c3_ord], "Verified NULL safety, join grain, and rounding accuracy.")

        c4_exec = _make_criterion("Clean execution & row inspection", 10 if all_passed else (3 if (not is_skeleton and not first_err) else 0), 10, "Executed with zero SQL errors and matching row count." if all_passed else "Inspect actual vs expected SQL output tables below.", "Compare column names, row count, and NULL cells in the SQL result table.")
        c4_cte = _make_criterion("Traceable query stages", 10 if (all_passed and len(lines) >= 2) else (5 if not is_skeleton else 0), 10, "Easy to dry-run table by table." if (all_passed and len(lines) >= 2) else "Structure intermediate filters cleanly so each step is verifiable.", "Use readable aliases or a CTE (`WITH ... AS (...)`) for multi-step logic.")
        ax4 = _build_axis_entry("Dry-Run & Debugging Readiness", [c4_exec, c4_cte], "Clear, easily verifiable SQL execution stages.")

        c5_idx = _make_criterion("Production & index friendliness", 10 if all_passed else (4 if has_from else 0), 10, "Avoids unnecessary table mutations and scales cleanly with B-tree indexes." if all_passed else "Keep predicates sargable (avoid wrapping indexed columns in functions where possible).", "Ensure filter predicates can leverage composite indexes cleanly.")
        c5_ext = _make_criterion("Schema contract & extensibility", 10 if (all_passed and has_explicit_cols) else (4 if not is_skeleton else 0), 10, "Explicit column contract survives upstream schema changes cleanly." if (all_passed and has_explicit_cols) else "Project explicit columns so schema additions never break downstream consumers.", f"Be ready for follow-up scale questions: {followup_q}")
        ax5 = _build_axis_entry("FDE Production & Extensibility", [c5_idx, c5_ext], "Production-ready SQL contract with index-friendly predicates.")

        rubric = [ax1, ax2, ax3, ax4, ax5]
        total_score = sum(a["score"] for a in rubric)
        points_to_full = 100 - total_score
        improvement_plan = _build_improvement_plan(rubric, run_ok=True)
        hiring_signal = "Strong Hire (Full Marks: 100 / 100)" if total_score == 100 else ("Leaning Hire (Refine SQL gaps below)" if total_score >= 70 else ("Starter SQL Template" if is_skeleton else "In Progress"))
        diagnosis = (
            "Full marks (100/100) on SQL 50! Every column, row, and edge case matches the SQLite dataset."
            if total_score == 100
            else f"Score is {total_score}/100 (+{points_to_full} pts available). Follow the priority SQL improvements below to hit 100/100."
        )
        return {
            "ok": True, "problemId": problem_id, "language": "sql", "analysedCode": code,
            "totalScore": total_score, "pointsToFullMarks": points_to_full, "hiringSignal": hiring_signal,
            "runResult": run_res, "diagnosis": diagnosis, "followUpStretch": followup_q,
            "improvementPlan": improvement_plan, "rubric": rubric,
            "thinkingShift": prob.get("mentalModel", {}),
            "chatPrompt": f"I am solving SQL 50 {prob['leetcodeId']}: {prob['title']}. Score: {total_score}/100.\n```sql\n{stripped}\n```\nExplain how to reach 100/100.",
        }

    # Python curated DSA problem: run full curated harness and compute transparent 5-axis 20-check rubric
    run_res = cl.execute_curated_python(prob, code, capture_frames=False) if not is_skeleton else {
        "ok": True, "passed": 0, "total": len(prob.get("testCases") or []),
        "visiblePassed": 0, "visibleTotal": len(prob.get("testCases") or []),
        "hiddenPassed": 0, "hiddenTotal": 0, "allPassed": False, "results": [], "isSkeleton": True,
    }
    func_name = prob.get("funcName") or prob.get("harness", {}).get("methodName", "solve")
    ref_code = (prob.get("solutionCode") or {}).get("python", "")
    user_m = _compute_code_metrics("python", code, func_name)
    ref_m = _compute_code_metrics("python", ref_code, func_name)
    # For class Solution / class-design methods, detect def inside class body too
    if not user_m["hasFuncDef"] and re.search(rf"\b(?:def\s+{re.escape(func_name)}|class\s+{re.escape(func_name)})\b", code):
        user_m["hasFuncDef"] = True
        user_m["hasTypeAnnotations"] = bool(re.search(r"def\s+\w+\s*\([^)]*:\s*[^)]+\)\s*->", code)) or ("class " in code and "def __init__" in code)
        user_m["hasReturnStmt"] = bool(re.search(r"\breturn\b", code)) or prob.get("harness", {}).get("returnType") == "void"

    run_ok = bool(run_res.get("ok"))
    all_passed = bool(run_res.get("allPassed")) and run_ok
    passed_cnt = int(run_res.get("passed", 0))
    total_cnt = max(1, int(run_res.get("total", len(prob.get("testCases") or []))))
    results_list = run_res.get("results") or []
    first_fail = next((r for r in results_list if not r.get("passed")), None)
    err_line = run_res.get("errorLine") or (first_fail.get("errorLine") if first_fail else None)
    err_msg = run_res.get("error") or (first_fail.get("error") if first_fail else "")
    fail_line = err_line or (first_fail.get("suspectLine") if first_fail else None)
    max_ms = max((float(r.get("runtimeMs") or 0.0) for r in results_list), default=0.0)
    opt_time = prob.get("complexity", {}).get("optimalTime", "O(N)")
    ref_loop_depth = max(1, ref_m["maxLoopDepth"])
    is_suboptimal_nested = (
        not is_skeleton and user_m["syntaxParseOk"] and user_m["maxLoopDepth"] > ref_loop_depth
        and "O(N^2)" not in opt_time and "O(N^3)" not in opt_time
    )
    mm = prob.get("mentalModel") or {"optimalPivot": "Use the optimal pattern.", "instinctiveTrap": "Avoid brute force.", "triggerSignal": ""}
    followup_q = prob.get("interviewFollowUp", {}).get("question", "")
    primary_tag = (prob.get("tags") or ["Core Pattern"])[0]

    c1_pass = _make_criterion("Test suite correctness", 8 if all_passed else (0 if (is_skeleton or not run_ok) else max(1, int(round(7 * passed_cnt / total_cnt)))), 8, f"Passed {passed_cnt}/{total_cnt} test cases." if not is_skeleton else "Starter template has no implementation yet.", f"Fix failing test cases (around Line {fail_line or 1}) until all {total_cnt} pass.", target_line=fail_line)
    c1_comp = _make_criterion("Optimal time-complexity structure", 0 if (is_skeleton or not user_m["syntaxParseOk"]) else (2 if is_suboptimal_nested else (6 if all_passed else 4)), 6, f"Loop depth {user_m['maxLoopDepth']} matches target `{opt_time}`." if not is_suboptimal_nested else f"Loop depth {user_m['maxLoopDepth']} exceeds optimal depth {ref_loop_depth} for `{opt_time}`.", f"Optimise toward `{opt_time}`: {mm['optimalPivot']}", target_line=err_line)
    c1_pat = _make_criterion("Core pattern & efficiency", 6 if (all_passed and not is_suboptimal_nested and max_ms < 400) else (3 if (not is_skeleton and passed_cnt > 0) else 0), 6, f"All {total_cnt} tests pass quickly (peak {max_ms:.2f} ms) using `{primary_tag}`." if (all_passed and not is_suboptimal_nested) else f"Align implementation with `{primary_tag}` invariant.", mm["optimalPivot"])
    ax1 = _build_axis_entry("Data Structures & Algorithms", [c1_pass, c1_comp, c1_pat], f"Passes all {total_cnt} tests in optimal `{opt_time}` structure.")

    c2_syn = _make_criterion("Clean compilation & syntax", 5 if (not is_skeleton and run_ok) else (2 if is_skeleton else 0), 5, "Compiles and runs cleanly in Python 3." if (not is_skeleton and run_ok) else (err_msg or "Starter placeholder."), f"Fix syntax or runtime issue on Line {err_line or 1}.", target_line=err_line)
    c2_sig = _make_criterion("Method signature & types", 5 if (user_m["hasFuncDef"] and user_m["hasTypeAnnotations"]) else (3 if user_m["hasFuncDef"] else 0), 5, f"Preserved `{func_name}` with clean type annotations." if user_m["hasTypeAnnotations"] else f"Add parameter and return type annotations on `{func_name}`.", "Keep complete Python type annotations on the method signature.", target_line=1)
    c2_idiom = _make_criterion("Idiomatic Python constructs", 5 if (not is_skeleton and (user_m["usesIdiomatic"] or all_passed)) else (0 if is_skeleton else 3), 5, "Clean, idiomatic Python style." if not is_skeleton else "Pending implementation.", "Use Pythonic helpers (`enumerate`, `.get()`, `deque`, comprehensions).")
    has_dbg = bool(user_m["debugPrintLines"])
    c2_clean = _make_criterion("Clean naming & zero debug prints", 0 if is_skeleton else (3 if has_dbg else 5), 5, f"Found debug print on Line {user_m['debugPrintLines'][0]}." if has_dbg else "Clean local naming with zero debug clutter.", f"Remove debug `print()` on Line {user_m['debugPrintLines'][0]}." if has_dbg else "Declare descriptive local state names.", target_line=user_m["debugPrintLines"][0] if has_dbg else None)
    ax2 = _build_axis_entry("Programming & Language Idioms", [c2_syn, c2_sig, c2_idiom, c2_clean], "Clean Python syntax, typed signature, idiomatic constructs, and zero debug prints.")

    c3_cases = _make_criterion("Full test & edge-case pass", 10 if all_passed else (0 if (is_skeleton or not run_ok) else max(1, int(round(8 * passed_cnt / total_cnt)))), 10, f"Cleared all {passed_cnt}/{total_cnt} problem test cases." if all_passed else f"Passed {passed_cnt}/{total_cnt}; check boundary inputs.", "Verify empty, single-element, duplicate, and boundary cases.", target_line=fail_line)
    c3_ret = _make_criterion("Complete return & invariant safety", 10 if (all_passed and user_m["hasReturnStmt"]) else (4 if user_m["hasReturnStmt"] else 0), 10, "Every execution path returns the expected structure cleanly." if all_passed else "Ensure all branches return or update the expected output structure.", "Add an explicit base-case or fallback return statement.", target_line=fail_line)
    ax3 = _build_axis_entry("Code Comprehension & Edge Cases", [c3_cases, c3_ret], "Passed all cases with safe boundary and return-path handling.")

    c4_exec = _make_criterion("Zero runtime exceptions", 10 if all_passed else (4 if (not is_skeleton and run_ok) else 0), 10, "Zero crashes or bounds errors." if all_passed else (err_msg or "Step through failing inputs in the Python Tutor visualiser."), f"Trace Line {fail_line or 1} in the side-by-side Python Tutor visualiser.", target_line=fail_line)
    c4_clean = _make_criterion("Zero shadowing & traceable flow", 10 if (not is_skeleton and not user_m["shadowedBuiltins"] and not user_m["hasBareExcept"]) else (0 if is_skeleton else 6), 10, "Clean traceable flow with zero built-in shadowing." if (not is_skeleton and not user_m["shadowedBuiltins"]) else "Check for built-in shadowing or bare except.", "Avoid shadowing built-ins (`list`, `dict`, `sum`, `max`) or bare `except:`.")
    ax4 = _build_axis_entry("Dry-Run & Debugging Readiness", [c4_exec, c4_clean], "Zero runtime faults and clean step-by-step dry-run clarity.")

    c5_mod = _make_criterion("Clean structure & isolation", 10 if (all_passed and not user_m["hasGlobalStmt"]) else (4 if not is_skeleton else 0), 10, "Self-contained, stateless per-call design." if all_passed else "Keep mutable state local and structure setup -> loop -> return cleanly.", "Keep state local to the class/method with shallow control nesting.")
    c5_ext = _make_criterion("Follow-up & production readiness", 10 if (all_passed and not is_suboptimal_nested and not has_dbg and user_m["hasTypeAnnotations"]) else (5 if all_passed else (2 if not is_skeleton else 0)), 10, f"Ready to extend for follow-up twist: {followup_q}" if all_passed else "Pass all tests with optimal complexity and typed contract first.", f"Ensure optimal `{opt_time}` complexity, clean types, and zero debug logs.")
    ax5 = _build_axis_entry("FDE Production & Extensibility", [c5_mod, c5_ext], "Clean, stateless, optimal design ready for follow-up extensions.")

    rubric = [ax1, ax2, ax3, ax4, ax5]
    total_score = sum(a["score"] for a in rubric)
    points_to_full = 100 - total_score
    improvement_plan = _build_improvement_plan(rubric, run_ok=run_ok)

    hiring_signal = (
        "Strong Hire (Full Marks: 100 / 100)" if total_score == 100 and all_passed
        else ("Strong Hire / Hire (Close to Full Marks)" if total_score >= 88 and all_passed
              else ("Leaning Hire (Close the gaps below)" if total_score >= 72
                    else ("Starter Skeleton" if is_skeleton else "In Progress")))
    )
    diagnosis = (
        f"Full marks (100/100) on {prob['leetcodeId']}: {prob['title']}! All {total_cnt} tests pass in optimal `{opt_time}` structure."
        if total_score == 100
        else f"Score is {total_score}/100 (+{points_to_full} pts available). Passing {passed_cnt}/{total_cnt} tests. Apply the fixes below to hit 100/100."
    )
    return {
        "ok": True, "problemId": problem_id, "language": "python", "analysedCode": code,
        "totalScore": total_score, "pointsToFullMarks": points_to_full, "hiringSignal": hiring_signal,
        "runResult": run_res, "diagnosis": diagnosis, "followUpStretch": followup_q,
        "improvementPlan": improvement_plan, "rubric": rubric, "thinkingShift": mm,
        "chatPrompt": f"I am solving {prob['leetcodeId']}: {prob['title']}. Score: {total_score}/100.\n```python\n{stripped}\n```\nExplain how to reach 100/100.",
    }


def diagnose_curated_in_chat(
    problem_id: str,
    language: str,
    code: str,
    user_message: str,
    model_mode: str = "flash",
    prompt_mode: str = "full_tutor",
) -> dict[str, Any]:
    """AI Co-Pilot handler for Grind 75, LC 150, NeetCode 150, and SQL 50 problems."""
    prob = cl.get_problem(problem_id)
    if not prob:
        return {"ok": False, "error": f"Unknown curated problem '{problem_id}'"}
    prog = load_progress(auto_advance=False)
    hist = prog.setdefault("chatHistory", {}).setdefault(problem_id, [])
    analysis = analyse_curated_code(problem_id, language, code)
    run_res = analysis.get("runResult") or {}
    mm = prob.get("mentalModel") or {}
    exec_frames = run_res.get("executionFrames") or []

    # Try optional Gemini API (if GEMINI_API_KEY is set and online); otherwise use built-in offline mentor
    prob_for_llm = {**prob, "day": 0}
    mode_prefix = {
        "hints_only": "[STRICT MODE: HINTS ONLY - Do NOT give the full code solution. Give Socratic nudges only.]\n",
        "debug_bug": "[MODE: DEBUG BUG - Pinpoint the exact bug, line, and expected vs actual mismatch.]\n",
        "explain_complexity": "[MODE: EXPLAIN COMPLEXITY - Derive exact Time and Space Big-O vs optimal.]\n",
        "visualize_trace": "[MODE: VISUALISE TRACE - Walk through a concrete step-by-step state table on Case 1.]\n",
    }.get(prompt_mode, "")
    gemini_reply = _call_gemini_coach(
        prob=prob_for_llm,
        language=language,
        code=code,
        user_message=mode_prefix + user_message,
        run_res=run_res,
        analysis=analysis,
        history=hist,
        model_mode=model_mode,
    )
    if gemini_reply:
        reply_text = gemini_reply
    else:
        top_gaps = analysis.get("improvementPlan", [])[:3]
        if prompt_mode == "hints_only":
            hints = prob.get("hints") or [mm.get("optimalPivot", "")]
            reply_text = (
                f"Socratic nudge for {prob['leetcodeId']}: {prob['title']} (no full code):\n"
                f"- Hint 1: {hints[0]}\n"
                f"- Core invariant: {mm.get('optimalPivot', '')}\n"
                f"- Check your current tests ({run_res.get('passed', 0)}/{run_res.get('total', 0)} passed): where does your state first diverge?"
            )
        elif run_res.get("allPassed"):
            reply_text = (
                f"All {run_res.get('total', 0)} test cases pass for {prob['title']} (`{analysis.get('totalScore')}/100` rubric score).\n"
                f"- Target complexity: `{prob['complexity']['optimalTime']}` time, `{prob['complexity']['optimalSpace']}` space.\n"
                f"- Interviewer follow-up: {prob.get('interviewFollowUp', {}).get('question', '')}"
            )
        else:
            gap_lines = "\n".join(f"- `+{g['gain']} pts` ({g['criterion']}): {g['howToImprove']}" for g in top_gaps)
            reply_text = (
                f"{analysis.get('diagnosis', '')}\n\n"
                f"Key invariant: {mm.get('optimalPivot', '')}\n"
                + (f"\nPriority fixes:\n{gap_lines}" if gap_lines else "")
            )

    highlight_line = run_res.get("errorLine") or run_res.get("highlightLine")
    with _PROGRESS_LOCK:
        prog = load_progress(auto_advance=False)
        hist = prog.setdefault("chatHistory", {}).setdefault(problem_id, [])
        hist.append({"role": "user", "text": user_message, "model": model_mode})
        hist.append({
            "role": "assistant",
            "text": reply_text,
            "highlightLine": highlight_line,
            "modelUsed": f"{model_mode.capitalize()} Co-Pilot ({prompt_mode.replace('_', ' ')})",
        })
        prog["chatHistory"][problem_id] = hist[-20:]
        save_progress(prog)
        saved_hist = prog["chatHistory"][problem_id]
    return {
        "ok": True,
        "reply": reply_text,
        "modelUsed": f"{model_mode.capitalize()} Co-Pilot",
        "highlightLine": highlight_line,
        "executionFrames": exec_frames,
        "runResult": run_res,
        "analysis": analysis,
        "history": saved_hist,
    }


def check_user_approach(day: int, approach_text: str, problem_id: str | None = None) -> dict[str, Any]:
    prob = cl.get_problem(problem_id) if problem_id else cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown problem {problem_id or day}"}
    txt = (approach_text or "").strip()
    if len(txt) < 6:
        return {
            "ok": True,
            "verdict": "needs_detail",
            "badge": "Add 1-2 sentences",
            "summary": "Describe your planned data structure and time/space complexity in one or two sentences before coding.",
            "targetTime": prob["complexity"]["optimalTime"],
            "targetSpace": prob["complexity"]["optimalSpace"],
        }

    low = txt.lower()
    mm = prob["mentalModel"]
    opt_pivot = mm["optimalPivot"]
    trap = mm["instinctiveTrap"]
    inv = mm.get("triggerSignal", opt_pivot)
    opt_time = prob["complexity"]["optimalTime"]
    opt_space = prob["complexity"]["optimalSpace"]
    tags_low = [t.lower() for t in prob.get("tags", [])]

    key_signals = []
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("hash", "map", "dict", "set", "complement")):
        key_signals.extend(["hash", "map", "dict", "set", "seen", "complement", "lookup", "o(1)"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("two pointer", "sliding window", "left", "right", "window")):
        key_signals.extend(["pointer", "window", "left", "right", "shrink", "expand", "two-pointer"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("binary search", "monotonic", "mid", "bisect")):
        key_signals.extend(["binary search", "mid", "low", "high", "monotonic", "log"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("stack", "monotonic stack", "lifo")):
        key_signals.extend(["stack", "monotonic", "push", "pop"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("heap", "priority", "top k", "k-way")):
        key_signals.extend(["heap", "priority", "heapq", "min-heap", "max-heap", "log k"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("dfs", "bfs", "tree", "graph", "recursion", "backtrack", "topological", "union")):
        key_signals.extend(["dfs", "bfs", "queue", "recurs", "tree", "graph", "visited", "indegree", "union", "backtrack"])
    if any(k in opt_pivot.lower() or k in " ".join(tags_low) for k in ("dp", "dynamic", "memo", "state", "subproblem", "greedy")):
        key_signals.extend(["dp", "dynamic", "memo", "state", "transition", "greedy", "prefix", "subproblem"])

    matched = [s for s in dict.fromkeys(key_signals) if s in low]
    mentions_brute = any(w in low for w in ("nested loop", "brute force", "all pairs", "o(n^2)", "every pair", "try all"))

    if mentions_brute and not matched:
        verdict = "suboptimal_trap"
        badge = f"Watch Out: {prob['complexity']['bruteTime']} Trap"
        summary = (
            f"Your plan sounds close to the brute-force trap ({trap}). "
            f"To hit `{opt_time}` time and `{opt_space}` space, pivot to: {opt_pivot} "
            f"Key invariant: {inv}"
        )
    elif matched:
        verdict = "optimal_aligned"
        badge = f"Aligned with {opt_time} Optimal"
        summary = (
            f"Strong pre-code plan. You identified the core mechanism ({', '.join(matched[:4])}) needed for `{opt_time}` time and `{opt_space}` space. "
            f"Keep this invariant locked while coding: {inv}"
        )
    else:
        verdict = "partial_pivot"
        badge = f"Check Invariant ({opt_time})"
        summary = (
            f"Good start, though make sure your data structure directly enforces `{opt_time}` time. "
            f"Optimal pivot: {opt_pivot} "
            f"Core invariant to maintain: {inv}"
        )

    return {
        "ok": True,
        "verdict": verdict,
        "badge": badge,
        "summary": summary,
        "targetTime": opt_time,
        "targetSpace": opt_space,
        "keyInvariant": inv,
    }


def run_fde_stress_test(day: int, language: str, code: str) -> dict[str, Any]:
    import copy
    prob = cd.PROBLEMS_BY_DAY.get(day)
    if not prob:
        return {"ok": False, "error": f"Unknown Day {day}"}
    base_cases = prob.get("testCases", [])
    if not base_cases:
        return {"ok": False, "error": "No baseline test cases available"}

    first_args = copy.deepcopy(base_cases[0]["args"])
    stress_args_list: list[tuple[str, list[Any]]] = []

    # 1. Minimal / Boundary input
    bound_args = copy.deepcopy(base_cases[-1]["args"])
    stress_args_list.append(("Boundary / Minimal Case", bound_args))

    # 2. Duplicate / Adversarial values if list-based
    adv_args = copy.deepcopy(first_args)
    for i, a in enumerate(adv_args):
        if isinstance(a, list) and len(a) >= 2 and all(isinstance(x, int) for x in a):
            adv_args[i] = list(reversed(a))
            break
    stress_args_list.append(("Reversed / Permuted Order", adv_args))

    # 3. Scaled-up FDE Throughput Benchmark (synthesised from reference solution)
    scale_args = copy.deepcopy(first_args)
    scaled_changed = False
    for i, a in enumerate(scale_args):
        if isinstance(a, list) and a and all(isinstance(x, int) for x in a):
            # Expand list deterministically while keeping values realistic
            base_len = len(a)
            if base_len >= 2:
                extra = [(a[j % base_len] + (j + 1) * 97) for j in range(min(180, max(30, base_len * 15)))]
                scale_args[i] = extra + a
                scaled_changed = True
                break
        elif isinstance(a, str) and len(a) >= 2:
            scale_args[i] = a * min(25, max(5, 120 // len(a)))
            scaled_changed = True
            break
    if scaled_changed:
        stress_args_list.append(("FDE Scale & Throughput Benchmark", scale_args))

    suite_results = []
    all_passed = True
    total_ms = 0.0
    for label, s_args in stress_args_list:
        res = execute_user_code(day, language, code, custom_test_args=s_args)
        if not res.get("ok"):
            return res
        tc_res = res.get("results", [None])[-1]
        if tc_res:
            tc_res["stressLabel"] = label
            suite_results.append(tc_res)
            total_ms += float(tc_res.get("runtimeMs", 0.0))
            if not tc_res.get("passed"):
                all_passed = False

    return {
        "ok": True,
        "stressTest": True,
        "passed": len(suite_results) if all_passed else sum(1 for r in suite_results if r.get("passed")),
        "total": len(suite_results),
        "totalRuntimeMs": round(total_ms, 2),
        "results": suite_results,
        "fdeProductionPrompt": prob.get("interviewFollowUp", {}).get("question", ""),
        "optimalTime": prob["complexity"]["optimalTime"],
    }



_MAX_REQUEST_BODY_BYTES = 4 * 1024 * 1024
_MAX_CODE_CHARS = 200_000
_MAX_NOTE_CHARS = 200_000
_MAX_CHAT_MSG_CHARS = 16_000
_MAX_BOOKMARKS = 500
_MAX_DRAFTS_BATCH = 400
_ALLOWED_LANGUAGES = {"python", "typescript", "go", "sql"}


def _parse_int_field(val: Any, default: int = 0, name: str = "value") -> int:
    if isinstance(val, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        return int(val)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid integer for {name}") from exc


def _parse_day_field(val: Any, default: int = 1) -> int:
    d = _parse_int_field(default if val is None else val, name="day")
    max_day = max(120, len(cd.PROBLEMS))
    if d < 1 or d > max_day:
        raise ValueError(f"day must be between 1 and {max_day}")
    return d


def _safe_str(val: Any, max_len: int = 500) -> str:
    return str("" if val is None else val)[:max_len]


def _sanitize_interview_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": _safe_str(raw.get("date", ""), 32),
        "problemId": _safe_str(raw.get("problemId", ""), 80),
        "title": _safe_str(raw.get("title", ""), 160),
        "difficulty": _safe_str(raw.get("difficulty", ""), 32),
        "score": max(0, min(100, _parse_int_field(raw.get("score", 0), name="score"))),
        "signal": _safe_str(raw.get("signal", ""), 120),
        "elapsedMin": max(0, min(600, _parse_int_field(raw.get("elapsedMin", 0), name="elapsedMin"))),
    }


def _sanitize_oa_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": _safe_str(raw.get("date", ""), 32),
        "totalPoints": max(0, min(10000, _parse_int_field(raw.get("totalPoints", 0), name="totalPoints"))),
        "maxPoints": max(1, min(10000, _parse_int_field(raw.get("maxPoints", 300), name="maxPoints"))),
        "passedQuestions": max(0, min(50, _parse_int_field(raw.get("passedQuestions", 0), name="passedQuestions"))),
        "totalQuestions": max(0, min(50, _parse_int_field(raw.get("totalQuestions", 3), name="totalQuestions"))),
        "elapsedMin": max(0, min(600, _parse_int_field(raw.get("elapsedMin", 0), name="elapsedMin"))),
    }


def _save_code_draft(draft_key: str, code: str, current_day: int | None = None) -> None:
    if len(draft_key) > 100 or len(code) > _MAX_CODE_CHARS:
        return
    with _PROGRESS_LOCK:
        prog = load_progress(auto_advance=False)
        prog.setdefault("drafts", {})[draft_key] = code
        if current_day is not None:
            prog["currentDay"] = current_day
        save_progress(prog)


class _ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class AlgoStudioHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        raw_len = self.headers.get("Content-Length", "0") or "0"
        length = int(raw_len)
        if length < 0:
            raise ValueError("Invalid negative Content-Length")
        if length == 0:
            return {}
        if length > _MAX_REQUEST_BODY_BYTES:
            raise ValueError(f"Request body exceeds {_MAX_REQUEST_BODY_BYTES} byte limit")
        raw = self.rfile.read(length)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route in ("/favicon.ico", "/favicon.svg", "/favicon.png", "/apple-touch-icon.png"):
            fav_path = PUBLIC_DIR / "favicon.svg"
            if fav_path.is_file():
                body = fav_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self._send_security_headers()
                self.end_headers()
                self.wfile.write(body)
                return

        if route == "/preload.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", "0")
            self._send_security_headers()
            self.end_headers()
            return

        if route == "/api/health":
            self._send_json({"ok": True, "app": "algo-studio"})
            return

        if route == "/api/export-progress":
            prog = load_progress(auto_advance=False)
            body = (json.dumps(prog, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="algo-studio-progress.json"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(body)
            return

        if route == "/api/curated":
            self._send_json(cl.get_catalog_payload())
            return

        if route == "/api/state":
            qs = parse_qs(parsed.query)
            is_sync = qs.get("sync", ["0"])[0].lower() in ("1", "true", "yes")
            prog = load_progress(auto_advance=not is_sync)
            tag_stats = compute_tag_stats(prog.get("solvedDays", {}))
            sr_insights = compute_spaced_repetition_insights(prog)
            self._send_json({
                "ok": True,
                "progress": prog,
                "phases": cd.PHASES,
                "tags": tag_stats,
                "spacedRepetition": sr_insights,
                "edgeCasePlaybook": cd.EDGE_CASE_PLAYBOOK,
                "edgeCaseResources": cd.EDGE_CASE_RESOURCES,
                "problems": cd.PROBLEMS,
            })
            return

        rel_path = "index.html" if route in ("/", "") else route.lstrip("/")
        try:
            public_root = PUBLIC_DIR.resolve()
            target = (PUBLIC_DIR / rel_path).resolve()
            if not target.is_relative_to(public_root) or not target.is_file():
                self._send_json({"ok": False, "error": "Not found"}, status=404)
                return
            content = target.read_bytes()
        except (OSError, ValueError):
            self._send_json({"ok": False, "error": "Not found"}, status=404)
            return

        ctype, _ = mimetypes.guess_type(str(target))
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Invalid JSON: {exc}"}, status=400)
            return

        try:
            self._handle_post_route(route, body)
        except (ValueError, TypeError) as exc:
            self._send_json({"ok": False, "error": f"Invalid request: {exc}"}, status=400)
        except Exception:
            self._send_json({"ok": False, "error": "Internal server error"}, status=500)

    def _handle_post_route(self, route: str, body: dict[str, Any]) -> None:
        if route == "/api/run":
            problem_id = body.get("problemId")
            lang = _safe_str(body.get("language", "python"), 32).lower()
            code = _safe_str(body.get("code", ""), _MAX_CODE_CHARS)
            custom_args = body.get("customTestArgs")
            is_custom = isinstance(custom_args, list)
            if problem_id:
                pid = _safe_str(problem_id, 100)
                res = cl.execute_curated_problem(
                    pid, lang, code, custom_test_args=custom_args if is_custom else None
                )
                if cl.get_problem(pid) is not None and lang in _ALLOWED_LANGUAGES:
                    with _PROGRESS_LOCK:
                        prog = load_progress(auto_advance=False)
                        prog.setdefault("drafts", {})[f"{pid}:{lang}"] = code
                        save_progress(prog)
                        res["progress"] = prog
                        res["tags"] = compute_tag_stats(prog.get("solvedDays", {}))
                        res["spacedRepetition"] = compute_spaced_repetition_insights(prog)
                self._send_json(res)
                return

            day = _parse_day_field(body.get("day", 1))
            res = execute_user_code(day, lang, code, custom_test_args=custom_args if is_custom else None)
            with _PROGRESS_LOCK:
                prog = load_progress(auto_advance=False)
                if lang in _ALLOWED_LANGUAGES:
                    prog.setdefault("drafts", {})[f"{day}:{lang}"] = code
                prog["currentDay"] = day
                if not res.get("ok") or int(res.get("passed", 0)) < int(res.get("total", 1)):
                    fa = prog.setdefault("failedAttemptsByDay", {})
                    fa[str(day)] = int(fa.get(str(day), 0)) + 1
                save_progress(prog)
                res["progress"] = prog
                res["tags"] = compute_tag_stats(prog.get("solvedDays", {}))
                res["spacedRepetition"] = compute_spaced_repetition_insights(prog)
            self._send_json(res)
            return

        if route == "/api/approach-check":
            day = _parse_day_field(body.get("day", 1))
            problem_id = body.get("problemId")
            approach_text = _safe_str(body.get("approach", ""), _MAX_CHAT_MSG_CHARS)
            self._send_json(check_user_approach(day, approach_text, problem_id=_safe_str(problem_id, 100) if problem_id else None))
            return

        if route == "/api/optimal-trace":
            problem_id = body.get("problemId")
            tc_idx = _parse_int_field(body.get("tcIdx", 0) or 0, name="tcIdx")
            if problem_id:
                self._send_json(cl.trace_curated_optimal(_safe_str(problem_id, 100), tc_idx))
                return
            day = _parse_day_field(body.get("day", 1))
            self._send_json(trace_optimal_solution(day, tc_idx))
            return

        if route == "/api/stress-test":
            day = _parse_day_field(body.get("day", 1))
            lang = _safe_str(body.get("language", "python"), 32).lower()
            code = _safe_str(body.get("code", ""), _MAX_CODE_CHARS)
            self._send_json(run_fde_stress_test(day, lang, code))
            return

        if route == "/api/analyse":
            problem_id = body.get("problemId")
            lang = _safe_str(body.get("language", "python"), 32).lower()
            code = _safe_str(body.get("code", ""), _MAX_CODE_CHARS)
            if problem_id:
                pid = _safe_str(problem_id, 100)
                if cl.get_problem(pid) is not None and lang in _ALLOWED_LANGUAGES:
                    _save_code_draft(f"{pid}:{lang}", code)
                self._send_json(analyse_curated_code(pid, lang, code))
                return
            day = _parse_day_field(body.get("day", 1))
            if lang in _ALLOWED_LANGUAGES:
                _save_code_draft(f"{day}:{lang}", code, current_day=day)
            res = analyse_user_code(day, lang, code)
            self._send_json(res)
            return

        if route == "/api/chat":
            problem_id = body.get("problemId")
            lang = _safe_str(body.get("language", "python"), 32).lower()
            code = _safe_str(body.get("code", ""), _MAX_CODE_CHARS)
            msg = _safe_str(body.get("message", "Diagnose my current code"), _MAX_CHAT_MSG_CHARS)
            model_mode = _safe_str(body.get("model", "flash"), 32).lower()
            prompt_mode = _safe_str(body.get("promptMode", "full_tutor"), 32).lower()
            if problem_id:
                pid = _safe_str(problem_id, 100)
                if cl.get_problem(pid) is not None and lang in _ALLOWED_LANGUAGES:
                    _save_code_draft(f"{pid}:{lang}", code)
                self._send_json(
                    diagnose_curated_in_chat(pid, lang, code, msg, model_mode=model_mode, prompt_mode=prompt_mode)
                )
                return
            day = _parse_day_field(body.get("day", 1))
            if lang in _ALLOWED_LANGUAGES:
                _save_code_draft(f"{day}:{lang}", code, current_day=day)
            mode_prefix = {
                "hints_only": "[Hints Only - Do not reveal full code, give Socratic nudges] ",
                "debug_bug": "[Debug Bug] ",
                "explain_complexity": "[Explain Complexity] ",
                "visualize_trace": "[Visualise Trace] ",
            }.get(prompt_mode, "")
            res = diagnose_in_chat(day, lang, code, mode_prefix + msg, model_mode=model_mode)
            self._send_json(res)
            return

        if route == "/api/progress":
            with _PROGRESS_LOCK:
                prog = load_progress(auto_advance=False)
                if "activeCourse" in body:
                    course_val = _safe_str(body["activeCourse"], 40)
                    if course_val in _ALLOWED_COURSES:
                        prog["activeCourse"] = course_val
                if "courseProblemId" in body:
                    cpid = _safe_str(body["courseProblemId"], 100)
                    course_key = _safe_str(body.get("course") or prog.get("activeCourse") or "", 40)
                    if course_key in _ALLOWED_COURSES and course_key != "schedule-120" and cl.get_problem(cpid) is not None:
                        prog.setdefault("coursePositions", {})[course_key] = cpid
                if "currentDay" in body:
                    prog["currentDay"] = max(1, min(len(cd.PROBLEMS) or 120, _parse_int_field(body["currentDay"], name="currentDay")))
                if "note" in body and "problemId" in body:
                    pid = _safe_str(body["problemId"], 100)
                    if cl.get_problem(pid) is not None:
                        prog.setdefault("notes", {})[pid] = _safe_str(body["note"], _MAX_NOTE_CHARS)
                elif "note" in body and "day" in body:
                    d_int = _parse_day_field(body["day"])
                    prog.setdefault("notes", {})[str(d_int)] = _safe_str(body["note"], _MAX_NOTE_CHARS)
                if "draft" in body and "problemId" in body and "language" in body:
                    pid = _safe_str(body["problemId"], 100)
                    d_lang = _safe_str(body["language"], 32).lower()
                    if cl.get_problem(pid) is not None and d_lang in _ALLOWED_LANGUAGES:
                        prog.setdefault("drafts", {})[f"{pid}:{d_lang}"] = _safe_str(body["draft"], _MAX_CODE_CHARS)
                elif "draft" in body and "day" in body and "language" in body:
                    d_int = _parse_day_field(body["day"])
                    d_lang = _safe_str(body["language"], 32).lower()
                    if d_lang in _ALLOWED_LANGUAGES:
                        prog.setdefault("drafts", {})[f"{d_int}:{d_lang}"] = _safe_str(body["draft"], _MAX_CODE_CHARS)
                if isinstance(body.get("draftsBatch"), dict):
                    drafts_map = prog.setdefault("drafts", {})
                    for dk, dv in list(body["draftsBatch"].items())[:_MAX_DRAFTS_BATCH]:
                        if isinstance(dk, str) and len(dk) <= 100 and isinstance(dv, str) and dv.strip():
                            if dk not in drafts_map or not str(drafts_map.get(dk, "")).strip():
                                drafts_map[dk] = dv[:_MAX_CODE_CHARS]
                if isinstance(body.get("layoutSizes"), dict):
                    ls = prog.setdefault("layoutSizes", {})
                    for lk, lv in list(body["layoutSizes"].items())[:20]:
                        if isinstance(lk, str) and len(lk) <= 64 and isinstance(lv, (int, float)) and not isinstance(lv, bool):
                            ls[lk] = max(0, min(5000, int(lv)))
                if body.get("resetLayout"):
                    prog["layoutSizes"] = {}
                if "revealHiddenDay" in body and "day" in body:
                    d_int = _parse_day_field(body["day"])
                    prog.setdefault("revealedHiddenDays", {})[str(d_int)] = bool(body["revealHiddenDay"])
                if body.get("clearChat") and "problemId" in body:
                    pid = _safe_str(body["problemId"], 100)
                    prog.setdefault("chatHistory", {})[pid] = []
                elif body.get("clearChat") and "day" in body:
                    d_int = _parse_day_field(body["day"])
                    prog.setdefault("chatHistory", {})[str(d_int)] = []
                if body.get("toggleBookmark") and body.get("key"):
                    bms = list(prog.get("bookmarks") or [])
                    k = _safe_str(body["key"], 100)
                    if k in bms:
                        bms.remove(k)
                    elif len(bms) < _MAX_BOOKMARKS:
                        bms.append(k)
                    prog["bookmarks"] = bms
                if body.get("savePressureScore") and body.get("key"):
                    k = _safe_str(body["key"], 100)
                    sc = max(0, min(1_000_000, _parse_int_field(body.get("score", 0), name="score")))
                    tr = max(1, min(10, _parse_int_field(body.get("tier", 1), name="tier")))
                    st = max(0, min(100_000, _parse_int_field(body.get("maxStreak", 0), name="maxStreak")))
                    ps_map = prog.setdefault("pressureScores", {})
                    if k in ps_map or len(ps_map) < 1000:
                        prev_p = ps_map.get(k) or {}
                        ps_map[k] = {
                            "bestScore": max(sc, int(prev_p.get("bestScore", 0))),
                            "bestTier": max(tr, int(prev_p.get("bestTier", 0))) if sc >= int(prev_p.get("bestScore", 0)) else int(prev_p.get("bestTier", tr)),
                            "bestStreak": max(st, int(prev_p.get("bestStreak", 0))),
                            "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                        }
                if isinstance(body.get("saveInterviewRecord"), dict):
                    ih = list(prog.get("interviewHistory") or [])
                    ih.insert(0, _sanitize_interview_record(body["saveInterviewRecord"]))
                    prog["interviewHistory"] = ih[:30]
                if isinstance(body.get("saveOaRecord"), dict):
                    oh = list(prog.get("oaHistory") or [])
                    oh.insert(0, _sanitize_oa_record(body["saveOaRecord"]))
                    prog["oaHistory"] = oh[:30]
                next_day = None
                next_problem_id = None
                if body.get("toggleSolvedCurated") and body.get("problemId"):
                    pid = _safe_str(body["problemId"], 100)
                    cprob = cl.get_problem(pid)
                    lc_n = cprob.get("lcNum") if cprob else None
                    want_solved = bool(body.get("solved", True))
                    now = datetime.now(timezone.utc)
                    rating = _safe_str(body.get("rating", "Good"), 16)
                    if rating not in ("Again", "Hard", "Good", "Easy"):
                        rating = "Good"
                    days_offset = {"Again": 1, "Hard": 3, "Good": 7, "Easy": 14}.get(rating, 7)
                    next_rev = (now + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                    entry_lang = _safe_str(body.get("language", "sql" if (cprob and cprob.get("isSql")) else "python"), 32).lower()
                    if entry_lang not in _ALLOWED_LANGUAGES:
                        entry_lang = "python"
                    entry = {
                        "solvedAt": now.strftime("%Y-%m-%d %H:%M UTC"),
                        "rating": rating,
                        "nextReviewDate": next_rev,
                        "language": entry_lang,
                        "attempts": 1,
                    }
                    solved_lc = prog.setdefault("solvedLcIds", {})
                    if lc_n is not None:
                        if want_solved:
                            solved_lc[str(lc_n)] = entry
                        else:
                            solved_lc.pop(str(lc_n), None)
                        # Sync matching 120-day schedule days automatically
                        for d_match in _lc_num_to_days(int(lc_n)):
                            if want_solved:
                                prog.setdefault("solvedDays", {})[str(d_match)] = entry
                            else:
                                prog.setdefault("solvedDays", {}).pop(str(d_match), None)
                    if want_solved and body.get("advanceToNext", False):
                        course_key = _safe_str(body.get("course") or prog.get("activeCourse") or "", 40)
                        if course_key in _ALLOWED_COURSES and course_key != "schedule-120":
                            next_problem_id = _next_unsolved_curated_id(course_key, solved_lc, after_pid=pid)
                            if next_problem_id:
                                prog.setdefault("coursePositions", {})[course_key] = next_problem_id
                if body.get("markSolved") and "day" in body:
                    d_int = _parse_day_field(body["day"])
                    d_str = str(d_int)
                    rating = _safe_str(body.get("rating", "Good"), 16)
                    if rating not in ("Again", "Hard", "Good", "Easy"):
                        rating = "Good"
                    days_offset = {"Again": 1, "Hard": 3, "Good": 7, "Easy": 14}.get(rating, 7)
                    now = datetime.now(timezone.utc)
                    next_rev = (now + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                    prev = prog.setdefault("solvedDays", {}).get(d_str, {})
                    entry_lang = _safe_str(body.get("language", "python"), 32).lower()
                    if entry_lang not in _ALLOWED_LANGUAGES:
                        entry_lang = "python"
                    entry = {
                        "solvedAt": now.strftime("%Y-%m-%d %H:%M UTC"),
                        "rating": rating,
                        "nextReviewDate": next_rev,
                        "language": entry_lang,
                        "attempts": int(prev.get("attempts", 0)) + 1,
                    }
                    prog["solvedDays"][d_str] = entry
                    lc_n = _day_to_lc_num(d_int)
                    if lc_n is not None:
                        prog.setdefault("solvedLcIds", {})[str(lc_n)] = entry
                    if body.get("advanceToNext", True):
                        next_day = _next_unsolved_day(prog["solvedDays"], after_day=d_int)
                        prog["currentDay"] = next_day
                if body.get("unmarkSolved") and "day" in body:
                    d_int = _parse_day_field(body["day"])
                    prog.setdefault("solvedDays", {}).pop(str(d_int), None)
                    lc_n = _day_to_lc_num(d_int)
                    if lc_n is not None:
                        prog.setdefault("solvedLcIds", {}).pop(str(lc_n), None)

                save_progress(prog)
                tag_stats = compute_tag_stats(prog.get("solvedDays", {}))
                sr_insights = compute_spaced_repetition_insights(prog)
                self._send_json({
                    "ok": True,
                    "progress": prog,
                    "tags": tag_stats,
                    "spacedRepetition": sr_insights,
                    "nextDay": next_day or prog.get("currentDay"),
                    "nextProblemId": next_problem_id,
                })
            return

        self._send_json({"ok": False, "error": "Unknown route"}, status=404)


def _watch_self() -> None:
    watched = [
        Path(__file__).resolve(),
        ROOT_DIR / "curriculum_data.py",
        ROOT_DIR / "curated_lists.py",
        ROOT_DIR / "curated_catalog.json",
        ROOT_DIR / "edge_cases_data.py",
        ROOT_DIR / "problems_part1.py",
        ROOT_DIR / "problems_part2.py",
    ]
    mtimes = {p: (p.stat().st_mtime if p.exists() else 0.0) for p in watched}
    while True:
        time.sleep(2.0)
        for p, old_m in list(mtimes.items()):
            try:
                cur_m = p.stat().st_mtime if p.exists() else 0.0
            except OSError:
                continue
            if cur_m != old_m:
                os.execv(sys.executable, [sys.executable] + sys.argv)


def main() -> None:
    default_host = os.environ.get("HOST") or "127.0.0.1"
    default_port = int(os.environ.get("PORT") or "8788")
    parser = argparse.ArgumentParser(description="Start Algo Studio offline coding workbench.")
    parser.add_argument("--host", default=default_host, help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=default_port, help="Port number (default: 8788)")
    parser.add_argument("--no-watch", action="store_true", help="Disable auto-reload file watcher")
    args = parser.parse_args()

    if not args.no_watch:
        threading.Thread(target=_watch_self, daemon=True).start()
    server = _ReusableThreadingHTTPServer((args.host, args.port), AlgoStudioHandler)
    print(f"Algo Studio running offline at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
