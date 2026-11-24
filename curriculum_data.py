#!/usr/bin/env python3
"""Comprehensive 120-Day SWE & FDE Coding Curriculum and Problem Engine.

Covers all 74 LeetCode topic tags from the user's taxonomy image plus 12
Software Engineer (SWE) and Forward Deployed Engineer (FDE) practical
interview pillars. Every problem includes problem statements, clarifying
questions, 3-tier progressive hints, a 'How to Change Your Thinking' mental
model shift, interactive dry-run trace steps, runnable test suites, and
annotated optimal solutions in Python, Go, and TypeScript.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from curriculum_extra_46 import EXTRA_46_PROBLEMS
from edge_cases_data import (
    EDGE_CASE_PLAYBOOK,
    EDGE_CASE_RESOURCES,
    EXPANDED_HIDDEN_TESTS_BY_FUNC,
    get_edge_case_checklist_for_tags,
)


def _load_curated_by_id() -> dict[str, dict[str, Any]]:
    cat_path = Path(__file__).resolve().parent / "curated_catalog.json"
    if not cat_path.exists():
        return {}
    try:
        raw = json.loads(cat_path.read_text(encoding="utf-8"))
        by_id = raw.get("problemsById")
        return by_id if isinstance(by_id, dict) else {}
    except Exception:
        return {}


_CURATED_BY_ID: dict[str, dict[str, Any]] = _load_curated_by_id()

# All 74 tags from the user's uploaded LeetCode topic image with problem counts
IMAGE_TAGS: list[dict[str, Any]] = [
    {"name": "Array", "lcCount": 2274, "group": "Core Arrays, Strings & Hashing"},
    {"name": "String", "lcCount": 896, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Hash Table", "lcCount": 844, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Math", "lcCount": 710, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Dynamic Programming", "lcCount": 686, "group": "Dynamic Programming & Greedy"},
    {"name": "Sorting", "lcCount": 540, "group": "Pointers, Windows & Sorting"},
    {"name": "Greedy", "lcCount": 483, "group": "Dynamic Programming & Greedy"},
    {"name": "Binary Search", "lcCount": 357, "group": "Binary Search & Divide and Conquer"},
    {"name": "Depth-First Search", "lcCount": 349, "group": "Trees, Tries & Graphs"},
    {"name": "Database", "lcCount": 310, "group": "Systems Design, Concurrency & Data"},
    {"name": "Bit Manipulation", "lcCount": 297, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Matrix", "lcCount": 285, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Prefix Sum", "lcCount": 277, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Tree", "lcCount": 270, "group": "Trees, Tries & Graphs"},
    {"name": "Two Pointers", "lcCount": 264, "group": "Pointers, Windows & Sorting"},
    {"name": "Breadth-First Search", "lcCount": 260, "group": "Trees, Tries & Graphs"},
    {"name": "Heap (Priority Queue)", "lcCount": 222, "group": "Heaps, Queues & Range Queries"},
    {"name": "Simulation", "lcCount": 218, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Counting", "lcCount": 215, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Graph Theory", "lcCount": 190, "group": "Trees, Tries & Graphs"},
    {"name": "Stack", "lcCount": 182, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Binary Tree", "lcCount": 181, "group": "Trees, Tries & Graphs"},
    {"name": "Sliding Window", "lcCount": 175, "group": "Pointers, Windows & Sorting"},
    {"name": "Enumeration", "lcCount": 163, "group": "Core Arrays, Strings & Hashing"},
    {"name": "Design", "lcCount": 136, "group": "Systems Design, Concurrency & Data"},
    {"name": "Backtracking", "lcCount": 114, "group": "Backtracking & Combinatorics"},
    {"name": "Number Theory", "lcCount": 105, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Union-Find", "lcCount": 99, "group": "Trees, Tries & Graphs"},
    {"name": "Segment Tree", "lcCount": 87, "group": "Heaps, Queues & Range Queries"},
    {"name": "Linked List", "lcCount": 82, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Ordered Set", "lcCount": 81, "group": "Heaps, Queues & Range Queries"},
    {"name": "Monotonic Stack", "lcCount": 76, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Divide and Conquer", "lcCount": 71, "group": "Binary Search & Divide and Conquer"},
    {"name": "Combinatorics", "lcCount": 65, "group": "Backtracking & Combinatorics"},
    {"name": "Trie", "lcCount": 61, "group": "Trees, Tries & Graphs"},
    {"name": "Queue", "lcCount": 58, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Bitmask", "lcCount": 56, "group": "Backtracking & Combinatorics"},
    {"name": "Binary Indexed Tree", "lcCount": 54, "group": "Heaps, Queues & Range Queries"},
    {"name": "Recursion", "lcCount": 51, "group": "Trees, Tries & Graphs"},
    {"name": "Hash Function", "lcCount": 47, "group": "Advanced Strings & Hashing"},
    {"name": "Geometry", "lcCount": 46, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Memoization", "lcCount": 44, "group": "Dynamic Programming & Greedy"},
    {"name": "Shortest Path", "lcCount": 43, "group": "Trees, Tries & Graphs"},
    {"name": "Binary Search Tree", "lcCount": 43, "group": "Trees, Tries & Graphs"},
    {"name": "Topological Sort", "lcCount": 40, "group": "Trees, Tries & Graphs"},
    {"name": "String Matching", "lcCount": 37, "group": "Advanced Strings & Hashing"},
    {"name": "Rolling Hash", "lcCount": 33, "group": "Advanced Strings & Hashing"},
    {"name": "Game Theory", "lcCount": 30, "group": "Dynamic Programming & Greedy"},
    {"name": "Monotonic Queue", "lcCount": 26, "group": "Pointers, Windows & Sorting"},
    {"name": "Interactive", "lcCount": 25, "group": "Binary Search & Divide and Conquer"},
    {"name": "Data Stream", "lcCount": 24, "group": "Systems Design, Concurrency & Data"},
    {"name": "Brainteaser", "lcCount": 22, "group": "Dynamic Programming & Greedy"},
    {"name": "Merge Sort", "lcCount": 17, "group": "Binary Search & Divide and Conquer"},
    {"name": "Minimax", "lcCount": 16, "group": "Dynamic Programming & Greedy"},
    {"name": "Doubly-Linked List", "lcCount": 15, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Randomized", "lcCount": 12, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Counting Sort", "lcCount": 11, "group": "Pointers, Windows & Sorting"},
    {"name": "Iterator", "lcCount": 9, "group": "Stacks, Queues & Linked Lists"},
    {"name": "Concurrency", "lcCount": 9, "group": "Systems Design, Concurrency & Data"},
    {"name": "Suffix Array", "lcCount": 9, "group": "Advanced Strings & Hashing"},
    {"name": "Quickselect", "lcCount": 8, "group": "Binary Search & Divide and Conquer"},
    {"name": "Sweep Line", "lcCount": 8, "group": "Heaps, Queues & Range Queries"},
    {"name": "Probability and Statistics", "lcCount": 7, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Minimum Spanning Tree", "lcCount": 6, "group": "Trees, Tries & Graphs"},
    {"name": "Bucket Sort", "lcCount": 6, "group": "Pointers, Windows & Sorting"},
    {"name": "Shell", "lcCount": 4, "group": "Systems Design, Concurrency & Data"},
    {"name": "Meet in the Middle", "lcCount": 4, "group": "Backtracking & Combinatorics"},
    {"name": "Reservoir Sampling", "lcCount": 4, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Eulerian Circuit", "lcCount": 3, "group": "Trees, Tries & Graphs"},
    {"name": "Radix Sort", "lcCount": 3, "group": "Pointers, Windows & Sorting"},
    {"name": "Strongly Connected Component", "lcCount": 2, "group": "Trees, Tries & Graphs"},
    {"name": "Rejection Sampling", "lcCount": 2, "group": "Math, Bit Manipulation & Sampling"},
    {"name": "Biconnected Component", "lcCount": 1, "group": "Trees, Tries & Graphs"},
    {"name": "Heap", "lcCount": 1, "group": "Heaps, Queues & Range Queries"},
]

# 12 Expanded SWE & FDE Coding Interview Pillars
EXPANDED_TAGS: list[dict[str, Any]] = [
    {
        "name": "Ambiguity & Constraint Clarification",
        "lcCount": 120,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Proactively asking about input size bounds, negative values, duplicates, memory limits, and failure modes before coding.",
    },
    {
        "name": "Dry-Run State Table Tracing",
        "lcCount": 120,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Walking through your code line by line with a small concrete example and state table before declaring completion.",
    },
    {
        "name": "Adversarial Edge-Case Synthesis",
        "lcCount": 120,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Designing boundary tests: empty input, single element, all-equal elements, skewed trees, disconnected graphs, and overflow.",
    },
    {
        "name": "Idiomatic Modularity & Helper Design",
        "lcCount": 40,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Writing clean, self-documenting helpers, type annotations, and modular interfaces without global state.",
    },
    {
        "name": "Space-Time Trade-Off & Amortised Analysis",
        "lcCount": 60,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Articulating worst-case vs amortised runtime and trading auxiliary memory for lower latency.",
    },
    {
        "name": "FDE: Dirty Data & Resilient Log Parsing",
        "lcCount": 12,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Handling malformed records, missing fields, out-of-order timestamps, and schema drift in customer data streams.",
    },
    {
        "name": "FDE: Stateful API Pagination & Rate Limiting",
        "lcCount": 10,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Building token-bucket rate limiters, cursor-based paginators, and idempotent retry pipelines.",
    },
    {
        "name": "FDE: In-Memory Transactional KV Store & TTL",
        "lcCount": 10,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Implementing KV stores with TTL expiration, point-in-time snapshots, and nested BEGIN/COMMIT/ROLLBACK transactions.",
    },
    {
        "name": "FDE: Multi-Step Requirement Evolution",
        "lcCount": 15,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Structuring code in Part 1 so Part 2 and Part 3 constraint twists require clean extension rather than a full rewrite.",
    },
    {
        "name": "FDE: Streaming Aggregation & Memory Bounds",
        "lcCount": 12,
        "group": "SWE & FDE Interview Craft",
        "isExpanded": True,
        "summary": "Processing unbounded streams with bounded memory via sliding windows, heaps, and reservoir/sketch techniques.",
    },
    {
        "name": "SQL & Analytical Window Queries",
        "lcCount": 15,
        "group": "Systems Design, Concurrency & Data",
        "isExpanded": True,
        "summary": "Using DENSE_RANK, LAG/LEAD, rolling window frames, and CTEs for analytical data interviews.",
    },
    {
        "name": "CLI & Log Pipeline Automation",
        "lcCount": 8,
        "group": "Systems Design, Concurrency & Data",
        "isExpanded": True,
        "summary": "Composing streaming text processing, regex extraction, and top-K aggregation for production debugging.",
    },
]

PHASES: list[dict[str, Any]] = [
    {
        "phase": 1,
        "title": "Phase 1: O(1) Complement Memory, Counting & Prefix Invariants",
        "days": "Days 1 to 8",
        "focus": "Shift from nested O(N^2) pair scans to single-pass hash state, frequency Signatures, and prefix accumulation.",
    },
    {
        "phase": 2,
        "title": "Phase 2: Two Pointers, Sliding Windows & Linear Sorting",
        "days": "Days 9 to 16",
        "focus": "Maintain a dynamic window invariant [L..R] where both pointers move monotonically forward in O(N) amortised time.",
    },
    {
        "phase": 3,
        "title": "Phase 3: Stacks, Monotonic Stacks, Queues & Linked Lists",
        "days": "Days 17 to 24",
        "focus": "Hold unresolved elements on a stack until a future element resolves them, and manipulate pointer links in-place.",
    },
    {
        "phase": 4,
        "title": "Phase 4: Binary Search on Index, Answer Space & Divide and Conquer",
        "days": "Days 25 to 32",
        "focus": "Turn optimisation problems into monotonic boolean decision predicates canAchieve(mid) over a bounded answer range.",
    },
    {
        "phase": 5,
        "title": "Phase 5: Trees, Binary Search Trees, Tries & Recursive Contracts",
        "days": "Days 33 to 42",
        "focus": "Define what each recursive call returns upward to its parent vs what invariant constraint it passes downward.",
    },
    {
        "phase": 6,
        "title": "Phase 6: Heaps, Priority Queues, Sweep Line & Ordered Sets",
        "days": "Days 43 to 50",
        "focus": "Maintain dynamic top-K, running medians, and active interval events in O(log N) per operation without full re-sorting.",
    },
    {
        "phase": 7,
        "title": "Phase 7: Backtracking, Combinatorics & Meet in the Middle",
        "days": "Days 51 to 58",
        "focus": "Explore decision trees with choose-explore-unchoose pruning and split exponential searches into two halves.",
    },
    {
        "phase": 8,
        "title": "Phase 8: Graph Theory I: BFS, DFS, Topological Sort & Union-Find",
        "days": "Days 59 to 68",
        "focus": "Model grids and dependencies as graphs; use Kahn's indegree queue for ordering and Union-Find for dynamic connectivity.",
    },
    {
        "phase": 9,
        "title": "Phase 9: Graph Theory II: Shortest Paths, MST, Eulerian & Tarjan SCC",
        "days": "Days 69 to 76",
        "focus": "Master Dijkstra, 0-1 BFS, Kruskal/Prim MST, Hierholzer Eulerian paths, and Tarjan low-link values for bridges and SCCs.",
    },
    {
        "phase": 10,
        "title": "Phase 10: Dynamic Programming I: 1D, 2D, Knapsack & Memoization",
        "days": "Days 77 to 86",
        "focus": "Formulate minimal subproblem states dp[i][s], state transitions, DAG evaluation order, and O(1)/O(N) space rolling arrays.",
    },
    {
        "phase": 11,
        "title": "Phase 11: Dynamic Programming II: Interval DP, Bitmask DP & Game Theory",
        "days": "Days 87 to 94",
        "focus": "Solve subarray merge recurrences, subset bitmask states, and Minimax optimal-play game states.",
    },
    {
        "phase": 12,
        "title": "Phase 12: Range Queries: Segment Trees & Fenwick (Binary Indexed) Trees",
        "days": "Days 95 to 100",
        "focus": "Support intertwined point updates and range queries in O(log N) time using Fenwick bit-stripping and Segment Trees.",
    },
    {
        "phase": 13,
        "title": "Phase 13: Advanced Strings: Rolling Hash, KMP & Suffix Arrays",
        "days": "Days 101 to 106",
        "focus": "Replace O(N*M) substring comparisons with polynomial rolling hashes, KMP prefix failure tables, and Suffix Arrays.",
    },
    {
        "phase": 14,
        "title": "Phase 14: Bit Manipulation, Number Theory, Geometry & Sampling",
        "days": "Days 107 to 112",
        "focus": "Use bitwise invariants, modular arithmetic, cross-product orientation, Reservoir Sampling, and Rejection Sampling.",
    },
    {
        "phase": 15,
        "title": "Phase 15: Data Structure Design, Concurrency, SQL & Shell Pipelines",
        "days": "Days 113 to 116",
        "focus": "Combine hash maps with doubly-linked lists, synchronise concurrent workers, and write analytical SQL & log pipelines.",
    },
    {
        "phase": 16,
        "title": "Phase 16: SWE & FDE Multi-Part Capstone Simulations",
        "days": "Days 117 to 120",
        "focus": "End-to-end 45-minute multi-part problems testing dirty data parsing, rate limiting, transactional KV stores, and scale-ups.",
    },
]

from problems_part1 import BLUEPRINTS_PART1, DETAILED_PART1
from problems_part2 import DETAILED_PART2, MASTER_120_SCHEDULE

PHASE_MAP: dict[int, dict[str, Any]] = {p["phase"]: p for p in PHASES}

# Phase-specific mental model defaults and runnable problem templates for schedule items
_PHASE_SOLVERS: dict[int, dict[str, Any]] = {
    1: {
        "funcName": "solveArrayHash",
        "statement": (
            "Given an integer array `nums` and an integer `target`, return the maximum length of a contiguous subarray "
            "whose sum equals `target` (or `0` if none exists). Use a single-pass prefix-sum hash map in O(N) time."
        ),
        "examples": [
            {"input": "nums = [1, -1, 5, -2, 3], target = 3", "output": "4", "explanation": "Subarray [1, -1, 5, -2] sums to 3 with length 4."},
            {"input": "nums = [-2, -1, 2, 1], target = 1", "output": "2", "explanation": "Subarray [-1, 2] sums to 1 with length 2."},
        ],
        "constraints": ["1 <= len(nums) <= 10^5", "-10^4 <= nums[i] <= 10^4", "Target Complexity: O(N) time, O(N) space"],
        "trap": "Checking all O(N^2) subarrays with nested loops or overwriting the earliest index in the prefix map.",
        "pivot": "Store only the EARLIEST index where each `prefix_sum` appears (`first_idx = {0: -1}`). Whenever `running - target` is in `first_idx`, `i - first_idx[running - target]` is the longest subarray ending at `i`.",
        "signal": "Longest contiguous subarray with exact sum `target` -> Prefix sum + earliest-index hash map.",
        "starter": {
            "python": "def solveArrayHash(nums: list[int], target: int) -> int:\n    # Return max subarray length summing to target in O(N) time\n    pass\n",
            "go": "package main\n\nfunc solveArrayHash(nums []int, target int) int {\n\t// Return max subarray length summing to target in O(N) time\n\treturn 0\n}\n",
            "typescript": "function solveArrayHash(nums: number[], target: number): number {\n  // Return max subarray length summing to target in O(N) time\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def solveArrayHash(nums: list[int], target: int) -> int:\n"
                "    first: dict[int, int] = {0: -1}\n"
                "    running = 0\n"
                "    best = 0\n"
                "    for i, x in enumerate(nums):\n"
                "        running += x\n"
                "        if running - target in first:\n"
                "            best = max(best, i - first[running - target])\n"
                "        if running not in first:\n"
                "            first[running] = i\n"
                "    return best\n"
            ),
            "go": (
                "package main\n\n"
                "func solveArrayHash(nums []int, target int) int {\n"
                "\tfirst := map[int]int{0: -1}\n"
                "\trunning, best := 0, 0\n"
                "\tfor i, x := range nums {\n"
                "\t\trunning += x\n"
                "\t\tif prev, ok := first[running-target]; ok && i-prev > best {\n"
                "\t\t\tbest = i - prev\n"
                "\t\t}\n"
                "\t\tif _, exists := first[running]; !exists {\n"
                "\t\t\tfirst[running] = i\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn best\n"
                "}\n"
            ),
            "typescript": (
                "function solveArrayHash(nums: number[], target: number): number {\n"
                "  const first = new Map<number, number>([[0, -1]]);\n"
                "  let running = 0, best = 0;\n"
                "  for (let i = 0; i < nums.length; i++) {\n"
                "    running += nums[i];\n"
                "    if (first.has(running - target)) {\n"
                "      best = Math.max(best, i - first.get(running - target)!);\n"
                "    }\n"
                "    if (!first.has(running)) first.set(running, i);\n"
                "  }\n"
                "  return best;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[1, -1, 5, -2, 3], 3], "expected": 4, "label": "Length 4 prefix match"},
            {"args": [[-2, -1, 2, 1], 1], "expected": 2, "label": "Middle subarray"},
            {"args": [[1, 2, 3], 10], "expected": 0, "label": "No match"},
        ],
    },
    2: {
        "funcName": "solveSlidingWindow",
        "statement": (
            "Given an array of positive integers `nums` and a positive integer `target`, return the minimal length "
            "of a contiguous subarray of which the sum is greater than or equal to `target`. If there is no such subarray, return `0`."
        ),
        "examples": [
            {"input": "nums = [2,3,1,2,4,3], target = 7", "output": "2", "explanation": "Subarray [4,3] has length 2 and sum 7."},
        ],
        "constraints": ["1 <= len(nums) <= 10^5", "1 <= nums[i] <= 10^4", "Target Complexity: O(N) time, O(1) space"],
        "trap": "Restarting the inner loop from `left` on every index (O(N^2)).",
        "pivot": "Because all `nums[i] > 0`, expanding `right` increases `window_sum` monotonically and advancing `left` decreases it monotonically. Advance `left` inside a `while window_sum >= target:` loop in O(N) amortised time.",
        "signal": "Shortest/longest subarray over positive numbers -> Two-pointer Sliding Window.",
        "starter": {
            "python": "def solveSlidingWindow(nums: list[int], target: int) -> int:\n    # O(N) two-pointer sliding window\n    pass\n",
            "go": "package main\n\nfunc solveSlidingWindow(nums []int, target int) int {\n\t// O(N) two-pointer sliding window\n\treturn 0\n}\n",
            "typescript": "function solveSlidingWindow(nums: number[], target: number): number {\n  // O(N) two-pointer sliding window\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def solveSlidingWindow(nums: list[int], target: int) -> int:\n"
                "    left = 0\n"
                "    cur = 0\n"
                "    best = len(nums) + 1\n"
                "    for right, x in enumerate(nums):\n"
                "        cur += x\n"
                "        while cur >= target:\n"
                "            best = min(best, right - left + 1)\n"
                "            cur -= nums[left]\n"
                "            left += 1\n"
                "    return 0 if best > len(nums) else best\n"
            ),
            "go": (
                "package main\n\n"
                "func solveSlidingWindow(nums []int, target int) int {\n"
                "\tleft, cur, best := 0, 0, len(nums)+1\n"
                "\tfor right, x := range nums {\n"
                "\t\tcur += x\n"
                "\t\tfor cur >= target {\n"
                "\t\t\tif right-left+1 < best {\n"
                "\t\t\t\tbest = right - left + 1\n"
                "\t\t\t}\n"
                "\t\t\tcur -= nums[left]\n"
                "\t\t\tleft++\n"
                "\t\t}\n"
                "\t}\n"
                "\tif best > len(nums) {\n"
                "\t\treturn 0\n"
                "\t}\n"
                "\treturn best\n"
                "}\n"
            ),
            "typescript": (
                "function solveSlidingWindow(nums: number[], target: number): number {\n"
                "  let left = 0, cur = 0, best = nums.length + 1;\n"
                "  for (let right = 0; right < nums.length; right++) {\n"
                "    cur += nums[right];\n"
                "    while (cur >= target) {\n"
                "      best = Math.min(best, right - left + 1);\n"
                "      cur -= nums[left++];\n"
                "    }\n"
                "  }\n"
                "  return best > nums.length ? 0 : best;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[2, 3, 1, 2, 4, 3], 7], "expected": 2, "label": "Tail pair [4,3]"},
            {"args": [[1, 4, 4], 4], "expected": 1, "label": "Single element"},
            {"args": [[1, 1, 1, 1], 11], "expected": 0, "label": "Unreachable sum"},
        ],
    },
    3: {
        "funcName": "largestRectangleArea",
        "statement": (
            "Given an array of integers `heights` representing the histogram's bar height where the width of each bar is 1, "
            "return the area of the largest rectangle in the histogram using a Monotonic Increasing Stack in O(N) time."
        ),
        "examples": [
            {"input": "heights = [2,1,5,6,2,3]", "output": "10", "explanation": "Bars of height 5 and 6 span width 2 with area 5 * 2 = 10."},
        ],
        "constraints": ["1 <= len(heights) <= 10^5", "0 <= heights[i] <= 10^4", "Target Complexity: O(N) time, O(N) space"],
        "trap": "Expanding left and right from every bar in O(N^2) time.",
        "pivot": "Maintain a Monotonic Increasing Stack of indices. When `heights[i] < heights[stack[-1]]`, the popped bar's right boundary is `i` and its left boundary is the new `stack[-1]`.",
        "signal": "Subarray range where element `i` is the minimum -> Monotonic Increasing Stack with trailing `0` sentinel.",
        "starter": {
            "python": "def largestRectangleArea(heights: list[int]) -> int:\n    # O(N) monotonic increasing stack\n    pass\n",
            "go": "package main\n\nfunc largestRectangleArea(heights []int) int {\n\t// O(N) monotonic increasing stack\n\treturn 0\n}\n",
            "typescript": "function largestRectangleArea(heights: number[]): number {\n  // O(N) monotonic increasing stack\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def largestRectangleArea(heights: list[int]) -> int:\n"
                "    stack: list[int] = [-1]\n"
                "    best = 0\n"
                "    extended = heights + [0]\n"
                "    for i, h in enumerate(extended):\n"
                "        while stack[-1] != -1 and extended[stack[-1]] > h:\n"
                "            height = extended[stack.pop()]\n"
                "            width = i - stack[-1] - 1\n"
                "            best = max(best, height * width)\n"
                "        stack.append(i)\n"
                "    return best\n"
            ),
            "go": (
                "package main\n\n"
                "func largestRectangleArea(heights []int) int {\n"
                "\textended := append(append([]int{}, heights...), 0)\n"
                "\tstack := []int{-1}\n"
                "\tbest := 0\n"
                "\tfor i, h := range extended {\n"
                "\t\tfor stack[len(stack)-1] != -1 && extended[stack[len(stack)-1]] > h {\n"
                "\t\t\ttop := stack[len(stack)-1]\n"
                "\t\t\tstack = stack[:len(stack)-1]\n"
                "\t\t\tw := i - stack[len(stack)-1] - 1\n"
                "\t\t\tif extended[top]*w > best {\n"
                "\t\t\t\tbest = extended[top] * w\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t\tstack = append(stack, i)\n"
                "\t}\n"
                "\treturn best\n"
                "}\n"
            ),
            "typescript": (
                "function largestRectangleArea(heights: number[]): number {\n"
                "  const ext = [...heights, 0];\n"
                "  const stack = [-1];\n"
                "  let best = 0;\n"
                "  for (let i = 0; i < ext.length; i++) {\n"
                "    while (stack[stack.length - 1] !== -1 && ext[stack[stack.length - 1]] > ext[i]) {\n"
                "      const h = ext[stack.pop()!];\n"
                "      const w = i - stack[stack.length - 1] - 1;\n"
                "      best = Math.max(best, h * w);\n"
                "    }\n"
                "    stack.push(i);\n"
                "  }\n"
                "  return best;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[2, 1, 5, 6, 2, 3]], "expected": 10, "label": "Standard histogram"},
            {"args": [[2, 4]], "expected": 4, "label": "Two bars"},
            {"args": [[6, 2, 5, 4, 5, 1, 6]], "expected": 12, "label": "3x4 plateau"},
        ],
    },
    4: {
        "funcName": "splitArray",
        "statement": (
            "Given an integer array `nums` and an integer `k`, split `nums` into `k` non-empty contiguous subarrays "
            "such that the largest sum among these `k` subarrays is minimised. Return that minimised largest sum."
        ),
        "examples": [
            {"input": "nums = [7,2,5,10,8], k = 2", "output": "18", "explanation": "Best split is [7,2,5] (14) and [10,8] (18), max is 18."},
        ],
        "constraints": ["1 <= len(nums) <= 1000", "0 <= nums[i] <= 10^6", "1 <= k <= len(nums)", "Target Complexity: O(N log(sum(nums))) time"],
        "trap": "Building an O(N^2 * K) DP table when binary searching the cap is O(N log(sum)).",
        "pivot": "Binary search the maximum allowed subarray sum `cap` in `[max(nums), sum(nums)]`. Greedily pack elements into the current subarray until adding the next element exceeds `cap`, counting total subarrays needed.",
        "signal": "Minimise the maximum contiguous partition cost -> Binary Search on Answer Space + Greedy Pack Check.",
        "starter": {
            "python": "def splitArray(nums: list[int], k: int) -> int:\n    # Binary search on answer space [max(nums), sum(nums)]\n    pass\n",
            "go": "package main\n\nfunc splitArray(nums []int, k int) int {\n\t// Binary search on answer space [max(nums), sum(nums)]\n\treturn 0\n}\n",
            "typescript": "function splitArray(nums: number[], k: number): number {\n  // Binary search on answer space [max(nums), sum(nums)]\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def splitArray(nums: list[int], k: int) -> int:\n"
                "    lo, hi = max(nums), sum(nums)\n"
                "    while lo < hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        parts, cur = 1, 0\n"
                "        for x in nums:\n"
                "            if cur + x > mid:\n"
                "                parts += 1\n"
                "                cur = x\n"
                "            else:\n"
                "                cur += x\n"
                "        if parts <= k:\n"
                "            hi = mid\n"
                "        else:\n"
                "            lo = mid + 1\n"
                "    return lo\n"
            ),
            "go": (
                "package main\n\n"
                "func splitArray(nums []int, k int) int {\n"
                "\tlo, hi := 0, 0\n"
                "\tfor _, x := range nums {\n"
                "\t\tif x > lo {\n"
                "\t\t\tlo = x\n"
                "\t\t}\n"
                "\t\thi += x\n"
                "\t}\n"
                "\tfor lo < hi {\n"
                "\t\tmid := lo + (hi-lo)/2\n"
                "\t\tparts, cur := 1, 0\n"
                "\t\tfor _, x := range nums {\n"
                "\t\t\tif cur+x > mid {\n"
                "\t\t\t\tparts++\n"
                "\t\t\t\tcur = x\n"
                "\t\t\t} else {\n"
                "\t\t\t\tcur += x\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t\tif parts <= k {\n"
                "\t\t\thi = mid\n"
                "\t\t} else {\n"
                "\t\t\tlo = mid + 1\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn lo\n"
                "}\n"
            ),
            "typescript": (
                "function splitArray(nums: number[], k: number): number {\n"
                "  let lo = Math.max(...nums);\n"
                "  let hi = nums.reduce((a, b) => a + b, 0);\n"
                "  while (lo < hi) {\n"
                "    const mid = lo + Math.floor((hi - lo) / 2);\n"
                "    let parts = 1, cur = 0;\n"
                "    for (const x of nums) {\n"
                "      if (cur + x > mid) { parts++; cur = x; }\n"
                "      else cur += x;\n"
                "    }\n"
                "    if (parts <= k) hi = mid;\n"
                "    else lo = mid + 1;\n"
                "  }\n"
                "  return lo;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[7, 2, 5, 10, 8], 2], "expected": 18, "label": "2 partitions"},
            {"args": [[1, 2, 3, 4, 5], 2], "expected": 9, "label": "Sequential"},
            {"args": [[1, 4, 4], 3], "expected": 4, "label": "Singletons"},
        ],
    },
    5: {
        "funcName": "simulateTrie",
        "statement": (
            "Implement a Prefix Tree (`Trie`) supporting `INSERT(word)`, `SEARCH(word)`, and `STARTSWITH(prefix)`.\n"
            "Given a list of operations `[['INSERT', 'apple'], ['SEARCH', 'apple'], ['SEARCH', 'app'], ['STARTSWITH', 'app']]`, "
            "return the list of boolean results for `SEARCH` and `STARTSWITH` operations."
        ),
        "examples": [
            {
                "input": "ops = [['INSERT','apple'],['SEARCH','apple'],['SEARCH','app'],['STARTSWITH','app'],['INSERT','app'],['SEARCH','app']]",
                "output": "[True, False, True, True]",
                "explanation": "'app' is a prefix before being inserted as a full word.",
            },
        ],
        "constraints": ["1 <= len(word) <= 2000", "Target Complexity: O(L) per operation where L is word length"],
        "trap": "Scanning a list of words in O(N * L) on every prefix check.",
        "pivot": "Store shared character prefixes along paths of `TrieNode` dictionaries with an explicit `is_end` boolean flag at terminal nodes.",
        "signal": "String prefix matching, autocomplete, or dictionary word filtering -> Prefix Trie.",
        "starter": {
            "python": "def simulateTrie(ops: list[list[str]]) -> list[bool]:\n    # Execute INSERT, SEARCH, STARTSWITH on a Prefix Trie\n    pass\n",
            "go": "package main\n\nfunc simulateTrie(ops [][]string) []bool {\n\t// Execute INSERT, SEARCH, STARTSWITH on a Prefix Trie\n\treturn nil\n}\n",
            "typescript": "function simulateTrie(ops: string[][]): boolean[] {\n  // Execute INSERT, SEARCH, STARTSWITH on a Prefix Trie\n  return [];\n}\n",
        },
        "solution": {
            "python": (
                "def simulateTrie(ops: list[list[str]]) -> list[bool]:\n"
                "    root: dict = {}\n"
                "    out: list[bool] = []\n"
                "    for kind, word in ops:\n"
                "        node = root\n"
                "        if kind == 'INSERT':\n"
                "            for ch in word:\n"
                "                node = node.setdefault(ch, {})\n"
                "            node['#'] = True\n"
                "        else:\n"
                "            ok = True\n"
                "            for ch in word:\n"
                "                if ch not in node:\n"
                "                    ok = False\n"
                "                    break\n"
                "                node = node[ch]\n"
                "            out.append(ok and ('#' in node if kind == 'SEARCH' else True))\n"
                "    return out\n"
            ),
            "go": (
                "package main\n\n"
                "type trieNode struct {\n"
                "\tchildren [26]*trieNode\n"
                "\tisEnd    bool\n"
                "}\n\n"
                "func simulateTrie(ops [][]string) []bool {\n"
                "\troot := &trieNode{}\n"
                "\tout := []bool{}\n"
                "\tfor _, op := range ops {\n"
                "\t\tkind, w := op[0], op[1]\n"
                "\t\tcur := root\n"
                "\t\tif kind == \"INSERT\" {\n"
                "\t\t\tfor i := 0; i < len(w); i++ {\n"
                "\t\t\t\tc := w[i] - 'a'\n"
                "\t\t\t\tif cur.children[c] == nil {\n"
                "\t\t\t\t\tcur.children[c] = &trieNode{}\n"
                "\t\t\t\t}\n"
                "\t\t\t\tcur = cur.children[c]\n"
                "\t\t\t}\n"
                "\t\t\tcur.isEnd = true\n"
                "\t\t} else {\n"
                "\t\t\tok := true\n"
                "\t\t\tfor i := 0; i < len(w); i++ {\n"
                "\t\t\t\tc := w[i] - 'a'\n"
                "\t\t\t\tif cur.children[c] == nil {\n"
                "\t\t\t\t\tok = false\n"
                "\t\t\t\t\tbreak\n"
                "\t\t\t\t}\n"
                "\t\t\t\tcur = cur.children[c]\n"
                "\t\t\t}\n"
                "\t\t\tif kind == \"SEARCH\" {\n"
                "\t\t\t\tout = append(out, ok && cur.isEnd)\n"
                "\t\t\t} else {\n"
                "\t\t\t\tout = append(out, ok)\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn out\n"
                "}\n"
            ),
            "typescript": (
                "function simulateTrie(ops: string[][]): boolean[] {\n"
                "  const root: Record<string, any> = {};\n"
                "  const out: boolean[] = [];\n"
                "  for (const [kind, word] of ops) {\n"
                "    let node = root;\n"
                "    if (kind === 'INSERT') {\n"
                "      for (const ch of word) node = (node[ch] ??= {});\n"
                "      node['#'] = true;\n"
                "    } else {\n"
                "      let ok = true;\n"
                "      for (const ch of word) {\n"
                "        if (!node[ch]) { ok = false; break; }\n"
                "        node = node[ch];\n"
                "      }\n"
                "      out.push(ok && (kind === 'SEARCH' ? Boolean(node['#']) : true));\n"
                "    }\n"
                "  }\n"
                "  return out;\n"
                "}\n"
            ),
        },
        "tests": [
            {
                "args": [[["INSERT", "apple"], ["SEARCH", "apple"], ["SEARCH", "app"], ["STARTSWITH", "app"], ["INSERT", "app"], ["SEARCH", "app"]]],
                "expected": [True, False, True, True],
                "label": "Prefix vs full word",
            },
        ],
    },
    6: {
        "funcName": "minMeetingRooms",
        "statement": (
            "Given an array of meeting time intervals `intervals` where `intervals[i] = [start_i, end_i]`, "
            "return the minimum number of conference rooms required using a Min-Heap or Event Sweep Line."
        ),
        "examples": [
            {"input": "intervals = [[0,30],[5,10],[15,20]]", "output": "2", "explanation": "[5,10] and [15,20] can share the second room."},
            {"input": "intervals = [[7,10],[2,4]]", "output": "1", "explanation": "Non-overlapping meetings reuse the same room."},
        ],
        "constraints": ["1 <= len(intervals) <= 10^4", "0 <= start_i < end_i <= 10^6", "Target Complexity: O(N log N) time, O(N) space"],
        "trap": "Checking pairwise interval overlaps in O(N^2) without sorting by start time.",
        "pivot": "Sort meetings by `start` time and keep a Min-Heap of active room `end` times (or sweep `+1` at `start` and `-1` at `end`). When `new_start >= heap[0]`, the earliest-ending meeting has finished and its room is reused!",
        "signal": "Minimum concurrent resources / maximum overlapping intervals -> Sweep Line (`+1` start, `-1` end) or Min-Heap of end times.",
        "starter": {
            "python": "def minMeetingRooms(intervals: list[list[int]]) -> int:\n    # O(N log N) sweep line or min-heap of end times\n    pass\n",
            "go": "package main\n\nfunc minMeetingRooms(intervals [][]int) int {\n\t// O(N log N) sweep line or min-heap of end times\n\treturn 0\n}\n",
            "typescript": "function minMeetingRooms(intervals: number[][]): number {\n  // O(N log N) sweep line or min-heap of end times\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def minMeetingRooms(intervals: list[list[int]]) -> int:\n"
                "    starts = sorted(iv[0] for iv in intervals)\n"
                "    ends = sorted(iv[1] for iv in intervals)\n"
                "    rooms = 0\n"
                "    end_ptr = 0\n"
                "    for s in starts:\n"
                "        if s < ends[end_ptr]:\n"
                "            rooms += 1\n"
                "        else:\n"
                "            end_ptr += 1\n"
                "    return rooms\n"
            ),
            "go": (
                "package main\n\nimport \"sort\"\n\n"
                "func minMeetingRooms(intervals [][]int) int {\n"
                "\tn := len(intervals)\n"
                "\tstarts := make([]int, n)\n"
                "\tends := make([]int, n)\n"
                "\tfor i, iv := range intervals {\n"
                "\t\tstarts[i] = iv[0]\n"
                "\t\tends[i] = iv[1]\n"
                "\t}\n"
                "\tsort.Ints(starts)\n"
                "\tsort.Ints(ends)\n"
                "\trooms, endPtr := 0, 0\n"
                "\tfor _, s := range starts {\n"
                "\t\tif s < ends[endPtr] {\n"
                "\t\t\trooms++\n"
                "\t\t} else {\n"
                "\t\t\tendPtr++\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn rooms\n"
                "}\n"
            ),
            "typescript": (
                "function minMeetingRooms(intervals: number[][]): number {\n"
                "  const starts = intervals.map((x) => x[0]).sort((a, b) => a - b);\n"
                "  const ends = intervals.map((x) => x[1]).sort((a, b) => a - b);\n"
                "  let rooms = 0, endPtr = 0;\n"
                "  for (const s of starts) {\n"
                "    if (s < ends[endPtr]) rooms++;\n"
                "    else endPtr++;\n"
                "  }\n"
                "  return rooms;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[[0, 30], [5, 10], [15, 20]]], "expected": 2, "label": "Overlapping"},
            {"args": [[[7, 10], [2, 4]]], "expected": 1, "label": "Disjoint"},
            {"args": [[[1, 5], [5, 10], [10, 15]]], "expected": 1, "label": "Touching endpoints reuse room"},
        ],
    },
    7: {
        "funcName": "combinationSum",
        "statement": (
            "Given an array of distinct integers `candidates` and a target integer `target`, return a list of all unique "
            "combinations of `candidates` where the chosen numbers sum to `target`. The same number may be chosen an unlimited number of times."
        ),
        "examples": [
            {"input": "candidates = [2,3,6,7], target = 7", "output": "[[2,2,3],[7]]", "explanation": "2+2+3=7 and 7=7."},
        ],
        "constraints": ["1 <= len(candidates) <= 30", "2 <= candidates[i] <= 40", "1 <= target <= 40"],
        "trap": "Branching to all indices `0..N-1` at every step, generating duplicate permutations like `[2,3,2]` and `[3,2,2]`.",
        "pivot": "Enforce canonical non-decreasing index order in the DFS (`dfs(start_idx, remaining)`): once you advance past `candidates[i]`, never pick `candidates[0..i-1]` again. Sort `candidates` so you can `break` early as soon as `candidates[i] > remaining`.",
        "signal": "Combinations (order-independent subsets) -> Pass `start_idx` into backtracking DFS so choices only move forward.",
        "starter": {
            "python": "def combinationSum(candidates: list[int], target: int) -> list[list[int]]:\n    # Backtracking with canonical start_idx and sorted pruning\n    pass\n",
            "go": "package main\n\nfunc combinationSum(candidates []int, target int) [][]int {\n\t// Backtracking with canonical start_idx and sorted pruning\n\treturn nil\n}\n",
            "typescript": "function combinationSum(candidates: number[], target: number): number[][] {\n  // Backtracking with canonical start_idx and sorted pruning\n  return [];\n}\n",
        },
        "solution": {
            "python": (
                "def combinationSum(candidates: list[int], target: int) -> list[list[int]]:\n"
                "    candidates.sort()\n"
                "    res: list[list[int]] = []\n"
                "    path: list[int] = []\n"
                "    def dfs(idx: int, rem: int) -> None:\n"
                "        if rem == 0:\n"
                "            res.append(path[:])\n"
                "            return\n"
                "        for i in range(idx, len(candidates)):\n"
                "            c = candidates[i]\n"
                "            if c > rem:\n"
                "                break\n"
                "            path.append(c)\n"
                "            dfs(i, rem - c)\n"
                "            path.pop()\n"
                "    dfs(0, target)\n"
                "    return res\n"
            ),
            "go": (
                "package main\n\nimport \"sort\"\n\n"
                "func combinationSum(candidates []int, target int) [][]int {\n"
                "\tsort.Ints(candidates)\n"
                "\tres := [][]int{}\n"
                "\tpath := []int{}\n"
                "\tvar dfs func(idx, rem int)\n"
                "\tdfs = func(idx, rem int) {\n"
                "\t\tif rem == 0 {\n"
                "\t\t\tcp := append([]int{}, path...)\n"
                "\t\t\tres = append(res, cp)\n"
                "\t\t\treturn\n"
                "\t\t}\n"
                "\t\tfor i := idx; i < len(candidates); i++ {\n"
                "\t\t\tif candidates[i] > rem {\n"
                "\t\t\t\tbreak\n"
                "\t\t\t}\n"
                "\t\t\tpath = append(path, candidates[i])\n"
                "\t\t\tdfs(i, rem-candidates[i])\n"
                "\t\t\tpath = path[:len(path)-1]\n"
                "\t\t}\n"
                "\t}\n"
                "\tdfs(0, target)\n"
                "\treturn res\n"
                "}\n"
            ),
            "typescript": (
                "function combinationSum(candidates: number[], target: number): number[][] {\n"
                "  candidates.sort((a, b) => a - b);\n"
                "  const res: number[][] = [];\n"
                "  const path: number[] = [];\n"
                "  const dfs = (idx: number, rem: number): void => {\n"
                "    if (rem === 0) { res.push([...path]); return; }\n"
                "    for (let i = idx; i < candidates.length; i++) {\n"
                "      if (candidates[i] > rem) break;\n"
                "      path.push(candidates[i]);\n"
                "      dfs(i, rem - candidates[i]);\n"
                "      path.pop();\n"
                "    }\n"
                "  };\n"
                "  dfs(0, target);\n"
                "  return res;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[2, 3, 6, 7], 7], "expected": [[2, 2, 3], [7]], "label": "Target 7"},
            {"args": [[2, 3, 5], 8], "expected": [[2, 2, 2, 2], [2, 3, 3], [3, 5]], "label": "Target 8"},
        ],
    },
    8: {
        "funcName": "findRedundantConnection",
        "statement": (
            "In this problem, a tree is an undirected graph that is connected and has no cycles. "
            "You are given a graph that started as a tree with `n` nodes labelled from `1` to `n`, with one additional edge added. "
            "Return the edge `[u, v]` that can be removed so that the resulting graph is a tree of `n` nodes (if multiple, return the last in `edges`)."
        ),
        "examples": [
            {"input": "edges = [[1,2],[1,3],[2,3]]", "output": "[2, 3]", "explanation": "Adding [2,3] closes the cycle 1-2-3."},
        ],
        "constraints": ["3 <= len(edges) <= 1000", "Target Complexity: O(N * alpha(N)) time, O(N) space"],
        "trap": "Running a full DFS from scratch before adding each edge in O(N^2) time.",
        "pivot": "Maintain a Disjoint Set Union (`Union-Find`) with path compression and union by rank. The very first edge `[u, v]` where `find(u) == find(v)` connects two vertices already in the same component, closing a cycle!",
        "signal": "Dynamic undirected connectivity or cycle detection as edges arrive -> Union-Find (`Disjoint Set`).",
        "starter": {
            "python": "def findRedundantConnection(edges: list[list[int]]) -> list[int]:\n    # Disjoint Set Union (Union-Find) in O(N * alpha(N)) time\n    pass\n",
            "go": "package main\n\nfunc findRedundantConnection(edges [][]int) []int {\n\t// Disjoint Set Union (Union-Find) in O(N * alpha(N)) time\n\treturn nil\n}\n",
            "typescript": "function findRedundantConnection(edges: number[][]): number[] {\n  // Disjoint Set Union (Union-Find) in O(N * alpha(N)) time\n  return [];\n}\n",
        },
        "solution": {
            "python": (
                "def findRedundantConnection(edges: list[list[int]]) -> list[int]:\n"
                "    parent = list(range(len(edges) + 2))\n"
                "    rank = [0] * (len(edges) + 2)\n"
                "    def find(x: int) -> int:\n"
                "        while parent[x] != x:\n"
                "            parent[x] = parent[parent[x]]\n"
                "            x = parent[x]\n"
                "        return x\n"
                "    for u, v in edges:\n"
                "        ru, rv = find(u), find(v)\n"
                "        if ru == rv:\n"
                "            return [u, v]\n"
                "        if rank[ru] < rank[rv]:\n"
                "            ru, rv = rv, ru\n"
                "        parent[rv] = ru\n"
                "        if rank[ru] == rank[rv]:\n"
                "            rank[ru] += 1\n"
                "    return []\n"
            ),
            "go": (
                "package main\n\n"
                "func findRedundantConnection(edges [][]int) []int {\n"
                "\tn := len(edges) + 2\n"
                "\tparent := make([]int, n)\n"
                "\tfor i := range parent {\n"
                "\t\tparent[i] = i\n"
                "\t}\n"
                "\tvar find func(int) int\n"
                "\tfind = func(x int) int {\n"
                "\t\tfor parent[x] != x {\n"
                "\t\t\tparent[x] = parent[parent[x]]\n"
                "\t\t\tx = parent[x]\n"
                "\t\t}\n"
                "\t\treturn x\n"
                "\t}\n"
                "\tfor _, e := range edges {\n"
                "\t\tru, rv := find(e[0]), find(e[1])\n"
                "\t\tif ru == rv {\n"
                "\t\t\treturn e\n"
                "\t\t}\n"
                "\t\tparent[rv] = ru\n"
                "\t}\n"
                "\treturn nil\n"
                "}\n"
            ),
            "typescript": (
                "function findRedundantConnection(edges: number[][]): number[] {\n"
                "  const parent = Array.from({ length: edges.length + 2 }, (_, i) => i);\n"
                "  const find = (x: number): number => {\n"
                "    while (parent[x] !== x) {\n"
                "      parent[x] = parent[parent[x]];\n"
                "      x = parent[x];\n"
                "    }\n"
                "    return x;\n"
                "  };\n"
                "  for (const [u, v] of edges) {\n"
                "    const ru = find(u), rv = find(v);\n"
                "    if (ru === rv) return [u, v];\n"
                "    parent[rv] = ru;\n"
                "  }\n"
                "  return [];\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[[1, 2], [1, 3], [2, 3]]], "expected": [2, 3], "label": "Triangle cycle"},
            {"args": [[[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]], "expected": [1, 4], "label": "4-cycle"},
        ],
    },
    9: {
        "funcName": "networkDelayTime",
        "statement": (
            "You are given a network of `n` nodes labelled `1` to `n`, and directed weighted edges `times[i] = [u, v, w]`. "
            "Send a signal from node `k`. Return the minimum time it takes for all `n` nodes to receive the signal, or `-1` if impossible."
        ),
        "examples": [
            {"input": "times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2", "output": "2", "explanation": "Node 2 -> 3 (1) -> 4 (2); max distance is 2."},
        ],
        "constraints": ["1 <= k <= n <= 100", "0 <= w <= 100", "Target Complexity: O((V + E) log V) time"],
        "trap": "Using plain unweighted BFS on a graph with non-uniform non-negative edge weights.",
        "pivot": "Use Dijkstra's algorithm with a Min-Heap `(dist, u)`. Skip stale heap entries (`if d > dist[u]: continue`). The time for all nodes to receive the signal is `max(dist.values())` provided all `n` nodes were reached.",
        "signal": "Single-source shortest paths with non-negative weights -> Dijkstra Min-Heap.",
        "starter": {
            "python": "def networkDelayTime(times: list[list[int]], n: int, k: int) -> int:\n    # Dijkstra shortest path in O((V + E) log V)\n    pass\n",
            "go": "package main\n\nfunc networkDelayTime(times [][]int, n int, k int) int {\n\t// Dijkstra shortest path in O((V + E) log V)\n\treturn 0\n}\n",
            "typescript": "function networkDelayTime(times: number[][], n: number, k: number): number {\n  // Dijkstra shortest path in O((V + E) log V)\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "import heapq\n\n"
                "def networkDelayTime(times: list[list[int]], n: int, k: int) -> int:\n"
                "    adj: list[list[tuple[int, int]]] = [[] for _ in range(n + 1)]\n"
                "    for u, v, w in times:\n"
                "        adj[u].append((v, w))\n"
                "    dist: dict[int, int] = {k: 0}\n"
                "    pq: list[tuple[int, int]] = [(0, k)]\n"
                "    while pq:\n"
                "        d, u = heapq.heappop(pq)\n"
                "        if d > dist.get(u, 10**18):\n"
                "            continue\n"
                "        for v, w in adj[u]:\n"
                "            nd = d + w\n"
                "            if nd < dist.get(v, 10**18):\n"
                "                dist[v] = nd\n"
                "                heapq.heappush(pq, (nd, v))\n"
                "    return max(dist.values()) if len(dist) == n else -1\n"
            ),
            "go": (
                "package main\n\n"
                "func networkDelayTime(times [][]int, n int, k int) int {\n"
                "\tconst inf = int(1e9)\n"
                "\tdist := make([]int, n+1)\n"
                "\tfor i := 1; i <= n; i++ {\n"
                "\t\tdist[i] = inf\n"
                "\t}\n"
                "\tdist[k] = 0\n"
                "\tused := make([]bool, n+1)\n"
                "\tfor step := 0; step < n; step++ {\n"
                "\t\tu := -1\n"
                "\t\tfor i := 1; i <= n; i++ {\n"
                "\t\t\tif !used[i] && (u == -1 || dist[i] < dist[u]) {\n"
                "\t\t\t\tu = i\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t\tif u == -1 || dist[u] == inf {\n"
                "\t\t\tbreak\n"
                "\t\t}\n"
                "\t\tused[u] = true\n"
                "\t\tfor _, e := range times {\n"
                "\t\t\tif e[0] == u && dist[u]+e[2] < dist[e[1]] {\n"
                "\t\t\t\tdist[e[1]] = dist[u] + e[2]\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\tans := 0\n"
                "\tfor i := 1; i <= n; i++ {\n"
                "\t\tif dist[i] == inf {\n"
                "\t\t\treturn -1\n"
                "\t\t}\n"
                "\t\tif dist[i] > ans {\n"
                "\t\t\tans = dist[i]\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn ans\n"
                "}\n"
            ),
            "typescript": (
                "function networkDelayTime(times: number[][], n: number, k: number): number {\n"
                "  const INF = 1e9;\n"
                "  const dist = new Array<number>(n + 1).fill(INF);\n"
                "  dist[k] = 0;\n"
                "  for (let i = 0; i < n; i++) {\n"
                "    let changed = false;\n"
                "    for (const [u, v, w] of times) {\n"
                "      if (dist[u] + w < dist[v]) {\n"
                "        dist[v] = dist[u] + w;\n"
                "        changed = true;\n"
                "      }\n"
                "    }\n"
                "    if (!changed) break;\n"
                "  }\n"
                "  let ans = 0;\n"
                "  for (let i = 1; i <= n; i++) {\n"
                "    if (dist[i] === INF) return -1;\n"
                "    ans = Math.max(ans, dist[i]);\n"
                "  }\n"
                "  return ans;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2], "expected": 2, "label": "4-node broadcast"},
            {"args": [[[1, 2, 1]], 2, 2], "expected": -1, "label": "Unreachable node 1"},
        ],
    },
    10: {
        "funcName": "coinChange",
        "statement": (
            "You are given an integer array `coins` representing coins of different denominations and an integer `amount`. "
            "Return the fewest number of coins that you need to make up that amount, or `-1` if that amount cannot be made."
        ),
        "examples": [
            {"input": "coins = [1, 2, 5], amount = 11", "output": "3", "explanation": "11 = 5 + 5 + 1."},
            {"input": "coins = [2], amount = 3", "output": "-1", "explanation": "Odd amount cannot be formed with coin 2."},
        ],
        "constraints": ["1 <= len(coins) <= 12", "0 <= amount <= 10^4", "Target Complexity: O(amount * len(coins)) time, O(amount) space"],
        "trap": "Greedily picking the largest coin first (which fails on `coins = [1, 3, 4], amount = 6`: greedy picks `4+1+1` (3 coins) instead of `3+3` (2 coins)!).",
        "pivot": "Define `dp[x]` = minimum coins to make exact amount `x`. Transition over all coins: `dp[x] = min(dp[x - c] + 1 for c in coins if x >= c)`.",
        "signal": "Failure of greedy choice on non-canonical denominations -> 1D Unbounded Knapsack DP.",
        "starter": {
            "python": "def coinChange(coins: list[int], amount: int) -> int:\n    # 1D bottom-up DP in O(amount * len(coins)) time\n    pass\n",
            "go": "package main\n\nfunc coinChange(coins []int, amount int) int {\n\t// 1D bottom-up DP in O(amount * len(coins)) time\n\treturn 0\n}\n",
            "typescript": "function coinChange(coins: number[], amount: number): number {\n  // 1D bottom-up DP in O(amount * len(coins)) time\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "def coinChange(coins: list[int], amount: int) -> int:\n"
                "    inf = amount + 1\n"
                "    dp = [0] + [inf] * amount\n"
                "    for c in coins:\n"
                "        for x in range(c, amount + 1):\n"
                "            if dp[x - c] + 1 < dp[x]:\n"
                "                dp[x] = dp[x - c] + 1\n"
                "    return dp[amount] if dp[amount] <= amount else -1\n"
            ),
            "go": (
                "package main\n\n"
                "func coinChange(coins []int, amount int) int {\n"
                "\tinf := amount + 1\n"
                "\tdp := make([]int, amount+1)\n"
                "\tfor i := 1; i <= amount; i++ {\n"
                "\t\tdp[i] = inf\n"
                "\t}\n"
                "\tfor _, c := range coins {\n"
                "\t\tfor x := c; x <= amount; x++ {\n"
                "\t\t\tif dp[x-c]+1 < dp[x] {\n"
                "\t\t\t\tdp[x] = dp[x-c] + 1\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\tif dp[amount] > amount {\n"
                "\t\treturn -1\n"
                "\t}\n"
                "\treturn dp[amount]\n"
                "}\n"
            ),
            "typescript": (
                "function coinChange(coins: number[], amount: number): number {\n"
                "  const inf = amount + 1;\n"
                "  const dp = new Int32Array(amount + 1).fill(inf);\n"
                "  dp[0] = 0;\n"
                "  for (const c of coins) {\n"
                "    for (let x = c; x <= amount; x++) {\n"
                "      if (dp[x - c] + 1 < dp[x]) dp[x] = dp[x - c] + 1;\n"
                "    }\n"
                "  }\n"
                "  return dp[amount] > amount ? -1 : dp[amount];\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[1, 2, 5], 11], "expected": 3, "label": "Standard 11"},
            {"args": [[1, 3, 4], 6], "expected": 2, "label": "Greedy trap (3+3 beats 4+1+1)"},
            {"args": [[2], 3], "expected": -1, "label": "Impossible amount"},
        ],
    },
    11: {
        "funcName": "predictTheWinner",
        "statement": (
            "You are given an integer array `nums`. Two players take turns picking either the left end `nums[l]` "
            "or the right end `nums[r]` of the remaining subarray. Both players play optimally to maximise their score.\n\n"
            "Return `True` if Player 1 can achieve at least as many points as Player 2 (`score1 - score2 >= 0`)."
        ),
        "examples": [
            {"input": "nums = [1, 5, 2]", "output": "False", "explanation": "Player 1 is forced to expose 5 to Player 2."},
            {"input": "nums = [1, 5, 233, 7]", "output": "True", "explanation": "Player 1 picks 1 or 7 to force access to 233."},
        ],
        "constraints": ["1 <= len(nums) <= 20", "0 <= nums[i] <= 10^7", "Target Complexity: O(N^2) time, O(N) space"],
        "trap": "Simulating two separate player scores instead of tracking the single relative score differential `my_score - opponent_score`.",
        "pivot": "In any zero-sum two-player turn game, define `dp[l][r]` = maximum net advantage `(current_player - other_player)` on subarray `nums[l..r]`. Picking `nums[l]` leaves the opponent with advantage `dp[l+1][r]`, so your net gain is `nums[l] - dp[l+1][r]`!",
        "signal": "Two-player optimal turn game on intervals -> Minimax Interval DP `dp[l][r] = max(nums[l] - dp[l+1][r], nums[r] - dp[l][r-1])`.",
        "starter": {
            "python": "def predictTheWinner(nums: list[int]) -> bool:\n    # Minimax interval DP in O(N^2) time, O(N) space\n    pass\n",
            "go": "package main\n\nfunc predictTheWinner(nums []int) bool {\n\t// Minimax interval DP in O(N^2) time, O(N) space\n\treturn false\n}\n",
            "typescript": "function predictTheWinner(nums: number[]): boolean {\n  // Minimax interval DP in O(N^2) time, O(N) space\n  return false;\n}\n",
        },
        "solution": {
            "python": (
                "def predictTheWinner(nums: list[int]) -> bool:\n"
                "    n = len(nums)\n"
                "    dp = nums[:]\n"
                "    for l in range(n - 2, -1, -1):\n"
                "        for r in range(l + 1, n):\n"
                "            dp[r] = max(nums[l] - dp[r], nums[r] - dp[r - 1])\n"
                "    return dp[n - 1] >= 0\n"
            ),
            "go": (
                "package main\n\n"
                "func predictTheWinner(nums []int) bool {\n"
                "\tn := len(nums)\n"
                "\tdp := append([]int{}, nums...)\n"
                "\tfor l := n - 2; l >= 0; l-- {\n"
                "\t\tfor r := l + 1; r < n; r++ {\n"
                "\t\t\ta := nums[l] - dp[r]\n"
                "\t\t\tb := nums[r] - dp[r-1]\n"
                "\t\t\tif a > b {\n"
                "\t\t\t\tdp[r] = a\n"
                "\t\t\t} else {\n"
                "\t\t\t\tdp[r] = b\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn dp[n-1] >= 0\n"
                "}\n"
            ),
            "typescript": (
                "function predictTheWinner(nums: number[]): boolean {\n"
                "  const n = nums.length;\n"
                "  const dp = [...nums];\n"
                "  for (let l = n - 2; l >= 0; l--) {\n"
                "    for (let r = l + 1; r < n; r++) {\n"
                "      dp[r] = Math.max(nums[l] - dp[r], nums[r] - dp[r - 1]);\n"
                "    }\n"
                "  }\n"
                "  return dp[n - 1] >= 0;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[1, 5, 2]], "expected": False, "label": "Odd trap [1,5,2]"},
            {"args": [[1, 5, 233, 7]], "expected": True, "label": "Even length always winnable"},
        ],
    },
    12: {
        "funcName": "simulateFenwickRangeSum",
        "statement": (
            "Given an integer array `nums` and a list of operations `[['SUM', l, r], ['UPDATE', idx, val], ...]`, "
            "support point updates `nums[idx] = val` and inclusive range sum queries `sum(nums[l..r])` in O(log N) time "
            "using a Fenwick Tree (Binary Indexed Tree)."
        ),
        "examples": [
            {"input": "nums = [1, 3, 5], ops = [['SUM', 0, 2], ['UPDATE', 1, 2], ['SUM', 0, 2]]", "output": "[9, 8]", "explanation": "Initial sum 1+3+5=9; after updating index 1 to 2, sum is 1+2+5=8."},
        ],
        "constraints": ["1 <= len(nums) <= 3 * 10^4", "Target Complexity: O(log N) per update and range sum"],
        "trap": "Using a plain array (O(N) range sum) or static prefix sums (O(N) rebuild on every point update).",
        "pivot": "A 1-indexed Fenwick Tree (`BIT`) stores partial dyadic ranges of length `i & -i`. Adding a delta moves up via `i += i & -i` and querying a prefix strips the lowest set bit via `i -= i & -i`, both in at most `log2(N)` steps.",
        "signal": "Interleaved point updates and prefix/range queries -> Fenwick Tree (Binary Indexed Tree) or Segment Tree.",
        "starter": {
            "python": "def simulateFenwickRangeSum(nums: list[int], ops: list[list]) -> list[int]:\n    # O(log N) Fenwick Tree (Binary Indexed Tree)\n    pass\n",
            "go": "package main\n\nfunc simulateFenwickRangeSum(nums []int, ops [][]any) []int {\n\t// O(log N) Fenwick Tree (Binary Indexed Tree)\n\treturn nil\n}\n",
            "typescript": "function simulateFenwickRangeSum(nums: number[], ops: any[][]): number[] {\n  // O(log N) Fenwick Tree (Binary Indexed Tree)\n  return [];\n}\n",
        },
        "solution": {
            "python": (
                "def simulateFenwickRangeSum(nums: list[int], ops: list[list]) -> list[int]:\n"
                "    n = len(nums)\n"
                "    arr = [0] * n\n"
                "    bit = [0] * (n + 1)\n"
                "    def add(i: int, delta: int) -> None:\n"
                "        i += 1\n"
                "        while i <= n:\n"
                "            bit[i] += delta\n"
                "            i += i & -i\n"
                "    def query(i: int) -> int:\n"
                "        i += 1\n"
                "        s = 0\n"
                "        while i > 0:\n"
                "            s += bit[i]\n"
                "            i -= i & -i\n"
                "        return s\n"
                "    for i, x in enumerate(nums):\n"
                "        arr[i] = x\n"
                "        add(i, x)\n"
                "    out: list[int] = []\n"
                "    for op in ops:\n"
                "        if op[0] == 'UPDATE':\n"
                "            idx, val = int(op[1]), int(op[2])\n"
                "            add(idx, val - arr[idx])\n"
                "            arr[idx] = val\n"
                "        else:\n"
                "            l, r = int(op[1]), int(op[2])\n"
                "            out.append(query(r) - (query(l - 1) if l > 0 else 0))\n"
                "    return out\n"
            ),
            "go": (
                "package main\n\n"
                "func simulateFenwickRangeSum(nums []int, ops [][]any) []int {\n"
                "\tn := len(nums)\n"
                "\tarr := append([]int{}, nums...)\n"
                "\tbit := make([]int, n+1)\n"
                "\tadd := func(i, delta int) {\n"
                "\t\tfor i++; i <= n; i += i & -i {\n"
                "\t\t\tbit[i] += delta\n"
                "\t\t}\n"
                "\t}\n"
                "\tquery := func(i int) int {\n"
                "\t\ts := 0\n"
                "\t\tfor i++; i > 0; i -= i & -i {\n"
                "\t\t\ts += bit[i]\n"
                "\t\t}\n"
                "\t\treturn s\n"
                "\t}\n"
                "\tfor i, x := range nums {\n"
                "\t\tadd(i, x)\n"
                "\t}\n"
                "\tout := []int{}\n"
                "\tfor _, op := range ops {\n"
                "\t\tkind := op[0].(string)\n"
                "\t\ta := int(op[1].(float64))\n"
                "\t\tb := int(op[2].(float64))\n"
                "\t\tif kind == \"UPDATE\" {\n"
                "\t\t\tadd(a, b-arr[a])\n"
                "\t\t\tarr[a] = b\n"
                "\t\t} else {\n"
                "\t\t\ts := query(b)\n"
                "\t\t\tif a > 0 {\n"
                "\t\t\t\ts -= query(a - 1)\n"
                "\t\t\t}\n"
                "\t\t\tout = append(out, s)\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn out\n"
                "}\n"
            ),
            "typescript": (
                "function simulateFenwickRangeSum(nums: number[], ops: any[][]): number[] {\n"
                "  const n = nums.length;\n"
                "  const arr = [...nums];\n"
                "  const bit = new Int32Array(n + 1);\n"
                "  const add = (i: number, d: number) => { for (i++; i <= n; i += i & -i) bit[i] += d; };\n"
                "  const query = (i: number): number => { let s = 0; for (i++; i > 0; i -= i & -i) s += bit[i]; return s; };\n"
                "  for (let i = 0; i < n; i++) add(i, nums[i]);\n"
                "  const out: number[] = [];\n"
                "  for (const op of ops) {\n"
                "    if (op[0] === 'UPDATE') {\n"
                "      const idx = Number(op[1]), val = Number(op[2]);\n"
                "      add(idx, val - arr[idx]);\n"
                "      arr[idx] = val;\n"
                "    } else {\n"
                "      const l = Number(op[1]), r = Number(op[2]);\n"
                "      out.push(query(r) - (l > 0 ? query(l - 1) : 0));\n"
                "    }\n"
                "  }\n"
                "  return out;\n"
                "}\n"
            ),
        },
        "tests": [
            {
                "args": [[1, 3, 5], [["SUM", 0, 2], ["UPDATE", 1, 2], ["SUM", 0, 2]]],
                "expected": [9, 8],
                "label": "Fenwick update and query",
            },
        ],
    },
    13: {
        "funcName": "longestHappyPrefix",
        "statement": (
            "A string is called a happy prefix if it is a non-empty prefix which is also a suffix (excluding the entire string itself). "
            "Given a string `s`, return the longest happy prefix of `s` using the KMP Prefix Function (`pi` table) or Rolling Hash in O(N) time."
        ),
        "examples": [
            {"input": 's = "level"', "output": '"l"', "explanation": "'l' is both prefix and suffix."},
            {"input": 's = "ababab"', "output": '"abab"', "explanation": "'abab' of length 4 is both a proper prefix and suffix."},
        ],
        "constraints": ["1 <= len(s) <= 10^5", "Target Complexity: O(N) time, O(N) space"],
        "trap": "Comparing every prefix `s[:k]` with suffix `s[-k:]` by string slicing in O(N^2) time.",
        "pivot": "Compute the KMP prefix function `lps[i]` (longest proper prefix of `s[0..i]` that is also a suffix of `s[0..i]`). When `s[i] != s[j]`, fall back along `j = lps[j - 1]` instead of restarting from 0. The answer is simply `s[:lps[-1]]`!",
        "signal": "Prefix-suffix self-overlap or linear-time substring matching -> KMP failure table `lps` or Rolling Hash.",
        "starter": {
            "python": "def longestHappyPrefix(s: str) -> str:\n    # KMP prefix table in O(N) time\n    pass\n",
            "go": "package main\n\nfunc longestHappyPrefix(s string) string {\n\t// KMP prefix table in O(N) time\n\treturn \"\"\n}\n",
            "typescript": "function longestHappyPrefix(s: string): string {\n  // KMP prefix table in O(N) time\n  return '';\n}\n",
        },
        "solution": {
            "python": (
                "def longestHappyPrefix(s: str) -> str:\n"
                "    n = len(s)\n"
                "    lps = [0] * n\n"
                "    j = 0\n"
                "    for i in range(1, n):\n"
                "        while j > 0 and s[i] != s[j]:\n"
                "            j = lps[j - 1]\n"
                "        if s[i] == s[j]:\n"
                "            j += 1\n"
                "            lps[i] = j\n"
                "    return s[:lps[-1]]\n"
            ),
            "go": (
                "package main\n\n"
                "func longestHappyPrefix(s string) string {\n"
                "\tn := len(s)\n"
                "\tlps := make([]int, n)\n"
                "\tj := 0\n"
                "\tfor i := 1; i < n; i++ {\n"
                "\t\tfor j > 0 && s[i] != s[j] {\n"
                "\t\t\tj = lps[j-1]\n"
                "\t\t}\n"
                "\t\tif s[i] == s[j] {\n"
                "\t\t\tj++\n"
                "\t\t\tlps[i] = j\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn s[:lps[n-1]]\n"
                "}\n"
            ),
            "typescript": (
                "function longestHappyPrefix(s: string): string {\n"
                "  const n = s.length;\n"
                "  const lps = new Int32Array(n);\n"
                "  let j = 0;\n"
                "  for (let i = 1; i < n; i++) {\n"
                "    while (j > 0 && s[i] !== s[j]) j = lps[j - 1];\n"
                "    if (s[i] === s[j]) lps[i] = ++j;\n"
                "  }\n"
                "  return s.slice(0, lps[n - 1]);\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": ["level"], "expected": "l", "label": "Single char border"},
            {"args": ["ababab"], "expected": "abab", "label": "Overlapping period"},
            {"args": ["a"], "expected": "", "label": "Single character"},
        ],
    },
    14: {
        "funcName": "maxPointsOnLine",
        "statement": (
            "Given an array of `points` where `points[i] = [x_i, y_i]` represents a point on the X-Y plane, "
            "return the maximum number of points that lie on the same straight line."
        ),
        "examples": [
            {"input": "points = [[1,1],[2,2],[3,3]]", "output": "3", "explanation": "All 3 points are collinear with slope 1/1."},
            {"input": "points = [[1,1],[3,2],[5,3],[4,1],[2,3],[1,4]]", "output": "4", "explanation": "4 points lie on y = -x + 5."},
        ],
        "constraints": ["1 <= len(points) <= 300", "-10^4 <= x_i, y_i <= 10^4", "Target Complexity: O(N^2) time, O(N) space"],
        "trap": "Using floating-point division `dy / dx` as a hash map key (which suffers from IEEE-754 precision collisions and divides by zero on vertical lines).",
        "pivot": "Represent every slope relative to anchor `points[i]` as a reduced integer fraction `(dy // g, dx // g)` where `g = gcd(dy, dx)` and normalise the sign so `dx > 0` (or `(1, 0)` when `dx == 0`).",
        "signal": "Exact rational ratios or slopes in hash maps -> Normalised GCD pair `(dy // g, dx // g)`.",
        "starter": {
            "python": "def maxPointsOnLine(points: list[list[int]]) -> int:\n    # O(N^2) GCD-normalised slope hashing\n    pass\n",
            "go": "package main\n\nfunc maxPointsOnLine(points [][]int) int {\n\t// O(N^2) GCD-normalised slope hashing\n\treturn 0\n}\n",
            "typescript": "function maxPointsOnLine(points: number[][]): number {\n  // O(N^2) GCD-normalised slope hashing\n  return 0;\n}\n",
        },
        "solution": {
            "python": (
                "import math\n\n"
                "def maxPointsOnLine(points: list[list[int]]) -> int:\n"
                "    n = len(points)\n"
                "    if n <= 2:\n"
                "        return n\n"
                "    best = 2\n"
                "    for i in range(n):\n"
                "        slopes: dict[tuple[int, int], int] = {}\n"
                "        for j in range(i + 1, n):\n"
                "            dx = points[j][0] - points[i][0]\n"
                "            dy = points[j][1] - points[i][1]\n"
                "            g = math.gcd(dx, dy)\n"
                "            dx //= g\n"
                "            dy //= g\n"
                "            if dx < 0 or (dx == 0 and dy < 0):\n"
                "                dx, dy = -dx, -dy\n"
                "            slopes[(dx, dy)] = slopes.get((dx, dy), 0) + 1\n"
                "        if slopes:\n"
                "            best = max(best, max(slopes.values()) + 1)\n"
                "    return best\n"
            ),
            "go": (
                "package main\n\n"
                "func gcd(a, b int) int {\n"
                "\tif a < 0 { a = -a }\n"
                "\tif b < 0 { b = -b }\n"
                "\tfor b != 0 { a, b = b, a%b }\n"
                "\treturn a\n"
                "}\n\n"
                "func maxPointsOnLine(points [][]int) int {\n"
                "\tn := len(points)\n"
                "\tif n <= 2 { return n }\n"
                "\tbest := 2\n"
                "\tfor i := 0; i < n; i++ {\n"
                "\t\tslopes := make(map[[2]int]int)\n"
                "\t\tfor j := i + 1; j < n; j++ {\n"
                "\t\t\tdx := points[j][0] - points[i][0]\n"
                "\t\t\tdy := points[j][1] - points[i][1]\n"
                "\t\t\tg := gcd(dx, dy)\n"
                "\t\t\tdx /= g\n"
                "\t\t\tdy /= g\n"
                "\t\t\tif dx < 0 || (dx == 0 && dy < 0) {\n"
                "\t\t\t\tdx, dy = -dx, -dy\n"
                "\t\t\t}\n"
                "\t\t\tk := [2]int{dx, dy}\n"
                "\t\t\tslopes[k]++\n"
                "\t\t\tif slopes[k]+1 > best {\n"
                "\t\t\t\tbest = slopes[k] + 1\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn best\n"
                "}\n"
            ),
            "typescript": (
                "function maxPointsOnLine(points: number[][]): number {\n"
                "  const n = points.length;\n"
                "  if (n <= 2) return n;\n"
                "  const gcd = (a: number, b: number): number => {\n"
                "    a = Math.abs(a); b = Math.abs(b);\n"
                "    while (b !== 0) { const t = b; b = a % b; a = t; }\n"
                "    return a;\n"
                "  };\n"
                "  let best = 2;\n"
                "  for (let i = 0; i < n; i++) {\n"
                "    const slopes = new Map<string, number>();\n"
                "    for (let j = i + 1; j < n; j++) {\n"
                "      let dx = points[j][0] - points[i][0];\n"
                "      let dy = points[j][1] - points[i][1];\n"
                "      const g = gcd(dx, dy);\n"
                "      dx /= g; dy /= g;\n"
                "      if (dx < 0 || (dx === 0 && dy < 0)) { dx = -dx; dy = -dy; }\n"
                "      const k = `${dx}/${dy}`;\n"
                "      const c = (slopes.get(k) ?? 0) + 1;\n"
                "      slopes.set(k, c);\n"
                "      if (c + 1 > best) best = c + 1;\n"
                "    }\n"
                "  }\n"
                "  return best;\n"
                "}\n"
            ),
        },
        "tests": [
            {"args": [[[1, 1], [2, 2], [3, 3]]], "expected": 3, "label": "Diagonal line"},
            {"args": [[[1, 1], [3, 2], [5, 3], [4, 1], [2, 3], [1, 4]]], "expected": 4, "label": "6-point plane"},
        ],
    },
    15: {
        "funcName": "simulateLRUCache",
        "statement": DETAILED_PART2[113]["statement"],
        "examples": DETAILED_PART2[113]["examples"],
        "constraints": DETAILED_PART2[113]["constraints"],
        "trap": DETAILED_PART2[113]["mentalModel"]["instinctiveTrap"],
        "pivot": DETAILED_PART2[113]["mentalModel"]["optimalPivot"],
        "signal": DETAILED_PART2[113]["mentalModel"]["triggerSignal"],
        "starter": DETAILED_PART2[113]["starterCode"],
        "solution": DETAILED_PART2[113]["solutionCode"],
        "tests": DETAILED_PART2[113]["testCases"],
    },
    16: {
        "funcName": "analyseServiceLogs",
        "statement": DETAILED_PART2[117]["statement"],
        "examples": DETAILED_PART2[117]["examples"],
        "constraints": DETAILED_PART2[117]["constraints"],
        "trap": DETAILED_PART2[117]["mentalModel"]["instinctiveTrap"],
        "pivot": DETAILED_PART2[117]["mentalModel"]["optimalPivot"],
        "signal": DETAILED_PART2[117]["mentalModel"]["triggerSignal"],
        "starter": DETAILED_PART2[117]["starterCode"],
        "solution": DETAILED_PART2[117]["solutionCode"],
        "tests": DETAILED_PART2[117]["testCases"],
    },
}

_BLUEPRINT_BY_DAY: dict[int, dict[str, Any]] = {b["day"]: b for b in BLUEPRINTS_PART1}

# Compiled authentic LeetCode hidden edge cases across all 29 problem engines
HIDDEN_TESTS_BY_FUNC: dict[str, list[dict[str, Any]]] = EXPANDED_HIDDEN_TESTS_BY_FUNC


def _attach_hidden_test_cases(prob: dict[str, Any]) -> dict[str, Any]:
    visible = [dict(tc, hidden=False) for tc in prob.get("testCases", [])]
    hidden_raw = HIDDEN_TESTS_BY_FUNC.get(prob["funcName"], [])
    hidden = [dict(tc, hidden=True) for tc in hidden_raw]
    prob["visibleTestCases"] = visible
    prob["hiddenTestCases"] = hidden
    prob["testCases"] = visible + hidden
    prob["edgeCaseChecklist"] = get_edge_case_checklist_for_tags(prob.get("tags", []))
    return prob


def _lookup_curated_problem(sched: dict[str, Any]) -> dict[str, Any] | None:
    lc = str(sched.get("lc") or "").strip()
    if lc.startswith("LC "):
        num = lc[3:].strip()
        if f"lc-{num}" in _CURATED_BY_ID:
            return _CURATED_BY_ID[f"lc-{num}"]
        if f"sql-{num}" in _CURATED_BY_ID:
            return _CURATED_BY_ID[f"sql-{num}"]
    return None


def _build_full_problem(sched: dict[str, Any]) -> dict[str, Any]:
    day = sched["day"]
    phase_num = sched["phase"]
    phase_info = PHASE_MAP[phase_num]

    if day in DETAILED_PART1:
        p = dict(DETAILED_PART1[day])
        p["day"] = day
        p["id"] = f"day-{day:03d}"
        p["phaseTitle"] = phase_info["title"]
        return _attach_hidden_test_cases(p)

    if day in DETAILED_PART2:
        p = dict(DETAILED_PART2[day])
        p["day"] = day
        p["id"] = f"day-{day:03d}"
        p["phaseTitle"] = phase_info["title"]
        return _attach_hidden_test_cases(p)

    bp = _BLUEPRINT_BY_DAY.get(day, {})

    if day in EXTRA_46_PROBLEMS:
        extra = copy.deepcopy(EXTRA_46_PROBLEMS[day])
        p = {
            **extra,
            "day": day,
            "id": f"day-{day:03d}",
            "leetcodeId": sched["lc"],
            "title": sched["title"],
            "difficulty": sched["diff"],
            "phase": phase_num,
            "phaseTitle": phase_info["title"],
            "tags": sched["tags"],
            "url": sched["url"],
            "edgeCaseChecklist": get_edge_case_checklist_for_tags(sched["tags"]),
        }
        return p

    cur = _lookup_curated_problem(sched)
    if cur is not None:
        cur_copy = copy.deepcopy(cur)
        cur_mm = cur_copy.get("mentalModel") or {}
        trap = bp.get("trap") or cur_mm.get("instinctiveTrap") or ""
        pivot = bp.get("pivot") or cur_mm.get("optimalPivot") or ""
        signal = bp.get("signal") or cur_mm.get("triggerSignal") or ""
        raw_tcs = list(cur_copy.get("testCases") or [])
        vis_tcs = [dict(tc, hidden=False) for tc in raw_tcs]
        is_sql = bool(cur_copy.get("isSql"))
        func_name = cur_copy.get("funcName") or (
            f"sql_day_{day}" if is_sql else (cur_copy.get("harness") or {}).get("methodName") or f"solve_day_{day}"
        )
        p = {
            "day": day,
            "id": f"day-{day:03d}",
            "leetcodeId": sched["lc"],
            "title": sched["title"],
            "difficulty": sched["diff"],
            "phase": phase_num,
            "phaseTitle": phase_info["title"],
            "tags": sched["tags"],
            "url": cur_copy.get("url") or sched["url"],
            "statement": cur_copy.get("statement") or "",
            "examples": cur_copy.get("examples") or [],
            "constraints": cur_copy.get("constraints") or [],
            "clarifyingQuestions": cur_copy.get("clarifyingQuestions") or [],
            "mentalModel": {
                "instinctiveTrap": trap,
                "optimalPivot": pivot,
                "triggerSignal": signal,
            },
            "hints": cur_copy.get("hints") or [],
            "funcName": func_name,
            "harness": cur_copy.get("harness"),
            "isSql": is_sql,
            "starterCode": cur_copy.get("starterCode") or {},
            "solutionCode": cur_copy.get("solutionCode") or {},
            "walkthrough": cur_copy.get("walkthrough") or "",
            "traceSteps": cur_copy.get("traceSteps") or [
                {"step": 1, "focus": "Initialise state & guard clauses", "stateVars": f"{sched['lc']} base state", "note": "Handle empty, single-element, or degenerate boundaries upfront."},
                {"step": 2, "focus": "Execute core invariant", "stateVars": f"Pattern: {sched['tags'][0]}", "note": pivot or f"Apply optimal transition for {sched['title']}."},
                {"step": 3, "focus": "Return verified result", "stateVars": f"Target: {(cur_copy.get('complexity') or {}).get('optimalTime', 'Optimal')}", "note": "Confirm boundary conditions before returning."},
            ],
            "complexity": cur_copy.get("complexity") or {},
            "interviewFollowUp": cur_copy.get("interviewFollowUp") or {
                "question": f"How would an interviewer extend {sched['title']} under production scale?",
                "answer": "Expect follow-ups around streaming inputs, bounded memory, concurrency, or custom tie-breaking requirements.",
            },
            "visibleTestCases": vis_tcs,
            "hiddenTestCases": [],
            "testCases": vis_tcs,
            "edgeCaseChecklist": get_edge_case_checklist_for_tags(sched["tags"]),
        }
        for opt_key in ("approaches", "beginnerGuide", "companies", "sqlSchema", "referenceSql", "schemaTables"):
            if opt_key in cur_copy:
                p[opt_key] = cur_copy[opt_key]
        return p

    solver = _PHASE_SOLVERS[phase_num]
    trap = bp.get("trap") or solver["trap"]
    pivot = bp.get("pivot") or solver["pivot"]
    signal = bp.get("signal") or solver["signal"]

    p = {
        "day": day,
        "id": f"day-{day:03d}",
        "leetcodeId": sched["lc"],
        "title": sched["title"],
        "difficulty": sched["diff"],
        "phase": phase_num,
        "phaseTitle": phase_info["title"],
        "tags": sched["tags"],
        "url": sched["url"],
        "statement": (
            f"Daily Focus ({sched['lc']}: {sched['title']}).\n\n"
            f"Core Pattern Exercise for {phase_info['title']}:\n"
            f"{solver['statement']}"
        ),
        "examples": solver["examples"],
        "constraints": solver["constraints"],
        "clarifyingQuestions": [
            "What are the minimum and maximum input sizes, and can the input contain negative values, duplicates, or empty structures?",
            "What is the target time and auxiliary space complexity expected for a Senior / Staff SWE & FDE Hire rating?",
            "Are there degenerate boundary topologies (single element, all-equal elements, skewed trees, or disconnected components) we must guard upfront?",
        ],
        "mentalModel": {
            "instinctiveTrap": trap,
            "optimalPivot": pivot,
            "triggerSignal": signal,
        },
        "hints": [
            f"Tier 1 (Pattern Cue): {signal}",
            f"Tier 2 (State & Invariant): Avoid the brute-force trap ({trap}). Instead, maintain the minimal invariant state needed at each step.",
            f"Tier 3 (Transition Blueprint): {pivot}",
        ],
        "funcName": solver["funcName"],
        "starterCode": solver["starter"],
        "solutionCode": solver["solution"],
        "walkthrough": (
            f"1. Clarify constraints and edge cases for {sched['title']} ({sched['lc']}).\n"
            f"2. Apply the core mental pivot: {pivot}\n"
            f"3. Dry-run your state variables against the boundary test cases before submitting."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Initialise state & guard clauses", "stateVars": "Set up invariant state container", "note": "Verify empty/single-element bounds first."},
            {"step": 2, "focus": "Apply invariant transition", "stateVars": f"Pattern: {sched['tags'][0]}", "note": pivot},
            {"step": 3, "focus": "Finalise & verify complexity", "stateVars": "Optimal target achieved", "note": "Check off-by-one boundaries on final state."},
        ],
        "complexity": {
            "bruteTime": "O(N^2) or exponential",
            "bruteSpace": "O(N)",
            "optimalTime": "Optimal (see constraints)",
            "optimalSpace": "Optimal auxiliary state",
            "derivation": f"By shifting from brute-force re-scanning to the {phase_info['title']} invariant, each element transitions a constant or logarithmic number of times.",
        },
        "interviewFollowUp": {
            "question": f"How would a SWE or FDE interviewer extend {sched['title']} in the final 10 minutes?",
            "answer": "They will typically either (a) make the input arrive as an unbounded data stream with a sliding window or memory cap, (b) ask for thread-safe concurrent access, or (c) introduce dirty/corrupted records that must be isolated without crashing the pipeline.",
        },
        "testCases": solver["tests"],
    }
    return _attach_hidden_test_cases(p)


PROBLEMS: list[dict[str, Any]] = [_build_full_problem(s) for s in MASTER_120_SCHEDULE]
PROBLEMS_BY_DAY: dict[int, dict[str, Any]] = {p["day"]: p for p in PROBLEMS}
ALL_TAGS: list[dict[str, Any]] = IMAGE_TAGS + EXPANDED_TAGS
