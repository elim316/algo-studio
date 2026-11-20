#!/usr/bin/env python3
"""Curriculum Problems Part 2: Flagship Detailed Problems across Phases 6 to 16
plus the complete 120-Day Schedule Catalog mapping every day 1..120 to its tags,
mental model, progressive hints, runnable Python/Go/TypeScript solutions, and
test suites.
"""

from __future__ import annotations

from typing import Any

DETAILED_PART2: dict[int, dict[str, Any]] = {
    45: {
        "leetcodeId": "LC 295",
        "title": "Find Median from Data Stream",
        "difficulty": "Hard",
        "phase": 6,
        "tags": ["Two Pointers", "Design", "Sorting", "Heap (Priority Queue)", "Heap", "Data Stream"],
        "url": "https://leetcode.com/problems/find-median-from-data-stream/",
        "statement": (
            "The median is the middle value in an ordered integer list. If the size of the list is even, "
            "there is no middle value, and the median is the mean of the two middle values.\n\n"
            "Given a stream of integers `nums`, return an array of medians after each integer is added to the stream."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3]", "output": "[1.0, 1.5, 2.0]", "explanation": "After [1] -> 1.0; after [1,2] -> 1.5; after [1,2,3] -> 2.0."},
        ],
        "constraints": ["1 <= len(nums) <= 5 * 10^4", "-10^5 <= nums[i] <= 10^5", "Target Complexity: O(log N) per addNum, O(1) per findMedian"],
        "clarifyingQuestions": [
            "Why not maintain a sorted array via `bisect.insort`? (Binary search is O(log N), but shifting elements on insertion costs O(N) per element, degrading to O(N^2) overall.)",
            "Which elements of the sorted stream do we actually need to compute the median? (Only the largest element of the lower half and the smallest element of the upper half!)",
            "How do we keep the two halves balanced? (Maintain `len(small_max_heap) == len(large_min_heap)` or `len(small_max_heap) == len(large_min_heap) + 1`.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Keeping the entire stream sorted when only the boundary between the lower 50% and upper 50% determines the median.",
            "optimalPivot": "Split the stream at its midpoint into two heaps: a Max-Heap `small` holding the smaller half, and a Min-Heap `large` holding the larger half. The two heap tops sit face-to-face right at the median!",
            "triggerSignal": "Dynamic median or quantile over a growing/sliding stream -> Two Balanced Heaps (`MaxHeap` for lower half, `MinHeap` for upper half).",
        },
        "hints": [
            "Tier 1 (Pattern Cue): To find the median in O(1), you only need quick access to the maximum of the lower half and the minimum of the upper half.",
            "Tier 2 (State & Invariant): Keep `small` (Max-Heap, simulated via negated values in Python) and `large` (Min-Heap) such that `0 <= len(small) - len(large) <= 1` and `max(small) <= min(large)`.",
            "Tier 3 (Transition Blueprint): Push new `x` to `small`, pop the largest of `small` into `large`, and if `len(large) > len(small)`, pop the smallest of `large` back into `small`.",
        ],
        "funcName": "streamMedians",
        "starterCode": {
            "python": "def streamMedians(nums: list[int]) -> list[float]:\n    # Return running median after each number using two heaps\n    pass\n",
            "go": "package main\n\nfunc streamMedians(nums []int) []float64 {\n\t// Return running median after each number using two heaps\n\treturn nil\n}\n",
            "typescript": "function streamMedians(nums: number[]): number[] {\n  // Return running median after each number\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "import heapq\n\n"
                "def streamMedians(nums: list[int]) -> list[float]:\n"
                "    small: list[int] = []  # max-heap (negated)\n"
                "    large: list[int] = []  # min-heap\n"
                "    res: list[float] = []\n"
                "    for x in nums:\n"
                "        heapq.heappush(small, -x)\n"
                "        heapq.heappush(large, -heapq.heappop(small))\n"
                "        if len(large) > len(small):\n"
                "            heapq.heappush(small, -heapq.heappop(large))\n"
                "        if len(small) > len(large):\n"
                "            res.append(float(-small[0]))\n"
                "        else:\n"
                "            res.append((-small[0] + large[0]) / 2.0)\n"
                "    return res\n"
            ),
            "go": (
                "package main\n\nimport \"container/heap\"\n\n"
                "type minH []int\n"
                "func (h minH) Len() int           { return len(h) }\n"
                "func (h minH) Less(i, j int) bool { return h[i] < h[j] }\n"
                "func (h minH) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }\n"
                "func (h *minH) Push(x any)        { *h = append(*h, x.(int)) }\n"
                "func (h *minH) Pop() any          { old := *h; n := len(old); v := old[n-1]; *h = old[:n-1]; return v }\n\n"
                "func streamMedians(nums []int) []float64 {\n"
                "\tsmall, large := &minH{}, &minH{}\n"
                "\tres := make([]float64, 0, len(nums))\n"
                "\tfor _, x := range nums {\n"
                "\t\theap.Push(small, -x)\n"
                "\t\theap.Push(large, -heap.Pop(small).(int))\n"
                "\t\tif large.Len() > small.Len() {\n"
                "\t\t\theap.Push(small, -heap.Pop(large).(int))\n"
                "\t\t}\n"
                "\t\tif small.Len() > large.Len() {\n"
                "\t\t\tres = append(res, float64(-(*small)[0]))\n"
                "\t\t} else {\n"
                "\t\t\tres = append(res, float64(-(*small)[0]+(*large)[0])/2.0)\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn res\n"
                "}\n"
            ),
            "typescript": (
                "function streamMedians(nums: number[]): number[] {\n"
                "  const sorted: number[] = [];\n"
                "  const res: number[] = [];\n"
                "  for (const x of nums) {\n"
                "    let lo = 0, hi = sorted.length;\n"
                "    while (lo < hi) {\n"
                "      const mid = (lo + hi) >> 1;\n"
                "      if (sorted[mid] < x) lo = mid + 1;\n"
                "      else hi = mid;\n"
                "    }\n"
                "    sorted.splice(lo, 0, x);\n"
                "    const n = sorted.length;\n"
                "    res.push(n % 2 === 1 ? sorted[n >> 1] : (sorted[(n >> 1) - 1] + sorted[n >> 1]) / 2);\n"
                "  }\n"
                "  return res;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Maintain `small` (max-heap of lower half) and `large` (min-heap of upper half).\n"
            "2. For each new number `x`, push `-x` into `small`, then pop `small`'s max and push it into `large` (ensuring ordering `max(small) <= min(large)`).\n"
            "3. If `len(large) > len(small)`, move `large`'s min back to `small`.\n"
            "4. Read the median in O(1) from `-small[0]` (odd count) or `(-small[0] + large[0]) / 2` (even count)."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Add 1", "stateVars": "small=[1], large=[] | median=1.0", "note": "Odd size: top of small is 1.0."},
            {"step": 2, "focus": "Add 2", "stateVars": "small=[1], large=[2] | median=1.5", "note": "Even size: average of 1 and 2 is 1.5."},
            {"step": 3, "focus": "Add 3", "stateVars": "small=[2, 1], large=[3] | median=2.0", "note": "Rebalanced: top of small is 2.0."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(N)",
            "optimalTime": "O(N log N) total (O(log N) per insert)",
            "optimalSpace": "O(N)",
            "derivation": "Each insertion performs at most 3 heap push/pop operations of O(log N) each.",
        },
        "interviewFollowUp": {
            "question": "If 99% of stream numbers fall in `[0, 100]` and 1% lie outside `[0, 100]`, how can you compute the median in O(1) space?",
            "answer": "Maintain a 101-bucket array `buckets[0..100]`, plus two integer counters `less_than_zero` and `greater_than_100` (and small sorted lists only if the median ever falls in the 1% tails).",
        },
        "testCases": [
            {"args": [[1, 2, 3]], "expected": [1.0, 1.5, 2.0], "label": "Ascending stream"},
            {"args": [[5, 15, 1, 3]], "expected": [5.0, 10.0, 5.0, 4.0], "label": "Mixed stream"},
        ],
    },
    62: {
        "leetcodeId": "LC 210",
        "title": "Course Schedule II (Topological Sort & Cycle Detection)",
        "difficulty": "Medium",
        "phase": 8,
        "tags": ["Depth-First Search", "Breadth-First Search", "Graph Theory", "Topological Sort"],
        "url": "https://leetcode.com/problems/course-schedule-ii/",
        "statement": (
            "There are a total of `numCourses` courses you have to take, labelled from `0` to `numCourses - 1`. "
            "You are given an array `prerequisites` where `prerequisites[i] = [a, b]` indicates that you must take course `b` first if you want to take course `a`.\n\n"
            "Return the ordering of courses you should take to finish all courses. If it is impossible to finish all courses (due to a cycle), return an empty array `[]`."
        ),
        "examples": [
            {"input": "numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]", "output": "[0, 1, 2, 3]", "explanation": "Course 0 has indegree 0, unlocking 1 and 2, which together unlock 3."},
            {"input": "numCourses = 2, prerequisites = [[1,0],[0,1]]", "output": "[]", "explanation": "Cycle 0 <-> 1 makes completion impossible."},
        ],
        "constraints": ["1 <= numCourses <= 2000", "0 <= len(prerequisites) <= numCourses * (numCourses - 1)", "Target Complexity: O(V + E) time, O(V + E) space"],
        "clarifyingQuestions": [
            "Which direction does the dependency edge point for `[a, b]`? (`b -> a`, because completing `b` unlocks `a`, so `indegree[a]` increases by 1.)",
            "Can the graph be disconnected (courses with no prerequisites at all)? (Yes, all nodes with `indegree == 0` are enqueued initially.)",
            "How do we detect a cycle using Kahn's BFS algorithm? (If `len(order) < numCourses` when the queue empties, the remaining nodes are locked in at least one directed cycle.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Running a separate DFS from each node without 3-colour state (`UNVISITED, VISITING, VISITED`), leading to O(V*(V+E)) time or infinite loops on cycles.",
            "optimalPivot": "Track `indegree[u]` (how many unmet prerequisites course `u` still has). Courses with `indegree == 0` can be taken immediately. Completing `u` decrements `indegree[v]` for all dependents `v`; the moment `indegree[v]` hits `0`, enqueue `v`!",
            "triggerSignal": "Task scheduling, build order, dependency resolution, or cycle detection in a directed graph -> Kahn's Indegree BFS (`Topological Sort`).",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Which courses can you take in your very first semester?",
            "Tier 2 (State & Invariant): Build adjacency list `adj[b].append(a)` and array `indeg[a] += 1`. Seed a queue with all `u` where `indeg[u] == 0`.",
            "Tier 3 (Transition Blueprint): Pop `u`, append to `order`, and for each `v` in `adj[u]`, decrement `indeg[v]`. If `indeg[v] == 0`, push `v`. Return `order` iff `len(order) == numCourses`.",
        ],
        "funcName": "findOrder",
        "starterCode": {
            "python": "def findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]:\n    # Kahn's BFS topological sort in O(V + E) time\n    pass\n",
            "go": "package main\n\nfunc findOrder(numCourses int, prerequisites [][]int) []int {\n\t// Kahn's BFS topological sort in O(V + E) time\n\treturn nil\n}\n",
            "typescript": "function findOrder(numCourses: number, prerequisites: number[][]): number[] {\n  // Kahn's BFS topological sort in O(V + E) time\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "from collections import deque\n\n"
                "def findOrder(numCourses: int, prerequisites: list[list[int]]) -> list[int]:\n"
                "    adj: list[list[int]] = [[] for _ in range(numCourses)]\n"
                "    indeg = [0] * numCourses\n"
                "    for a, b in prerequisites:\n"
                "        adj[b].append(a)\n"
                "        indeg[a] += 1\n"
                "    q = deque(i for i in range(numCourses) if indeg[i] == 0)\n"
                "    order: list[int] = []\n"
                "    while q:\n"
                "        u = q.popleft()\n"
                "        order.append(u)\n"
                "        for v in adj[u]:\n"
                "            indeg[v] -= 1\n"
                "            if indeg[v] == 0:\n"
                "                q.append(v)\n"
                "    return order if len(order) == numCourses else []\n"
            ),
            "go": (
                "package main\n\n"
                "func findOrder(numCourses int, prerequisites [][]int) []int {\n"
                "\tadj := make([][]int, numCourses)\n"
                "\tindeg := make([]int, numCourses)\n"
                "\tfor _, p := range prerequisites {\n"
                "\t\ta, b := p[0], p[1]\n"
                "\t\tadj[b] = append(adj[b], a)\n"
                "\t\tindeg[a]++\n"
                "\t}\n"
                "\tq := make([]int, 0, numCourses)\n"
                "\tfor i := 0; i < numCourses; i++ {\n"
                "\t\tif indeg[i] == 0 {\n"
                "\t\t\tq = append(q, i)\n"
                "\t\t}\n"
                "\t}\n"
                "\torder := make([]int, 0, numCourses)\n"
                "\tfor len(q) > 0 {\n"
                "\t\tu := q[0]\n"
                "\t\tq = q[1:]\n"
                "\t\torder = append(order, u)\n"
                "\t\tfor _, v := range adj[u] {\n"
                "\t\t\tindeg[v]--\n"
                "\t\t\tif indeg[v] == 0 {\n"
                "\t\t\t\tq = append(q, v)\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\tif len(order) != numCourses {\n"
                "\t\treturn []int{}\n"
                "\t}\n"
                "\treturn order\n"
                "}\n"
            ),
            "typescript": (
                "function findOrder(numCourses: number, prerequisites: number[][]): number[] {\n"
                "  const adj: number[][] = Array.from({ length: numCourses }, () => []);\n"
                "  const indeg = new Int32Array(numCourses);\n"
                "  for (const [a, b] of prerequisites) {\n"
                "    adj[b].push(a);\n"
                "    indeg[a]++;\n"
                "  }\n"
                "  const q: number[] = [];\n"
                "  for (let i = 0; i < numCourses; i++) if (indeg[i] === 0) q.push(i);\n"
                "  const order: number[] = [];\n"
                "  let head = 0;\n"
                "  while (head < q.length) {\n"
                "    const u = q[head++];\n"
                "    order.push(u);\n"
                "    for (const v of adj[u]) {\n"
                "      if (--indeg[v] === 0) q.push(v);\n"
                "    }\n"
                "  }\n"
                "  return order.length === numCourses ? order : [];\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Build directed graph `b -> a` and count incoming edges `indeg[a]`.\n"
            "2. Enqueue all nodes with `indeg[i] == 0`.\n"
            "3. Repeatedly dequeue `u`, append `u` to `order`, and decrement `indeg[v]` for each outgoing neighbour `v`. Enqueue `v` when `indeg[v]` reaches 0.\n"
            "4. If `len(order) == numCourses`, return `order`; otherwise a cycle prevented some nodes from reaching indegree 0, so return `[]`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Init [[1,0],[2,0],[3,1],[3,2]]", "stateVars": "indeg=[0,1,1,2] | q=[0] | order=[]", "note": "Only course 0 has 0 prerequisites."},
            {"step": 2, "focus": "Pop 0", "stateVars": "indeg=[0,0,0,2] | q=[1,2] | order=[0]", "note": "Completing 0 unlocks courses 1 and 2."},
            {"step": 3, "focus": "Pop 1, then Pop 2", "stateVars": "indeg=[0,0,0,0] | q=[3] | order=[0,1,2]", "note": "Completing 1 and 2 drops indeg[3] from 2 to 0."},
            {"step": 4, "focus": "Pop 3", "stateVars": "q=[] | order=[0,1,2,3]", "note": "All 4 courses scheduled; return [0,1,2,3]."},
        ],
        "complexity": {
            "bruteTime": "O(V * (V + E))",
            "bruteSpace": "O(V + E)",
            "optimalTime": "O(V + E)",
            "optimalSpace": "O(V + E)",
            "derivation": "Each vertex is enqueued/dequeued at most once and each directed edge is relaxed at most once.",
        },
        "interviewFollowUp": {
            "question": "Suppose you can take unlimited courses in parallel each semester. What is the minimum number of semesters needed to graduate (Parallel Courses, LC 1136)?",
            "answer": "Process Kahn's BFS queue level-by-level (`for _ in range(len(q)):`), incrementing `semesters += 1` per BFS layer. The number of layers is the length of the longest dependency chain (critical path) in the DAG!",
        },
        "testCases": [
            {"args": [4, [[1, 0], [2, 0], [3, 1], [3, 2]]], "expected": [0, 1, 2, 3], "label": "Diamond DAG"},
            {"args": [2, [[1, 0], [0, 1]]], "expected": [], "label": "2-node cycle"},
            {"args": [1, []], "expected": [0], "label": "Single course"},
        ],
    },
    76: {
        "leetcodeId": "LC 1192",
        "title": "Critical Connections in a Network (Tarjan Bridges & Biconnected Components)",
        "difficulty": "Hard",
        "phase": 9,
        "tags": ["Depth-First Search", "Graph Theory", "Biconnected Component", "Strongly Connected Component"],
        "url": "https://leetcode.com/problems/critical-connections-in-a-network/",
        "statement": (
            "There are `n` servers numbered from `0` to `n - 1` connected by undirected server-to-server `connections` "
            "forming a network where `connections[i] = [a, b]`. A critical connection (bridge) is a connection that, "
            "if removed, will make some servers unable to reach some other server.\n\n"
            "Return all critical connections in the network sorted lexicographically."
        ),
        "examples": [
            {"input": "n = 4, connections = [[0,1],[1,2],[2,0],[1,3]]", "output": "[[1, 3]]", "explanation": "0-1-2 form a cycle (biconnected component); removing [1,3] disconnects server 3."},
        ],
        "constraints": ["2 <= n <= 10^5", "n - 1 <= len(connections) <= 10^5", "Target Complexity: O(V + E) time, O(V + E) space"],
        "clarifyingQuestions": [
            "When is an undirected edge `(u, v)` NOT a critical connection? (If and only if `(u, v)` lies on a simple cycle!)",
            "How can DFS detect in O(1) whether subtree `v` has a back-edge reaching `u` or an ancestor of `u`? (Compare `low[v]` against `disc[u]`.)",
            "What is the exact bridge condition between parent `u` and DFS child `v`? (`low[v] > disc[u]` strictly! If `low[v] == disc[u]`, `v` reaches `u` via a cycle, so `(u, v)` is not a bridge.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Removing each edge one by one and running BFS to check connectivity, which costs O(E * (V + E)) and times out at N = 10^5.",
            "optimalPivot": "Run a single Tarjan DFS recording discovery timestamp `disc[u]` and `low[u]` (the earliest discovery time reachable from `u`'s subtree using at most one back-edge). Tree edge `(u, v)` is a bridge iff `low[v] > disc[u]`.",
            "triggerSignal": "Single points of failure (bridges / articulation points / biconnected components) -> Tarjan `disc[u]` and `low[u]` DFS.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): An edge `(u, v)` is a bridge if and only if no node in `v`'s DFS subtree has a back-edge to `u` or an ancestor of `u`.",
            "Tier 2 (State & Invariant): Track `disc[u]` (discovery time) and `low[u]` (minimum `disc` reachable from `u`'s subtree excluding the parent edge `(v, u)`).",
            "Tier 3 (Transition Blueprint): For each neighbour `v != parent`: if unvisited, recurse on `v`, set `low[u] = min(low[u], low[v])`, and if `low[v] > disc[u]`, record `[min(u,v), max(u,v)]`. If visited, set `low[u] = min(low[u], disc[v])`.",
        ],
        "funcName": "criticalConnections",
        "starterCode": {
            "python": "def criticalConnections(n: int, connections: list[list[int]]) -> list[list[int]]:\n    # Tarjan bridge-finding algorithm in O(V + E) time\n    pass\n",
            "go": "package main\n\nfunc criticalConnections(n int, connections [][]int) [][]int {\n\t// Tarjan bridge-finding algorithm in O(V + E) time\n\treturn nil\n}\n",
            "typescript": "function criticalConnections(n: number, connections: number[][]): number[][] {\n  // Tarjan bridge-finding algorithm in O(V + E) time\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "import sys\n\n"
                "def criticalConnections(n: int, connections: list[list[int]]) -> list[list[int]]:\n"
                "    sys.setrecursionlimit(max(200000, n + 1000))\n"
                "    adj: list[list[int]] = [[] for _ in range(n)]\n"
                "    for u, v in connections:\n"
                "        adj[u].append(v)\n"
                "        adj[v].append(u)\n"
                "    disc = [-1] * n\n"
                "    low = [-1] * n\n"
                "    timer = 0\n"
                "    bridges: list[list[int]] = []\n"
                "    def dfs(u: int, parent: int) -> None:\n"
                "        nonlocal timer\n"
                "        disc[u] = low[u] = timer\n"
                "        timer += 1\n"
                "        for v in adj[u]:\n"
                "            if v == parent:\n"
                "                continue\n"
                "            if disc[v] == -1:\n"
                "                dfs(v, u)\n"
                "                if low[v] < low[u]:\n"
                "                    low[u] = low[v]\n"
                "                if low[v] > disc[u]:\n"
                "                    bridges.append([min(u, v), max(u, v)])\n"
                "            elif disc[v] < low[u]:\n"
                "                low[u] = disc[v]\n"
                "    dfs(0, -1)\n"
                "    bridges.sort()\n"
                "    return bridges\n"
            ),
            "go": (
                "package main\n\nimport \"sort\"\n\n"
                "func criticalConnections(n int, connections [][]int) [][]int {\n"
                "\tadj := make([][]int, n)\n"
                "\tfor _, e := range connections {\n"
                "\t\tu, v := e[0], e[1]\n"
                "\t\tadj[u] = append(adj[u], v)\n"
                "\t\tadj[v] = append(adj[v], u)\n"
                "\t}\n"
                "\tdisc := make([]int, n)\n"
                "\tlow := make([]int, n)\n"
                "\tfor i := range disc {\n"
                "\t\tdisc[i] = -1\n"
                "\t}\n"
                "\ttimer := 0\n"
                "\tbridges := [][]int{}\n"
                "\tvar dfs func(u, p int)\n"
                "\tdfs = func(u, p int) {\n"
                "\t\tdisc[u] = timer\n"
                "\t\tlow[u] = timer\n"
                "\t\ttimer++\n"
                "\t\tfor _, v := range adj[u] {\n"
                "\t\t\tif v == p {\n"
                "\t\t\t\tcontinue\n"
                "\t\t\t}\n"
                "\t\t\tif disc[v] == -1 {\n"
                "\t\t\t\tdfs(v, u)\n"
                "\t\t\t\tif low[v] < low[u] {\n"
                "\t\t\t\t\tlow[u] = low[v]\n"
                "\t\t\t\t}\n"
                "\t\t\t\tif low[v] > disc[u] {\n"
                "\t\t\t\t\ta, b := u, v\n"
                "\t\t\t\t\tif a > b {\n"
                "\t\t\t\t\t\ta, b = b, a\n"
                "\t\t\t\t\t}\n"
                "\t\t\t\t\tbridges = append(bridges, []int{a, b})\n"
                "\t\t\t\t}\n"
                "\t\t\t} else if disc[v] < low[u] {\n"
                "\t\t\t\tlow[u] = disc[v]\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\tdfs(0, -1)\n"
                "\tsort.Slice(bridges, func(i, j int) bool {\n"
                "\t\tif bridges[i][0] != bridges[j][0] {\n"
                "\t\t\treturn bridges[i][0] < bridges[j][0]\n"
                "\t\t}\n"
                "\t\treturn bridges[i][1] < bridges[j][1]\n"
                "\t})\n"
                "\treturn bridges\n"
                "}\n"
            ),
            "typescript": (
                "function criticalConnections(n: number, connections: number[][]): number[][] {\n"
                "  const adj: number[][] = Array.from({ length: n }, () => []);\n"
                "  for (const [u, v] of connections) {\n"
                "    adj[u].push(v);\n"
                "    adj[v].push(u);\n"
                "  }\n"
                "  const disc = new Int32Array(n).fill(-1);\n"
                "  const low = new Int32Array(n).fill(-1);\n"
                "  let timer = 0;\n"
                "  const bridges: number[][] = [];\n"
                "  const dfs = (u: number, p: number): void => {\n"
                "    disc[u] = low[u] = timer++;\n"
                "    for (const v of adj[u]) {\n"
                "      if (v === p) continue;\n"
                "      if (disc[v] === -1) {\n"
                "        dfs(v, u);\n"
                "        if (low[v] < low[u]) low[u] = low[v];\n"
                "        if (low[v] > disc[u]) bridges.push([Math.min(u, v), Math.max(u, v)]);\n"
                "      } else if (disc[v] < low[u]) {\n"
                "        low[u] = disc[v];\n"
                "      }\n"
                "    }\n"
                "  };\n"
                "  dfs(0, -1);\n"
                "  bridges.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));\n"
                "  return bridges;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Build an undirected adjacency list.\n"
            "2. Run DFS tracking `disc[u]` (when `u` was first visited) and `low[u]` (smallest `disc` reachable from `u`'s subtree).\n"
            "3. Ignore the immediate parent edge `v == parent`.\n"
            "4. After returning from child `v`, if `low[v] > disc[u]`, no back-edge from `v`'s subtree reaches `u` or higher, so `(u, v)` is a bridge."
        ),
        "traceSteps": [
            {"step": 1, "focus": "DFS 0 -> 1 -> 2", "stateVars": "disc=[0,1,2,-1], low=[0,1,2,-1]", "note": "Tree edges 0-1 and 1-2 explored."},
            {"step": 2, "focus": "Back-edge 2 -> 0", "stateVars": "low[2]=min(2, disc[0])=0 -> low[1]=0", "note": "Cycle 0-1-2 lowers low[2] and low[1] to 0."},
            {"step": 3, "focus": "Tree edge 1 -> 3", "stateVars": "disc[3]=3, low[3]=3 > disc[1](1)", "note": "low[3] (3) > disc[1] (1) -> [1, 3] is a critical bridge!"},
        ],
        "complexity": {
            "bruteTime": "O(E * (V + E))",
            "bruteSpace": "O(V + E)",
            "optimalTime": "O(V + E)",
            "optimalSpace": "O(V + E)",
            "derivation": "Single DFS pass visiting each vertex and edge constant times.",
        },
        "interviewFollowUp": {
            "question": "How does Tarjan's Strongly Connected Components (SCC) algorithm on a DIRECTED graph differ from this undirected bridge finder?",
            "answer": "In a directed graph, a cross-edge to an already-completed SCC must not lower `low[u]`. We maintain an explicit `on_stack` boolean array and a stack of active vertices, only updating `low[u] = min(low[u], disc[v])` when `on_stack[v]` is True, and popping an entire SCC whenever `low[u] == disc[u]`.",
        },
        "testCases": [
            {"args": [4, [[0, 1], [1, 2], [2, 0], [1, 3]]], "expected": [[1, 3]], "label": "Triangle + bridge"},
            {"args": [2, [[0, 1]]], "expected": [[0, 1]], "label": "Single edge"},
        ],
    },
    113: {
        "leetcodeId": "LC 146",
        "title": "LRU Cache (Hash Map + Doubly-Linked List Design)",
        "difficulty": "Medium",
        "phase": 15,
        "tags": ["Hash Table", "Linked List", "Design", "Doubly-Linked List", "Idiomatic Modularity & Helper Design"],
        "url": "https://leetcode.com/problems/lru-cache/",
        "statement": (
            "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.\n\n"
            "Implement `get(key)` (returns value or `-1` if absent) and `put(key, value)` (inserts/updates and evicts the least recently used key when capacity is exceeded), both in strict O(1) time.\n"
            "For testing, `simulateLRUCache(capacity, ops)` takes operations `[['PUT', k, v], ['GET', k], ...]` and returns the list of `GET` outputs."
        ),
        "examples": [
            {"input": "capacity = 2, ops = [['PUT',1,1],['PUT',2,2],['GET',1],['PUT',3,3],['GET',2],['PUT',4,4],['GET',1],['GET',3],['GET',4]]", "output": "[1, -1, -1, 3, 4]", "explanation": "GET 1 refreshes key 1, so PUT 3 evicts key 2."},
        ],
        "constraints": ["1 <= capacity <= 3000", "0 <= key <= 10^4", "Target Complexity: O(1) time per get and put"],
        "clarifyingQuestions": [
            "Does updating an existing key via `put(key, new_val)` also mark `key` as most recently used? (Yes!)",
            "What happens if `capacity == 0`? (Good edge case to guard: if `capacity <= 0`, `put` is a no-op and `get` returns `-1`.)",
            "How do dummy sentinel `head` and `tail` nodes simplify Doubly-Linked List pointer surgery? (They eliminate all `if node.prev is None` and `if node.next is None` null checks!)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Using a dynamic array or queue to track recency (which takes O(N) to remove a middle element on cache hit) or forgetting to update the hash map key when evicting `tail.prev`.",
            "optimalPivot": "Pair a Hash Map `cache[key] -> Node` (for O(1) lookup) with a Doubly-Linked List bounded by dummy sentinels `head <-> ... <-> tail` (for O(1) detachment and insertion). Write two tiny 4-line helpers `_remove(node)` and `_add_front(node)` and build `get` and `put` purely out of those two helpers!",
            "triggerSignal": "O(1) key lookup + O(1) arbitrary removal + recency order -> Hash Map of Doubly-Linked List nodes with dummy `head` and `tail` sentinels.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): No single primitive gives both O(1) lookup by key and O(1) splicing from the middle of an ordered sequence. Combine two structures.",
            "Tier 2 (State & Invariant): Create dummy `head` and `tail` nodes wired as `head.next = tail; tail.prev = head`. Keep most recent right after `head` and LRU right before `tail`.",
            "Tier 3 (Transition Blueprint): Write `_remove(node)` and `_insert_front(node)`. Every `get` or `put` hit is simply `_remove(node); _insert_front(node)`. Eviction is `lru = tail.prev; _remove(lru); del cache[lru.key]`.",
        ],
        "funcName": "simulateLRUCache",
        "starterCode": {
            "python": "def simulateLRUCache(capacity: int, ops: list[list]) -> list[int]:\n    # Implement LRU Cache with O(1) get and put\n    pass\n",
            "go": "package main\n\nfunc simulateLRUCache(capacity int, ops [][]int) []int {\n\t// ops entry: [1, k, v] for PUT, [0, k, 0] for GET\n\treturn nil\n}\n",
            "typescript": "function simulateLRUCache(capacity: number, ops: any[][]): number[] {\n  // Implement LRU Cache with O(1) get and put\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "class _Node:\n"
                "    __slots__ = ('key', 'val', 'prev', 'next')\n"
                "    def __init__(self, key: int = 0, val: int = 0) -> None:\n"
                "        self.key = key\n"
                "        self.val = val\n"
                "        self.prev: _Node | None = None\n"
                "        self.next: _Node | None = None\n\n"
                "def simulateLRUCache(capacity: int, ops: list[list]) -> list[int]:\n"
                "    head, tail = _Node(), _Node()\n"
                "    head.next, tail.prev = tail, head\n"
                "    cache: dict[int, _Node] = {}\n"
                "    def remove(node: _Node) -> None:\n"
                "        p, n = node.prev, node.next\n"
                "        assert p is not None and n is not None\n"
                "        p.next, n.prev = n, p\n"
                "    def add_front(node: _Node) -> None:\n"
                "        nxt = head.next\n"
                "        assert nxt is not None\n"
                "        node.next, node.prev = nxt, head\n"
                "        head.next = nxt.prev = node\n"
                "    out: list[int] = []\n"
                "    for op in ops:\n"
                "        if op[0] == 'GET':\n"
                "            k = int(op[1])\n"
                "            if k not in cache:\n"
                "                out.append(-1)\n"
                "            else:\n"
                "                node = cache[k]\n"
                "                remove(node)\n"
                "                add_front(node)\n"
                "                out.append(node.val)\n"
                "        else:\n"
                "            k, v = int(op[1]), int(op[2])\n"
                "            if k in cache:\n"
                "                remove(cache[k])\n"
                "            node = _Node(k, v)\n"
                "            cache[k] = node\n"
                "            add_front(node)\n"
                "            if len(cache) > capacity:\n"
                "                lru = tail.prev\n"
                "                assert lru is not None\n"
                "                remove(lru)\n"
                "                del cache[lru.key]\n"
                "    return out\n"
            ),
            "go": (
                "package main\n\n"
                "type lruNode struct {\n"
                "\tkey, val   int\n"
                "\tprev, next *lruNode\n"
                "}\n\n"
                "func simulateLRUCache(capacity int, ops [][]any) []int {\n"
                "\thead, tail := &lruNode{}, &lruNode{}\n"
                "\thead.next = tail\n"
                "\ttail.prev = head\n"
                "\tcache := make(map[int]*lruNode)\n"
                "\tremove := func(n *lruNode) {\n"
                "\t\tn.prev.next = n.next\n"
                "\t\tn.next.prev = n.prev\n"
                "\t}\n"
                "\taddFront := func(n *lruNode) {\n"
                "\t\tn.next = head.next\n"
                "\t\tn.prev = head\n"
                "\t\thead.next.prev = n\n"
                "\t\thead.next = n\n"
                "\t}\n"
                "\tout := []int{}\n"
                "\tfor _, op := range ops {\n"
                "\t\tkind := op[0].(string)\n"
                "\t\tk := int(op[1].(float64))\n"
                "\t\tif kind == \"GET\" {\n"
                "\t\t\tif n, ok := cache[k]; !ok {\n"
                "\t\t\t\tout = append(out, -1)\n"
                "\t\t\t} else {\n"
                "\t\t\t\tremove(n)\n"
                "\t\t\t\taddFront(n)\n"
                "\t\t\t\tout = append(out, n.val)\n"
                "\t\t\t}\n"
                "\t\t} else {\n"
                "\t\t\tv := int(op[2].(float64))\n"
                "\t\t\tif n, ok := cache[k]; ok {\n"
                "\t\t\t\tremove(n)\n"
                "\t\t\t}\n"
                "\t\t\tn := &lruNode{key: k, val: v}\n"
                "\t\t\tcache[k] = n\n"
                "\t\t\taddFront(n)\n"
                "\t\t\tif len(cache) > capacity {\n"
                "\t\t\t\tlru := tail.prev\n"
                "\t\t\t\tremove(lru)\n"
                "\t\t\t\tdelete(cache, lru.key)\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn out\n"
                "}\n"
            ),
            "typescript": (
                "function simulateLRUCache(capacity: number, ops: any[][]): number[] {\n"
                "  const cache = new Map<number, number>();\n"
                "  const out: number[] = [];\n"
                "  for (const op of ops) {\n"
                "    const kind = op[0];\n"
                "    const k = Number(op[1]);\n"
                "    if (kind === 'GET') {\n"
                "      if (!cache.has(k)) {\n"
                "        out.push(-1);\n"
                "      } else {\n"
                "        const val = cache.get(k)!;\n"
                "        cache.delete(k);\n"
                "        cache.set(k, val);\n"
                "        out.push(val);\n"
                "      }\n"
                "    } else {\n"
                "      const v = Number(op[2]);\n"
                "      if (cache.has(k)) cache.delete(k);\n"
                "      cache.set(k, v);\n"
                "      if (cache.size > capacity) {\n"
                "        const lruKey = cache.keys().next().value!;\n"
                "        cache.delete(lruKey);\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "  return out;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Wire dummy sentinel nodes `head <-> tail` so the doubly-linked list is never empty.\n"
            "2. Encapsulate pointer rewiring into two 4-line functions: `remove(node)` and `add_front(node)`.\n"
            "3. On `GET(k)`, if present, `remove(node)` + `add_front(node)` and return `node.val`.\n"
            "4. On `PUT(k, v)`, remove old node if present, insert new node at front, and if `len(cache) > capacity`, evict `tail.prev` and delete `lru.key` from `cache`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "PUT(1,1), PUT(2,2)", "stateVars": "head <-> (2:2) <-> (1:1) <-> tail", "note": "Key 2 is MRU (at head); key 1 is LRU (at tail)."},
            {"step": 2, "focus": "GET(1) -> returns 1", "stateVars": "head <-> (1:1) <-> (2:2) <-> tail", "note": "Key 1 moves to front; key 2 becomes LRU."},
            {"step": 3, "focus": "PUT(3,3) (cap=2)", "stateVars": "head <-> (3:3) <-> (1:1) <-> tail", "note": "Evicts tail.prev (key 2). GET(2) now returns -1."},
        ],
        "complexity": {
            "bruteTime": "O(N) per operation",
            "bruteSpace": "O(capacity)",
            "optimalTime": "O(1) per GET and PUT",
            "optimalSpace": "O(capacity)",
            "derivation": "Hash table lookup is O(1) and doubly-linked list splice via node pointer is 4 pointer assignments in O(1).",
        },
        "interviewFollowUp": {
            "question": "How would you make this LRU cache thread-safe for high-throughput concurrent reads in Go or Java?",
            "answer": "Even `GET` mutates the linked list order, so a naive `RWMutex` still requires a write lock on `GET`! In production (such as Groupcache or Caffeine), shard the keyspace into `M = 64` independent LRU shards (`hash(key) % 64`), or buffer read-hit promotions in a lock-free ring buffer drained in batches.",
        },
        "testCases": [
            {
                "args": [2, [["PUT", 1, 1], ["PUT", 2, 2], ["GET", 1], ["PUT", 3, 3], ["GET", 2], ["PUT", 4, 4], ["GET", 1], ["GET", 3], ["GET", 4]]],
                "expected": [1, -1, -1, 3, 4],
                "label": "Standard LRU eviction sequence",
            },
        ],
    },
    117: {
        "leetcodeId": "FDE-1",
        "title": "FDE Multi-Part: Resilient Telemetry Log Parser & Error-Rate Aggregator",
        "difficulty": "FDE Multi-Part",
        "phase": 16,
        "tags": [
            "String",
            "Hash Table",
            "Sorting",
            "FDE: Dirty Data & Resilient Log Parsing",
            "FDE: Multi-Step Requirement Evolution",
            "Idiomatic Modularity & Helper Design",
        ],
        "url": "https://leetcode.com/problemset/",
        "statement": (
            "In Forward Deployed Engineer (FDE) and SWE interviews, you are frequently handed messy real-world telemetry logs "
            "and asked to evolve your solution across 3 parts:\n\n"
            "- Part 1 (Parse & Clean): Each log line is formatted as `\"<timestamp_sec>|<service>|<status_code>|<latency_ms>\"`. "
            "However, customer streams contain malformed lines (missing fields, non-integer timestamps/status/latency, negative latency, or empty service names). "
            "Silently skip malformed lines.\n"
            "- Part 2 (Windowed Deduplication): Duplicate retries with the exact same `(timestamp_sec, service, status_code, latency_ms)` within the input must be deduplicated.\n"
            "- Part 3 (SLO Breach Ranking): For each service with at least 1 valid request, compute its error rate (`status_code >= 500` count divided by total valid requests, rounded to 4 decimal places) "
            "and return services whose error rate is `>= threshold`, sorted by error rate descending, then service name ascending: `[[service, error_rate_pct_int, p95_or_max_latency], ...]` "
            "(specifically return `[service, error_count, total_count, max_latency]` for exact integer verification)."
        ),
        "examples": [
            {
                "input": 'logs = ["100|auth|500|120", "100|auth|500|120", "101|auth|200|40", "bad_line", "102|pay|503|310", "103|pay|502|-5"], minErrorRate = 0.5',
                "output": '[["pay", 1, 1, 310], ["auth", 1, 2, 120]]',
                "explanation": "Duplicate auth 500 is deduplicated (auth has 1 error / 2 total = 0.5, max latency 120). Negative latency on pay is dropped (pay has 1 error / 1 total = 1.0, max latency 310).",
            },
        ],
        "constraints": ["1 <= len(logs) <= 5 * 10^4", "0.0 <= minErrorRate <= 1.0", "Target Complexity: O(N + S log S) where S is unique services"],
        "clarifyingQuestions": [
            "How should malformed records be handled: raise an exception or drop and continue? (In FDE pipelines, never let one corrupt customer row crash the batch; skip invalid rows cleanly.)",
            "What constitutes a valid HTTP status code and latency? (`100 <= status <= 599` and `latency >= 0`.)",
            "How should ties in error rate be broken? (Compare error rates via cross-multiplication or float, then sort alphabetically by service name.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Writing a single monolithic loop with inline `split('|')` indexing that crashes with `IndexError` or `ValueError` on dirty inputs and becomes spaghetti when Part 2 (deduplication) and Part 3 (ranking) are added.",
            "optimalPivot": "Decompose into 3 clean pipeline stages mirroring production FDE code: `parse_record(raw) -> Record | None` (validation boundary), `deduplicate(records)`, and `aggregate_metrics(records, min_error_rate)`. When the interviewer adds Part 2 or Part 3, you only touch one isolated stage!",
            "triggerSignal": "Multi-part FDE or practical SWE interview -> Separate `parse/validate`, `transform/dedupe`, and `aggregate/rank` into composable functions.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Isolate parsing into a helper that returns `None` if `len(parts) != 4`, `service == ''`, `not (100 <= status <= 599)`, or `latency < 0`.",
            "Tier 2 (State & Invariant): Use a `seen` set of `(ts, service, status, latency)` tuples to deduplicate retries in O(1).",
            "Tier 3 (Transition Blueprint): Accumulate `[errors, total, max_lat]` per service, filter by `errors / total >= minErrorRate`, and sort by `(-errors / total, service)`.",
        ],
        "funcName": "analyseServiceLogs",
        "starterCode": {
            "python": "def analyseServiceLogs(logs: list[str], minErrorRate: float) -> list[list]:\n    # Parse dirty logs, deduplicate, and rank services breaching minErrorRate\n    pass\n",
            "go": "package main\n\nfunc analyseServiceLogs(logs []string, minErrorRate float64) [][]any {\n\t// Parse dirty logs, deduplicate, and rank services breaching minErrorRate\n\treturn nil\n}\n",
            "typescript": "function analyseServiceLogs(logs: string[], minErrorRate: number): any[][] {\n  // Parse dirty logs, deduplicate, and rank services breaching minErrorRate\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "def analyseServiceLogs(logs: list[str], minErrorRate: float) -> list[list]:\n"
                "    seen: set[tuple[int, str, int, int]] = set()\n"
                "    stats: dict[str, list[int]] = {}  # service -> [errors, total, max_lat]\n"
                "    for raw in logs:\n"
                "        parts = raw.split('|')\n"
                "        if len(parts) != 4:\n"
                "            continue\n"
                "        ts_s, svc, st_s, lat_s = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()\n"
                "        if not svc:\n"
                "            continue\n"
                "        try:\n"
                "            ts, status, lat = int(ts_s), int(st_s), int(lat_s)\n"
                "        except ValueError:\n"
                "            continue\n"
                "        if status < 100 or status > 599 or lat < 0 or ts < 0:\n"
                "            continue\n"
                "        rec = (ts, svc, status, lat)\n"
                "        if rec in seen:\n"
                "            continue\n"
                "        seen.add(rec)\n"
                "        if svc not in stats:\n"
                "            stats[svc] = [0, 0, 0]\n"
                "        entry = stats[svc]\n"
                "        if status >= 500:\n"
                "            entry[0] += 1\n"
                "        entry[1] += 1\n"
                "        if lat > entry[2]:\n"
                "            entry[2] = lat\n"
                "    out: list[list] = []\n"
                "    for svc, (errs, tot, max_lat) in stats.items():\n"
                "        if errs / tot + 1e-12 >= minErrorRate:\n"
                "            out.append([svc, errs, tot, max_lat])\n"
                "    out.sort(key=lambda r: (-(r[1] / r[2]), r[0]))\n"
                "    return out\n"
            ),
            "go": (
                "package main\n\nimport (\n\t\"sort\"\n\t\"strconv\"\n\t\"strings\"\n)\n\n"
                "func analyseServiceLogs(logs []string, minErrorRate float64) [][]any {\n"
                "\tseen := make(map[string]bool)\n"
                "\ttype stat struct{ errs, tot, maxLat int }\n"
                "\tstats := make(map[string]*stat)\n"
                "\tfor _, raw := range logs {\n"
                "\t\tparts := strings.Split(raw, \"|\")\n"
                "\t\tif len(parts) != 4 {\n"
                "\t\t\tcontinue\n"
                "\t\t}\n"
                "\t\tsvc := strings.TrimSpace(parts[1])\n"
                "\t\tif svc == \"\" {\n"
                "\t\t\tcontinue\n"
                "\t\t}\n"
                "\t\tts, e1 := strconv.Atoi(strings.TrimSpace(parts[0]))\n"
                "\t\tst, e2 := strconv.Atoi(strings.TrimSpace(parts[2]))\n"
                "\t\tlat, e3 := strconv.Atoi(strings.TrimSpace(parts[3]))\n"
                "\t\tif e1 != nil || e2 != nil || e3 != nil || ts < 0 || st < 100 || st > 599 || lat < 0 {\n"
                "\t\t\tcontinue\n"
                "\t\t}\n"
                "\t\tkey := strconv.Itoa(ts) + \"|\" + svc + \"|\" + strconv.Itoa(st) + \"|\" + strconv.Itoa(lat)\n"
                "\t\tif seen[key] {\n"
                "\t\t\tcontinue\n"
                "\t\t}\n"
                "\t\tseen[key] = true\n"
                "\t\ts, ok := stats[svc]\n"
                "\t\tif !ok {\n"
                "\t\t\ts = &stat{}\n"
                "\t\t\tstats[svc] = s\n"
                "\t\t}\n"
                "\t\tif st >= 500 {\n"
                "\t\t\ts.errs++\n"
                "\t\t}\n"
                "\t\ts.tot++\n"
                "\t\tif lat > s.maxLat {\n"
                "\t\t\ts.maxLat = lat\n"
                "\t\t}\n"
                "\t}\n"
                "\tout := [][]any{}\n"
                "\tfor svc, s := range stats {\n"
                "\t\tif float64(s.errs)/float64(s.tot)+1e-12 >= minErrorRate {\n"
                "\t\t\tout = append(out, []any{svc, s.errs, s.tot, s.maxLat})\n"
                "\t\t}\n"
                "\t}\n"
                "\tsort.Slice(out, func(i, j int) bool {\n"
                "\t\tri := float64(out[i][1].(int)) / float64(out[i][2].(int))\n"
                "\t\trj := float64(out[j][1].(int)) / float64(out[j][2].(int))\n"
                "\t\tif ri != rj {\n"
                "\t\t\treturn ri > rj\n"
                "\t\t}\n"
                "\t\treturn out[i][0].(string) < out[j][0].(string)\n"
                "\t})\n"
                "\treturn out\n"
                "}\n"
            ),
            "typescript": (
                "function analyseServiceLogs(logs: string[], minErrorRate: number): any[][] {\n"
                "  const seen = new Set<string>();\n"
                "  const stats = new Map<string, [number, number, number]>();\n"
                "  for (const raw of logs) {\n"
                "    const parts = raw.split('|');\n"
                "    if (parts.length !== 4) continue;\n"
                "    const svc = parts[1].trim();\n"
                "    if (!svc) continue;\n"
                "    const ts = Number(parts[0].trim());\n"
                "    const st = Number(parts[2].trim());\n"
                "    const lat = Number(parts[3].trim());\n"
                "    if (!Number.isInteger(ts) || !Number.isInteger(st) || !Number.isInteger(lat)) continue;\n"
                "    if (ts < 0 || st < 100 || st > 599 || lat < 0) continue;\n"
                "    const key = `${ts}|${svc}|${st}|${lat}`;\n"
                "    if (seen.has(key)) continue;\n"
                "    seen.add(key);\n"
                "    const cur = stats.get(svc) ?? [0, 0, 0];\n"
                "    if (st >= 500) cur[0]++;\n"
                "    cur[1]++;\n"
                "    if (lat > cur[2]) cur[2] = lat;\n"
                "    stats.set(svc, cur);\n"
                "  }\n"
                "  const out: any[][] = [];\n"
                "  for (const [svc, [errs, tot, maxLat]] of stats.entries()) {\n"
                "    if (errs / tot + 1e-12 >= minErrorRate) out.push([svc, errs, tot, maxLat]);\n"
                "  }\n"
                "  out.sort((a, b) => {\n"
                "    const ra = a[1] / a[2], rb = b[1] / b[2];\n"
                "    if (Math.abs(ra - rb) > 1e-12) return rb - ra;\n"
                "    return a[0] < b[0] ? -1 : 1;\n"
                "  });\n"
                "  return out;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Validate each raw log line defensively: check field count == 4, non-empty service name, valid integer conversions, and domain bounds (`ts >= 0`, `100 <= status <= 599`, `lat >= 0`).\n"
            "2. Deduplicate canonical `(ts, svc, status, lat)` tuples via a `seen` hash set.\n"
            "3. Update per-service `[errors, total, max_latency]` counters in O(1).\n"
            "4. Filter services meeting `minErrorRate` and sort by `(-error_rate, service_name)`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "'100|auth|500|120' x2", "stateVars": "seen={(100,'auth',500,120)} | stats['auth']=[1,1,120]", "note": "Second identical retry is deduplicated."},
            {"step": 2, "focus": "'101|auth|200|40'", "stateVars": "stats['auth']=[1,2,120] (error rate 0.5)", "note": "Valid 200 increments total count for auth."},
            {"step": 3, "focus": "'bad_line' & '103|pay|502|-5'", "stateVars": "Both skipped cleanly", "note": "Malformed format and negative latency rejected without crashing."},
            {"step": 4, "focus": "Rank & Filter (>= 0.5)", "stateVars": "out=[['pay',1,1,310], ['auth',1,2,120]]", "note": "pay (1.0) ranks ahead of auth (0.5)."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(N)",
            "optimalTime": "O(N + S log S)",
            "optimalSpace": "O(N)",
            "derivation": "Single O(N) parsing/deduplication pass plus O(S log S) sort over unique services S.",
        },
        "interviewFollowUp": {
            "question": "Part 4 Scale-Up: Suppose the log stream is unbounded (100 GB/day) and you only need to deduplicate retries within a 60-second sliding window of `(ts)` while reporting rolling 5-minute error rates.",
            "answer": "Evict entries from `seen` and per-second ring buckets as `watermark_ts - bucket_ts > 300` using a time-ordered deque + sliding window counters so memory stays strictly bounded by 5 minutes of active keys rather than growing forever.",
        },
        "testCases": [
            {
                "args": [["100|auth|500|120", "100|auth|500|120", "101|auth|200|40", "bad_line", "102|pay|503|310", "103|pay|502|-5"], 0.5],
                "expected": [["pay", 1, 1, 310], ["auth", 1, 2, 120]],
                "label": "Dirty logs with retries and negative latency",
            },
            {
                "args": [["10|db|200|15", "11|db|200|20"], 0.1],
                "expected": [],
                "label": "Healthy service below error threshold",
            },
        ],
    },
}

# Master 120-Day Curriculum Schedule (Days 1 to 120) ensuring 100% coverage of all 86 tags
MASTER_120_SCHEDULE: list[dict[str, Any]] = [
    # Phase 1: Days 1-8 (Arrays, Strings, Hashing, Prefix Sum)
    {"day": 1, "lc": "LC 1", "title": "Two Sum", "diff": "Easy", "phase": 1, "tags": ["Array", "Hash Table", "Ambiguity & Constraint Clarification", "Space-Time Trade-Off & Amortised Analysis"], "url": "https://leetcode.com/problems/two-sum/"},
    {"day": 2, "lc": "LC 242", "title": "Valid Anagram", "diff": "Easy", "phase": 1, "tags": ["String", "Hash Table", "Sorting", "Counting", "Adversarial Edge-Case Synthesis"], "url": "https://leetcode.com/problems/valid-anagram/"},
    {"day": 3, "lc": "LC 49", "title": "Group Anagrams", "diff": "Medium", "phase": 1, "tags": ["Array", "String", "Hash Table", "Sorting", "Counting", "Hash Function"], "url": "https://leetcode.com/problems/group-anagrams/"},
    {"day": 4, "lc": "LC 560", "title": "Subarray Sum Equals K", "diff": "Medium", "phase": 1, "tags": ["Array", "Hash Table", "Prefix Sum", "Space-Time Trade-Off & Amortised Analysis"], "url": "https://leetcode.com/problems/subarray-sum-equals-k/"},
    {"day": 5, "lc": "LC 238", "title": "Product of Array Except Self", "diff": "Medium", "phase": 1, "tags": ["Array", "Prefix Sum", "Dry-Run State Table Tracing"], "url": "https://leetcode.com/problems/product-of-array-except-self/"},
    {"day": 6, "lc": "LC 128", "title": "Longest Consecutive Sequence", "diff": "Medium", "phase": 1, "tags": ["Array", "Hash Table", "Union-Find"], "url": "https://leetcode.com/problems/longest-consecutive-sequence/"},
    {"day": 7, "lc": "LC 54", "title": "Spiral Matrix", "diff": "Medium", "phase": 1, "tags": ["Array", "Matrix", "Simulation"], "url": "https://leetcode.com/problems/spiral-matrix/"},
    {"day": 8, "lc": "LC 204", "title": "Count Primes (Enumeration & Sieve)", "diff": "Medium", "phase": 1, "tags": ["Array", "Math", "Enumeration", "Number Theory"], "url": "https://leetcode.com/problems/count-primes/"},
    # Phase 2: Days 9-16 (Two Pointers, Sliding Windows, Linear Sorting)
    {"day": 9, "lc": "LC 15", "title": "3Sum", "diff": "Medium", "phase": 2, "tags": ["Array", "Two Pointers", "Sorting", "Adversarial Edge-Case Synthesis"], "url": "https://leetcode.com/problems/3sum/"},
    {"day": 10, "lc": "LC 11", "title": "Container With Most Water", "diff": "Medium", "phase": 2, "tags": ["Array", "Two Pointers", "Greedy"], "url": "https://leetcode.com/problems/container-with-most-water/"},
    {"day": 11, "lc": "LC 42", "title": "Trapping Rain Water", "diff": "Hard", "phase": 2, "tags": ["Array", "Two Pointers", "Dynamic Programming", "Stack", "Monotonic Stack"], "url": "https://leetcode.com/problems/trapping-rain-water/"},
    {"day": 12, "lc": "LC 3", "title": "Longest Substring Without Repeating Characters", "diff": "Medium", "phase": 2, "tags": ["String", "Hash Table", "Sliding Window"], "url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/"},
    {"day": 13, "lc": "LC 76", "title": "Minimum Window Substring", "diff": "Hard", "phase": 2, "tags": ["String", "Hash Table", "Sliding Window"], "url": "https://leetcode.com/problems/minimum-window-substring/"},
    {"day": 14, "lc": "LC 239", "title": "Sliding Window Maximum", "diff": "Hard", "phase": 2, "tags": ["Array", "Queue", "Sliding Window", "Heap (Priority Queue)", "Monotonic Queue"], "url": "https://leetcode.com/problems/sliding-window-maximum/"},
    {"day": 15, "lc": "LC 347", "title": "Top K Frequent Elements (Bucket Sort)", "diff": "Medium", "phase": 2, "tags": ["Array", "Hash Table", "Sorting", "Heap (Priority Queue)", "Counting", "Bucket Sort", "Quickselect"], "url": "https://leetcode.com/problems/top-k-frequent-elements/"},
    {"day": 16, "lc": "LC 164", "title": "Maximum Gap (Radix & Counting Sort)", "diff": "Medium", "phase": 2, "tags": ["Array", "Sorting", "Bucket Sort", "Counting Sort", "Radix Sort"], "url": "https://leetcode.com/problems/maximum-gap/"},
    # Phase 3: Days 17-24 (Stacks, Monotonic Stacks, Queues, Linked Lists)
    {"day": 17, "lc": "LC 20", "title": "Valid Parentheses", "diff": "Easy", "phase": 3, "tags": ["String", "Stack"], "url": "https://leetcode.com/problems/valid-parentheses/"},
    {"day": 18, "lc": "LC 739", "title": "Daily Temperatures", "diff": "Medium", "phase": 3, "tags": ["Array", "Stack", "Monotonic Stack"], "url": "https://leetcode.com/problems/daily-temperatures/"},
    {"day": 19, "lc": "LC 84", "title": "Largest Rectangle in Histogram", "diff": "Hard", "phase": 3, "tags": ["Array", "Stack", "Monotonic Stack"], "url": "https://leetcode.com/problems/largest-rectangle-in-histogram/"},
    {"day": 20, "lc": "LC 206", "title": "Reverse Linked List", "diff": "Easy", "phase": 3, "tags": ["Linked List", "Recursion"], "url": "https://leetcode.com/problems/reverse-linked-list/"},
    {"day": 21, "lc": "LC 143", "title": "Reorder List", "diff": "Medium", "phase": 3, "tags": ["Linked List", "Two Pointers", "Stack", "Recursion"], "url": "https://leetcode.com/problems/reorder-list/"},
    {"day": 22, "lc": "LC 287", "title": "Find the Duplicate Number (Floyd Cycle)", "diff": "Medium", "phase": 3, "tags": ["Array", "Two Pointers", "Binary Search", "Bit Manipulation"], "url": "https://leetcode.com/problems/find-the-duplicate-number/"},
    {"day": 23, "lc": "LC 622", "title": "Design Circular Queue & Nested Iterator", "diff": "Medium", "phase": 3, "tags": ["Array", "Linked List", "Design", "Queue", "Iterator"], "url": "https://leetcode.com/problems/design-circular-queue/"},
    {"day": 24, "lc": "LC 432", "title": "All O(1) Data Structure (Doubly-Linked List)", "diff": "Hard", "phase": 3, "tags": ["Hash Table", "Linked List", "Design", "Doubly-Linked List"], "url": "https://leetcode.com/problems/all-oone-data-structure/"},
    # Phase 4: Days 25-32 (Binary Search & Divide and Conquer)
    {"day": 25, "lc": "LC 33", "title": "Search in Rotated Sorted Array", "diff": "Medium", "phase": 4, "tags": ["Array", "Binary Search"], "url": "https://leetcode.com/problems/search-in-rotated-sorted-array/"},
    {"day": 26, "lc": "LC 4", "title": "Median of Two Sorted Arrays", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer"], "url": "https://leetcode.com/problems/median-of-two-sorted-arrays/"},
    {"day": 27, "lc": "LC 875", "title": "Koko Eating Bananas", "diff": "Medium", "phase": 4, "tags": ["Array", "Binary Search"], "url": "https://leetcode.com/problems/koko-eating-bananas/"},
    {"day": 28, "lc": "LC 410", "title": "Split Array Largest Sum", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Dynamic Programming", "Greedy", "Prefix Sum"], "url": "https://leetcode.com/problems/split-array-largest-sum/"},
    {"day": 29, "lc": "LC 215", "title": "Kth Largest Element (Quickselect)", "diff": "Medium", "phase": 4, "tags": ["Array", "Divide and Conquer", "Sorting", "Heap (Priority Queue)", "Quickselect", "Randomized"], "url": "https://leetcode.com/problems/kth-largest-element-in-an-array/"},
    {"day": 30, "lc": "LC 315", "title": "Count of Smaller Numbers After Self (Merge Sort)", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer", "Binary Indexed Tree", "Segment Tree", "Merge Sort"], "url": "https://leetcode.com/problems/count-of-smaller-numbers-after-self/"},
    {"day": 31, "lc": "LC 1095", "title": "Find in Mountain Array (Interactive)", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Interactive"], "url": "https://leetcode.com/problems/find-in-mountain-array/"},
    {"day": 32, "lc": "LC 240", "title": "Search a 2D Matrix II", "diff": "Medium", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer", "Matrix"], "url": "https://leetcode.com/problems/search-a-2d-matrix-ii/"},
    # Phase 5: Days 33-42 (Trees, BST, Tries, Recursion)
    {"day": 33, "lc": "LC 104", "title": "Maximum Depth of Binary Tree", "diff": "Easy", "phase": 5, "tags": ["Tree", "Depth-First Search", "Breadth-First Search", "Binary Tree", "Recursion"], "url": "https://leetcode.com/problems/maximum-depth-of-binary-tree/"},
    {"day": 34, "lc": "LC 543", "title": "Diameter of Binary Tree", "diff": "Easy", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/diameter-of-binary-tree/"},
    {"day": 35, "lc": "LC 124", "title": "Binary Tree Maximum Path Sum", "diff": "Hard", "phase": 5, "tags": ["Dynamic Programming", "Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/binary-tree-maximum-path-sum/"},
    {"day": 36, "lc": "LC 102", "title": "Binary Tree Level Order Traversal", "diff": "Medium", "phase": 5, "tags": ["Tree", "Breadth-First Search", "Binary Tree", "Queue"], "url": "https://leetcode.com/problems/binary-tree-level-order-traversal/"},
    {"day": 37, "lc": "LC 98", "title": "Validate Binary Search Tree", "diff": "Medium", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Search Tree", "Binary Tree"], "url": "https://leetcode.com/problems/validate-binary-search-tree/"},
    {"day": 38, "lc": "LC 236", "title": "Lowest Common Ancestor of a Binary Tree", "diff": "Medium", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/"},
    {"day": 39, "lc": "LC 297", "title": "Serialize and Deserialize Binary Tree", "diff": "Hard", "phase": 5, "tags": ["String", "Tree", "Depth-First Search", "Breadth-First Search", "Design", "Binary Tree"], "url": "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/"},
    {"day": 40, "lc": "LC 208", "title": "Implement Trie (Prefix Tree)", "diff": "Medium", "phase": 5, "tags": ["String", "Hash Table", "Design", "Trie"], "url": "https://leetcode.com/problems/implement-trie-prefix-tree/"},
    {"day": 41, "lc": "LC 212", "title": "Word Search II (Trie + Grid Pruning)", "diff": "Hard", "phase": 5, "tags": ["Array", "String", "Backtracking", "Trie", "Matrix"], "url": "https://leetcode.com/problems/word-search-ii/"},
    {"day": 42, "lc": "LC 230", "title": "Kth Smallest Element in a BST (Inorder Iterator)", "diff": "Medium", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Search Tree", "Binary Tree", "Iterator"], "url": "https://leetcode.com/problems/kth-smallest-element-in-a-bst/"},
    # Phase 6: Days 43-50 (Heaps, Priority Queues, Sweep Line & Ordered Sets)
    {"day": 43, "lc": "LC 23", "title": "Merge k Sorted Lists", "diff": "Hard", "phase": 6, "tags": ["Linked List", "Divide and Conquer", "Heap (Priority Queue)", "Heap", "Merge Sort"], "url": "https://leetcode.com/problems/merge-k-sorted-lists/"},
    {"day": 44, "lc": "LC 621", "title": "Task Scheduler (Greedy Cooldown Cycles)", "diff": "Medium", "phase": 6, "tags": ["Array", "Hash Table", "Greedy", "Sorting", "Heap (Priority Queue)", "Counting"], "url": "https://leetcode.com/problems/task-scheduler/"},
    {"day": 45, "lc": "LC 295", "title": "Find Median from Data Stream", "diff": "Hard", "phase": 6, "tags": ["Two Pointers", "Design", "Sorting", "Heap (Priority Queue)", "Heap", "Data Stream"], "url": "https://leetcode.com/problems/find-median-from-data-stream/"},
    {"day": 46, "lc": "LC 253", "title": "Meeting Rooms II (Min-Heap & Sweep Line)", "diff": "Medium", "phase": 6, "tags": ["Array", "Two Pointers", "Greedy", "Sorting", "Heap (Priority Queue)", "Prefix Sum", "Sweep Line"], "url": "https://leetcode.com/problems/meeting-rooms-ii/"},
    {"day": 47, "lc": "LC 218", "title": "The Skyline Problem (Event Sweep Line)", "diff": "Hard", "phase": 6, "tags": ["Array", "Divide and Conquer", "Binary Indexed Tree", "Segment Tree", "Heap (Priority Queue)", "Ordered Set", "Sweep Line"], "url": "https://leetcode.com/problems/the-skyline-problem/"},
    {"day": 48, "lc": "LC 729", "title": "My Calendar I & III (Ordered Set Boundary)", "diff": "Medium", "phase": 6, "tags": ["Binary Search", "Design", "Segment Tree", "Ordered Set", "Sweep Line"], "url": "https://leetcode.com/problems/my-calendar-i/"},
    {"day": 49, "lc": "LC 502", "title": "IPO (Two-Heap Capital Unlock Greedy)", "diff": "Hard", "phase": 6, "tags": ["Array", "Greedy", "Sorting", "Heap (Priority Queue)"], "url": "https://leetcode.com/problems/ipo/"},
    {"day": 50, "lc": "LC 857", "title": "Minimum Cost to Hire K Workers", "diff": "Hard", "phase": 6, "tags": ["Array", "Greedy", "Sorting", "Heap (Priority Queue)"], "url": "https://leetcode.com/problems/minimum-cost-to-hire-k-workers/"},
    # Phase 7: Days 51-58 (Backtracking, Combinatorics & Meet in the Middle)
    {"day": 51, "lc": "LC 78", "title": "Subsets & Subsets II (Duplicate Pruning)", "diff": "Medium", "phase": 7, "tags": ["Array", "Backtracking", "Bit Manipulation", "Bitmask"], "url": "https://leetcode.com/problems/subsets/"},
    {"day": 52, "lc": "LC 46", "title": "Permutations & Next Permutation", "diff": "Medium", "phase": 7, "tags": ["Array", "Backtracking", "Combinatorics"], "url": "https://leetcode.com/problems/permutations/"},
    {"day": 53, "lc": "LC 39", "title": "Combination Sum", "diff": "Medium", "phase": 7, "tags": ["Array", "Backtracking"], "url": "https://leetcode.com/problems/combination-sum/"},
    {"day": 54, "lc": "LC 51", "title": "N-Queens (Diagonal Bitmask Pruning)", "diff": "Hard", "phase": 7, "tags": ["Array", "Backtracking", "Bitmask"], "url": "https://leetcode.com/problems/n-queens/"},
    {"day": 55, "lc": "LC 22", "title": "Generate Parentheses (Catalan Combinatorics)", "diff": "Medium", "phase": 7, "tags": ["String", "Dynamic Programming", "Backtracking", "Combinatorics"], "url": "https://leetcode.com/problems/generate-parentheses/"},
    {"day": 56, "lc": "LC 60", "title": "Permutation Sequence (Factorial Number System)", "diff": "Hard", "phase": 7, "tags": ["Math", "Recursion", "Combinatorics"], "url": "https://leetcode.com/problems/permutation-sequence/"},
    {"day": 57, "lc": "LC 1755", "title": "Closest Subsequence Sum (Meet in the Middle)", "diff": "Hard", "phase": 7, "tags": ["Array", "Two Pointers", "Dynamic Programming", "Bit Manipulation", "Sorting", "Bitmask", "Meet in the Middle"], "url": "https://leetcode.com/problems/closest-subsequence-sum/"},
    {"day": 58, "lc": "LC 2035", "title": "Partition Array Into Two Arrays to Minimize Sum Difference", "diff": "Hard", "phase": 7, "tags": ["Array", "Two Pointers", "Binary Search", "Dynamic Programming", "Bit Manipulation", "Ordered Set", "Bitmask", "Meet in the Middle"], "url": "https://leetcode.com/problems/partition-array-into-two-arrays-to-minimize-sum-difference/"},
    # Phase 8: Days 59-68 (Graph Theory I: BFS, DFS, Topo Sort, Union-Find)
    {"day": 59, "lc": "LC 200", "title": "Number of Islands", "diff": "Medium", "phase": 8, "tags": ["Array", "Depth-First Search", "Breadth-First Search", "Union-Find", "Matrix"], "url": "https://leetcode.com/problems/number-of-islands/"},
    {"day": 60, "lc": "LC 994", "title": "Rotting Oranges (Multi-Source BFS)", "diff": "Medium", "phase": 8, "tags": ["Array", "Breadth-First Search", "Matrix", "Queue"], "url": "https://leetcode.com/problems/rotting-oranges/"},
    {"day": 61, "lc": "LC 127", "title": "Word Ladder (Bidirectional BFS)", "diff": "Hard", "phase": 8, "tags": ["String", "Hash Table", "Breadth-First Search"], "url": "https://leetcode.com/problems/word-ladder/"},
    {"day": 62, "lc": "LC 210", "title": "Course Schedule II (Topological Sort)", "diff": "Medium", "phase": 8, "tags": ["Depth-First Search", "Breadth-First Search", "Graph Theory", "Topological Sort"], "url": "https://leetcode.com/problems/course-schedule-ii/"},
    {"day": 63, "lc": "LC 269", "title": "Alien Dictionary (Lexicographical DAG Topo Sort)", "diff": "Hard", "phase": 8, "tags": ["Array", "String", "Depth-First Search", "Breadth-First Search", "Graph Theory", "Topological Sort"], "url": "https://leetcode.com/problems/alien-dictionary/"},
    {"day": 64, "lc": "LC 684", "title": "Redundant Connection (Union-Find with Path Compression)", "diff": "Medium", "phase": 8, "tags": ["Depth-First Search", "Breadth-First Search", "Union-Find", "Graph Theory"], "url": "https://leetcode.com/problems/redundant-connection/"},
    {"day": 65, "lc": "LC 721", "title": "Accounts Merge (Disjoint Set Equivalence)", "diff": "Medium", "phase": 8, "tags": ["Array", "String", "Depth-First Search", "Breadth-First Search", "Union-Find", "Sorting"], "url": "https://leetcode.com/problems/accounts-merge/"},
    {"day": 66, "lc": "LC 399", "title": "Evaluate Division (Weighted Graph / Union-Find)", "diff": "Medium", "phase": 8, "tags": ["Array", "Depth-First Search", "Breadth-First Search", "Union-Find", "Graph Theory", "Shortest Path"], "url": "https://leetcode.com/problems/evaluate-division/"},
    {"day": 67, "lc": "LC 785", "title": "Is Graph Bipartite? (2-Colouring BFS/DFS)", "diff": "Medium", "phase": 8, "tags": ["Depth-First Search", "Breadth-First Search", "Union-Find", "Graph Theory"], "url": "https://leetcode.com/problems/is-graph-bipartite/"},
    {"day": 68, "lc": "LC 815", "title": "Bus Routes (Hypergraph Route-Node BFS)", "diff": "Hard", "phase": 8, "tags": ["Array", "Hash Table", "Breadth-First Search", "Graph Theory"], "url": "https://leetcode.com/problems/bus-routes/"},
    # Phase 9: Days 69-76 (Shortest Path, MST, Eulerian, Tarjan SCC & Biconnected)
    {"day": 69, "lc": "LC 743", "title": "Network Delay Time (Dijkstra Shortest Path)", "diff": "Medium", "phase": 9, "tags": ["Depth-First Search", "Breadth-First Search", "Graph Theory", "Heap (Priority Queue)", "Shortest Path"], "url": "https://leetcode.com/problems/network-delay-time/"},
    {"day": 70, "lc": "LC 787", "title": "Cheapest Flights Within K Stops (Bellman-Ford)", "diff": "Medium", "phase": 9, "tags": ["Dynamic Programming", "Depth-First Search", "Breadth-First Search", "Graph Theory", "Heap (Priority Queue)", "Shortest Path"], "url": "https://leetcode.com/problems/cheapest-flights-within-k-stops/"},
    {"day": 71, "lc": "LC 1631", "title": "Path With Minimum Effort (Minimax Dijkstra)", "diff": "Medium", "phase": 9, "tags": ["Array", "Binary Search", "Depth-First Search", "Breadth-First Search", "Union-Find", "Heap (Priority Queue)", "Matrix", "Shortest Path"], "url": "https://leetcode.com/problems/path-with-minimum-effort/"},
    {"day": 72, "lc": "LC 1368", "title": "Minimum Cost to Make Valid Path in a Grid (0-1 BFS)", "diff": "Hard", "phase": 9, "tags": ["Array", "Breadth-First Search", "Graph Theory", "Heap (Priority Queue)", "Matrix", "Shortest Path"], "url": "https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/"},
    {"day": 73, "lc": "LC 1584", "title": "Min Cost to Connect All Points (Prim & Kruskal MST)", "diff": "Medium", "phase": 9, "tags": ["Array", "Union-Find", "Graph Theory", "Minimum Spanning Tree"], "url": "https://leetcode.com/problems/min-cost-to-connect-all-points/"},
    {"day": 74, "lc": "LC 332", "title": "Reconstruct Itinerary (Hierholzer Eulerian Circuit)", "diff": "Hard", "phase": 9, "tags": ["Depth-First Search", "Graph Theory", "Eulerian Circuit"], "url": "https://leetcode.com/problems/reconstruct-itinerary/"},
    {"day": 75, "lc": "LC 2097", "title": "Valid Arrangement of Pairs (Directed Eulerian Path)", "diff": "Hard", "phase": 9, "tags": ["Depth-First Search", "Graph Theory", "Eulerian Circuit"], "url": "https://leetcode.com/problems/valid-arrangement-of-pairs/"},
    {"day": 76, "lc": "LC 1192", "title": "Critical Connections in a Network (Tarjan Bridges & SCC)", "diff": "Hard", "phase": 9, "tags": ["Depth-First Search", "Graph Theory", "Biconnected Component", "Strongly Connected Component"], "url": "https://leetcode.com/problems/critical-connections-in-a-network/"},
    # Phase 10: Days 77-86 (Dynamic Programming I: 1D, 2D, Knapsack & Memoization)
    {"day": 77, "lc": "LC 198", "title": "House Robber I & II (1D Rolling State DP)", "diff": "Medium", "phase": 10, "tags": ["Array", "Dynamic Programming"], "url": "https://leetcode.com/problems/house-robber/"},
    {"day": 78, "lc": "LC 322", "title": "Coin Change (Unbounded Knapsack DP)", "diff": "Medium", "phase": 10, "tags": ["Array", "Dynamic Programming", "Breadth-First Search"], "url": "https://leetcode.com/problems/coin-change/"},
    {"day": 79, "lc": "LC 300", "title": "Longest Increasing Subsequence (Patience Sorting)", "diff": "Medium", "phase": 10, "tags": ["Array", "Binary Search", "Dynamic Programming"], "url": "https://leetcode.com/problems/longest-increasing-subsequence/"},
    {"day": 80, "lc": "LC 139", "title": "Word Break", "diff": "Medium", "phase": 10, "tags": ["Array", "String", "Hash Table", "Dynamic Programming", "Trie", "Memoization"], "url": "https://leetcode.com/problems/word-break/"},
    {"day": 81, "lc": "LC 416", "title": "Partition Equal Subset Sum (0/1 Knapsack Bitset)", "diff": "Medium", "phase": 10, "tags": ["Array", "Dynamic Programming"], "url": "https://leetcode.com/problems/partition-equal-subset-sum/"},
    {"day": 82, "lc": "LC 1143", "title": "Longest Common Subsequence", "diff": "Medium", "phase": 10, "tags": ["String", "Dynamic Programming"], "url": "https://leetcode.com/problems/longest-common-subsequence/"},
    {"day": 83, "lc": "LC 72", "title": "Edit Distance (Levenshtein Alignment DP)", "diff": "Medium", "phase": 10, "tags": ["String", "Dynamic Programming"], "url": "https://leetcode.com/problems/edit-distance/"},
    {"day": 84, "lc": "LC 10", "title": "Regular Expression Matching", "diff": "Hard", "phase": 10, "tags": ["String", "Dynamic Programming", "Recursion", "Memoization"], "url": "https://leetcode.com/problems/regular-expression-matching/"},
    {"day": 85, "lc": "LC 329", "title": "Longest Increasing Path in a Matrix (DAG Memoization)", "diff": "Hard", "phase": 10, "tags": ["Array", "Dynamic Programming", "Depth-First Search", "Breadth-First Search", "Graph Theory", "Topological Sort", "Memoization", "Matrix"], "url": "https://leetcode.com/problems/longest-increasing-path-in-a-matrix/"},
    {"day": 86, "lc": "LC 1235", "title": "Maximum Profit in Job Scheduling (DP + Binary Search)", "diff": "Hard", "phase": 10, "tags": ["Array", "Binary Search", "Dynamic Programming", "Sorting"], "url": "https://leetcode.com/problems/maximum-profit-in-job-scheduling/"},
    # Phase 11: Days 87-94 (Interval DP, Bitmask DP, Game Theory & Brainteasers)
    {"day": 87, "lc": "LC 312", "title": "Burst Balloons (Last-Popped Interval DP)", "diff": "Hard", "phase": 11, "tags": ["Array", "Dynamic Programming", "Divide and Conquer", "Memoization"], "url": "https://leetcode.com/problems/burst-balloons/"},
    {"day": 88, "lc": "LC 1547", "title": "Minimum Cost to Cut a Stick", "diff": "Hard", "phase": 11, "tags": ["Array", "Dynamic Programming", "Sorting"], "url": "https://leetcode.com/problems/minimum-cost-to-cut-a-stick/"},
    {"day": 89, "lc": "LC 847", "title": "Shortest Path Visiting All Nodes (Bitmask BFS/DP)", "diff": "Hard", "phase": 11, "tags": ["Dynamic Programming", "Bit Manipulation", "Breadth-First Search", "Graph Theory", "Bitmask"], "url": "https://leetcode.com/problems/shortest-path-visiting-all-nodes/"},
    {"day": 90, "lc": "LC 1125", "title": "Smallest Sufficient Team (Set-Cover Bitmask DP)", "diff": "Hard", "phase": 11, "tags": ["Array", "String", "Dynamic Programming", "Bit Manipulation", "Bitmask"], "url": "https://leetcode.com/problems/smallest-sufficient-team/"},
    {"day": 91, "lc": "LC 486", "title": "Predict the Winner (Zero-Sum Minimax DP)", "diff": "Medium", "phase": 11, "tags": ["Array", "Math", "Dynamic Programming", "Recursion", "Game Theory", "Minimax"], "url": "https://leetcode.com/problems/predict-the-winner/"},
    {"day": 92, "lc": "LC 1140", "title": "Stone Game II (Minimax with Suffix Sums)", "diff": "Medium", "phase": 11, "tags": ["Array", "Math", "Dynamic Programming", "Prefix Sum", "Game Theory", "Minimax", "Memoization"], "url": "https://leetcode.com/problems/stone-game-ii/"},
    {"day": 93, "lc": "LC 877", "title": "Stone Game & Nim Parity (Brainteaser & Game Theory)", "diff": "Medium", "phase": 11, "tags": ["Array", "Math", "Dynamic Programming", "Game Theory", "Brainteaser"], "url": "https://leetcode.com/problems/stone-game/"},
    {"day": 94, "lc": "LC 843", "title": "Guess the Word (Minimax Entropy Elimination)", "diff": "Hard", "phase": 11, "tags": ["Array", "String", "Math", "Interactive", "Game Theory", "Minimax", "Randomized"], "url": "https://leetcode.com/problems/guess-the-word/"},
    # Phase 12: Days 95-100 (Segment Trees & Binary Indexed Trees)
    {"day": 95, "lc": "LC 307", "title": "Range Sum Query Mutable (Fenwick / BIT)", "diff": "Medium", "phase": 12, "tags": ["Array", "Design", "Binary Indexed Tree", "Segment Tree"], "url": "https://leetcode.com/problems/range-sum-query-mutable/"},
    {"day": 96, "lc": "LC 493", "title": "Reverse Pairs (Coordinate-Compressed BIT)", "diff": "Hard", "phase": 12, "tags": ["Array", "Binary Search", "Divide and Conquer", "Binary Indexed Tree", "Segment Tree", "Merge Sort", "Ordered Set"], "url": "https://leetcode.com/problems/reverse-pairs/"},
    {"day": 97, "lc": "LC 327", "title": "Count of Range Sum (Prefix Sum + Segment Tree)", "diff": "Hard", "phase": 12, "tags": ["Array", "Binary Search", "Divide and Conquer", "Binary Indexed Tree", "Segment Tree", "Merge Sort", "Ordered Set"], "url": "https://leetcode.com/problems/count-of-range-sum/"},
    {"day": 98, "lc": "LC 699", "title": "Falling Squares (Lazy Propagation Segment Tree)", "diff": "Hard", "phase": 12, "tags": ["Array", "Segment Tree", "Ordered Set"], "url": "https://leetcode.com/problems/falling-squares/"},
    {"day": 99, "lc": "LC 715", "title": "Range Module (Dynamic Interval Segment Tree)", "diff": "Hard", "phase": 12, "tags": ["Design", "Segment Tree", "Ordered Set"], "url": "https://leetcode.com/problems/range-module/"},
    {"day": 100, "lc": "LC 2407", "title": "Longest Increasing Subsequence II (Max Segment Tree)", "diff": "Hard", "phase": 12, "tags": ["Array", "Divide and Conquer", "Dynamic Programming", "Binary Indexed Tree", "Segment Tree", "Queue", "Monotonic Queue"], "url": "https://leetcode.com/problems/longest-increasing-subsequence-ii/"},
    # Phase 13: Days 101-106 (Advanced Strings: Rolling Hash, KMP, Suffix Array)
    {"day": 101, "lc": "LC 28", "title": "Find the Index of the First Occurrence (KMP Prefix Table)", "diff": "Easy", "phase": 13, "tags": ["Two Pointers", "String", "String Matching"], "url": "https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/"},
    {"day": 102, "lc": "LC 214", "title": "Shortest Palindrome (KMP + Rolling Hash)", "diff": "Hard", "phase": 13, "tags": ["String", "Rolling Hash", "String Matching", "Hash Function"], "url": "https://leetcode.com/problems/shortest-palindrome/"},
    {"day": 103, "lc": "LC 1392", "title": "Longest Happy Prefix (Polynomial Rolling Hash)", "diff": "Hard", "phase": 13, "tags": ["String", "Rolling Hash", "String Matching", "Hash Function"], "url": "https://leetcode.com/problems/longest-happy-prefix/"},
    {"day": 104, "lc": "LC 1044", "title": "Longest Duplicate Substring (Binary Search + Rolling Hash)", "diff": "Hard", "phase": 13, "tags": ["String", "Binary Search", "Sliding Window", "Rolling Hash", "Suffix Array", "Hash Function"], "url": "https://leetcode.com/problems/longest-duplicate-substring/"},
    {"day": 105, "lc": "LC 1163", "title": "Last Substring in Lexicographical Order (Suffix Array / Duval)", "diff": "Hard", "phase": 13, "tags": ["Two Pointers", "String", "Suffix Array"], "url": "https://leetcode.com/problems/last-substring-in-lexicographical-order/"},
    {"day": 106, "lc": "LC 718", "title": "Maximum Length of Repeated Subarray (Rolling Hash / SA)", "diff": "Medium", "phase": 13, "tags": ["Array", "Binary Search", "Dynamic Programming", "Sliding Window", "Rolling Hash", "Hash Function", "Suffix Array"], "url": "https://leetcode.com/problems/maximum-length-of-repeated-subarray/"},
    # Phase 14: Days 107-112 (Bit Manipulation, Number Theory, Geometry, Sampling)
    {"day": 107, "lc": "LC 137", "title": "Single Number II & III (Bitwise Finite State Machine)", "diff": "Medium", "phase": 14, "tags": ["Array", "Bit Manipulation"], "url": "https://leetcode.com/problems/single-number-ii/"},
    {"day": 108, "lc": "LC 149", "title": "Max Points on a Line (GCD Normalised Slopes & Geometry)", "diff": "Hard", "phase": 14, "tags": ["Array", "Hash Table", "Math", "Geometry", "Number Theory"], "url": "https://leetcode.com/problems/max-points-on-a-line/"},
    {"day": 109, "lc": "LC 587", "title": "Erect the Fence (Monotone Chain Convex Hull Geometry)", "diff": "Hard", "phase": 14, "tags": ["Array", "Math", "Geometry"], "url": "https://leetcode.com/problems/erect-the-fence/"},
    {"day": 110, "lc": "LC 528", "title": "Random Pick with Weight (Prefix CDF + Binary Search)", "diff": "Medium", "phase": 14, "tags": ["Array", "Math", "Binary Search", "Prefix Sum", "Randomized", "Probability and Statistics"], "url": "https://leetcode.com/problems/random-pick-with-weight/"},
    {"day": 111, "lc": "LC 382", "title": "Linked List Random Node & Random Pick Index (Reservoir Sampling)", "diff": "Medium", "phase": 14, "tags": ["Linked List", "Math", "Reservoir Sampling", "Randomized", "Probability and Statistics"], "url": "https://leetcode.com/problems/linked-list-random-node/"},
    {"day": 112, "lc": "LC 470", "title": "Implement Rand10() Using Rand7() (Rejection Sampling)", "diff": "Medium", "phase": 14, "tags": ["Math", "Rejection Sampling", "Randomized", "Probability and Statistics"], "url": "https://leetcode.com/problems/implement-rand10-using-rand7/"},
    # Phase 15: Days 113-116 (Design, Concurrency, Database/SQL, Shell)
    {"day": 113, "lc": "LC 146", "title": "LRU Cache (Hash Map + Doubly-Linked List Design)", "diff": "Medium", "phase": 15, "tags": ["Hash Table", "Linked List", "Design", "Doubly-Linked List", "Idiomatic Modularity & Helper Design"], "url": "https://leetcode.com/problems/lru-cache/"},
    {"day": 114, "lc": "LC 1188", "title": "Design Bounded Blocking Queue & Dining Philosophers (Concurrency)", "diff": "Medium", "phase": 15, "tags": ["Design", "Queue", "Concurrency"], "url": "https://leetcode.com/problems/design-bounded-blocking-queue/"},
    {"day": 115, "lc": "LC 185", "title": "Department Top Three Salaries (Database & DENSE_RANK Window)", "diff": "Hard", "phase": 15, "tags": ["Database", "SQL & Analytical Window Queries"], "url": "https://leetcode.com/problems/department-top-three-salaries/"},
    {"day": 116, "lc": "LC 192", "title": "Word Frequency & Tenth Line Log Pipeline (Shell & Streaming)", "diff": "Medium", "phase": 15, "tags": ["Shell", "Counting", "CLI & Log Pipeline Automation"], "url": "https://leetcode.com/problems/word-frequency/"},
    # Phase 16: Days 117-120 (SWE & FDE Multi-Part Capstone Simulations)
    {"day": 117, "lc": "FDE-1", "title": "FDE Multi-Part: Resilient Telemetry Log Parser & Error-Rate Aggregator", "diff": "FDE Multi-Part", "phase": 16, "tags": ["String", "Hash Table", "Sorting", "FDE: Dirty Data & Resilient Log Parsing", "FDE: Multi-Step Requirement Evolution", "Idiomatic Modularity & Helper Design"], "url": "https://leetcode.com/problemset/"},
    {"day": 118, "lc": "FDE-2", "title": "FDE Multi-Part: Token-Bucket Rate Limiter & Per-Tenant Quota Engine", "diff": "FDE Multi-Part", "phase": 16, "tags": ["Hash Table", "Design", "Queue", "Data Stream", "FDE: Stateful API Pagination & Rate Limiting", "FDE: Multi-Step Requirement Evolution"], "url": "https://leetcode.com/problems/logger-rate-limiter/"},
    {"day": 119, "lc": "FDE-3", "title": "FDE Multi-Part: In-Memory Transactional KV Store with TTL & Rollback", "diff": "FDE Multi-Part", "phase": 16, "tags": ["Hash Table", "Stack", "Design", "Binary Search", "FDE: In-Memory Transactional KV Store & TTL", "FDE: Multi-Step Requirement Evolution", "Dry-Run State Table Tracing"], "url": "https://leetcode.com/problems/time-based-key-value-store/"},
    {"day": 120, "lc": "FDE-4", "title": "FDE Multi-Part: Streaming Top-K Anomaly Detector Under Memory Bounds", "diff": "FDE Multi-Part", "phase": 16, "tags": ["Heap (Priority Queue)", "Sliding Window", "Data Stream", "Reservoir Sampling", "FDE: Streaming Aggregation & Memory Bounds", "Ambiguity & Constraint Clarification", "Adversarial Edge-Case Synthesis"], "url": "https://leetcode.com/problemset/"},
]
