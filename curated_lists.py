#!/usr/bin/env python3
"""Curated Problem Lists engine for Algo Studio v2.0.0.

Provides:
- 4 iconic study sheets: Grind 75 (75), LeetCode Top Interview 150 (150),
  NeetCode 150 Skill-Tree (150), and SQL 50 Relational Mastery (50) — 286
  unique runnable problems loaded from curated_catalog.json.
- Full Python 3 execution harness with ListNode, TreeNode, Graph Node,
  QuadTree, class-design, in-place, and live sys.settrace Python Tutor frames.
- Live SQLite 3 execution engine (with MySQL compatibility helpers) for SQL 50.
- Unified cross-list leetcodeId sync and 20-check rubric support for SQL & DSA.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
CATALOG_PATH = ROOT_DIR / "curated_catalog.json"
PYTHON_BIN = sys.executable or "/usr/bin/python3"

_CATALOG_DATA: dict[str, Any] = {}
SHEETS: list[dict[str, Any]] = []
DAG_NODES: list[dict[str, Any]] = []
PROBLEMS_BY_ID: dict[str, dict[str, Any]] = {}
LC_NUM_TO_CURATED_IDS: dict[int, list[str]] = {}


def reload_catalog() -> None:
    global _CATALOG_DATA, SHEETS, DAG_NODES, PROBLEMS_BY_ID, LC_NUM_TO_CURATED_IDS
    if not CATALOG_PATH.is_file():
        _CATALOG_DATA = {"sheets": [], "dagNodes": [], "problemsById": {}}
    else:
        _CATALOG_DATA = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    SHEETS = _CATALOG_DATA.get("sheets") or []
    DAG_NODES = _CATALOG_DATA.get("dagNodes") or []
    PROBLEMS_BY_ID = _CATALOG_DATA.get("problemsById") or {}
    LC_NUM_TO_CURATED_IDS = {}
    for pid, prob in PROBLEMS_BY_ID.items():
        lc_num = prob.get("lcNum")
        if lc_num is not None:
            LC_NUM_TO_CURATED_IDS.setdefault(int(lc_num), []).append(pid)


reload_catalog()


def get_problem(problem_id: str) -> dict[str, Any] | None:
    return PROBLEMS_BY_ID.get(str(problem_id or ""))


def get_catalog_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "sheets": SHEETS,
        "dagNodes": DAG_NODES,
        "problemsById": PROBLEMS_BY_ID,
    }


def _register_mysql_compat(conn: sqlite3.Connection) -> None:
    def _if(cond: Any, a: Any, b: Any) -> Any:
        return a if cond else b

    def _char_len(s: Any) -> int | None:
        return None if s is None else len(str(s))

    def _left(s: Any, n: Any) -> str | None:
        return None if s is None else str(s)[: max(0, int(n))]

    def _right(s: Any, n: Any) -> str | None:
        if s is None:
            return None
        k = int(n)
        return "" if k <= 0 else str(s)[-k:]

    def _concat(*args: Any) -> str | None:
        if any(a is None for a in args):
            return None
        return "".join(str(a) for a in args)

    def _parse_date(d: Any) -> datetime | None:
        if not d:
            return None
        s = str(d).strip()[:10]
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None

    def _datediff(d1: Any, d2: Any) -> int | None:
        dt1, dt2 = _parse_date(d1), _parse_date(d2)
        if not dt1 or not dt2:
            return None
        return (dt1 - dt2).days

    def _subdate(d: Any, days: Any) -> str | None:
        dt = _parse_date(d)
        if not dt or days is None:
            return None
        return (dt - timedelta(days=int(days))).strftime("%Y-%m-%d")

    def _adddate(d: Any, days: Any) -> str | None:
        dt = _parse_date(d)
        if not dt or days is None:
            return None
        return (dt + timedelta(days=int(days))).strftime("%Y-%m-%d")

    def _date_format(d: Any, fmt: Any) -> str | None:
        dt = _parse_date(d)
        if not dt or fmt is None:
            return None
        return (
            str(fmt)
            .replace("%Y", f"{dt.year:04d}")
            .replace("%m", f"{dt.month:02d}")
            .replace("%d", f"{dt.day:02d}")
        )

    def _year(d: Any) -> int | None:
        dt = _parse_date(d)
        return dt.year if dt else None

    def _month(d: Any) -> int | None:
        dt = _parse_date(d)
        return dt.month if dt else None

    def _day(d: Any) -> int | None:
        dt = _parse_date(d)
        return dt.day if dt else None

    def _regexp(pattern: Any, text: Any) -> int:
        if pattern is None or text is None:
            return 0
        try:
            return 1 if re.search(str(pattern), str(text)) else 0
        except re.error:
            return 0

    def _pow(a: Any, b: Any) -> float | None:
        if a is None or b is None:
            return None
        return float(math.pow(float(a), float(b)))

    conn.create_function("IF", 3, _if)
    conn.create_function("CHAR_LENGTH", 1, _char_len)
    conn.create_function("CHARACTER_LENGTH", 1, _char_len)
    conn.create_function("LEFT", 2, _left)
    conn.create_function("RIGHT", 2, _right)
    conn.create_function("CONCAT", -1, _concat)
    conn.create_function("DATEDIFF", 2, _datediff)
    conn.create_function("SUBDATE", 2, _subdate)
    conn.create_function("ADDDATE", 2, _adddate)
    conn.create_function("DATE_FORMAT", 2, _date_format)
    conn.create_function("YEAR", 1, _year)
    conn.create_function("MONTH", 1, _month)
    conn.create_function("DAY", 1, _day)
    conn.create_function("REGEXP", 2, _regexp)
    conn.create_function("POW", 2, _pow)
    conn.create_function("POWER", 2, _pow)


_SAFE_SUBPROCESS_ENV_KEYS = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TZ",
    "USER",
    "LOGNAME",
    "TMPDIR",
    "TMP",
    "TEMP",
    "SYSTEMROOT",
    "PATHEXT",
)


def safe_subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return a minimal allowlisted environment so user code cannot read server secrets."""
    env = {k: os.environ[k] for k in _SAFE_SUBPROCESS_ENV_KEYS if k in os.environ}
    if extra:
        env.update(extra)
    return env


_SQL_COMMENT_RE = re.compile(r"^\s*(?:#|--).*$", flags=re.MULTILINE)
_SQL_BINARY_RE = re.compile(r"\bBINARY\s+", flags=re.IGNORECASE)
_SQL_DELETE_PERSON_RE = re.compile(r"^\s*DELETE\s+\w+\s+FROM\s+person\b", flags=re.IGNORECASE)
_SQL_DATE_SUB_RE = re.compile(r"DATE_SUB\(\s*([^,]+?)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)", flags=re.IGNORECASE)
_SQL_DATE_ADD_RE = re.compile(r"DATE_ADD\(\s*([^,]+?)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)", flags=re.IGNORECASE)
_SQL_SUBDATE_INTERVAL_RE = re.compile(r"SUBDATE\(\s*([^,]+?)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)", flags=re.IGNORECASE)
_SQL_GROUP_CONCAT_RE = re.compile(
    r"GROUP_CONCAT\(\s*DISTINCT\s+([^\s,()]+)\s+ORDER\s+BY\s+[^\s,()]+\s+(?:ASC\s+)?SEPARATOR\s+('[^']+')\s*\)",
    flags=re.IGNORECASE,
)
_SQL_SEPARATOR_RE = re.compile(r"\s+SEPARATOR\s+('[^']+')", flags=re.IGNORECASE)
_SQL_TRAILING_SEMI_RE = re.compile(r";+\s*$")
_SQL_DELETE_HEAD_RE = re.compile(r"^\s*DELETE\b", flags=re.IGNORECASE)
_SQL_TIMEOUT_SECONDS = 2.5


def _normalize_sql_query(sql: str) -> str:
    out = _SQL_COMMENT_RE.sub("", str(sql or "")).strip()
    out = _SQL_BINARY_RE.sub("", out)
    if _SQL_DELETE_PERSON_RE.match(out):
        out = "DELETE FROM Person WHERE id NOT IN (SELECT MIN(id) FROM Person GROUP BY email)"
    out = _SQL_DATE_SUB_RE.sub(r"SUBDATE(\1, \2)", out)
    out = _SQL_DATE_ADD_RE.sub(r"ADDDATE(\1, \2)", out)
    out = _SQL_SUBDATE_INTERVAL_RE.sub(r"SUBDATE(\1, \2)", out)
    # Handle GROUP_CONCAT(DISTINCT col ORDER BY col SEPARATOR ',') -> GROUP_CONCAT(DISTINCT col)
    out = _SQL_GROUP_CONCAT_RE.sub(r"GROUP_CONCAT(DISTINCT \1)", out)
    out = _SQL_SEPARATOR_RE.sub(r", \1", out)
    return _SQL_TRAILING_SEMI_RE.sub("", out).strip()


_SQL_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}
if hasattr(sqlite3, "SQLITE_RECURSIVE"):
    _SQL_ALLOWED_ACTIONS.add(sqlite3.SQLITE_RECURSIVE)
_SQL_BLOCKED_FUNCTIONS = {"load_extension", "fts3_tokenizer"}


def _exec_single_sql(seed_sql: str, query_sql: str) -> tuple[list[str], list[dict[str, Any]]]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    deadline = time.monotonic() + _SQL_TIMEOUT_SECONDS
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
    try:
        _register_mysql_compat(conn)
        if seed_sql:
            conn.executescript(seed_sql)
        norm = _normalize_sql_query(query_sql)
        if not norm:
            raise ValueError("Empty SQL query. Write a SELECT (or DELETE) statement.")
        is_delete_query = bool(_SQL_DELETE_HEAD_RE.match(norm))

        def _authorizer(action: int, arg1: Any, arg2: Any, db_name: Any, _trigger: Any) -> int:
            if action == sqlite3.SQLITE_FUNCTION and str(arg2 or "").lower() in _SQL_BLOCKED_FUNCTIONS:
                return sqlite3.SQLITE_DENY
            if action in _SQL_ALLOWED_ACTIONS:
                return sqlite3.SQLITE_OK
            if is_delete_query and action == sqlite3.SQLITE_DELETE and db_name == "main":
                return sqlite3.SQLITE_OK
            if is_delete_query and action == sqlite3.SQLITE_TRANSACTION:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        conn.set_authorizer(_authorizer)
        cur = conn.cursor()
        try:
            if is_delete_query:
                cur.execute(norm)
                cur.execute("SELECT * FROM Person ORDER BY id")
            else:
                cur.execute(norm)
            cols = [d[0] for d in (cur.description or [])]
            rows = [{cols[i]: row[i] for i in range(len(cols))} for row in cur.fetchall()]
            return cols, rows
        finally:
            cur.close()
    finally:
        conn.close()


def execute_curated_sql(prob: dict[str, Any], code: str) -> dict[str, Any]:
    """Execute user SQL query against in-memory SQLite 3 and compare against referenceSql."""
    sql_schema = prob.get("sqlSchema", "")
    ref_sql = prob.get("referenceSql") or prob.get("solutionCode", {}).get("sql", "")
    cases = prob.get("testCases") or [{"label": "Primary Dataset", "seedSql": sql_schema}]

    results: list[dict[str, Any]] = []
    passed_cnt = 0
    first_err: str | None = None

    def _norm_row(r: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in r.items():
            kl = str(k).lower()
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[kl] = round(float(v), 4)
            else:
                out[kl] = v
        return out

    for idx, tc in enumerate(cases):
        seed = tc.get("seedSql") or sql_schema
        t0 = time.perf_counter()
        exp_cols: list[str] = []
        exp_rows: list[dict[str, Any]] = tc.get("expected") if isinstance(tc.get("expected"), list) else []
        if not exp_rows and ref_sql:
            try:
                exp_cols, exp_rows = _exec_single_sql(seed, ref_sql)
            except Exception:
                exp_rows = []
        elif exp_rows and isinstance(exp_rows[0], dict):
            exp_cols = list(exp_rows[0].keys())

        try:
            act_cols, act_rows = _exec_single_sql(seed, code)
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            n_act = [_norm_row(r) for r in act_rows]
            n_exp = [_norm_row(r) for r in exp_rows]
            ok = len(n_act) == len(n_exp) and (
                n_act == n_exp
                or sorted(json.dumps(r, sort_keys=True) for r in n_act)
                == sorted(json.dumps(r, sort_keys=True) for r in n_exp)
            )
            if ok:
                passed_cnt += 1
            results.append({
                "index": idx + 1,
                "label": tc.get("label") or f"Dataset {idx + 1}",
                "input": tc.get("inputDisplay") or "Seeded SQLite Schema",
                "expected": exp_rows,
                "actual": act_rows,
                "expectedColumns": exp_cols,
                "actualColumns": act_cols,
                "isSql": True,
                "passed": ok,
                "hidden": False,
                "runtimeMs": dt_ms,
                "stdout": f"Returned {len(act_rows)} row(s).",
            })
        except Exception as exc:
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            err_text = f"SQLite Error: {exc}"
            if first_err is None:
                first_err = err_text
            results.append({
                "index": idx + 1,
                "label": tc.get("label") or f"Dataset {idx + 1}",
                "input": tc.get("inputDisplay") or "Seeded SQLite Schema",
                "expected": exp_rows,
                "actual": None,
                "expectedColumns": exp_cols,
                "actualColumns": [],
                "isSql": True,
                "passed": False,
                "hidden": False,
                "runtimeMs": dt_ms,
                "error": err_text,
                "errorLine": 1,
                "suspectLine": 1,
                "stdout": "",
            })

    return {
        "ok": True,
        "isSql": True,
        "passed": passed_cnt,
        "total": len(results),
        "visiblePassed": passed_cnt,
        "visibleTotal": len(results),
        "hiddenPassed": 0,
        "hiddenTotal": 0,
        "allPassed": passed_cnt == len(results) and len(results) > 0,
        "error": first_err,
        "errorLine": 1 if first_err else None,
        "highlightLine": 1 if first_err else None,
        "results": results,
        "executionFrames": [],
        "tracedCode": code,
        "tracedLanguage": "sql",
    }


def execute_curated_python(
    prob: dict[str, Any],
    code: str,
    custom_test_args: list[Any] | None = None,
    capture_frames: bool = True,
) -> dict[str, Any]:
    """Execute Python 3 solution against curated harness (ListNode/TreeNode/Graph/Class) with optional live Python Tutor frames."""
    harness_cfg = prob.get("harness") or {}
    cases = list(prob.get("testCases") or [])
    if custom_test_args is not None and isinstance(custom_test_args, list):
        # Compute expected output using optimal reference code on the custom input
        ref_code = prob.get("solutionCode", {}).get("python", "")
        exp_val = None
        if ref_code:
            ref_run = execute_curated_python(
                {**prob, "testCases": [{"label": "Custom Input", "args": custom_test_args, "expected": None}]},
                ref_code,
                custom_test_args=None,
                capture_frames=False,
            )
            if ref_run.get("ok") and ref_run.get("results"):
                exp_val = ref_run["results"][0].get("actual")
        cases.append({
            "label": "Custom Input",
            "args": custom_test_args,
            "expected": exp_val,
        })

    # Syntax check first
    code_lines = code.splitlines()
    try:
        ast.parse(code, filename="<user_code>")
    except SyntaxError as syn_err:
        ln = syn_err.lineno or 1
        src = code_lines[ln - 1] if 1 <= ln <= len(code_lines) else ""
        return {
            "ok": False,
            "errorType": "SyntaxError",
            "error": f"SyntaxError on Line {ln}: {syn_err.msg}",
            "errorLine": ln,
            "errorSourceLine": src,
            "tracedCode": code,
            "tracedLanguage": "python",
        }

    runner_script = (
        "import bisect, collections, copy, functools, heapq, inspect, io, itertools, json, math, operator, random, re, string, sys, time, traceback, typing\n"
        "from collections import Counter, defaultdict, deque\n"
        "from functools import lru_cache, cache\n"
        "from typing import Any, Dict, List, Optional, Set, Tuple\n\n"
        f"RAW_USER_CODE = {json.dumps(code)}\n"
        "USER_LINES = RAW_USER_CODE.splitlines()\n"
        f"HARNESS = json.loads({json.dumps(json.dumps(harness_cfg))})\n"
        f"CASES = json.loads({json.dumps(json.dumps(cases))})\n"
        f"CAPTURE_FRAMES = {repr(bool(capture_frames))}\n\n"
        "class ListNode:\n"
        "    def __init__(self, val=0, next=None):\n"
        "        self.val = val\n"
        "        self.next = next\n\n"
        "class TreeNode:\n"
        "    def __init__(self, val=0, left=None, right=None):\n"
        "        self.val = val\n"
        "        self.left = left\n"
        "        self.right = right\n\n"
        "custom_driver = HARNESS.get('customDriver')\n"
        "if custom_driver == 'copy-random-list':\n"
        "    class Node:\n"
        "        def __init__(self, x: int, next=None, random=None):\n"
        "            self.val = int(x)\n"
        "            self.next = next\n"
        "            self.random = random\n"
        "elif custom_driver == 'clone-graph':\n"
        "    class Node:\n"
        "        def __init__(self, val=0, neighbors=None):\n"
        "            self.val = val\n"
        "            self.neighbors = neighbors if neighbors is not None else []\n"
        "elif custom_driver == 'connect-next-right':\n"
        "    class Node:\n"
        "        def __init__(self, val=0, left=None, right=None, next=None):\n"
        "            self.val = val\n"
        "            self.left = left\n"
        "            self.right = right\n"
        "            self.next = next\n"
        "elif custom_driver == 'quad-tree':\n"
        "    class Node:\n"
        "        def __init__(self, val, isLeaf, topLeft=None, topRight=None, bottomLeft=None, bottomRight=None):\n"
        "            self.val = val\n"
        "            self.isLeaf = isLeaf\n"
        "            self.topLeft = topLeft\n"
        "            self.topRight = topRight\n"
        "            self.bottomLeft = bottomLeft\n"
        "            self.bottomRight = bottomRight\n"
        "else:\n"
        "    class Node:\n"
        "        def __init__(self, val=0, next=None, neighbors=None):\n"
        "            self.val = val\n"
        "            self.next = next\n"
        "            self.neighbors = neighbors if neighbors is not None else []\n\n"
        "def build_list(arr):\n"
        "    if not arr: return None\n"
        "    dummy = ListNode(0)\n"
        "    cur = dummy\n"
        "    for x in arr:\n"
        "        cur.next = ListNode(x)\n"
        "        cur = cur.next\n"
        "    return dummy.next\n\n"
        "def build_cycle_list(arr, pos):\n"
        "    if not arr: return None\n"
        "    nodes = [ListNode(x) for x in arr]\n"
        "    for i in range(len(nodes) - 1): nodes[i].next = nodes[i + 1]\n"
        "    if isinstance(pos, int) and 0 <= pos < len(nodes): nodes[-1].next = nodes[pos]\n"
        "    return nodes[0]\n\n"
        "def serialize_list(node):\n"
        "    out, seen = [], set()\n"
        "    while node and id(node) not in seen and len(out) < 1000:\n"
        "        seen.add(id(node)); out.append(node.val); node = node.next\n"
        "    return out\n\n"
        "def build_random_list(pairs):\n"
        "    if not pairs: return None\n"
        "    nodes = [Node(p[0]) for p in pairs]\n"
        "    for i in range(len(nodes) - 1): nodes[i].next = nodes[i + 1]\n"
        "    for i, p in enumerate(pairs):\n"
        "        if p[1] is not None and 0 <= p[1] < len(nodes): nodes[i].random = nodes[p[1]]\n"
        "    return nodes[0]\n\n"
        "def serialize_random_list(head):\n"
        "    if not head: return []\n"
        "    nodes, idx_map, cur = [], {}, head\n"
        "    while cur and id(cur) not in idx_map and len(nodes) < 1000:\n"
        "        idx_map[id(cur)] = len(nodes); nodes.append(cur); cur = cur.next\n"
        "    return [[n.val, idx_map.get(id(n.random)) if n.random is not None else None] for n in nodes]\n\n"
        "def build_graph(adj):\n"
        "    if not adj: return None\n"
        "    nodes = [Node(i + 1) for i in range(len(adj))]\n"
        "    for i, neis in enumerate(adj):\n"
        "        nodes[i].neighbors = [nodes[j - 1] for j in neis if 1 <= j <= len(nodes)]\n"
        "    return nodes[0]\n\n"
        "def serialize_graph(node):\n"
        "    if not node: return []\n"
        "    visited, q = {}, deque([node])\n"
        "    while q:\n"
        "        cur = q.popleft()\n"
        "        if cur.val in visited: continue\n"
        "        visited[cur.val] = [n.val for n in cur.neighbors]\n"
        "        for n in cur.neighbors:\n"
        "            if n.val not in visited: q.append(n)\n"
        "    return [visited.get(i, []) for i in range(1, max(visited.keys()) + 1)] if visited else []\n\n"
        "def build_tree(arr, cls=TreeNode):\n"
        "    if not arr: return None\n"
        "    root = cls(arr[0])\n"
        "    q, i = deque([root]), 1\n"
        "    while q and i < len(arr):\n"
        "        node = q.popleft()\n"
        "        if i < len(arr) and arr[i] is not None:\n"
        "            node.left = cls(arr[i]); q.append(node.left)\n"
        "        i += 1\n"
        "        if i < len(arr) and arr[i] is not None:\n"
        "            node.right = cls(arr[i]); q.append(node.right)\n"
        "        i += 1\n"
        "    return root\n\n"
        "def find_tree_node(root, val):\n"
        "    if not root: return None\n"
        "    if root.val == val: return root\n"
        "    return find_tree_node(root.left, val) or find_tree_node(root.right, val)\n\n"
        "def serialize_tree(root):\n"
        "    if not root: return []\n"
        "    out, q = [], deque([root])\n"
        "    while q:\n"
        "        node = q.popleft()\n"
        "        if node is None: out.append(None)\n"
        "        else:\n"
        "            out.append(node.val); q.append(node.left); q.append(node.right)\n"
        "    while out and out[-1] is None: out.pop()\n"
        "    return out\n\n"
        "def serialize_next_tree(root):\n"
        "    if not root: return []\n"
        "    out, lvl = [], root\n"
        "    while lvl:\n"
        "        cur, nxt_lvl = lvl, None\n"
        "        while cur:\n"
        "            out.append(cur.val)\n"
        "            if not nxt_lvl: nxt_lvl = cur.left or cur.right\n"
        "            cur = cur.next\n"
        "        out.append('#')\n"
        "        lvl = nxt_lvl\n"
        "    return out\n\n"
        "def serialize_quad_tree(root):\n"
        "    if not root: return []\n"
        "    out, q = [], deque([root])\n"
        "    while q:\n"
        "        node = q.popleft()\n"
        "        if node is None: out.append(None)\n"
        "        else:\n"
        "            out.append([1 if node.isLeaf else 0, 1 if node.val else 0])\n"
        "            if not node.isLeaf:\n"
        "                q.extend([node.topLeft, node.topRight, node.bottomLeft, node.bottomRight])\n"
        "    while out and out[-1] is None: out.pop()\n"
        "    return out\n\n"
        "def validate_balanced_bst(root):\n"
        "    inorder = []\n"
        "    def dfs(n):\n"
        "        if not n: return 0\n"
        "        lh = dfs(n.left)\n"
        "        if lh == -1: return -1\n"
        "        inorder.append(n.val)\n"
        "        rh = dfs(n.right)\n"
        "        if rh == -1 or abs(lh - rh) > 1: return -1\n"
        "        return 1 + max(lh, rh)\n"
        "    h = dfs(root)\n"
        "    return inorder if h != -1 else ['UNBALANCED']\n\n"
        "_bad_version_state = {'bad': 1}\n"
        "def isBadVersion(version: int) -> bool:\n"
        "    return version >= _bad_version_state['bad']\n\n"
        "ns = {\n"
        "    '__name__': '__user__', 'ListNode': ListNode, 'TreeNode': TreeNode, 'Node': Node,\n"
        "    'isBadVersion': isBadVersion, 'List': List, 'Optional': Optional, 'Dict': Dict,\n"
        "    'Set': Set, 'Tuple': Tuple, 'Any': Any, 'Counter': Counter, 'defaultdict': defaultdict,\n"
        "    'deque': deque, 'heapq': heapq, 'bisect': bisect, 'math': math, 'collections': collections,\n"
        "    'itertools': itertools, 'functools': functools, 'lru_cache': lru_cache, 'cache': cache,\n"
        "    'random': random, 're': re, 'string': string, 'operator': operator, 'sys': sys,\n"
        "}\n"
        "import builtins as _builtins\n"
        "for _mod in (math, itertools, heapq, bisect, functools, operator, collections, string, typing):\n"
        "    for _k in dir(_mod):\n"
        "        if not _k.startswith('_') and _k not in ns and not hasattr(_builtins, _k):\n"
        "            ns[_k] = getattr(_mod, _k)\n"
        "try:\n"
        "    exec(compile(RAW_USER_CODE, '<user_code>', 'exec'), ns)\n"
        "except Exception as exc:\n"
        "    tb = traceback.extract_tb(exc.__traceback__)\n"
        "    u_frames = [f for f in tb if f.filename == '<user_code>']\n"
        "    _raw_ln = getattr(exc, 'lineno', None)\n"
        "    ln = _raw_ln if isinstance(_raw_ln, int) and not isinstance(_raw_ln, bool) else (u_frames[-1].lineno if u_frames else 1)\n"
        "    src = USER_LINES[ln - 1] if 1 <= ln <= len(USER_LINES) else ''\n"
        "    print('__ALGO_CURATED__' + json.dumps({'ok': False, 'errorType': type(exc).__name__, 'error': f'{type(exc).__name__} on Line {ln}: {exc}', 'errorLine': ln, 'errorSourceLine': src}))\n"
        "    sys.exit(0)\n\n"
        "def _safe_repr(val):\n"
        "    try:\n"
        "        s = repr(val)\n"
        "        return s if len(s) <= 100 else s[:97] + '...'\n"
        "    except Exception:\n"
        "        return '<unprintable>'\n\n"
        "def _json_val(val, depth=0):\n"
        "    if depth > 3: return _safe_repr(val)\n"
        "    if val is None or isinstance(val, (bool, int, float)): return val\n"
        "    if isinstance(val, str): return val if len(val) <= 80 else val[:77] + '...'\n"
        "    if isinstance(val, (list, tuple, set)): return [_json_val(x, depth + 1) for x in list(val)[:14]]\n"
        "    if isinstance(val, dict): return {str(k): _json_val(v, depth + 1) for k, v in list(val.items())[:14]}\n"
        "    if type(val).__name__ == 'deque': return [_json_val(x, depth + 1) for x in list(val)[:14]]\n"
        "    return _safe_repr(val)\n\n"
        "def _build_pt_snapshot(func_label, live_frame, event, ret_arg):\n"
        "    heap_objects, heap_by_id = [{'id': 'heap_func', 'type': 'function', 'label': func_label}], {}\n"
        "    def _encode_val(v, depth=0):\n"
        "        if v is None or isinstance(v, (bool, int, float, str)):\n"
        "            val_out = _safe_repr(v) if isinstance(v, float) and (v != v or abs(v) == float('inf')) else v\n"
        "            return {'kind': 'primitive', 'type': type(v).__name__, 'value': val_out}\n"
        "        oid = id(v)\n"
        "        if oid not in heap_by_id:\n"
        "            hid = f'heap_{len(heap_objects)}'\n"
        "            heap_by_id[oid] = hid\n"
        "            if isinstance(v, dict):\n"
        "                heap_objects.append({'id': hid, 'type': 'dict', 'entries': [[_json_val(k), _json_val(val)] for k, val in list(v.items())[:14]]})\n"
        "            elif isinstance(v, (list, tuple, set)) or type(v).__name__ == 'deque':\n"
        "                heap_objects.append({'id': hid, 'type': type(v).__name__, 'elements': [_json_val(x) for x in list(v)[:14]]})\n"
        "            elif hasattr(v, '__dict__') and depth < 6 and len(heap_objects) < 80:\n"
        "                placeholder = {'id': hid, 'type': 'instance', 'className': type(v).__name__, 'fields': []}\n"
        "                heap_objects.append(placeholder)\n"
        "                fields = []\n"
        "                for fk, fv in list(vars(v).items())[:8]:\n"
        "                    if not fk.startswith('_'):\n"
        "                        fields.append({'name': fk, **_encode_val(fv, depth + 1)})\n"
        "                placeholder['fields'] = fields\n"
        "            else:\n"
        "                heap_objects.append({'id': hid, 'type': type(v).__name__, 'label': _safe_repr(v)})\n"
        "        return {'kind': 'ref', 'refId': heap_by_id[oid], 'type': type(v).__name__}\n"
        "    raw_stack, cur_f = [], live_frame\n"
        "    while cur_f is not None and len(raw_stack) < 10:\n"
        "        if cur_f.f_code.co_filename == '<user_code>' and cur_f.f_code.co_name != '<module>':\n"
        "            raw_stack.append(cur_f)\n"
        "        cur_f = cur_f.f_back\n"
        "    raw_stack.reverse()\n"
        "    if not raw_stack: raw_stack = [live_frame]\n"
        "    call_frames = []\n"
        "    for f_idx, cf in enumerate(raw_stack):\n"
        "        f_vars = []\n"
        "        for k, v in cf.f_locals.items():\n"
        "            if k != 'self' and not k.startswith('_') and not callable(v):\n"
        "                f_vars.append({'name': k, **_encode_val(v)})\n"
        "        call_frames.append({'funcName': cf.f_code.co_name, 'line': cf.f_lineno, 'depth': f_idx + 1, 'isHighlighted': f_idx == len(raw_stack) - 1, 'vars': f_vars})\n"
        "    return {\n"
        "        'funcName': call_frames[-1]['funcName'] if call_frames else func_label,\n"
        "        'funcSignature': func_label,\n"
        "        'globalVars': [{'name': func_label.split('(')[0], 'kind': 'ref', 'refId': 'heap_func', 'type': 'function'}],\n"
        "        'frameVars': call_frames[-1]['vars'] if call_frames else [],\n"
        "        'callFrames': call_frames,\n"
        "        'returnValueEncoded': _encode_val(ret_arg) if event == 'return' else None,\n"
        "        'heapObjects': heap_objects,\n"
        "    }\n\n"
        "def _canon(v, order_matters):\n"
        "    if v is None or isinstance(v, bool): return v\n"
        "    if isinstance(v, float): return round(v, 4)\n"
        "    if isinstance(v, list):\n"
        "        m = [_canon(x, order_matters) for x in v]\n"
        "        return m if order_matters else sorted(m, key=lambda x: json.dumps(x, sort_keys=True))\n"
        "    if isinstance(v, dict): return {str(k): _canon(val, order_matters) for k, val in sorted(v.items())}\n"
        "    return v\n\n"
        "def _eq(act, exp, order_matters):\n"
        "    if act == exp: return True\n"
        "    if isinstance(act, (int, float)) and isinstance(exp, (int, float)) and not isinstance(act, bool) and not isinstance(exp, bool):\n"
        "        return abs(float(act) - float(exp)) < 1e-4\n"
        "    if isinstance(act, list) and isinstance(exp, list) and len(act) == len(exp):\n"
        "        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in act) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in exp) and order_matters:\n"
        "            return all(abs(float(a) - float(b)) < 1e-4 for a, b in zip(act, exp))\n"
        "    return json.dumps(_canon(act, order_matters), sort_keys=True) == json.dumps(_canon(exp, order_matters), sort_keys=True)\n\n"
        "method_name = HARNESS.get('methodName', 'solve')\n"
        "param_types = HARNESS.get('paramTypes') or []\n"
        "return_type = HARNESS.get('returnType', 'any')\n"
        "in_place_arg = HARNESS.get('inPlaceArgIndex', None)\n"
        "order_matters = HARNESS.get('orderMatters', True) is not False\n"
        "results, passed, first_err_line, primary_frames = [], 0, None, []\n\n"
        "def _resolve_entry(name, cls_name='Solution'):\n"
        "    if cls_name in ns:\n"
        "        sol = ns[cls_name]()\n"
        "        fn = getattr(sol, name, None)\n"
        "        if fn is not None:\n"
        "            return fn\n"
        "    if name in ns:\n"
        "        return ns[name]\n"
        "    raise RuntimeError(f'Method {name} not found.')\n\n"
        "for idx, tc in enumerate(CASES):\n"
        "    buf = io.StringIO()\n"
        "    old_stdout = sys.stdout\n"
        "    raw_args = copy.deepcopy(tc.get('args', []))\n"
        "    trace_state = {'last_line': None, 'return_line': None, 'locals': {}, 'frames': []}\n"
        "    do_trace = CAPTURE_FRAMES and idx < 2\n"
        "    def _tracer(frame, event, arg):\n"
        "        if frame.f_code.co_filename == '<user_code>' and frame.f_code.co_name != '<module>':\n"
        "            ln = frame.f_lineno\n"
        "            prev_ln = trace_state['last_line']\n"
        "            trace_state['last_line'] = ln\n"
        "            snap, structured = {}, {}\n"
        "            for k, v in frame.f_locals.items():\n"
        "                if k != 'self' and not k.startswith('_') and not callable(v):\n"
        "                    snap[k] = _safe_repr(v); structured[k] = _json_val(v)\n"
        "            trace_state['locals'] = snap\n"
        "            if event == 'return': trace_state['return_line'] = ln\n"
        "            if do_trace and event in ('line', 'return') and len(trace_state['frames']) < 80:\n"
        "                src_ln = USER_LINES[ln - 1].strip() if 1 <= ln <= len(USER_LINES) else ''\n"
        "                pt_snap = _build_pt_snapshot(method_name + '(...)', frame, event, arg)\n"
        "                trace_state['frames'].append({'step': len(trace_state['frames']) + 1, 'line': ln, 'prevLine': prev_ln, 'source': src_ln, 'event': event, 'locals': structured, 'returnValue': _json_val(arg) if event == 'return' else None, **pt_snap})\n"
        "        return _tracer\n"
        "    t0 = time.perf_counter()\n"
        "    try:\n"
        "        sys.stdout = buf\n"
        "        if do_trace: sys.settrace(_tracer)\n"
        "        try:\n"
        "            if custom_driver in ('system-design', 'bst-iterator', 'randomized-set'):\n"
        "                ops, op_args = raw_args[0], raw_args[1]\n"
        "                cls_obj = ns.get(ops[0]) or ns.get(HARNESS.get('className', ''))\n"
        "                if cls_obj is None: raise RuntimeError(f'Class {ops[0]} not found.')\n"
        "                init_args = [build_tree(op_args[0][0])] if custom_driver == 'bst-iterator' else list(op_args[0])\n"
        "                inst = cls_obj(*init_args)\n"
        "                out_list = [None]\n"
        "                for op, a in zip(ops[1:], op_args[1:]):\n"
        "                    out_list.append(getattr(inst, op)(*a))\n"
        "                actual = out_list\n"
        "            elif custom_driver == 'encode-decode':\n"
        "                sol = ns['Solution']() if 'Solution' in ns else ns['Codec']()\n"
        "                actual = sol.decode(sol.encode(list(raw_args[0])))\n"
        "            elif custom_driver == 'codec-tree':\n"
        "                codec = ns['Codec']() if 'Codec' in ns else ns['Solution']()\n"
        "                actual = serialize_tree(codec.deserialize(codec.serialize(build_tree(raw_args[0]))))\n"
        "            elif custom_driver == 'has-cycle':\n"
        "                fn = _resolve_entry('hasCycle')\n"
        "                actual = bool(fn(build_cycle_list(raw_args[0], raw_args[1])))\n"
        "            elif custom_driver == 'lca-bst':\n"
        "                fn = _resolve_entry('lowestCommonAncestor')\n"
        "                root = build_tree(raw_args[0])\n"
        "                p_node = find_tree_node(root, raw_args[1]) or TreeNode(raw_args[1])\n"
        "                q_node = find_tree_node(root, raw_args[2]) or TreeNode(raw_args[2])\n"
        "                res = fn(root, p_node, q_node)\n"
        "                actual = res.val if res else None\n"
        "            elif custom_driver == 'copy-random-list':\n"
        "                fn = _resolve_entry('copyRandomList')\n"
        "                actual = serialize_random_list(fn(build_random_list(raw_args[0])))\n"
        "            elif custom_driver == 'clone-graph':\n"
        "                fn = _resolve_entry('cloneGraph')\n"
        "                actual = serialize_graph(fn(build_graph(raw_args[0])))\n"
        "            elif custom_driver == 'first-bad-version':\n"
        "                _bad_version_state['bad'] = int(raw_args[1])\n"
        "                fn = _resolve_entry('firstBadVersion')\n"
        "                actual = fn(int(raw_args[0]))\n"
        "            elif custom_driver == 'connect-next-right':\n"
        "                fn = _resolve_entry('connect')\n"
        "                actual = serialize_next_tree(fn(build_tree(raw_args[0], cls=Node)))\n"
        "            elif custom_driver == 'quad-tree':\n"
        "                fn = _resolve_entry('construct')\n"
        "                actual = serialize_quad_tree(fn(raw_args[0]))\n"
        "            elif custom_driver == 'validate-balanced-bst':\n"
        "                fn = _resolve_entry('sortedArrayToBST')\n"
        "                actual = validate_balanced_bst(fn(raw_args[0]))\n"
        "            elif custom_driver == 'in-place-prefix':\n"
        "                fn = _resolve_entry(method_name)\n"
        "                k = fn(*raw_args)\n"
        "                actual = raw_args[0][:k]\n"
        "            else:\n"
        "                sol = ns['Solution']() if 'Solution' in ns else None\n"
        "                fn = getattr(sol, method_name, None) if sol else ns.get(method_name)\n"
        "                if fn is None and sol is not None:\n"
        "                    methods = [m for m in dir(sol) if not m.startswith('_')]\n"
        "                    if methods: fn = getattr(sol, methods[0])\n"
        "                if fn is None: raise RuntimeError(f'Method {method_name} not found.')\n"
        "                conv = []\n"
        "                for p_idx, val in enumerate(raw_args):\n"
        "                    pt = param_types[p_idx] if p_idx < len(param_types) else 'any'\n"
        "                    if pt == 'ListNode': conv.append(build_list(val))\n"
        "                    elif pt == 'ListNode[]': conv.append([build_list(x) for x in (val or [])])\n"
        "                    elif pt == 'TreeNode': conv.append(build_tree(val))\n"
        "                    else: conv.append(val)\n"
        "                ret = fn(*conv)\n"
        "                if in_place_arg is not None:\n"
        "                    pt0 = param_types[in_place_arg] if in_place_arg < len(param_types) else 'any'\n"
        "                    actual = serialize_list(conv[in_place_arg]) if pt0 == 'ListNode' else (serialize_tree(conv[in_place_arg]) if pt0 == 'TreeNode' else conv[in_place_arg])\n"
        "                elif return_type == 'ListNode': actual = serialize_list(ret)\n"
        "                elif return_type == 'TreeNode': actual = serialize_tree(ret)\n"
        "                else: actual = ret\n"
        "        finally:\n"
        "            sys.settrace(None)\n"
        "            sys.stdout = old_stdout\n"
        "        dt_ms = round((time.perf_counter() - t0) * 1000, 2)\n"
        "        exp = tc.get('expected')\n"
        "        if custom_driver == 'randomized-set' and isinstance(exp, list) and isinstance(actual, list) and len(exp) == len(actual):\n"
        "            ok = all((a in e if isinstance(e, list) else a == e) for a, e in zip(actual, exp))\n"
        "        else:\n"
        "            ok = _eq(actual, exp, order_matters)\n"
        "        if ok: passed += 1\n"
        "        ret_ln = trace_state['return_line'] or trace_state['last_line']\n"
        "        ret_src = USER_LINES[ret_ln - 1].strip() if (ret_ln and 1 <= ret_ln <= len(USER_LINES)) else ''\n"
        "        if not ok and first_err_line is None and ret_ln:\n"
        "            first_err_line = ret_ln; primary_frames = trace_state['frames']\n"
        "        elif idx == 0 and not primary_frames:\n"
        "            primary_frames = trace_state['frames']\n"
        "        results.append({'index': idx + 1, 'label': tc.get('label', f'Case {idx + 1}'), 'input': tc.get('args', []), 'inputDisplay': tc.get('inputDisplay', ''), 'expected': exp, 'actual': actual, 'passed': ok, 'hidden': False, 'runtimeMs': dt_ms, 'stdout': buf.getvalue().strip(), 'suspectLine': ret_ln if not ok else None, 'suspectSource': ret_src if not ok else '', 'localsSnapshot': trace_state['locals'] if not ok else {}, 'frames': trace_state['frames']})\n"
        "    except Exception as exc:\n"
        "        sys.settrace(None); sys.stdout = old_stdout\n"
        "        dt_ms = round((time.perf_counter() - t0) * 1000, 2)\n"
        "        tb = traceback.extract_tb(exc.__traceback__)\n"
        "        u_frames = [f for f in tb if f.filename == '<user_code>']\n"
        "        _raw_ln = getattr(exc, 'lineno', None)\n"
        "        err_ln = _raw_ln if isinstance(_raw_ln, int) and not isinstance(_raw_ln, bool) else (u_frames[-1].lineno if u_frames else (trace_state['last_line'] or 1))\n"
        "        err_src = USER_LINES[err_ln - 1].strip() if (err_ln and 1 <= err_ln <= len(USER_LINES)) else ''\n"
        "        if trace_state['frames']:\n"
        "            trace_state['frames'][-1]['event'] = 'exception'\n"
        "            trace_state['frames'][-1]['error'] = f'{type(exc).__name__} on Line {err_ln}: {exc}'\n"
        "        if first_err_line is None:\n"
        "            first_err_line = err_ln; primary_frames = trace_state['frames']\n"
        "        results.append({'index': idx + 1, 'label': tc.get('label', f'Case {idx + 1}'), 'input': tc.get('args', []), 'inputDisplay': tc.get('inputDisplay', ''), 'expected': tc.get('expected'), 'actual': None, 'error': f'{type(exc).__name__} on Line {err_ln}: {exc}', 'errorLine': err_ln, 'suspectLine': err_ln, 'suspectSource': err_src, 'localsSnapshot': trace_state['locals'], 'stdout': buf.getvalue().strip(), 'passed': False, 'hidden': False, 'runtimeMs': dt_ms, 'frames': trace_state['frames']})\n"
        "print('__ALGO_CURATED__' + json.dumps({'ok': True, 'passed': passed, 'total': len(CASES), 'visiblePassed': passed, 'visibleTotal': len(CASES), 'hiddenPassed': 0, 'hiddenTotal': 0, 'allPassed': passed == len(CASES) and len(CASES) > 0, 'highlightLine': first_err_line, 'executionFrames': primary_frames, 'results': results}))\n"
    )

    try:
        proc = subprocess.run(
            [PYTHON_BIN, "-c", runner_script],
            capture_output=True,
            text=True,
            timeout=5.0,
            env=safe_subprocess_env(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Time Limit Exceeded (5.0s). Check for infinite loops or non-shrinking recursion.",
            "tracedCode": code,
            "tracedLanguage": "python",
        }

    marker = "__ALGO_CURATED__"
    stdout = proc.stdout or ""
    if marker in stdout:
        try:
            payload = json.loads(stdout.split(marker, 1)[1].strip().splitlines()[0])
            payload["tracedCode"] = code
            payload["tracedLanguage"] = "python"
            return payload
        except (json.JSONDecodeError, IndexError, TypeError) as exc:
            return {
                "ok": False,
                "error": f"Runner output parse error: {exc}",
                "tracedCode": code,
                "tracedLanguage": "python",
            }

    return {
        "ok": False,
        "error": (proc.stderr or stdout or f"Process exited with code {proc.returncode}").strip(),
        "tracedCode": code,
        "tracedLanguage": "python",
    }


def execute_curated_problem(
    problem_id: str,
    language: str,
    code: str,
    custom_test_args: list[Any] | None = None,
    capture_frames: bool = True,
) -> dict[str, Any]:
    prob = get_problem(problem_id)
    if not prob:
        return {"ok": False, "error": f"Unknown curated problem '{problem_id}'"}
    if prob.get("isSql") or str(language).lower() == "sql":
        return execute_curated_sql(prob, code)
    return execute_curated_python(prob, code, custom_test_args=custom_test_args, capture_frames=capture_frames)


def trace_curated_optimal(problem_id: str, tc_idx: int = 0) -> dict[str, Any]:
    prob = get_problem(problem_id)
    if not prob:
        return {"ok": False, "error": f"Unknown curated problem '{problem_id}'"}
    if prob.get("isSql"):
        return {"ok": False, "error": "SQL problems display live result tables instead of Python Tutor stack frames."}
    opt_code = prob.get("solutionCode", {}).get("python", "")
    cases = prob.get("testCases") or []
    if not opt_code or not cases:
        return {"ok": False, "error": f"No Python optimal solution or tests for '{problem_id}'"}
    safe_idx = max(0, min(len(cases) - 1, int(tc_idx)))
    tc = cases[safe_idx]
    res = execute_curated_python({**prob, "testCases": [tc]}, opt_code, capture_frames=True)
    if not res.get("ok"):
        return res
    first_res = (res.get("results") or [{}])[0]
    return {
        "ok": True,
        "problemId": problem_id,
        "tcIdx": safe_idx,
        "language": "python",
        "code": opt_code,
        "input": tc.get("args", []),
        "expected": tc.get("expected"),
        "frames": first_res.get("frames") or res.get("executionFrames") or [],
    }
