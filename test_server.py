#!/usr/bin/env python3
"""Unit and integration test suite for Algo Studio (SWE & FDE Coding Coach)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("ALGO_STUDIO_OFFLINE_TESTS", "1")

import curriculum_data as cd
import server


class AlgoStudioTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_progress_path = server.PROGRESS_PATH
        self._tmp_dir = tempfile.TemporaryDirectory()
        server.PROGRESS_PATH = Path(self._tmp_dir.name) / "progress.json"

    def tearDown(self) -> None:
        server.PROGRESS_PATH = self._orig_progress_path
        self._tmp_dir.cleanup()
    def test_curriculum_completeness(self) -> None:
        self.assertEqual(len(cd.PROBLEMS), 120)
        self.assertEqual(len(cd.IMAGE_TAGS), 74)
        self.assertEqual(len(cd.EXPANDED_TAGS), 12)
        self.assertEqual(len(cd.ALL_TAGS), 86)

        covered = set()
        for p in cd.PROBLEMS:
            for t in p["tags"]:
                covered.add(t)
        for tag in cd.ALL_TAGS:
            self.assertIn(tag["name"], covered, f"Tag {tag['name']} not covered in 120-day schedule")

    def test_python_typescript_go_execution(self) -> None:
        for day in (1, 2, 3, 4, 5, 9, 11, 12, 18, 27, 45, 62, 76, 113, 117):
            prob = cd.PROBLEMS_BY_DAY[day]
            for lang in ("python", "typescript", "go"):
                res = server.execute_user_code(day, lang, prob["solutionCode"][lang])
                self.assertTrue(res.get("ok"), f"Day {day} {lang} failed to run: {res}")
                self.assertTrue(res.get("allPassed"), f"Day {day} {lang} did not pass all tests: {res}")

    def test_debugger_line_and_stdout_capture(self) -> None:
        # 1. Python wrong answer with print() + suspectLine + localsSnapshot
        buggy_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = {}\n"
            "    for i, x in enumerate(nums):\n"
            "        print(f'checking idx={i} val={x}')\n"
            "        seen[x] = i\n"
            "    return [0, 0]\n"
        )
        py_res = server.execute_user_code(1, "python", buggy_py)
        self.assertTrue(py_res["ok"])
        self.assertFalse(py_res["allPassed"])
        first_fail = py_res["results"][0]
        self.assertFalse(first_fail["passed"])
        self.assertEqual(first_fail["suspectLine"], 6)
        self.assertIn("checking idx=0", first_fail["stdout"])
        self.assertIn("seen", first_fail["localsSnapshot"])

        # 2. Python runtime exception line capture
        crash_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    x = 10\n"
            "    y = 0\n"
            "    z = x // y\n"
            "    return [z, 0]\n"
        )
        crash_res = server.execute_user_code(1, "python", crash_py)
        self.assertTrue(crash_res["ok"])
        self.assertEqual(crash_res["results"][0]["errorLine"], 4)
        self.assertEqual(crash_res["results"][0]["suspectLine"], 4)

        # 3. TypeScript console.log + suspectLine capture
        buggy_ts = (
            "function twoSum(nums: number[], target: number): number[] {\n"
            "    console.log('ts debug nums=', nums.length);\n"
            "    return [-1, -1];\n"
            "}\n"
        )
        ts_res = server.execute_user_code(1, "typescript", buggy_ts)
        self.assertTrue(ts_res["ok"])
        self.assertFalse(ts_res["allPassed"])
        self.assertEqual(ts_res["results"][0]["suspectLine"], 3)
        self.assertIn("ts debug nums=", ts_res["results"][0]["stdout"])

    def test_in_tab_ai_diagnostic_chat(self) -> None:
        buggy_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    for i in range(len(nums)):\n"
            "        return [i, i]\n"
        )
        chat_res = server.diagnose_in_chat(1, "python", buggy_py, "Why is my test case failing?")
        self.assertTrue(chat_res["ok"])
        self.assertEqual(chat_res["highlightLine"], 3)
        self.assertIn("Line 3", chat_res["reply"])
        self.assertTrue(len(chat_res["executionFrames"]) > 0)

        # Verify visual complexity contrast on user's working O(N^2) nested-loop Two Sum code
        nested_two_sum = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    n = len(nums)\n"
            "    for i in range(n):\n"
            "        for j in range(i + 1, n):\n"
            "            if nums[i] + nums[j] == target:\n"
            "                return [i, j]\n"
            "    return []\n"
        )
        contrast_res = server.diagnose_in_chat(
            1, "python", nested_two_sum, "Contrast hash-map vs brute-force complexity", model_mode="pro"
        )
        self.assertTrue(contrast_res["ok"])
        self.assertEqual(contrast_res["visualWidget"]["type"], "complexity_contrast")
        self.assertEqual(contrast_res["visualWidget"]["loopDepth"], 2)
        self.assertTrue(len(contrast_res["executionFrames"]) >= 4)

    def test_code_analyser_rubric(self) -> None:
        prob = cd.PROBLEMS_BY_DAY[1]
        skeleton_res = server.analyse_user_code(1, "python", prob["starterCode"]["python"])
        self.assertTrue(skeleton_res["ok"])
        self.assertLess(skeleton_res["totalScore"], 50)

        optimal_res = server.analyse_user_code(1, "python", prob["solutionCode"]["python"])
        self.assertTrue(optimal_res["ok"])
        self.assertGreaterEqual(optimal_res["totalScore"], 88)
        self.assertEqual(len(optimal_res["rubric"]), 5)

    def test_python_tutor_partial_syntax_error_trace(self) -> None:
        # Mirrors the user's exact code where Line 8 has `return [seen{complement}, i]`
        partial_syntax_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    # Write your O(N) hash-table solution here\n"
            "    seen = {}\n"
            "\n"
            "    for i, num in enumerate(nums):\n"
            "        complement = target - num\n"
            "        if complement in seen:\n"
            "            return [seen{complement}, i]\n"
            "        seen[num] = i\n"
            "\n"
            "    return []\n"
        )
        res = server.execute_user_code(1, "python", partial_syntax_py)
        self.assertTrue(res["ok"])
        self.assertFalse(res["allPassed"])
        first = res["results"][0]
        self.assertEqual(first["errorLine"], 8)
        self.assertEqual(first["suspectLine"], 8)
        # Must have executed i=0 (storing seen[2]=0) and i=1 (computing complement=2) right up to Line 8!
        frames = res["executionFrames"]
        self.assertGreaterEqual(len(frames), 6)
        self.assertEqual(frames[-1]["line"], 8)
        self.assertEqual(frames[-1]["locals"].get("complement"), 2)
        self.assertEqual(frames[-1]["locals"].get("seen"), {"2": 0})

    def test_conversational_copilot_no_duplicate_reply(self) -> None:
        partial_syntax_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = {}\n"
            "    for i, num in enumerate(nums):\n"
            "        complement = target - num\n"
            "        if complement in seen:\n"
            "            return [seen{complement}, i]\n"
            "        seen[num] = i\n"
            "    return []\n"
        )
        turn1 = server.diagnose_in_chat(
            1, "python", partial_syntax_py, "what's the issue with my syntax", history=[]
        )
        self.assertTrue(turn1["ok"])
        self.assertEqual(turn1["highlightLine"], 6)
        self.assertIn("seen[complement]", turn1["reply"])

        history = [
            {"role": "user", "text": "what's the issue with my syntax"},
            {"role": "assistant", "text": turn1["reply"]},
        ]
        turn2 = server.diagnose_in_chat(
            1, "python", partial_syntax_py, "what's the issue with my syntax", history=history
        )
        self.assertTrue(turn2["ok"])
        self.assertNotEqual(turn1["reply"], turn2["reply"])
        self.assertIn("seen[complement]", turn2["reply"])

    def test_next_unsolved_day_and_dom_order(self) -> None:
        self.assertEqual(server._next_unsolved_day([1], 1), 2)
        self.assertEqual(server._next_unsolved_day([1, 2, 3], 1), 4)
        self.assertEqual(server._next_unsolved_day([1, 3], 1), 2)
        self.assertEqual(server._next_unsolved_day([1, 3], 2), 4)

        html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        console_pos = html.index('id="test-results-container"')
        animator_pos = html.index('id="live-visualiser-card"')
        self.assertLess(console_pos, animator_pos, "Console output must appear above the code animator")
        self.assertIn('id="submit-solution-btn"', html)
        self.assertIn("submitCurrentSolution", html)
        self.assertIn('id="pt-stage-wrap"', html)
        self.assertIn('id="pt-arrows-svg"', html)
        self.assertIn('id="vis-first-btn"', html)
        self.assertIn('id="vis-last-btn"', html)
        self.assertIn("drawPythonTutorArrows", html)

    def test_python_tutor_frames_objects_and_shared_references(self) -> None:
        prob = cd.PROBLEMS_BY_DAY[1]
        res = server.execute_user_code(1, "python", prob["solutionCode"]["python"])
        self.assertTrue(res["ok"])
        self.assertTrue(res["allPassed"])
        # Inspect Test Case 2 (nums = [3, 2, 4], target = 6) matching user's Python Tutor screenshot
        tc2_frames = res["results"][1]["frames"]
        self.assertGreaterEqual(len(tc2_frames), 10)
        last_frame = tc2_frames[-1]
        self.assertEqual(last_frame["event"], "return")
        self.assertEqual(last_frame["funcName"], "twoSum")
        self.assertEqual(last_frame["funcSignature"], "twoSum(nums, target)")
        # Verify Global frame -> nums and twoSum -> nums share the exact same heapId ('heap_1')
        global_nums = next(v for v in last_frame["globalVars"] if v["name"] == "nums")
        frame_nums = next(v for v in last_frame["frameVars"] if v["name"] == "nums")
        self.assertEqual(global_nums["kind"], "ref")
        self.assertEqual(global_nums["refId"], frame_nums["refId"])
        # Verify Return value points to heap_3 ([1, 2])
        self.assertEqual(last_frame["returnValueEncoded"]["kind"], "ref")
        heap_by_id = {h["id"]: h for h in last_frame["heapObjects"]}
        ret_heap = heap_by_id[last_frame["returnValueEncoded"]["refId"]]
        self.assertEqual(ret_heap["type"], "list")
        self.assertEqual(ret_heap["elements"], [1, 2])

    def test_recursive_call_stack_and_instance_heap(self):
        # Write a recursive helper + custom Node class inside Day 1 solution to verify full call stack & instance heap objects
        recursive_code = (
            "class Node:\n"
            "    def __init__(self, val, nxt=None):\n"
            "        self.val = val\n"
            "        self.next = nxt\n\n"
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    head = Node(nums[0], Node(nums[1]))\n"
            "    seen = {}\n"
            "    def helper(idx: int) -> list[int]:\n"
            "        if idx >= len(nums):\n"
            "            return []\n"
            "        comp = target - nums[idx]\n"
            "        if comp in seen:\n"
            "            return [seen[comp], idx]\n"
            "        seen[nums[idx]] = idx\n"
            "        return helper(idx + 1)\n"
            "    return helper(0)\n"
        )
        res = server.execute_user_code(1, "python", recursive_code)
        self.assertTrue(res["ok"])
        self.assertTrue(res["allPassed"])
        frames = res["results"][0]["frames"]
        # Find a frame inside recursive `helper` where callFrames depth >= 2
        deep_frames = [f for f in frames if len(f.get("callFrames", [])) >= 2]
        self.assertGreater(len(deep_frames), 0)
        deepest = max(deep_frames, key=lambda f: len(f["callFrames"]))
        self.assertGreaterEqual(len(deepest["callFrames"]), 2)
        self.assertEqual(deepest["callFrames"][0]["funcName"], "twoSum")
        self.assertEqual(deepest["callFrames"][-1]["funcName"], "helper")
        # Verify `Node` instances are captured in `heapObjects` with `type == 'instance'` and `.next` ref
        inst_objs = [h for h in frames[-1]["heapObjects"] if h.get("type") == "instance"]
        self.assertGreaterEqual(len(inst_objs), 2)
        self.assertEqual(inst_objs[0]["className"], "Node")

    def test_custom_test_case_approach_check_and_stress_test(self):
        sol_py = cd.PROBLEMS[0]["solutionCode"]["python"]
        # 1. Custom test case execution
        custom_res = server.execute_user_code(1, "python", sol_py, custom_test_args=[[10, 20, 30, 40], 50])
        self.assertTrue(custom_res["ok"])
        self.assertTrue(custom_res["allPassed"])
        last_tc = custom_res["results"][-1]
        self.assertEqual(last_tc["input"], [[10, 20, 30, 40], 50])
        self.assertEqual(last_tc["expected"], [1, 2])
        self.assertEqual(last_tc["actual"], [1, 2])

        # 2. Pre-code approach check
        opt_check = server.check_user_approach(1, "Use a hash map dictionary to store seen numbers and lookup complement in O(1) time.")
        self.assertTrue(opt_check["ok"])
        self.assertEqual(opt_check["verdict"], "optimal_aligned")

        trap_check = server.check_user_approach(1, "Use a nested loop to check all pairs in O(N^2).")
        self.assertTrue(trap_check["ok"])
        self.assertEqual(trap_check["verdict"], "suboptimal_trap")

        # 3. FDE Stress Test
        stress_res = server.run_fde_stress_test(1, "python", sol_py)
        self.assertTrue(stress_res["ok"])
        self.assertTrue(stress_res["stressTest"])
        self.assertEqual(stress_res["passed"], stress_res["total"])
        self.assertGreaterEqual(stress_res["total"], 3)

    def test_spaced_repetition_and_v16_dom_elements(self):
        fake_prog = {
            "solvedDays": {
                "1": {"rating": "Again", "nextReviewDate": "2020-01-01", "attempts": 2},
                "2": {"rating": "Easy", "nextReviewDate": "2099-01-01", "attempts": 1},
            },
            "failedAttemptsByDay": {"3": 3},
        }
        sr = server.compute_spaced_repetition_insights(fake_prog)
        due_days = [d["day"] for d in sr["dueReviewDays"]]
        self.assertIn(1, due_days)
        self.assertIn(3, due_days)
        self.assertNotIn(2, due_days)
        self.assertGreater(len(sr["weakTopics"]), 0)

        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for required_id in (
            'id="toggle-pt-layout-btn"',
            'id="approach-check-input"',
            'id="verify-approach-btn"',
            'id="custom-tc-input"',
            'id="run-custom-tc-btn"',
            'id="stress-test-btn"',
            'id="vis-breakpoint-btn"',
            'id="due-review-counter"',
            'id="sr-radar-card"',
        ):
            self.assertIn(required_id, html)

    def test_copilot_answers_specific_question_despite_unfinished_syntax_line(self) -> None:
        day2_mid_edit_py = (
            "def isAnagram(s: str, t: str) -> bool:\n"
            "    # Write your O(N) frequency-counting solution here\n"
            "    seen = {}\n"
            "    \n"
            "    for i in s:\n"
            "        if i in seen:\n"
            '            i["s"] = seen\n'
            "        else:\n"
            "            continue\n"
            "    \n"
            "    for j in t:\n"
            "        if j in  \n"
        )
        res = server.diagnose_in_chat(
            2,
            "python",
            day2_mid_edit_py,
            "how do I add the frequency of letters I've seen",
            history=[],
        )
        self.assertTrue(res["ok"])
        self.assertNotIn("Python expects a colon", res["reply"])
        self.assertIn("seen[i]", res["reply"])
        self.assertEqual(res["highlightLine"], 7)

    def test_v17_hidden_tests_resizing_and_draft_persistence(self) -> None:
        # 1. Verify every problem across all 120 days has both visibleTestCases and hiddenTestCases
        for prob in cd.PROBLEMS:
            vis = prob.get("visibleTestCases", [])
            hid = prob.get("hiddenTestCases", [])
            self.assertGreaterEqual(len(vis), 1, f"Day {prob['day']} missing visibleTestCases")
            self.assertGreaterEqual(len(hid), 1, f"Day {prob['day']} missing hiddenTestCases")
            self.assertGreaterEqual(len(prob["testCases"]), 2, f"Day {prob['day']} should have >= 2 total testCases")
            self.assertEqual(len(prob["testCases"]), len(vis) + len(hid))
            for htc in hid:
                self.assertTrue(htc.get("hidden"), f"Day {prob['day']} hidden test missing hidden=True")
                self.assertTrue(htc.get("edgeReason"), f"Day {prob['day']} hidden test missing edgeReason")

        # 2. Verify execute_user_code returns hidden flags, edgeReason, visiblePassed/hiddenPassed across all 29 unique solvers
        seen_funcs = set()
        for prob in cd.PROBLEMS:
            fn = prob["funcName"]
            if fn in seen_funcs:
                continue
            seen_funcs.add(fn)
            py_res = server.execute_user_code(prob["day"], "python", prob["solutionCode"]["python"])
            self.assertTrue(py_res["ok"], f"Day {prob['day']} ({fn}) failed ok")
            self.assertTrue(py_res["allPassed"], f"Day {prob['day']} ({fn}) failed hidden/visible tests: {py_res.get('results')}")
            self.assertGreaterEqual(py_res.get("visibleTotal", 0), 1)
            self.assertGreaterEqual(py_res.get("hiddenTotal", 0), 1)
            self.assertEqual(py_res["visiblePassed"], py_res["visibleTotal"])
            self.assertEqual(py_res["hiddenPassed"], py_res["hiddenTotal"])
            hidden_results = [r for r in py_res["results"] if r.get("hidden")]
            self.assertEqual(len(hidden_results), py_res["hiddenTotal"])
            self.assertTrue(all(r.get("edgeReason") for r in hidden_results))

        # 3. Verify UI markup for resizable boxes, Reset Layout, Reveal Hidden Cases, and live draft auto-save
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for required_token in (
            'id="reset-layout-btn"',
            'id="editor-reset-layout-btn"',
            'id="toggle-hidden-cases-btn"',
            'id="console-reveal-hidden-btn"',
            'id="draft-save-status"',
            "scheduleDraftSave",
            "flushDraftSaveNow",
            "resetLayoutSizes",
            "initResizableBoxes",
        ):
            self.assertIn(required_token, html)

    def test_v18_editor_keyboard_shortcuts_and_multiline_commenting(self) -> None:
        import subprocess
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for required_token in (
            'id="shortcuts-palette-btn"',
            'id="toggle-comment-btn"',
            'id="command-palette-modal"',
            'id="cmd-palette-search"',
            "toggleCommentSelection",
            "indentOrOutdentSelection",
            "moveSelectedLines",
            "duplicateSelectedLines",
            "deleteSelectedLines",
            "openCommandPalette",
        ):
            self.assertIn(required_token, html)

        # Verify actual multi-line comment / uncomment & multi-line Tab indent behaviour via Node
        import json

        html_path_js = json.dumps(str(server.PUBLIC_DIR / "index.html"))
        js_harness = f"const HTML_PATH = {html_path_js};\n" + r"""
const fs = require('fs');
const html = fs.readFileSync(HTML_PATH, 'utf8');
const m = html.match(/function replaceTextareaRangePreservingUndo[\s\S]*?function deleteSelectedLines\(\) \{[\s\S]*?\n    \}/);
if (!m) throw new Error('Could not extract editor shortcut functions');

let state = { activeLang: 'python' };
let statusText = '';
const ta = {
  value: '',
  selectionStart: 0,
  selectionEnd: 0,
  focus() {},
  setSelectionRange(s, e) { this.selectionStart = s; this.selectionEnd = e; },
};
const document = {
  getElementById(id) {
    if (id === 'code-editor') return ta;
    if (id === 'run-status-summary') return { set textContent(v) { statusText = v; } };
    return null;
  },
  execCommand() { return false; },
};
function closeAutocomplete() {}
function updateEditorRender() {}
function scheduleDraftSave() {}

eval(m[0]);

// Test 1: Multi-line comment in Python at common indentation (4 spaces)
ta.value = "def twoSum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if x in seen:\n            return [seen[x], i]";
ta.selectionStart = ta.value.indexOf("    seen = {}");
ta.selectionEnd = ta.value.length;
toggleCommentSelection();
const expectedCommentedPy = "def twoSum(nums, target):\n    # seen = {}\n    # for i, x in enumerate(nums):\n    #     if x in seen:\n    #         return [seen[x], i]";
if (ta.value !== expectedCommentedPy) {
  throw new Error('Mismatch after multi-line comment:\n' + ta.value);
}

// Test 2: Pressing Ctrl+/ again uncomments all 4 selected lines restoring exact indentation
toggleCommentSelection();
const expectedUncommentedPy = "def twoSum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if x in seen:\n            return [seen[x], i]";
if (ta.value !== expectedUncommentedPy) {
  throw new Error('Mismatch after multi-line uncomment:\n' + ta.value);
}

// Test 3: Go / TypeScript uses '// ' for multi-line comments
state.activeLang = 'go';
ta.value = "func f() {\n    a := 1\n    b := 2\n}";
ta.selectionStart = ta.value.indexOf("    a := 1");
ta.selectionEnd = ta.value.indexOf("b := 2") + 6;
toggleCommentSelection();
if (ta.value !== "func f() {\n    // a := 1\n    // b := 2\n}") {
  throw new Error('Mismatch in Go comment:\n' + ta.value);
}
toggleCommentSelection();
if (ta.value !== "func f() {\n    a := 1\n    b := 2\n}") {
  throw new Error('Mismatch in Go uncomment:\n' + ta.value);
}

// Test 4: Multi-line Tab indent & Shift+Tab outdent
indentOrOutdentSelection(false);
if (ta.value !== "func f() {\n        a := 1\n        b := 2\n}") {
  throw new Error('Mismatch in multi-line Tab indent:\n' + ta.value);
}
indentOrOutdentSelection(true);
if (ta.value !== "func f() {\n    a := 1\n    b := 2\n}") {
  throw new Error('Mismatch in multi-line Shift+Tab outdent:\n' + ta.value);
}
console.log('ALL_JS_SHORTCUT_CHECKS_OK');
"""
        proc = subprocess.run(
            [server.NODE_BIN, "-e", js_harness],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("ALL_JS_SHORTCUT_CHECKS_OK", proc.stdout)

    def test_v181_sidepanel_responsive_header_and_fullscreen_controls(self) -> None:
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for required_token in (
            'class="header-window-actions"',
            'id="fullscreen-btn"',
            '<a class="icon-btn icon-link-btn" id="popout-btn"',
            'target="_blank"',
            'function toggleFullScreen()',
            'function openFullBrowserTab()',
            'function syncPopoutLink()',
            'class="tab-label-short"',
            '@media (max-width: 1060px)',
            '@media (max-width: 740px)',
            '@media (max-width: 460px)',
            'flex-wrap: wrap;',
        ):
            self.assertIn(required_token, html)

        # Ensure .stats-strip does NOT stay flex-wrap: nowrap and cause overlap in narrow sidepanels
        stats_idx = html.index(".stats-strip {")
        stats_block = html[stats_idx:stats_idx + 220]
        self.assertIn("flex-wrap: wrap;", stats_block)
        self.assertNotIn("flex-wrap: nowrap;", stats_block)

    def test_v182_solution_pre_formatting_and_reliable_state_persistence(self) -> None:
        import http.client
        import json
        import threading

        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")

        # 1. Solution code <pre> must use display: block (.solution-code-pre), never flex-column .example-item
        self.assertIn('<pre id="solution-code-display" class="solution-code-pre"></pre>', html)
        self.assertNotIn('id="solution-code-display" class="example-item"', html)
        sol_css_idx = html.index(".solution-code-pre {")
        sol_css_block = html[sol_css_idx:html.index("}", sol_css_idx) + 1]
        self.assertIn("display: block;", sol_css_block)
        self.assertIn("white-space: pre;", sol_css_block)
        self.assertNotIn("display: flex;", sol_css_block)

        # 2. Draft auto-save / blur flush must be guarded by draftDirty and never overwrite currentDay
        flush_idx = html.index("function flushDraftSaveNow()")
        flush_block = html[flush_idx:flush_idx + 600]
        self.assertIn("if (!state.initialized || !state.draftDirty) return;", flush_block)
        self.assertNotIn("currentDay:", flush_block)

        sched_idx = html.index("function scheduleDraftSave()")
        sched_block = html[sched_idx:sched_idx + 600]
        self.assertNotIn("currentDay:", sched_block)
        self.assertIn("syncStateFromServer", html)

        # 3. End-to-end HTTP persistence: passing /api/run marks day solved; /api/state advances past solved days
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def post_json(path: str, payload: dict) -> dict:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                try:
                    raw = json.dumps(payload).encode("utf-8")
                    conn.request("POST", path, body=raw, headers={"Content-Type": "application/json"})
                    resp = conn.getresponse()
                    body = resp.read().decode("utf-8")
                    self.assertEqual(resp.status, 200, f"POST {path} returned {resp.status}: {body}")
                    return json.loads(body)
                finally:
                    conn.close()

            def get_json(path: str) -> dict:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                try:
                    conn.request("GET", path)
                    resp = conn.getresponse()
                    body = resp.read().decode("utf-8")
                    self.assertEqual(resp.status, 200, f"GET {path} returned {resp.status}: {body}")
                    return json.loads(body)
                finally:
                    conn.close()

            for day in (1, 2, 3):
                prob = cd.PROBLEMS_BY_DAY[day]
                run_res = post_json("/api/run", {
                    "day": day,
                    "language": "python",
                    "code": prob["solutionCode"]["python"],
                })
                self.assertTrue(run_res["ok"])
                self.assertTrue(run_res["allPassed"])
                # Running tests or visualising code must NOT silently mark a day solved
                self.assertNotIn(str(day), run_res["progress"]["solvedDays"])
                submit_res = post_json("/api/progress", {
                    "day": day,
                    "markSolved": True,
                    "advanceToNext": True,
                    "rating": "Good",
                    "language": "python",
                })
                self.assertTrue(submit_res["ok"])
                self.assertIn(str(day), submit_res["progress"]["solvedDays"])

            # A draft-only save for Day 1 must NOT reset currentDay back to 1
            post_json("/api/progress", {"day": 1, "language": "python", "draft": "# reviewed day 1"})
            # Stale draftsBatch must NOT clobber newer server drafts
            post_json("/api/progress", {"draftsBatch": {"1:python": "# stale local draft", "4:python": "# fresh day 4"}})
            state_res = get_json("/api/state")
            self.assertTrue(state_res["ok"])
            self.assertEqual(state_res["progress"]["currentDay"], 4)
            self.assertEqual(sorted(state_res["progress"]["solvedDays"].keys()), ["1", "2", "3"])
            self.assertEqual(state_res["progress"]["drafts"]["1:python"], "# reviewed day 1")
            self.assertEqual(state_res["progress"]["drafts"]["4:python"], "# fresh day 4")

            # Manual add/remove solved toggle + sync=1 preserves viewing a solved day
            unmark_res = post_json("/api/progress", {"day": 3, "unmarkSolved": True, "currentDay": 3})
            self.assertTrue(unmark_res["ok"])
            self.assertNotIn("3", unmark_res["progress"]["solvedDays"])
            self.assertEqual(sorted(unmark_res["progress"]["solvedDays"].keys()), ["1", "2"])

            # Viewing already-solved Day 2 and re-syncing via ?sync=1 or fresh boot (/api/state) remembers last visited Day 2
            post_json("/api/progress", {"currentDay": 2})
            sync_res = get_json("/api/state?sync=1")
            self.assertEqual(sync_res["progress"]["currentDay"], 2)
            self.assertEqual(sync_res["progress"]["lastVisited"]["day"], 2)

            # Fresh boot (/api/state without sync=1) remembers last visited solved Day 2 without auto-skipping
            boot_res = get_json("/api/state")
            self.assertEqual(boot_res["progress"]["currentDay"], 2)
            self.assertEqual(boot_res["progress"]["lastVisited"]["day"], 2)

            # Manual Mark Solved (default advanceToNext=False) keeps currentDay on Day 3
            readd_res = post_json("/api/progress", {
                "day": 3,
                "markSolved": True,
                "rating": "Good",
                "language": "python",
                "currentDay": 3,
            })
            self.assertTrue(readd_res["ok"])
            self.assertIn("3", readd_res["progress"]["solvedDays"])
            self.assertEqual(readd_res["progress"]["currentDay"], 3)
            self.assertEqual(readd_res["progress"]["lastVisited"]["day"], 3)
        finally:
            srv.shutdown()
            srv.server_close()

        # 4. Manual add/remove solved UI controls exist in Day Strip, Tab 3, and Tab 4 Roadmap
        self.assertIn('id="toggle-solved-btn"', html)
        self.assertIn('id="unmark-solved-tab3-btn"', html)
        self.assertIn('data-toggle-solved-day=', html)
        self.assertIn('async function toggleSolvedForDay(', html)
        self.assertIn("apiGet('/api/state?sync=1')", html)

    def test_v190_compiled_hidden_edge_cases_and_playbook(self) -> None:
        import http.client
        import json
        import threading

        # 1. Every single one of the 120 problems has >= 5 non-duplicate, categorised hidden edge cases
        seen_funcs = set()
        for prob in cd.PROBLEMS:
            vis = prob.get("visibleTestCases", [])
            hid = prob.get("hiddenTestCases", [])
            self.assertGreaterEqual(len(hid), 5, f"Day {prob['day']} ({prob['funcName']}) must have >= 5 hidden cases")
            vis_args = {json.dumps(tc["args"], sort_keys=True) for tc in vis}
            seen_hid = set()
            for tc in hid:
                self.assertTrue(tc.get("hidden"))
                self.assertTrue(tc.get("category"), f"Day {prob['day']} missing category")
                self.assertTrue(tc.get("edgeReason"), f"Day {prob['day']} missing edgeReason")
                key = json.dumps(tc["args"], sort_keys=True)
                self.assertNotIn(key, vis_args, f"Day {prob['day']} hidden case duplicates visible args: {key}")
                self.assertNotIn(key, seen_hid, f"Day {prob['day']} duplicate hidden args: {key}")
                seen_hid.add(key)
            self.assertGreaterEqual(len(prob.get("edgeCaseChecklist", [])), 3)
            seen_funcs.add(prob["funcName"])

        self.assertEqual(len(seen_funcs), 29)
        self.assertGreaterEqual(len(cd.EDGE_CASE_PLAYBOOK), 9)
        self.assertGreaterEqual(len(cd.EDGE_CASE_RESOURCES), 4)

        # 2. All 29 unique engines pass all sample + compiled hidden edge cases in Python and TypeScript
        tested = set()
        for prob in cd.PROBLEMS:
            fn = prob["funcName"]
            if fn in tested:
                continue
            tested.add(fn)
            for lang in ("python", "typescript"):
                res = server.execute_user_code(prob["day"], lang, prob["solutionCode"][lang])
                self.assertTrue(res.get("ok"), f"Day {prob['day']} {fn} ({lang}) error: {res}")
                self.assertTrue(res.get("allPassed"), f"Day {prob['day']} {fn} ({lang}) failed: {res}")
                self.assertGreaterEqual(res.get("hiddenTotal", 0), 5)
                self.assertEqual(res.get("hiddenPassed"), res.get("hiddenTotal"))
                hidden_rows = [r for r in res.get("results", []) if r.get("hidden")]
                self.assertTrue(all(r.get("category") for r in hidden_rows))

        # 3. Live HTTP /api/state exposes edgeCasePlaybook and edgeCaseResources
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                conn.request("GET", "/api/state")
                resp = conn.getresponse()
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(resp.status, 200)
                self.assertTrue(payload["ok"])
                self.assertEqual(len(payload["edgeCasePlaybook"]), len(cd.EDGE_CASE_PLAYBOOK))
                self.assertEqual(len(payload["edgeCaseResources"]), len(cd.EDGE_CASE_RESOURCES))
            finally:
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()

        # 4. UI DOM hooks exist for Pre-Submit Checklist, Category Pills, and Tab 4 Edge-Case Playbook
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="prob-edge-checklist-box"',
            'id="edge-case-playbook-card"',
            'id="playbook-filter-bar"',
            'id="playbook-checks-grid"',
            'id="playbook-resources-grid"',
            'class="edge-cat-pill"',
            'function renderProblemEdgeChecklist(',
            'function renderEdgeCasePlaybook(',
        ):
            self.assertIn(needle, html)

    def test_v191_python_tutor_side_by_side_code_sync(self) -> None:
        import http.client
        import json
        import threading

        # 1. Verify execute_user_code returns tracedCode and accurate line mappings including return events
        day3_code = (
            "def get_first_element(group):\n"
            "    return group[0]\n"
            "\n"
            "def groupAnagrams(strs: list[str]) -> list[list[str]]:\n"
            "    groups = {}\n"
            "    for word in strs:\n"
            "        key = ''.join(sorted(word))\n"
            "        groups.setdefault(key, []).append(word)\n"
            "    res = [sorted(v) for v in groups.values()]\n"
            "    res.sort(key=get_first_element)\n"
            "    return res\n"
        )
        run_res = server.execute_user_code(3, "python", day3_code)
        self.assertTrue(run_res["ok"])
        self.assertEqual(run_res.get("tracedCode"), day3_code)
        self.assertEqual(run_res.get("tracedLanguage"), "python")
        frames = run_res["results"][0]["frames"]
        self.assertGreaterEqual(len(frames), 8)
        code_lines = day3_code.splitlines()
        for fr in frames:
            ln = fr["line"]
            self.assertGreaterEqual(ln, 1)
            self.assertLessEqual(ln, len(code_lines))
            self.assertEqual(fr["source"], code_lines[ln - 1].strip())
        self.assertEqual(frames[-1]["event"], "return")

        # 2. Verify POST /api/optimal-trace returns real sys.settrace frames and exact optimal Python source
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                body = json.dumps({"day": 3, "tcIdx": 0}).encode("utf-8")
                conn.request("POST", "/api/optimal-trace", body=body, headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(resp.status, 200)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["day"], 3)
                self.assertIn("def groupAnagrams", payload["code"])
                self.assertGreaterEqual(len(payload["frames"]), 5)
                opt_lines = payload["code"].splitlines()
                for fr in payload["frames"]:
                    self.assertEqual(fr["source"], opt_lines[fr["line"] - 1].strip())
            finally:
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()

        # 3. Verify side-by-side Code Trace DOM & JS synchronisation hooks in public/index.html
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="pt-workspace-split"',
            'id="pt-code-pane"',
            'id="pt-code-lines"',
            'id="pt-active-line-pill"',
            'id="pt-split-resizer"',
            'id="pt-toggle-code-btn"',
            'function renderPtCodePane(',
            'function loadOptimalTraceFrames(',
            'function togglePtCodePane(',
            '/api/optimal-trace',
        ):
            self.assertIn(needle, html)

    def test_v192_guided_coaching_score_explanations_and_full_marks(self) -> None:
        import http.client
        import json
        import threading

        def assert_rubric_invariants(res: dict) -> None:
            self.assertTrue(res.get("ok"))
            rubric = res.get("rubric") or []
            self.assertEqual(len(rubric), 5)
            axis_sum = 0
            gap_sum = 0
            for ax in rubric:
                criteria = ax.get("criteria") or []
                self.assertEqual(len(criteria), 4, f"Axis {ax['axis']} must have 4 transparent criteria")
                self.assertEqual(sum(c["possible"] for c in criteria), 20)
                self.assertEqual(sum(c["earned"] for c in criteria), ax["score"])
                self.assertEqual(ax["max"], 20)
                self.assertEqual(ax["pointsToFullMarks"], 20 - ax["score"])
                self.assertTrue(ax.get("whyScore"), f"Axis {ax['axis']} missing whyScore")
                self.assertTrue(ax.get("howToFullMarks"), f"Axis {ax['axis']} missing howToFullMarks")
                for c in criteria:
                    self.assertTrue(c.get("evidence"), f"Criterion {c['label']} missing evidence")
                    self.assertEqual(c["gap"], c["possible"] - c["earned"])
                    if c["gap"] > 0:
                        self.assertTrue(c.get("howToImprove"), f"Missing howToImprove for {c['label']}")
                        gap_sum += c["gap"]
                    else:
                        self.assertEqual(c["status"], "met")
                axis_sum += ax["score"]
            self.assertEqual(res["totalScore"], axis_sum)
            self.assertEqual(res["pointsToFullMarks"], 100 - axis_sum)
            self.assertEqual(sum(i["gain"] for i in res.get("improvementPlan", [])), gap_sum)
            self.assertEqual(gap_sum, 100 - axis_sum)

        # 1. All 29 unique optimal Python solutions (plus TS/Go spot checks) earn full 100/100 marks
        seen_funcs = set()
        for prob in cd.PROBLEMS:
            fn = prob["funcName"]
            if fn in seen_funcs:
                continue
            seen_funcs.add(fn)
            opt_res = server.analyse_user_code(prob["day"], "python", prob["solutionCode"]["python"])
            assert_rubric_invariants(opt_res)
            self.assertEqual(
                opt_res["totalScore"],
                100,
                f"Day {prob['day']} ({fn}) optimal python did not earn 100/100: {opt_res['improvementPlan']}",
            )
            self.assertEqual(opt_res["improvementPlan"], [])
            self.assertTrue(opt_res.get("followUpStretch"))

        for sample_day in (1, 9, 43, 76):
            prob = cd.PROBLEMS_BY_DAY[sample_day]
            for lang in ("typescript", "go"):
                res_lang = server.analyse_user_code(sample_day, lang, prob["solutionCode"][lang])
                assert_rubric_invariants(res_lang)
                self.assertEqual(res_lang["totalScore"], 100, f"Day {sample_day} {lang} got {res_lang['totalScore']}")

        # 2. Starter skeleton explains why score is low and provides full improvement roadmap
        skel_res = server.analyse_user_code(1, "python", cd.PROBLEMS_BY_DAY[1]["starterCode"]["python"])
        assert_rubric_invariants(skel_res)
        self.assertLess(skel_res["totalScore"], 25)
        self.assertGreater(len(skel_res["improvementPlan"]), 10)

        # 3. Syntax error puts compilation fix first with exact targetLine
        syntax_code = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = {}\n"
            "    for i, x in enumerate(nums):\n"
            "        comp = target - x\n"
            "        if comp in seen:\n"
            "            return [seen{comp}, i]\n"
            "        seen[x] = i\n"
            "    return []\n"
        )
        syn_res = server.analyse_user_code(1, "python", syntax_code)
        assert_rubric_invariants(syn_res)
        self.assertEqual(syn_res["improvementPlan"][0]["criterion"], "Clean compilation & syntax")
        self.assertEqual(syn_res["improvementPlan"][0]["targetLine"], 6)

        # 4. Brute-force O(N^2) passing solution deducts on DSA complexity & explains how to reach O(N)
        brute_code = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    n = len(nums)\n"
            "    for i in range(n):\n"
            "        for j in range(i + 1, n):\n"
            "            if nums[i] + nums[j] == target:\n"
            "                return [i, j]\n"
            "    return []\n"
        )
        brute_res = server.analyse_user_code(1, "python", brute_code)
        assert_rubric_invariants(brute_res)
        self.assertLess(brute_res["totalScore"], 90)
        dsa_axis = brute_res["rubric"][0]
        self.assertLess(dsa_axis["score"], 15)
        self.assertIn("depth 2", dsa_axis["criteria"][1]["evidence"])
        self.assertTrue(dsa_axis["criteria"][1]["howToImprove"])

        # 5. Hidden O(N) list membership scan inside loop is detected and explained
        hidden_scan_code = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    for i, x in enumerate(nums):\n"
            "        need = target - x\n"
            "        if need in nums[i + 1:]:\n"
            "            return [i, nums.index(need, i + 1)]\n"
            "    return []\n"
        )
        scan_res = server.analyse_user_code(1, "python", hidden_scan_code)
        assert_rubric_invariants(scan_res)
        self.assertIn("hidden O(N)", scan_res["rubric"][0]["criteria"][1]["evidence"])

        # 6. Craft deductions (missing types, debug print on Line 5, single-letter container) cite exact fixes
        craft_code = (
            "def twoSum(nums, target):\n"
            "    d = {}\n"
            "    for i in range(len(nums)):\n"
            "        x = nums[i]\n"
            "        print(i, x)\n"
            "        if target - x in d:\n"
            "            return [d[target - x], i]\n"
            "        d[x] = i\n"
            "    return []\n"
        )
        craft_res = server.analyse_user_code(1, "python", craft_code)
        assert_rubric_invariants(craft_res)
        self.assertEqual(craft_res["rubric"][0]["score"], 20)
        prog_axis = craft_res["rubric"][1]
        self.assertLess(prog_axis["score"], 16)
        self.assertIn("Line 5", prog_axis["criteria"][3]["evidence"])
        self.assertEqual(prog_axis["criteria"][3]["targetLine"], 5)

        # 7. Live HTTP POST /api/analyse returns structured breakdown and UI hooks exist
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                body = json.dumps({"day": 1, "language": "python", "code": brute_code}).encode("utf-8")
                conn.request("POST", "/api/analyse", body=body, headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(resp.status, 200)
                assert_rubric_invariants(payload)
                self.assertGreater(len(payload["improvementPlan"]), 0)
            finally:
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()

        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="analysis-gap-pill"',
            'id="analysis-improvement-plan"',
            'id="toggle-all-criteria-btn"',
            'function renderAnalysisResult(',
            'function resetAnalysisPanel(',
            'function ensureFreshAnalysis(',
            'function jumpToEditorLineFromCoaching(',
            'function askCopilotAboutImprovement(',
        ):
            self.assertIn(needle, html)

    def test_v200_curated_lists_sql50_and_exam_modes(self) -> None:
        import http.client
        import json
        import threading
        import curated_lists as cl

        # 1. Verify exact sheet problem counts, Core 70 split, and DAG nodes
        sheets_by_id = {s["id"]: s for s in cl.SHEETS}
        self.assertEqual(set(sheets_by_id.keys()), {"grind-75", "leetcode-150", "neetcode-150", "sql-50"})
        for sid, expected_cnt in (
            ("grind-75", 75),
            ("leetcode-150", 150),
            ("neetcode-150", 150),
            ("sql-50", 50),
        ):
            ids = []
            for g in sheets_by_id[sid]["groups"]:
                ids.extend(g["problemIds"])
            self.assertEqual(len(set(ids)), expected_cnt, f"{sid} count mismatch")

        core70 = [
            pid for pid, pr in cl.PROBLEMS_BY_ID.items()
            if pr.get("sheetMeta", {}).get("grind-75", {}).get("isCore70") is True
        ]
        self.assertEqual(len(core70), 70)
        self.assertEqual(len(cl.PROBLEMS_BY_ID), 286)
        self.assertEqual(len([n for n in cl.DAG_NODES if n["sheetId"] == "neetcode-150"]), 18)
        self.assertEqual(len([n for n in cl.DAG_NODES if n["sheetId"] == "sql-50"]), 7)

        # 2. Verify live HTTP endpoints (/api/curated, /studio_v2.js, /api/run SQL & DSA, /api/optimal-trace, /api/analyse, /api/progress sync)
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def req_json(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    raw = json.dumps(body).encode("utf-8") if body is not None else None
                    hdrs = {"Content-Type": "application/json"} if raw is not None else {}
                    conn.request(method, path, body=raw, headers=hdrs)
                    resp = conn.getresponse()
                    return resp.status, json.loads(resp.read().decode("utf-8"))
                finally:
                    conn.close()

            st, cur_payload = req_json("GET", "/api/curated")
            self.assertEqual(st, 200)
            self.assertTrue(cur_payload["ok"])
            self.assertEqual(len(cur_payload["sheets"]), 4)
            self.assertEqual(len(cur_payload["problemsById"]), 286)

            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                conn.request("GET", "/studio_v2.js")
                r_js = conn.getresponse()
                js_body = r_js.read().decode("utf-8")
                self.assertEqual(r_js.status, 200)
                self.assertIn("window.StudioV2", js_body)
            finally:
                conn.close()

            # SQL 50 live run (pass + fail + error) and 100/100 rubric score
            p_sql = cl.get_problem("sql-1757")
            st, sql_ok = req_json("POST", "/api/run", {"problemId": "sql-1757", "language": "sql", "code": p_sql["solutionCode"]["sql"]})
            self.assertEqual(st, 200)
            self.assertTrue(sql_ok["isSql"])
            self.assertTrue(sql_ok["allPassed"])
            self.assertEqual(sql_ok["results"][0]["expectedColumns"], ["product_id"])

            st, sql_bad = req_json("POST", "/api/run", {"problemId": "sql-1757", "language": "sql", "code": "SELECT product_id FROM Products;"})
            self.assertEqual(st, 200)
            self.assertFalse(sql_bad["allPassed"])

            st, sql_ana = req_json("POST", "/api/analyse", {"problemId": "sql-1757", "language": "sql", "code": p_sql["solutionCode"]["sql"]})
            self.assertEqual(st, 200)
            self.assertEqual(sql_ana["totalScore"], 100)

            # Curated DSA harnesses (ListNode lc-206, TreeNode lc-226, system-design lc-146) + Python Tutor trace
            for pid in ("lc-206", "lc-226", "lc-146"):
                pr = cl.get_problem(pid)
                st, r_dsa = req_json("POST", "/api/run", {"problemId": pid, "language": "python", "code": pr["solutionCode"]["python"]})
                self.assertEqual(st, 200, f"{pid} HTTP status")
                self.assertTrue(r_dsa["allPassed"], f"{pid} failed: {r_dsa}")

            st, tr_res = req_json("POST", "/api/optimal-trace", {"problemId": "lc-206", "tcIdx": 0})
            self.assertEqual(st, 200)
            self.assertTrue(tr_res["ok"])
            self.assertGreaterEqual(len(tr_res["frames"]), 5)

            st, dsa_ana = req_json("POST", "/api/analyse", {"problemId": "lc-206", "language": "python", "code": cl.get_problem("lc-206")["solutionCode"]["python"]})
            self.assertEqual(st, 200)
            self.assertEqual(dsa_ana["totalScore"], 100)

            # Unified cross-list solved sync (lc-1 <-> Day 1) + bookmarks + pressureScores + interview/OA history
            st, sync_on = req_json("POST", "/api/progress", {"toggleSolvedCurated": True, "problemId": "lc-1", "solved": True})
            self.assertEqual(st, 200)
            self.assertIn("1", sync_on["progress"]["solvedLcIds"])
            self.assertIn("1", sync_on["progress"]["solvedDays"])

            st, sync_off = req_json("POST", "/api/progress", {"toggleSolvedCurated": True, "problemId": "lc-1", "solved": False})
            self.assertEqual(st, 200)
            self.assertNotIn("1", sync_off["progress"]["solvedLcIds"])
            self.assertNotIn("1", sync_off["progress"]["solvedDays"])

            st, bm_res = req_json("POST", "/api/progress", {"toggleBookmark": True, "key": "lc-206"})
            self.assertEqual(st, 200)
            self.assertIn("lc-206", bm_res["progress"]["bookmarks"])

            st, pr_res = req_json("POST", "/api/progress", {"savePressureScore": True, "key": "lc-206", "score": 850, "tier": 2, "maxStreak": 6})
            self.assertEqual(st, 200)
            self.assertEqual(pr_res["progress"]["pressureScores"]["lc-206"]["bestScore"], 850)

            st, iv_res = req_json("POST", "/api/progress", {"saveInterviewRecord": {"date": "2026-11-20", "title": "LC 206: Reverse Linked List", "score": 92}})
            self.assertEqual(st, 200)
            self.assertEqual(iv_res["progress"]["interviewHistory"][0]["score"], 92)

            st, oa_res = req_json("POST", "/api/progress", {"saveOaRecord": {"date": "2026-11-20", "totalPoints": 270, "maxPoints": 300}})
            self.assertEqual(st, 200)
            self.assertEqual(oa_res["progress"]["oaHistory"][0]["totalPoints"], 270)
        finally:
            srv.shutdown()
            srv.server_close()

        # 3. Verify v2.0.0 DOM & JS hooks in public/index.html and public/studio_v2.js
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        v2_js = (server.PUBLIC_DIR / "studio_v2.js").read_text(encoding="utf-8")
        for needle in (
            'data-tab="lists"',
            'id="pane-lists"',
            'id="curated-context-banner"',
            'id="prob-sql-schema-box"',
            'id="toggle-bookmark-btn"',
            'id="editor-find-bar"',
            'id="copilot-prompt-mode-select"',
            'id="copy-for-ai-btn"',
            'id="coach-mode-bar"',
            'id="coach-panel-pressure"',
            'id="coach-panel-exam"',
            'id="solution-approaches-card"',
            'src="/studio_v2.js"',
        ):
            self.assertIn(needle, html)
        for needle in (
            'renderCuratedListsTab',
            'buildDagSvgHtml',
            'renderSqlTestResults',
            'initPressureDrillForProblem',
            'startMockInterview',
            'startOaSimulation',
            'renderApproachesMatrix',
        ):
            self.assertIn(needle, v2_js)

    def test_security_hardening(self) -> None:
        import http.client
        import json
        import stat
        import subprocess
        import threading
        import curated_lists as cl

        # 1. SQLite authorizer blocks stacked SQLi, ATTACH DATABASE, PRAGMA, and allows all 50 SQL 50 queries
        sql_probs = [p for p in cl.PROBLEMS_BY_ID.values() if p.get("isSql")]
        self.assertEqual(len(sql_probs), 50)
        for p in sql_probs:
            ref = p.get("referenceSql") or p.get("solutionCode", {}).get("sql", "")
            res = cl.execute_curated_sql(p, ref)
            self.assertTrue(res["allPassed"], f"SQL 50 {p['id']} failed under authorizer: {res}")

        for evil_sql in (
            "ATTACH DATABASE '/tmp/pwn.db' AS pwn;",
            "DELETE FROM Person; ATTACH DATABASE '/tmp/pwn.db' AS pwn;",
            "PRAGMA database_list;",
            "VACUUM INTO '/tmp/pwn.db';",
        ):
            evil_res = cl.execute_curated_sql(cl.get_problem("sql-196"), evil_sql)
            self.assertFalse(evil_res["allPassed"])
            self.assertTrue(evil_res.get("error"), f"Evil SQL did not error: {evil_sql}")

        # 2. Subprocess env hygiene strips secrets from user-submitted Python/TS/curated code
        orig_secret = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "test-super-secret-value"
        try:
            leak_py = (
                "import os\n"
                "def twoSum(nums: list[int], target: int) -> list[int]:\n"
                "    print(os.environ.get('GEMINI_API_KEY', 'STRIPPED'))\n"
                "    return [0, 1]\n"
            )
            r_py = server.execute_user_code(1, "python", leak_py)
            self.assertIn("STRIPPED", r_py["results"][0]["stdout"])
            self.assertNotIn("test-super-secret-value", r_py["results"][0]["stdout"])

            r_cur = cl.execute_curated_python(cl.get_problem("lc-1"), leak_py, capture_frames=False)
            self.assertIn("STRIPPED", r_cur["results"][0]["stdout"])
            self.assertNotIn("test-super-secret-value", r_cur["results"][0]["stdout"])
        finally:
            if orig_secret is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = orig_secret

        # 3. Non-integer exc.lineno in user Python code cannot inject XSS into errorLine
        evil_exc_py = (
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    e = ValueError('boom')\n"
            "    e.lineno = '<img src=x onerror=alert(1)>'\n"
            "    raise e\n"
        )
        r_exc = server.execute_user_code(1, "python", evil_exc_py)
        self.assertTrue(r_exc["ok"])
        self.assertIsInstance(r_exc["results"][0]["errorLine"], int)

        # 4. HTTP hardening: security headers, 400 on bad types, 404 on traversal/null-byte, stored XSS sanitization, 0600 perms
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                conn.request("GET", "/api/state")
                r_state = conn.getresponse()
                r_state.read()
                self.assertEqual(r_state.status, 200)
                self.assertEqual(r_state.getheader("X-Content-Type-Options"), "nosniff")
                self.assertEqual(r_state.getheader("Referrer-Policy"), "no-referrer")

                conn.request("GET", "/../../etc/passwd")
                r_trav = conn.getresponse()
                r_trav.read()
                self.assertEqual(r_trav.status, 404)

                conn.request("GET", "/index.html%00.js")
                r_null = conn.getresponse()
                r_null.read()
                self.assertEqual(r_null.status, 404)

                bad_body = json.dumps({"day": "not-an-int", "language": "python", "code": "x"}).encode("utf-8")
                conn.request("POST", "/api/run", body=bad_body, headers={"Content-Type": "application/json"})
                r_bad = conn.getresponse()
                bad_json = json.loads(r_bad.read().decode("utf-8"))
                self.assertEqual(r_bad.status, 400)
                self.assertFalse(bad_json["ok"])

                xss_rec = json.dumps({
                    "saveInterviewRecord": {
                        "date": "2026-11-20",
                        "title": "<script>alert(1)</script>",
                        "score": "<img src=x onerror=alert(1)>",
                    }
                }).encode("utf-8")
                conn.request("POST", "/api/progress", body=xss_rec, headers={"Content-Type": "application/json"})
                r_xss = conn.getresponse()
                r_xss.read()
                self.assertEqual(r_xss.status, 400)

                ok_rec = json.dumps({
                    "saveInterviewRecord": {
                        "date": "2026-11-20",
                        "title": "Two Sum",
                        "score": 95,
                        "elapsedMin": 20,
                    }
                }).encode("utf-8")
                conn.request("POST", "/api/progress", body=ok_rec, headers={"Content-Type": "application/json"})
                r_ok = conn.getresponse()
                r_ok.read()
                self.assertEqual(r_ok.status, 200)
                mode = stat.S_IMODE(server.PROGRESS_PATH.stat().st_mode)
                self.assertEqual(mode, 0o600)
            finally:
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()

        # 5. Client-side escapeHtml, safeExternalUrl, and formatRichText placeholder hardening via Node
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        html_path_js = json.dumps(str(server.PUBLIC_DIR / "index.html"))
        js_sec_check = f"const HTML_PATH = {html_path_js};\n" + r"""
const fs = require('fs');
const html = fs.readFileSync(HTML_PATH, 'utf8');
const m = html.match(/function escapeHtml\(str\)[\s\S]*?return html;\n    \}/);
if (!m) throw new Error('Could not extract escapeHtml/safeExternalUrl/formatRichText');
const window = { location: { origin: 'http://127.0.0.1:8788' } };
eval(m[0]);
if (escapeHtml(`"'<>&`) !== `&quot;&#39;&lt;&gt;&amp;`) throw new Error('escapeHtml failed');
if (safeExternalUrl('javascript:alert(1)', 'https://leetcode.com') !== 'https://leetcode.com') throw new Error('safeExternalUrl allowed javascript:');
if (safeExternalUrl('https://leetcode.com/problems/two-sum/') !== 'https://leetcode.com/problems/two-sum/') throw new Error('safeExternalUrl rejected https:');
const rt = formatRichText('@@CODEBLOCK_0@@ ```py\nprint("<img src=x>")\n```');
if (rt.includes('<img')) throw new Error('formatRichText unescaped img');
console.log('CLIENT_SECURITY_OK');
"""
        proc = subprocess.run([server.NODE_BIN, "-e", js_sec_check], capture_output=True, text=True, check=True)
        self.assertIn("CLIENT_SECURITY_OK", proc.stdout)

    def test_weekly_qa_regressions_and_edge_cases(self) -> None:
        import http.client
        import json
        import subprocess
        import threading
        import curated_lists as cl

        # 1. SQLite progress-handler timeout interrupts runaway recursive CTE cleanly
        orig_timeout = cl._SQL_TIMEOUT_SECONDS
        cl._SQL_TIMEOUT_SECONDS = 0.05
        try:
            cte_sql = "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM cnt) SELECT * FROM cnt;"
            cte_res = cl.execute_curated_sql(cl.get_problem("sql-1757"), cte_sql)
            self.assertFalse(cte_res["allPassed"])
            self.assertIn("interrupted", str(cte_res.get("error", "")).lower())
        finally:
            cl._SQL_TIMEOUT_SECONDS = orig_timeout

        # 2. HTTP boundary checks: non-object JSON, oversized Content-Length, negative Content-Length -> 400
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                conn.request("POST", "/api/run", body=b"[]", headers={"Content-Type": "application/json"})
                r_arr = conn.getresponse()
                arr_json = json.loads(r_arr.read().decode("utf-8"))
                self.assertEqual(r_arr.status, 400)
                self.assertFalse(arr_json["ok"])

                conn.request("POST", "/api/run", body=b"{}", headers={"Content-Type": "application/json", "Content-Length": "-5"})
                r_neg = conn.getresponse()
                r_neg.read()
                self.assertEqual(r_neg.status, 400)

                oversize = str(server._MAX_REQUEST_BODY_BYTES + 1024)
                conn.putrequest("POST", "/api/run")
                conn.putheader("Content-Type", "application/json")
                conn.putheader("Content-Length", oversize)
                conn.endheaders()
                r_big = conn.getresponse()
                r_big.read()
                self.assertEqual(r_big.status, 400)
            finally:
                conn.close()
        finally:
            srv.shutdown()
            srv.server_close()

        # 3. Lock-safe diagnose_in_chat preserves concurrent progress updates
        with server._PROGRESS_LOCK:
            prog = server.load_progress(auto_advance=False)
            prog["bookmarks"] = ["day-1"]
            server.save_progress(prog)
        chat_res = server.diagnose_in_chat(1, "python", "def twoSum(nums, target):\n    return []\n", "Check my solution")
        self.assertTrue(chat_res["ok"])
        reloaded = server.load_progress(auto_advance=False)
        self.assertIn("day-1", reloaded.get("bookmarks", []))
        self.assertGreaterEqual(len(reloaded.get("chatHistory", {}).get("1", [])), 2)

        # 4. studio_v2.js regression invariants (hiringSignal, literal $ replaceAllMatches, escaped OA/SQL errors)
        v2_js = (server.PUBLIC_DIR / "studio_v2.js").read_text(encoding="utf-8")
        self.assertIn("grade.hiringSignal || grade.signal", v2_js)
        self.assertIn("esc(cur.runResult.error)", v2_js)
        self.assertIn("esc(tc?.stdout", v2_js)
        self.assertIn("function buildCuratedGroupsHtml(", v2_js)
        self.assertIn("ta.value.replace(re, () => rep)", v2_js)

        dollar_check = (
            "const re = new RegExp('foo', 'gi');\n"
            "const rep = '$&$1';\n"
            "const out = 'foo bar'.replace(re, () => rep);\n"
            "if (out !== '$&$1 bar') throw new Error('bad replace: ' + out);\n"
            "console.log('DOLLAR_REPLACE_OK');\n"
        )
        proc = subprocess.run([server.NODE_BIN, "-e", dollar_check], capture_output=True, text=True, check=True)
        self.assertIn("DOLLAR_REPLACE_OK", proc.stdout)

    def test_v210_course_selection_menu_and_persistence(self) -> None:
        import http.client
        import json
        import threading

        # 1. Verify ordered course problem IDs and Grind 70 Core filtering
        self.assertEqual(len(server._ordered_course_problem_ids("grind-75")), 75)
        self.assertEqual(len(server._ordered_course_problem_ids("grind-70")), 70)
        self.assertEqual(len(server._ordered_course_problem_ids("leetcode-150")), 150)
        self.assertEqual(len(server._ordered_course_problem_ids("neetcode-150")), 150)
        self.assertEqual(len(server._ordered_course_problem_ids("sql-50")), 50)

        # 2. Live HTTP course switching, per-course position memory, advanceToNext, and invalid course rejection
        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def req_json(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    raw = json.dumps(body).encode("utf-8") if body is not None else None
                    hdrs = {"Content-Type": "application/json"} if raw is not None else {}
                    conn.request(method, path, body=raw, headers=hdrs)
                    resp = conn.getresponse()
                    return resp.status, json.loads(resp.read().decode("utf-8"))
                finally:
                    conn.close()

            # Switch to LeetCode Top 150 at lc-88
            st, res1 = req_json("POST", "/api/progress", {
                "activeCourse": "leetcode-150",
                "course": "leetcode-150",
                "courseProblemId": "lc-88",
            })
            self.assertEqual(st, 200)
            self.assertEqual(res1["progress"]["activeCourse"], "leetcode-150")
            self.assertEqual(res1["progress"]["coursePositions"]["leetcode-150"], "lc-88")

            # Submit & Next inside LeetCode Top 150 marks lc-88 solved and advances to next unsolved LC 150 problem
            st, res2 = req_json("POST", "/api/progress", {
                "toggleSolvedCurated": True,
                "problemId": "lc-88",
                "course": "leetcode-150",
                "advanceToNext": True,
                "solved": True,
                "rating": "Good",
                "language": "python",
            })
            self.assertEqual(st, 200)
            self.assertIn("88", res2["progress"]["solvedLcIds"])
            self.assertTrue(res2.get("nextProblemId"))
            self.assertNotEqual(res2["nextProblemId"], "lc-88")
            self.assertEqual(res2["progress"]["coursePositions"]["leetcode-150"], res2["nextProblemId"])

            # Switch to Grind 75 at lc-206 and verify reload (/api/state) preserves activeCourse and both coursePositions
            st, res3 = req_json("POST", "/api/progress", {
                "activeCourse": "grind-75",
                "course": "grind-75",
                "courseProblemId": "lc-206",
            })
            self.assertEqual(st, 200)
            self.assertEqual(res3["progress"]["activeCourse"], "grind-75")

            # Invalid course name is ignored safely without corrupting activeCourse
            st, res_bad = req_json("POST", "/api/progress", {"activeCourse": "nonexistent-course"})
            self.assertEqual(st, 200)
            self.assertEqual(res_bad["progress"]["activeCourse"], "grind-75")

            st, state_res = req_json("GET", "/api/state")
            self.assertEqual(st, 200)
            self.assertEqual(state_res["progress"]["activeCourse"], "grind-75")
            self.assertEqual(state_res["progress"]["coursePositions"]["grind-75"], "lc-206")
            self.assertEqual(state_res["progress"]["coursePositions"]["leetcode-150"], res2["nextProblemId"])
        finally:
            srv.shutdown()
            srv.server_close()

        # 3. Verify Course Selection Menu DOM & JS hooks in public/index.html and public/studio_v2.js
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        v2_js = (server.PUBLIC_DIR / "studio_v2.js").read_text(encoding="utf-8")
        for needle in (
            'id="course-select"',
            'value="schedule-120"',
            'value="leetcode-150"',
            'value="grind-75"',
            'value="grind-70"',
            'const COURSES_META =',
            'function getCourseEntries(',
            'function switchCourse(',
        ):
            self.assertIn(needle, html)
        self.assertIn("syncSheetFromCourse", v2_js)

    def test_v220_python_tutor_resizable_and_expandable(self) -> None:
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="pt-fit-height-btn"',
            'id="pt-expand-modal-btn"',
            'id="pt-wrap-btn"',
            'id="pt-font-dec-btn"',
            'id="pt-font-inc-btn"',
            'id="pt-vis-resizer-bar"',
            'id="pt-modal-backdrop"',
            '.visualiser-stage.pt-expanded-modal',
            '.pt-code-lines.pt-code-wrap .pt-code-src',
            'function fitPtHeightToCode(',
            'function togglePtExpandedModal(',
            'function togglePtCodeWrap(',
            'function applyPtCodeFontSize(',
            'max: 1200',
        ):
            self.assertIn(needle, html)


    def test_v230_accepted_submissions_and_practise_again(self) -> None:
        import http.client
        import json
        import threading

        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def req_json(method: str, path: str, body: dict | None = None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    raw = json.dumps(body).encode("utf-8") if body is not None else None
                    hdrs = {"Content-Type": "application/json"} if raw is not None else {}
                    conn.request(method, path, body=raw, headers=hdrs)
                    resp = conn.getresponse()
                    return resp.status, json.loads(resp.read().decode("utf-8"))
                finally:
                    conn.close()

            # 1. Failed or partial submissions are strictly rejected from progress.submissions
            st, r_fail = req_json("POST", "/api/progress", {
                "saveAcceptedSubmission": {
                    "day": 1,
                    "allPassed": False,
                    "passed": 2,
                    "total": 10,
                    "language": "python",
                    "code": "def twoSum(nums, target):\n    return [0, 0]\n",
                },
            })
            self.assertEqual(st, 200)
            self.assertEqual(r_fail["progress"].get("submissions", {}), {})

            # 2. Partial pass claiming allPassed=True is also rejected
            st, r_partial = req_json("POST", "/api/progress", {
                "saveAcceptedSubmission": {
                    "day": 1,
                    "allPassed": True,
                    "passed": 9,
                    "total": 10,
                    "language": "python",
                    "code": "def twoSum(nums, target):\n    return [0, 1]\n",
                },
            })
            self.assertEqual(st, 200)
            self.assertEqual(r_partial["progress"].get("submissions", {}), {})

            # 3. Verified passed Day 1 submission is stored under canonical lc:1 key
            sol_v1 = "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n"
            st, r_ok1 = req_json("POST", "/api/progress", {
                "day": 1,
                "markSolved": True,
                "advanceToNext": False,
                "language": "python",
                "draft": sol_v1,
                "saveAcceptedSubmission": {
                    "day": 1,
                    "allPassed": True,
                    "passed": 10,
                    "total": 10,
                    "runtimeMs": 12.4,
                    "language": "python",
                    "code": sol_v1,
                    "course": "schedule-120",
                    "problemLabel": "Day 1 (LC 1): Two Sum",
                },
            })
            self.assertEqual(st, 200)
            subs_lc1 = r_ok1["progress"]["submissions"].get("lc:1", [])
            self.assertEqual(len(subs_lc1), 1)
            self.assertEqual(subs_lc1[0]["code"], sol_v1)
            self.assertEqual(subs_lc1[0]["passed"], 10)
            self.assertEqual(subs_lc1[0]["total"], 10)

            # 4. Submitting a second, optimal solution on lc-1 from Grind 75 appends newest-first under the same lc:1 key
            sol_v2 = "def twoSum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if target - x in seen:\n            return [seen[target - x], i]\n        seen[x] = i\n"
            st, r_ok2 = req_json("POST", "/api/progress", {
                "toggleSolvedCurated": True,
                "problemId": "lc-1",
                "solved": True,
                "advanceToNext": False,
                "language": "python",
                "draft": sol_v2,
                "saveAcceptedSubmission": {
                    "problemId": "lc-1",
                    "allPassed": True,
                    "passed": 3,
                    "total": 3,
                    "runtimeMs": 1.8,
                    "language": "python",
                    "code": sol_v2,
                    "course": "grind-75",
                    "problemLabel": "LC 1: Two Sum",
                },
            })
            self.assertEqual(st, 200)
            subs_lc1_after = r_ok2["progress"]["submissions"].get("lc:1", [])
            self.assertEqual(len(subs_lc1_after), 2)
            self.assertEqual(subs_lc1_after[0]["code"], sol_v2)
            self.assertEqual(subs_lc1_after[1]["code"], sol_v1)

            # 5. Re-submitting identical code updates newest in-place without noisy duplicate
            st, r_dup = req_json("POST", "/api/progress", {
                "saveAcceptedSubmission": {
                    "problemId": "lc-1",
                    "allPassed": True,
                    "passed": 3,
                    "total": 3,
                    "runtimeMs": 1.5,
                    "language": "python",
                    "code": sol_v2,
                    "course": "grind-75",
                },
            })
            self.assertEqual(st, 200)
            self.assertEqual(len(r_dup["progress"]["submissions"]["lc:1"]), 2)
            self.assertEqual(r_dup["progress"]["submissions"]["lc:1"][0]["runtimeMs"], 1.5)

            # 6. Reloading /api/state preserves submissions even if user overwrites draft with starter code to practise again
            st, _ = req_json("POST", "/api/progress", {"day": 1, "language": "python", "draft": "def twoSum(nums, target):\n    pass\n"})
            self.assertEqual(st, 200)
            st, state_res = req_json("GET", "/api/state")
            self.assertEqual(st, 200)
            self.assertEqual(len(state_res["progress"]["submissions"]["lc:1"]), 2)
        finally:
            srv.shutdown()
            srv.server_close()

        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        v2_js = (server.PUBLIC_DIR / "studio_v2.js").read_text(encoding="utf-8")
        for needle in (
            'id="toggle-submissions-btn"',
            'id="practise-again-btn"',
            'id="accepted-submissions-panel"',
            'id="practice-revert-strip"',
            'id="strip-revert-latest-btn"',
            'id="accepted-save-stay-btn"',
            'function submissionKeyForProblem(',
            'function getAcceptedSubmissionsForProblem(',
            'function practiseAgainCurrentProblem(',
            'function revertToSubmission(',
            'saveAcceptedSubmission:',
        ):
            self.assertIn(needle, html)
        self.assertIn('id="accepted-sql-save-stay-btn"', v2_js)

    def test_v231_gemini_key_setup_and_backend_storage(self) -> None:
        import http.client
        import json
        import stat
        import threading

        orig_env_key = os.environ.pop("GEMINI_API_KEY", None)
        key_path = server._get_gemini_key_path()
        if key_path.is_file():
            key_path.unlink()

        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def req_json(method: str, path: str, body: dict | None = None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    raw = json.dumps(body).encode("utf-8") if body is not None else None
                    hdrs = {"Content-Type": "application/json"} if raw is not None else {}
                    conn.request(method, path, body=raw, headers=hdrs)
                    resp = conn.getresponse()
                    return resp.status, json.loads(resp.read().decode("utf-8"))
                finally:
                    conn.close()

            # 1. Starts unconfigured
            st, st0 = req_json("GET", "/api/gemini-key/status")
            self.assertEqual(st, 200)
            self.assertTrue(st0["ok"])
            self.assertFalse(st0["configured"])
            self.assertEqual(st0["source"], "none")
            self.assertEqual(st0["masked"], "")

            # 2. Rejects short or whitespace-containing keys with 400
            for bad in ("", "short", "contains spaces in key"):
                st, r_bad = req_json("POST", "/api/gemini-key", {"apiKey": bad})
                self.assertEqual(st, 400)
                self.assertFalse(r_bad["ok"])

            # 3. Valid key populates backend file (0600 perms) + os.environ, returns masked preview only
            dummy_key = "TESTKEY_DUMMY_1234567890_9999"
            st, r_save = req_json("POST", "/api/gemini-key", {"apiKey": dummy_key})
            self.assertEqual(st, 200)
            self.assertTrue(r_save["ok"])
            self.assertTrue(r_save["configured"])
            self.assertEqual(r_save["source"], "file")
            self.assertEqual(r_save["masked"], "TEST...9999")
            self.assertNotIn(dummy_key, json.dumps(r_save))
            self.assertTrue(key_path.is_file())
            self.assertEqual(stat.S_IMODE(key_path.stat().st_mode), 0o600)
            self.assertEqual(os.environ.get("GEMINI_API_KEY"), dummy_key)

            # 4. GET /api/gemini-key/status never leaks the raw key
            st, st1 = req_json("GET", "/api/gemini-key/status")
            self.assertEqual(st, 200)
            self.assertTrue(st1["configured"])
            self.assertEqual(st1["masked"], "TEST...9999")
            self.assertNotIn(dummy_key, json.dumps(st1))

            # 5. User code subprocess still strips the newly populated GEMINI_API_KEY
            leak_py = (
                "import os\n"
                "def twoSum(nums: list[int], target: int) -> list[int]:\n"
                "    print(os.environ.get('GEMINI_API_KEY', 'STRIPPED'))\n"
                "    return [0, 1]\n"
            )
            r_run = server.execute_user_code(1, "python", leak_py)
            self.assertIn("STRIPPED", r_run["results"][0]["stdout"])
            self.assertNotIn(dummy_key, r_run["results"][0]["stdout"])

            # 6. Export progress NEVER includes the saved Gemini key
            st, exp = req_json("GET", "/api/export-progress")
            self.assertEqual(st, 200)
            self.assertNotIn(dummy_key, json.dumps(exp))

            # 7. Clear removes file + env var cleanly
            st, r_clr = req_json("POST", "/api/gemini-key", {"clear": True})
            self.assertEqual(st, 200)
            self.assertFalse(r_clr["configured"])
            self.assertEqual(r_clr["source"], "none")
            self.assertFalse(key_path.is_file())
            self.assertIsNone(os.environ.get("GEMINI_API_KEY"))
        finally:
            srv.shutdown()
            srv.server_close()
            if key_path.is_file():
                key_path.unlink()
            if orig_env_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = orig_env_key

        # 8. Verify guided Gemini setup DOM & JS hooks exist in public/index.html
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="copilot-apikey-bar"',
            'id="copilot-apikey-pill"',
            'id="copilot-apikey-reveal-btn"',
            'id="copilot-apikey-test-btn"',
            'id="copilot-apikey-save-btn"',
            'id="copilot-apikey-clear-btn"',
            'id="copilot-apikey-close-btn"',
            'id="copilot-aistudio-link"',
            "setupCard.id = 'copilot-hero-setup-card'",
            'id="copilot-hero-setup-btn"',
            'https://aistudio.google.com/apikey',
            '/api/gemini-key/status',
            '/api/gemini-key',
            'async function verifyGeminiApiKey(',
            'async function persistGeminiApiKey(',
            'async function syncGeminiKeyStatus(',
        ):
            self.assertIn(needle, html)

    def test_v232_visual_explainer_and_storyboard(self) -> None:
        import http.client
        import json
        import threading

        srv = server._ReusableThreadingHTTPServer(("127.0.0.1", 0), server.AlgoStudioHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            def req_json(method: str, path: str, body: dict | None = None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    raw = json.dumps(body).encode("utf-8") if body is not None else None
                    hdrs = {"Content-Type": "application/json"} if raw is not None else {}
                    conn.request(method, path, body=raw, headers=hdrs)
                    resp = conn.getresponse()
                    return resp.status, json.loads(resp.read().decode("utf-8"))
                finally:
                    conn.close()

            # 1. Day 1 visual_explainer returns ASCII diagram + visual_storyboard with real traceSteps
            st, r1 = req_json("POST", "/api/chat", {
                "day": 1,
                "language": "python",
                "code": "def twoSum(nums, target):\n    pass\n",
                "message": "Explain Two Sum visually step-by-step",
                "model": "flash",
                "promptMode": "visual_explainer",
            })
            self.assertEqual(st, 200)
            self.assertTrue(r1["ok"])
            self.assertIn("```text", r1["reply"])
            vw1 = r1.get("visualWidget") or {}
            self.assertEqual(vw1.get("type"), "visual_storyboard")
            self.assertTrue(vw1.get("trap"))
            self.assertTrue(vw1.get("pivot"))
            self.assertTrue(vw1.get("example"))
            self.assertGreaterEqual(len(vw1.get("traceSteps") or []), 2)

            # 2. Curated Linked List problem (lc-206) also returns visual_storyboard widget
            st, r2 = req_json("POST", "/api/chat", {
                "problemId": "lc-206",
                "language": "python",
                "code": "def reverseList(head):\n    return None\n",
                "message": "Explain Reverse Linked List visually",
                "model": "flash",
                "promptMode": "visual_explainer",
            })
            self.assertEqual(st, 200)
            self.assertTrue(r2["ok"])
            self.assertIn("```text", r2["reply"])
            vw2 = r2.get("visualWidget") or {}
            self.assertEqual(vw2.get("type"), "visual_storyboard")
            self.assertIn("Linked List", vw2.get("tags") or [])
            self.assertTrue(vw2.get("example"))

            # 3. appendChatTurn persists visualWidget for live Gemini turns
            st, r_app = req_json("POST", "/api/progress", {
                "appendChatTurn": {
                    "key": "1",
                    "userText": "Draw this visually",
                    "assistantText": "Visual diagram reply",
                    "model": "flash",
                    "modelUsed": "Gemini 2.5 Flash (Live)",
                    "visualWidget": vw1,
                }
            })
            self.assertEqual(st, 200)
            last_msg = r_app["progress"]["chatHistory"]["1"][-1]
            self.assertEqual((last_msg.get("visualWidget") or {}).get("type"), "visual_storyboard")
        finally:
            srv.shutdown()
            srv.server_close()

        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        v2_js = (server.PUBLIC_DIR / "studio_v2.js").read_text(encoding="utf-8")
        for needle in (
            'value="visual_explainer" selected',
            'function buildClientVisualStoryboardWidget(',
            'function parseVisualInputTokens(',
            'function extractActivePointers(',
            'visual-storyboard-card',
            'vs-stepper-box',
            'Copy Visual Prompt',
        ):
            self.assertIn(needle, html)
        for needle in (
            'visual_explainer:',
            'buildCopyForAiPrompt',
            'line-numbered',
        ):
            self.assertIn(needle, v2_js)

    def test_v233_python_tutor_inline_code_editing(self) -> None:
        html = (server.PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
        for needle in (
            'id="pt-edit-code-btn"',
            'id="pt-run-trace-btn"',
            'id="pt-run-status-pill"',
            'id="pt-inline-editor-wrap"',
            'id="pt-inline-gutter"',
            'id="pt-inline-editor"',
            'function setPtEditMode(',
            'async function runFromPythonTutor(',
            'function updatePtRunStatusPill(',
            'function updatePtInlineGutter(',
        ):
            self.assertIn(needle, html)


if __name__ == "__main__":
    unittest.main()
