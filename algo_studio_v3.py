#!/usr/bin/env python3
"""Algo Studio v2.4 Shared Engine: Empirical Big-O Benchmarker, Private GitHub Gist Sync,
and Think-Aloud Interview Communication Evaluator.

Zero external dependencies (pure Python 3 standard library). Works identically in local
CPython 3 HTTP mode and inside Pyodide WebAssembly in-browser mode.
"""

from __future__ import annotations

import copy
import datetime
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

_EXPONENTIAL_HINTS = (
    "2^",
    "n!",
    "factorial",
    "backtrack",
    "subsets",
    "permute",
    "solveNQueens",
    "generateParenthesis",
    "combinationSum",
    "minAbsDifference",
    "minimumDifference",
    "shortestPathLength",
    "smallestSufficientTeam",
)

_QUADRATIC_HINTS = (
    "O(N^2)",
    "O(n^2)",
    "O(N^3)",
    "O(n^3)",
    "O(C^3)",
    "O(M * N)",
    "O(mn)",
    "minDistance",
    "longestCommonSubsequence",
    "isMatch",
    "maxCoins",
    "minCostCutStick",
    "predictTheWinner",
    "stoneGame",
    "maxPoints",
    "findLength",
    "countPalindromic",
    "minimaxGuessWord",
)


def _is_exponential_problem(prob: dict[str, Any]) -> bool:
    fn = str(prob.get("funcName") or "")
    opt = str((prob.get("complexity") or {}).get("optimalTime") or "")
    tags = " ".join(str(t) for t in (prob.get("tags") or []))
    hay = f"{fn} {opt} {tags}".lower()
    return any(tok.lower() in hay for tok in _EXPONENTIAL_HINTS)


def _is_quadratic_problem(prob: dict[str, Any]) -> bool:
    fn = str(prob.get("funcName") or "")
    opt = str((prob.get("complexity") or {}).get("optimalTime") or "")
    hay = f"{fn} {opt}".lower()
    return any(tok.lower() in hay for tok in _QUADRATIC_HINTS)


def _scale_int_list(base: list[int], target_n: int, avoid_small_sum: int | None = None) -> list[int]:
    if not base:
        return [((i * 37 + 13) % 97) - 20 for i in range(target_n)]
    mn = min(base)
    mx = max(base)
    is_sorted = base == sorted(base)
    span = max(16, mx - mn + 1)
    # Deterministic sequence independent of target_n so early-return probability does not drift across N
    if is_sorted:
        step = max(1, span // max(1, len(base)))
        offset = (abs(avoid_small_sum) + 17) if (avoid_small_sum is not None and mn >= 0) else mn
        return [offset + i * step for i in range(target_n)]
    base_floor = (abs(avoid_small_sum) + 17) if (avoid_small_sum is not None and mn >= 0) else mn
    mod = max(span, 97)
    return [base_floor + ((i * 73 + base[i % len(base)] * 17 + 11) % mod) for i in range(target_n)]


def _scale_string(base: str, target_n: int) -> str:
    if not base:
        alpha = "abcdef"
        return "".join(alpha[(i * 7 + 3) % len(alpha)] for i in range(target_n))
    chars = sorted(set(base))
    if len(chars) < 2:
        chars = list(chars) + ["a", "b", "c"]
    return "".join(chars[(i * 5 + (i // 3)) % len(chars)] for i in range(target_n))


def _scale_matrix(base: list[list[Any]], side: int) -> list[list[Any]]:
    sample = base[0][0] if base and base[0] else 1
    is_str = isinstance(sample, str)
    if is_str:
        vals = sorted({str(c) for row in base for c in row}) or ["0", "1"]
        return [[vals[(r * 7 + c * 3) % len(vals)] for c in range(side)] for r in range(side)]
    return [[((r * 13 + c * 7 + 5) % 29) + 1 for c in range(side)] for r in range(side)]


def _build_scaled_cases(prob: dict[str, Any]) -> list[tuple[int, list[Any]]]:
    """Synthesise 4 progressively larger valid argument tuples for empirical complexity benchmarking."""
    tcs = prob.get("testCases") or []
    if not tcs or not isinstance(tcs[0].get("args"), list):
        return []

    base_args = copy.deepcopy(tcs[0]["args"])
    harness = prob.get("harness") or {}
    custom_driver = harness.get("customDriver")
    param_types = harness.get("paramTypes") or []

    # Skip special interactive / fixed-invariant drivers that cannot be blindly scaled
    if custom_driver in ("system-design", "bst-iterator", "randomized-set", "codec-tree", "lca-bst", "clone-graph", "has-cycle", "copy-random-list", "quad-tree"):
        return []
    if any(pt in ("TreeNode", "ListNode[]") for pt in param_types):
        return []

    is_exp = _is_exponential_problem(prob)
    is_quad = _is_quadratic_problem(prob)

    # Identify primary scalable argument
    for idx, val in enumerate(base_args):
        # 1. 2D matrix of ints or chars (not edge lists / intervals / coordinates)
        if (
            isinstance(val, list)
            and len(val) >= 2
            and all(isinstance(r, list) and len(r) == len(val[0]) and len(r) >= 2 for r in val)
            and len(val[0]) >= 3
        ):
            sides = (3, 5, 8, 12) if not is_exp else (2, 3, 4, 5)
            out_cases = []
            for s in sides:
                args_copy = copy.deepcopy(base_args)
                args_copy[idx] = _scale_matrix(val, s)
                out_cases.append((s * s, args_copy))
            return out_cases

        # 2. 1D integer list (or ListNode serialized as int list)
        if isinstance(val, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in val):
            if is_exp:
                sizes = (4, 6, 8, 10)
            elif is_quad:
                sizes = (8, 16, 28, 44)
            else:
                sizes = (16, 48, 128, 280)
            scalar_target = (
                base_args[idx + 1]
                if idx + 1 < len(base_args) and isinstance(base_args[idx + 1], int) and not isinstance(base_args[idx + 1], bool) and base_args[idx + 1] > len(val)
                else None
            )
            out_cases = []
            for n in sizes:
                args_copy = copy.deepcopy(base_args)
                args_copy[idx] = _scale_int_list(val, n, avoid_small_sum=scalar_target)
                # Keep secondary scalar k in valid bounds if present
                for j, other in enumerate(args_copy):
                    if j != idx and isinstance(other, int) and not isinstance(other, bool) and other > 0:
                        if j == idx + 1 and other <= max(1, len(val)):
                            args_copy[j] = max(1, min(other, n))
                out_cases.append((n, args_copy))
            return out_cases

        # 3. String input
        if isinstance(val, str) and len(val) >= 2:
            if is_exp:
                sizes = (4, 6, 8, 10)
            elif is_quad:
                sizes = (8, 16, 28, 44)
            else:
                sizes = (16, 48, 128, 280)
            out_cases = []
            for n in sizes:
                args_copy = copy.deepcopy(base_args)
                args_copy[idx] = _scale_string(val, n)
                if len(args_copy) >= 2 and idx == 0 and isinstance(args_copy[1], str) and len(args_copy[1]) >= 2:
                    args_copy[1] = _scale_string(args_copy[1], max(3, n // 2))
                out_cases.append((n, args_copy))
            return out_cases

        # 4. Scalar integer n (e.g. countPrimes, solveNQueens, generateParenthesis)
        if isinstance(val, int) and not isinstance(val, bool) and val >= 1:
            if is_exp:
                sizes = (2, 3, 4, 5)
            elif val <= 20:
                sizes = (20, 80, 240, 600)
            else:
                sizes = (25, 100, 300, 800)
            out_cases = []
            for n in sizes:
                args_copy = copy.deepcopy(base_args)
                args_copy[idx] = n
                out_cases.append((n, args_copy))
            return out_cases

    return []


def _fit_asymptotic_class(points: list[dict[str, Any]]) -> tuple[str, dict[str, list[float]]]:
    """Fit measured operation counts across 4 N values against reference Big-O growth curves."""
    if len(points) < 2:
        return "O(N)", {}

    ns = [max(2.0, float(p["n"])) for p in points]
    ops = [max(1.0, float(p["ops"])) for p in points]

    models: dict[str, Any] = {
        "O(1)": lambda x: 1.0,
        "O(log N)": lambda x: math.log2(max(2.0, x)),
        "O(N)": lambda x: x,
        "O(N log N)": lambda x: x * math.log2(max(2.0, x)),
        "O(N^2)": lambda x: x * x,
        "O(2^N)": lambda x: math.pow(2.0, min(28.0, x)),
    }

    best_name = "O(N)"
    best_err = float("inf")
    curves: dict[str, list[float]] = {}

    for name, fn in models.items():
        raw_vals = [max(1e-6, float(fn(x))) for x in ns]
        # Scale reference curve to match geometric mean / anchor of measured ops
        ratios = [o / r for o, r in zip(ops, raw_vals)]
        scale = sum(ratios) / len(ratios)
        pred = [round(r * scale, 1) for r in raw_vals]
        if name in ("O(N)", "O(N log N)", "O(N^2)"):
            # Anchor display reference curves cleanly at first point so divergence is immediately visible
            anchor_scale = ops[0] / raw_vals[0]
            curves[name] = [round(r * anchor_scale, 1) for r in raw_vals]
        # Log-space RMS error captures multiplicative growth fidelity across orders of magnitude
        err = sum((math.log(max(1.0, o)) - math.log(max(1.0, p))) ** 2 for o, p in zip(ops, pred)) / len(ops)
        if err < best_err:
            best_err = err
            best_name = name

    return best_name, curves


def run_complexity_benchmark(
    prob: dict[str, Any],
    language: str,
    code: str,
    python_bin: str = "",
) -> dict[str, Any]:
    """Execute user Python code across 4 progressively larger inputs under sys.settrace step counting."""
    if prob.get("isSql") or language == "sql":
        return {"ok": False, "error": "Big-O scaling plotter applies to Python algorithm solutions."}
    if language != "python":
        return {
            "ok": False,
            "error": "Switch the language selector to Python 3 to run the step-counted Big-O scaling visualiser.",
        }
    if not code or not code.strip():
        return {"ok": False, "error": "Write a Python solution first before running the Big-O benchmark."}

    scaled = _build_scaled_cases(prob)
    if not scaled:
        return {
            "ok": False,
            "error": (
                f"{prob.get('title', 'This problem')} uses a custom class or tree topology that cannot be "
                "auto-scaled uniformly. Try Big-O Plot on array, string, matrix, or numeric problems."
            ),
        }

    harness = prob.get("harness") or {}
    func_name = str(prob.get("funcName") or harness.get("methodName") or "solve")
    param_types = harness.get("paramTypes") or []

    runner = (
        "import builtins, collections, copy, functools, heapq, itertools, json, math, operator, random, re, string, sys, time, typing\n"
        "from collections import Counter, defaultdict, deque\n"
        "from functools import lru_cache\n"
        "try:\n"
        "    from functools import cache\n"
        "except ImportError:\n"
        "    cache = lru_cache(maxsize=None)\n"
        "from typing import Any, Dict, List, Optional, Set, Tuple\n"
        f"RAW_CODE = {code!r}\n"
        f"FUNC_NAME = {func_name!r}\n"
        f"PARAM_TYPES = {param_types!r}\n"
        f"SCALED = {json.dumps(scaled)!r}\n"
        "CASES = json.loads(SCALED)\n\n"
        "class ListNode:\n"
        "    def __init__(self, val=0, next=None):\n"
        "        self.val = val; self.next = next\n"
        "def build_list(arr):\n"
        "    dummy = ListNode(0); cur = dummy\n"
        "    for v in (arr or []): cur.next = ListNode(v); cur = cur.next\n"
        "    return dummy.next\n\n"
        "ns = {'__name__': '__user__', 'ListNode': ListNode, 'List': List, 'Optional': Optional, 'Dict': Dict, 'Set': Set, 'Tuple': Tuple, 'Any': Any, 'Counter': Counter, 'defaultdict': defaultdict, 'deque': deque, 'heapq': heapq, 'math': math, 'collections': collections, 'itertools': itertools, 'functools': functools, 'lru_cache': lru_cache, 'cache': cache, 'random': random, 're': re, 'string': string, 'operator': operator, 'sys': sys}\n"
        "import bisect\n"
        "ns['bisect'] = bisect\n"
        "for _m in (math, itertools, heapq, bisect, functools, operator, collections, string, typing):\n"
        "    for _k in dir(_m):\n"
        "        if not _k.startswith('_') and _k not in ns and not hasattr(builtins, _k):\n"
        "            ns[_k] = getattr(_m, _k)\n"
        "try:\n"
        "    exec(compile(RAW_CODE, '<bench_code>', 'exec'), ns)\n"
        "except Exception as exc:\n"
        "    print('__ALGO_BENCH__' + json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}))\n"
        "    sys.exit(0)\n\n"
        "fn = None\n"
        "if 'Solution' in ns:\n"
        "    sol = ns['Solution']()\n"
        "    fn = getattr(sol, FUNC_NAME, None)\n"
        "    if fn is None:\n"
        "        ms = [m for m in dir(sol) if not m.startswith('_')]\n"
        "        if ms: fn = getattr(sol, ms[0])\n"
        "if fn is None:\n"
        "    fn = ns.get(FUNC_NAME)\n"
        "if not callable(fn):\n"
        "    print('__ALGO_BENCH__' + json.dumps({'ok': False, 'error': f'Entry function {FUNC_NAME} not found.'}))\n"
        "    sys.exit(0)\n\n"
        "points = []\n"
        "MAX_STEPS = 120000\n"
        "for n_val, raw_args in CASES:\n"
        "    conv = []\n"
        "    for pi, v in enumerate(copy.deepcopy(raw_args)):\n"
        "        pt = PARAM_TYPES[pi] if pi < len(PARAM_TYPES) else 'any'\n"
        "        conv.append(build_list(v) if pt == 'ListNode' else v)\n"
        "    steps = [0]\n"
        "    def _count(frame, event, arg):\n"
        "        if event == 'line' and frame.f_code.co_filename == '<bench_code>':\n"
        "            steps[0] += 1\n"
        "            if steps[0] > MAX_STEPS:\n"
        "                raise RuntimeError('Step budget exceeded (>120,000 lines)')\n"
        "        return _count\n"
        "    t0 = time.perf_counter()\n"
        "    err = None\n"
        "    try:\n"
        "        sys.settrace(_count)\n"
        "        fn(*conv)\n"
        "    except Exception as exc:\n"
        "        err = f'{type(exc).__name__}: {exc}'\n"
        "    finally:\n"
        "        sys.settrace(None)\n"
        "    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)\n"
        "    points.append({'n': n_val, 'ops': max(1, steps[0]), 'ms': dt_ms, 'error': err})\n"
        "    if err and 'Step budget' in err:\n"
        "        break\n"
        "print('__ALGO_BENCH__' + json.dumps({'ok': True, 'points': points}))\n"
    )

    exe = python_bin or sys.executable or "python3"
    safe_env_keys = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "HOME", "TERM", "TZ", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "PATHEXT")
    safe_env = {k: os.environ[k] for k in safe_env_keys if k in os.environ}
    try:
        proc = subprocess.run(
            [exe, "-c", runner],
            capture_output=True,
            text=True,
            timeout=3.5,
            check=False,
            env=safe_env,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Benchmark timed out (>3.5s), which usually indicates O(N^2) or exponential blowup on larger N.",
        }

    marker = "__ALGO_BENCH__"
    payload = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith(marker):
            try:
                payload = json.loads(line[len(marker) :])
            except Exception:
                payload = None
            break

    if not payload:
        return {
            "ok": False,
            "error": (proc.stderr or "Could not complete benchmark.").strip()[:220],
        }
    if not payload.get("ok"):
        return payload

    points = payload.get("points") or []
    valid_pts = [p for p in points if not p.get("error")]
    if len(valid_pts) < 2:
        first_err = next((p.get("error") for p in points if p.get("error")), "Execution error on scaled inputs.")
        return {"ok": False, "error": str(first_err)}

    detected, ref_curves = _fit_asymptotic_class(valid_pts)
    cx = prob.get("complexity") or {}
    target_opt = str(cx.get("optimalTime") or "O(N)")
    brute_t = str(cx.get("bruteTime") or "O(N^2)")

    rank = {"O(1)": 0, "O(log N)": 1, "O(N)": 2, "O(N log N)": 3, "O(N^2)": 4, "O(2^N)": 5}
    det_r = rank.get(detected, 2)
    target_norm = target_opt.upper()
    if "2^" in target_norm or "!" in target_norm:
        tar_r = 5
    elif "N^2" in target_norm or "N^3" in target_norm or "M * N" in target_norm or "MN" in target_norm:
        tar_r = 4
    elif "LOG" in target_norm and "N" in target_norm:
        tar_r = 3
    elif "LOG" in target_norm:
        tar_r = 1
    elif "O(1)" in target_norm:
        tar_r = 0
    else:
        tar_r = 2

    if det_r <= tar_r:
        status = "optimal"
        verdict = f"Empirical growth tracks {detected}, matching target {target_opt}."
    else:
        status = "slower"
        verdict = f"Empirical growth tracks {detected}, slower than target {target_opt} (closer to brute-force {brute_t})."

    return {
        "ok": True,
        "problemTitle": prob.get("title", ""),
        "detectedClass": detected,
        "targetOptimal": target_opt,
        "bruteTime": brute_t,
        "status": status,
        "verdict": verdict,
        "points": valid_pts,
        "referenceCurves": ref_curves,
    }


def merge_progress_dicts(local_prog: dict[str, Any], remote_prog: dict[str, Any]) -> dict[str, Any]:
    """Non-destructively merge local and remote Algo Studio progress objects across devices."""
    merged = copy.deepcopy(local_prog) if isinstance(local_prog, dict) else {}
    rem = remote_prog if isinstance(remote_prog, dict) else {}

    def _merge_solved(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
        out = dict(dst or {})
        for k, v in (src or {}).items():
            if k not in out:
                out[k] = copy.deepcopy(v)
            elif isinstance(v, dict) and isinstance(out[k], dict):
                if str(v.get("solvedAt", "")) > str(out[k].get("solvedAt", "")):
                    out[k] = copy.deepcopy(v)
        return out

    merged["solvedDays"] = _merge_solved(merged.get("solvedDays") or {}, rem.get("solvedDays") or {})
    merged["solvedLcIds"] = _merge_solved(merged.get("solvedLcIds") or {}, rem.get("solvedLcIds") or {})

    # Union bookmarks preserving order
    bms = list(merged.get("bookmarks") or [])
    bm_set = set(bms)
    for b in rem.get("bookmarks") or []:
        if b not in bm_set:
            bms.append(b)
            bm_set.add(b)
    merged["bookmarks"] = bms[:500]

    # Merge submissions per canonical key deduped by (language, code)
    subs: dict[str, list[dict[str, Any]]] = copy.deepcopy(merged.get("submissions") or {})
    for k, r_list in (rem.get("submissions") or {}).items():
        if not isinstance(r_list, list):
            continue
        cur_list = list(subs.get(k) or [])
        seen = {(str(x.get("language", "")), str(x.get("code", "")).strip()) for x in cur_list if isinstance(x, dict)}
        for item in r_list:
            if not isinstance(item, dict):
                continue
            sig = (str(item.get("language", "")), str(item.get("code", "")).strip())
            if sig not in seen:
                cur_list.append(copy.deepcopy(item))
                seen.add(sig)
        cur_list.sort(key=lambda x: str(x.get("submittedAt", "")), reverse=True)
        subs[k] = cur_list[:15]
    merged["submissions"] = subs

    # Merge dicts where non-empty wins (keep local on conflict)
    for dict_key in ("drafts", "notes", "whiteboards", "revealedHiddenDays", "coursePositions", "pressureScores"):
        dst_map = dict(merged.get(dict_key) or {})
        for k, v in (rem.get(dict_key) or {}).items():
            if k not in dst_map or not dst_map[k]:
                dst_map[k] = copy.deepcopy(v)
        merged[dict_key] = dst_map

    # Merge failedAttemptsByDay taking max count
    fails = dict(merged.get("failedAttemptsByDay") or {})
    for k, v in (rem.get("failedAttemptsByDay") or {}).items():
        try:
            fails[k] = max(int(fails.get(k, 0)), int(v or 0))
        except Exception:
            pass
    merged["failedAttemptsByDay"] = fails

    # Merge exam histories deduped by timestamp
    for hist_key in ("interviewHistory", "oaHistory"):
        combined = list(merged.get(hist_key) or [])
        seen_ts = {str(x.get("completedAt") or x.get("date") or json.dumps(x, sort_keys=True)) for x in combined if isinstance(x, dict)}
        for item in rem.get(hist_key) or []:
            if not isinstance(item, dict):
                continue
            sig = str(item.get("completedAt") or item.get("date") or json.dumps(item, sort_keys=True))
            if sig not in seen_ts:
                combined.append(copy.deepcopy(item))
                seen_ts.add(sig)
        merged[hist_key] = combined[-60:]

    # Merge flash drill stats
    lf = merged.get("flashDrillStats") or {}
    rf = rem.get("flashDrillStats") or {}
    merged["flashDrillStats"] = {
        "attempted": max(int(lf.get("attempted", 0)), int(rf.get("attempted", 0))),
        "correct": max(int(lf.get("correct", 0)), int(rf.get("correct", 0))),
        "bestStreak": max(int(lf.get("bestStreak", 0)), int(rf.get("bestStreak", 0))),
    }

    merged["streak"] = max(int(merged.get("streak", 1)), int(rem.get("streak", 1)))
    if str(rem.get("lastActiveDate", "")) > str(merged.get("lastActiveDate", "")):
        merged["lastActiveDate"] = rem["lastActiveDate"]

    return merged


def _github_request(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "AlgoStudio-Sync",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(body)
            msg = err_json.get("message") or body[:160]
        except Exception:
            msg = body[:160]
        return int(exc.code), {"error": f"GitHub API HTTP {exc.code}: {msg}"}
    except Exception as exc:
        return 0, {"error": f"Network error contacting GitHub Gist API: {exc}"}


def load_gist_sync_config(config_path: Path) -> dict[str, str]:
    if not config_path.is_file():
        return {"token": "", "gistId": "", "lastSyncedAt": ""}
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {
                "token": str(raw.get("token") or "").strip(),
                "gistId": str(raw.get("gistId") or "").strip(),
                "lastSyncedAt": str(raw.get("lastSyncedAt") or "").strip(),
            }
    except Exception:
        pass
    return {"token": "", "gistId": "", "lastSyncedAt": ""}


def save_gist_sync_config(config_path: Path, token: str, gist_id: str, last_synced_at: str = "") -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = config_path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"token": token, "gistId": gist_id, "lastSyncedAt": last_synced_at}, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    os.replace(tmp, config_path)


def sync_github_gist_local(
    action: str,
    local_prog: dict[str, Any],
    config_path: Path,
    token_override: str = "",
    gist_id_override: str = "",
) -> dict[str, Any]:
    """Local/sidecar GitHub Gist Sync handler with 0600 credential storage and non-destructive merge."""
    cfg = load_gist_sync_config(config_path)
    if action == "disconnect":
        if config_path.exists():
            config_path.unlink(missing_ok=True)
        return {"ok": True, "configured": False, "gistId": "", "masked": "", "lastSyncedAt": ""}

    token = token_override.strip() or cfg["token"]
    gist_id = gist_id_override.strip() or cfg["gistId"]
    masked = f"{token[:4]}...{token[-4:]}" if len(token) >= 10 else ("****" if token else "")

    if action == "status":
        return {
            "ok": True,
            "configured": bool(token),
            "gistId": gist_id,
            "masked": masked,
            "lastSyncedAt": cfg.get("lastSyncedAt", ""),
        }

    if not token:
        return {"ok": False, "error": "Enter a GitHub Personal Access Token with gist scope first."}

    if gist_id and not re.fullmatch(r"[A-Za-z0-9]{6,64}", gist_id):
        return {"ok": False, "error": "Invalid Gist ID format. Use the alphanumeric ID from your Gist URL or leave blank to create a new private Gist."}

    now_stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    filename = "algo-studio-progress.json"

    if action == "save_config":
        save_gist_sync_config(config_path, token, gist_id, cfg.get("lastSyncedAt", ""))
        return {
            "ok": True,
            "configured": True,
            "gistId": gist_id,
            "masked": masked,
            "lastSyncedAt": cfg.get("lastSyncedAt", ""),
        }

    remote_prog: dict[str, Any] = {}
    if gist_id:
        status, g_data = _github_request("GET", f"https://api.github.com/gists/{gist_id}", token)
        if status != 200:
            return {"ok": False, "error": g_data.get("error") or f"Could not fetch Gist {gist_id} (HTTP {status})."}
        files = g_data.get("files") or {}
        f_obj = files.get(filename) or next(iter(files.values()), None)
        if isinstance(f_obj, dict) and f_obj.get("content"):
            try:
                parsed = json.loads(f_obj["content"])
                if isinstance(parsed, dict):
                    remote_prog = parsed
            except Exception:
                remote_prog = {}

    merged = merge_progress_dicts(local_prog, remote_prog)

    if action == "pull":
        if not gist_id:
            return {"ok": False, "error": "Enter an existing Gist ID to pull progress from another device."}
        save_gist_sync_config(config_path, token, gist_id, now_stamp)
        return {
            "ok": True,
            "configured": True,
            "gistId": gist_id,
            "masked": masked,
            "lastSyncedAt": now_stamp,
            "mergedProgress": merged,
            "summary": f"Pulled & merged ({len(merged.get('solvedDays') or {})} days, {len(merged.get('solvedLcIds') or {})} LC problems).",
        }

    # Push or Sync (create new private Gist if none yet, else PATCH existing Gist)
    # Strip any accidental secrets before uploading
    clean_payload = {k: v for k, v in merged.items() if "key" not in k.lower() and "token" not in k.lower()}
    gist_body = {
        "description": "Algo Studio cross-device progress sync (private)",
        "public": False,
        "files": {filename: {"content": json.dumps(clean_payload, indent=2, ensure_ascii=False)}},
    }
    if gist_id:
        status, res_data = _github_request("PATCH", f"https://api.github.com/gists/{gist_id}", token, gist_body)
    else:
        status, res_data = _github_request("POST", "https://api.github.com/gists", token, gist_body)

    if status not in (200, 201):
        return {"ok": False, "error": res_data.get("error") or f"GitHub Gist save failed (HTTP {status})."}

    new_gist_id = str(res_data.get("id") or gist_id)
    save_gist_sync_config(config_path, token, new_gist_id, now_stamp)
    return {
        "ok": True,
        "configured": True,
        "gistId": new_gist_id,
        "gistUrl": str(res_data.get("html_url") or f"https://gist.github.com/{new_gist_id}"),
        "masked": masked,
        "lastSyncedAt": now_stamp,
        "mergedProgress": merged,
        "summary": f"Synced to private Gist ({len(merged.get('solvedDays') or {})} days, {len(merged.get('solvedLcIds') or {})} LC problems).",
    }


def grade_think_aloud_transcript(
    prob: dict[str, Any],
    transcript: str,
) -> dict[str, Any]:
    """Evaluate interview verbal explanation quality across 4 Senior SWE/FDE communication pillars."""
    text = str(transcript or "").strip()
    low = text.lower()
    words = re.findall(r"[a-z0-9_+^]+", low)
    wc = len(words)

    def _has_any(terms: tuple[str, ...]) -> bool:
        return any(t in low for t in terms)

    has_constraints = _has_any((
        "empty", "null", "none", "duplicate", "negative", "bound", "constraint",
        "size", "length", "sorted", "unsorted", "valid", "overflow", "assume", "clarify", "range",
    ))
    has_big_o = bool(re.search(r"\bo\s*\(\s*[^)]{1,20}\)", low)) or _has_any((
        "time complexity", "space complexity", "linear time", "constant space", "logarithmic", "quadratic", "auxiliary space", "big o",
    ))
    has_tradeoff = _has_any((
        "brute", "naive", "instead", "trade", "optimis", "optimiz", "invariant",
        "hash", "map", "set", "heap", "stack", "queue", "pointer", "window", "dp", "binary search", "bfs", "dfs", "trie", "prefix", "union", "segment",
    ))
    has_dryrun = _has_any((
        "example", "trace", "walk through", "dry run", "step", "edge case", "single element", "base case", "index", "pointer", "return",
    ))

    pillars = [
        {
            "name": "Constraint Clarification",
            "score": 25 if (has_constraints and wc >= 12) else (12 if has_constraints else 0),
            "max": 25,
            "met": has_constraints and wc >= 12,
            "tip": "Explicitly confirm empty/single inputs, duplicates, negative values, and input bounds before coding.",
        },
        {
            "name": "Big-O Time & Space",
            "score": 25 if (has_big_o and wc >= 12) else (12 if has_big_o else 0),
            "max": 25,
            "met": has_big_o and wc >= 12,
            "tip": f"State both Time and auxiliary Space complexity aloud (target: {(prob.get('complexity') or {}).get('optimalTime', 'optimal')}).",
        },
        {
            "name": "Naive-to-Optimal Trade-off",
            "score": 25 if (has_tradeoff and wc >= 18) else (12 if has_tradeoff else 0),
            "max": 25,
            "met": has_tradeoff and wc >= 18,
            "tip": f"Contrast the brute-force approach with the {(prob.get('tags') or ['core'])[0]} invariant you are choosing.",
        },
        {
            "name": "Dry-Run & Edge Verification",
            "score": 25 if (has_dryrun and wc >= 18) else (12 if has_dryrun else 0),
            "max": 25,
            "met": has_dryrun and wc >= 18,
            "tip": "Walk through Example 1 variable by variable and verbally test one boundary case before finishing.",
        },
    ]
    total = sum(p["score"] for p in pillars)
    missing = [p["tip"] for p in pillars if not p["met"]]
    if wc == 0:
        summary = "No verbal transcript captured. Speak aloud or jot short explanation bullet points during the mock interview."
    elif total >= 85:
        summary = f"Strong interview communication ({total}/100 across {wc} words): clear constraints, trade-off, Big-O, and dry-run."
    elif total >= 50:
        summary = f"Solid partial narration ({total}/100 across {wc} words). Cover the remaining cues below for a Strong Hire signal."
    else:
        summary = f"Brief narration ({total}/100 across {wc} words). Practise narrating constraints, brute-vs-optimal trade-off, and Big-O aloud."

    return {
        "ok": True,
        "communicationScore": total,
        "wordCount": wc,
        "pillars": pillars,
        "missingPrompts": missing,
        "summary": summary,
    }
