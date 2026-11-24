"""46 bespoke real LeetCode & FDE problems completing all 120 unique days of Algo Studio."""

from __future__ import annotations

from typing import Any


def _mk(
    day: int,
    func: str,
    stmt: str,
    examples: list[dict[str, str]],
    constraints: list[str],
    starter: str,
    solution: str,
    visible: list[dict[str, Any]],
    hidden: list[dict[str, Any]],
    trap: str,
    pivot: str,
    signal: str,
    hints: list[str],
    walkthrough: str,
    trace_steps: list[dict[str, Any]],
    brute_t: str,
    brute_s: str,
    opt_t: str,
    opt_s: str,
    derivation: str,
    followup_q: str,
    followup_a: str,
    harness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    vis_norm = [dict(tc, hidden=False) for tc in visible]
    hid_norm = [
        dict(
            tc,
            hidden=True,
            category=tc.get("category", "Boundary & Edge Cases"),
            edgeReason=tc.get("edgeReason", "Verifies boundary handling and algorithmic invariants."),
        )
        for tc in hidden
    ]
    return {
        "day": day,
        "funcName": func,
        "harness": harness if harness is not None else {"methodName": func, "orderMatters": True},
        "statement": stmt,
        "examples": examples,
        "constraints": constraints,
        "clarifyingQuestions": [
            "What are the minimum and maximum input bounds, including empty or single-element inputs?",
            f"Is {opt_t} time and {opt_s} auxiliary space required to pass the largest constraints?",
            "Can the input contain duplicate values, negative numbers, or disconnected components?",
        ],
        "mentalModel": {
            "instinctiveTrap": trap,
            "optimalPivot": pivot,
            "triggerSignal": signal,
        },
        "hints": hints,
        "starterCode": {"python": starter.strip() + "\n"},
        "solutionCode": {"python": solution.strip() + "\n"},
        "walkthrough": walkthrough.strip(),
        "traceSteps": trace_steps,
        "complexity": {
            "bruteTime": brute_t,
            "bruteSpace": brute_s,
            "optimalTime": opt_t,
            "optimalSpace": opt_s,
            "derivation": derivation,
        },
        "interviewFollowUp": {
            "question": followup_q,
            "answer": followup_a,
        },
        "visibleTestCases": vis_norm,
        "hiddenTestCases": hid_norm,
        "testCases": vis_norm + hid_norm,
    }


EXTRA_46_PROBLEMS: dict[int, dict[str, Any]] = {}


def _reg(item: dict[str, Any]) -> None:
    EXTRA_46_PROBLEMS[int(item["day"])] = item


# Day 8: LC 204 - Count Primes
_reg(_mk(
    day=8,
    func="countPrimes",
    stmt=(
        "Given an integer `n`, return the number of prime numbers that are strictly less than `n`.\n\n"
        "A prime number is an integer greater than 1 with no positive divisors other than 1 and itself."
    ),
    examples=[
        {"input": "n = 10", "output": "4", "explanation": "There are 4 prime numbers strictly less than 10: 2, 3, 5, 7."},
        {"input": "n = 0", "output": "0", "explanation": "No primes are strictly less than 0."},
        {"input": "n = 1", "output": "0", "explanation": "1 is not prime, so there are 0 primes less than 1."},
    ],
    constraints=["0 <= n <= 5 * 10^6"],
    starter="""
def countPrimes(n: int) -> int:
    # Write your O(N log log N) Sieve of Eratosthenes solution here
    pass
""",
    solution="""
def countPrimes(n: int) -> int:
    if n < 3:
        return 0
    is_prime = bytearray(b"\\x01") * n
    is_prime[0] = 0
    is_prime[1] = 0
    limit = int(n ** 0.5) + 1
    for p in range(2, limit):
        if is_prime[p]:
            start = p * p
            step_count = (n - 1 - start) // p + 1
            is_prime[start:n:p] = bytearray(step_count)
    return sum(is_prime)
""",
    visible=[
        {"label": "n = 10", "args": [10], "expected": 4},
        {"label": "n = 0", "args": [0], "expected": 0},
        {"label": "n = 1", "args": [1], "expected": 0},
    ],
    hidden=[
        {"label": "n = 2 (strictly less)", "args": [2], "expected": 0, "category": "Off-by-One Boundary", "edgeReason": "Must count primes strictly less than n, so n = 2 returns 0."},
        {"label": "n = 3 (smallest prime)", "args": [3], "expected": 1, "category": "Small Input", "edgeReason": "Only prime 2 is strictly less than 3."},
        {"label": "n = 20", "args": [20], "expected": 8, "category": "Composite Elimination", "edgeReason": "Verifies marking multiples starting at p * p."},
        {"label": "n = 100", "args": [100], "expected": 25, "category": "Classic Check", "edgeReason": "Known exact count of primes under 100 is 25."},
        {"label": "n = 1000", "args": [1000], "expected": 168, "category": "Scale Check", "edgeReason": "Verifies O(N log log N) sieve accuracy at larger n."},
    ],
    trap="Testing every integer `k < n` individually by trial division up to `sqrt(k)` takes O(N sqrt(N)) time and times out for `n = 5 * 10^6`.",
    pivot="Invert the question from 'is k prime?' to 'cross out multiples of each discovered prime p starting from p * p' using a bytearray Sieve of Eratosthenes.",
    signal="Counting or enumerating all primes up to a large upper bound `n` calls for the Sieve of Eratosthenes.",
    hints=[
        "If `p` is prime, every multiple `2p, 3p, ..., (p-1)p` has already been crossed out by a smaller prime factor.",
        "Therefore you only need to iterate `p` up to `sqrt(n)` and start marking multiples at `p * p`.",
        "Using a `bytearray` slice assignment `is_prime[p*p:n:p] = ...` runs at C speed inside Python.",
    ],
    walkthrough="1. Guard `n < 3` by returning 0.\n2. Create a `bytearray` of length `n` initialised to 1, setting indices 0 and 1 to 0.\n3. For each `p` from 2 to `isqrt(n)`, if `is_prime[p]` is still 1, zero out all multiples from `p * p` to `n - 1` stepping by `p`.\n4. Return `sum(is_prime)`.",
    trace_steps=[
        {"step": 1, "focus": "Init n=10", "stateVars": "is_prime = [0,0,1,1,1,1,1,1,1,1]", "note": "Mark 0 and 1 composite; candidates 2..9 start as prime."},
        {"step": 2, "focus": "p=2 (p*p=4)", "stateVars": "mark 4, 6, 8 -> 0", "note": "2 is prime; clear multiples 4, 6, 8."},
        {"step": 3, "focus": "p=3 (p*p=9)", "stateVars": "mark 9 -> 0 | sum = 4", "note": "3 is prime; clear 9. Remaining primes: 2, 3, 5, 7 -> return 4."},
    ],
    brute_t="O(N sqrt(N))",
    brute_s="O(1)",
    opt_t="O(N log log N)",
    opt_s="O(N)",
    derivation="The sum of reciprocals of primes up to N grows as O(log log N), so marking multiples across the array performs O(N log log N) writes.",
    followup_q="How would you count primes up to 10^9 if memory is limited to a few megabytes?",
    followup_a="Use a segmented sieve: precompute base primes up to sqrt(N) (~31,622), then sieve windows of size ~sqrt(N) one cache-friendly block at a time.",
))


# Day 16: LC 164 - Maximum Gap
_reg(_mk(
    day=16,
    func="maximumGap",
    stmt=(
        "Given an integer array `nums`, return the maximum difference between two successive elements in its sorted form. "
        "If the array contains fewer than two elements, return `0`.\n\n"
        "You must write an algorithm that runs in linear time `O(N)` and uses linear extra space."
    ),
    examples=[
        {"input": "nums = [3, 6, 9, 1]", "output": "3", "explanation": "The sorted form is [1, 3, 6, 9]; adjacent differences are 2, 3, and 3, so the maximum gap is 3."},
        {"input": "nums = [10]", "output": "0", "explanation": "Fewer than 2 elements returns 0."},
    ],
    constraints=["1 <= len(nums) <= 10^5", "0 <= nums[i] <= 10^9"],
    starter="""
def maximumGap(nums: list[int]) -> int:
    # Write your O(N) Pigeonhole Bucket Sort solution here
    pass
""",
    solution="""
def maximumGap(nums: list[int]) -> int:
    n = len(nums)
    if n < 2:
        return 0
    lo, hi = min(nums), max(nums)
    if lo == hi:
        return 0
    bucket_size = max(1, (hi - lo) // (n - 1))
    bucket_count = (hi - lo) // bucket_size + 1
    b_min = [None] * bucket_count
    b_max = [None] * bucket_count
    for x in nums:
        idx = (x - lo) // bucket_size
        if b_min[idx] is None or x < b_min[idx]:
            b_min[idx] = x
        if b_max[idx] is None or x > b_max[idx]:
            b_max[idx] = x
    best = 0
    prev_max = lo
    for i in range(bucket_count):
        if b_min[i] is None:
            continue
        best = max(best, b_min[i] - prev_max)
        prev_max = b_max[i]
    return best
""",
    visible=[
        {"label": "Standard unsorted array", "args": [[3, 6, 9, 1]], "expected": 3},
        {"label": "Single element", "args": [[10]], "expected": 0},
        {"label": "Large jump", "args": [[1, 10000000]], "expected": 9999999},
    ],
    hidden=[
        {"label": "All identical values", "args": [[5, 5, 5, 5]], "expected": 0, "category": "Zero Range", "edgeReason": "Guards division by zero when min == max."},
        {"label": "Already sorted consecutive", "args": [[1, 2, 3, 4, 5]], "expected": 1, "category": "Tight Spacing", "edgeReason": "Checks bucket_size = max(1, ...) when range == n - 1."},
        {"label": "Duplicates with big gap", "args": [[1, 1, 1, 1, 1, 5, 5, 5, 5, 5]], "expected": 4, "category": "Heavy Duplicates", "edgeReason": "Empty intermediate buckets must be skipped cleanly."},
        {"label": "Reverse sorted", "args": [[100, 3, 2, 1]], "expected": 97, "category": "Skewed Distribution", "edgeReason": "Extreme outlier creates many empty buckets."},
        {"label": "Two elements equal", "args": [[7, 7]], "expected": 0, "category": "Minimum Pair", "edgeReason": "Two equal elements have gap 0."},
    ],
    trap="Calling comparison sort (`sorted(nums)`) takes O(N log N) time, violating the linear-time constraint.",
    pivot="By the Pigeonhole Principle, the maximum gap is at least `ceil((hi - lo) / (n - 1))`. Place numbers into buckets of that width and only track each bucket's min and max; the maximum gap must span across non-empty buckets, never inside one.",
    signal="Linear-time requirement on unsorted integers with a gap/order property points to Bucket Sort (Pigeonhole) or LSD Radix Sort.",
    hints=[
        "If `n` values span `[lo, hi]`, the average adjacent gap is `(hi - lo) / (n - 1)`, so the maximum gap cannot be smaller than that.",
        "Choose bucket width `b = max(1, (hi - lo) // (n - 1))`. Two elements inside the same bucket differ by at most `b - 1`.",
        "Store only `(bucket_min, bucket_max)` per bucket and scan consecutive non-empty buckets computing `cur_min - prev_max`.",
    ],
    walkthrough="1. Guard `n < 2` and `lo == hi`.\n2. Compute `bucket_size = max(1, (hi - lo) // (n - 1))` and allocate min/max arrays.\n3. Map each value `x` to bucket `(x - lo) // bucket_size` and update its min and max.\n4. Sweep non-empty buckets updating `best = max(best, b_min[i] - prev_max)`.",
    trace_steps=[
        {"step": 1, "focus": "lo=1, hi=9, n=4", "stateVars": "bucket_size = 2 | buckets = 5", "note": "Any gap inside a bucket is at most 1; max gap must cross buckets."},
        {"step": 2, "focus": "Place [3,6,9,1]", "stateVars": "B0:[1,1] | B1:[3,3] | B2:[6,6] | B4:[9,9]", "note": "Each bucket only stores its local min and max."},
        {"step": 3, "focus": "Sweep non-empty buckets", "stateVars": "3-1=2, 6-3=3, 9-6=3 -> best=3", "note": "Skip empty bucket B3 and return 3 in O(N) time."},
    ],
    brute_t="O(N log N)",
    brute_s="O(N)",
    opt_t="O(N)",
    opt_s="O(N)",
    derivation="Finding min/max, bucketing every element once, and sweeping at most N + 1 buckets each take O(N) time.",
    followup_q="When would LSD Radix Sort be preferable to Pigeonhole Bucket Sort here?",
    followup_a="Radix Sort uses fixed 256-entry counting tables with tight cache locality when integers fit in 32 bits, whereas Pigeonhole bucketing adapts directly to floating-point or arbitrary-precision numbers.",
))


# Day 23: LC 622 - Design Circular Queue
_reg(_mk(
    day=23,
    func="MyCircularQueue",
    harness={"customDriver": "system-design", "className": "MyCircularQueue"},
    stmt=(
        "Design your implementation of a fixed-capacity circular queue (`MyCircularQueue`) where the last position connects back to the first position.\n\n"
        "Implement the `MyCircularQueue` class:\n"
        "- `MyCircularQueue(k)`: Initialise the queue with capacity `k`.\n"
        "- `enQueue(value) -> bool`: Insert an element into the circular queue. Return `True` if successful, `False` if full.\n"
        "- `deQueue() -> bool`: Delete an element from the front. Return `True` if successful, `False` if empty.\n"
        "- `Front() -> int`: Return the front item, or `-1` if empty.\n"
        "- `Rear() -> int`: Return the last item, or `-1` if empty.\n"
        "- `isEmpty() -> bool`: Check whether the queue is empty.\n"
        "- `isFull() -> bool`: Check whether the queue is full."
    ),
    examples=[
        {
            "input": '["MyCircularQueue","enQueue","enQueue","enQueue","enQueue","Rear","isFull","deQueue","enQueue","Rear"], [[3],[1],[2],[3],[4],[],[],[],[4],[]]',
            "output": "[null, true, true, true, false, 3, true, true, true, 4]",
            "explanation": "Capacity 3 rejects the 4th enQueue until one deQueue frees a slot, then wraps around to store 4.",
        }
    ],
    constraints=["1 <= k <= 1000", "0 <= value <= 1000", "At most 3000 calls will be made across all operations."],
    starter="""
class MyCircularQueue:
    def __init__(self, k: int):
        pass

    def enQueue(self, value: int) -> bool:
        pass

    def deQueue(self) -> bool:
        pass

    def Front(self) -> int:
        pass

    def Rear(self) -> int:
        pass

    def isEmpty(self) -> bool:
        pass

    def isFull(self) -> bool:
        pass
""",
    solution="""
class MyCircularQueue:
    def __init__(self, k: int):
        self.buf = [0] * k
        self.cap = k
        self.head = 0
        self.count = 0

    def enQueue(self, value: int) -> bool:
        if self.count == self.cap:
            return False
        tail = (self.head + self.count) % self.cap
        self.buf[tail] = value
        self.count += 1
        return True

    def deQueue(self) -> bool:
        if self.count == 0:
            return False
        self.head = (self.head + 1) % self.cap
        self.count -= 1
        return True

    def Front(self) -> int:
        return -1 if self.count == 0 else self.buf[self.head]

    def Rear(self) -> int:
        if self.count == 0:
            return -1
        return self.buf[(self.head + self.count - 1) % self.cap]

    def isEmpty(self) -> bool:
        return self.count == 0

    def isFull(self) -> bool:
        return self.count == self.cap
""",
    visible=[
        {
            "label": "Standard wrap-around sequence",
            "args": [
                ["MyCircularQueue", "enQueue", "enQueue", "enQueue", "enQueue", "Rear", "isFull", "deQueue", "enQueue", "Rear"],
                [[3], [1], [2], [3], [4], [], [], [], [4], []],
            ],
            "expected": [None, True, True, True, False, 3, True, True, True, 4],
        },
        {
            "label": "Empty queue guards",
            "args": [
                ["MyCircularQueue", "isEmpty", "Front", "Rear", "deQueue"],
                [[2], [], [], [], []],
            ],
            "expected": [None, True, -1, -1, False],
        },
    ],
    hidden=[
        {"label": "Capacity 1 fill/drain cycle", "args": [["MyCircularQueue", "enQueue", "isFull", "enQueue", "Front", "Rear", "deQueue", "isEmpty", "enQueue", "Front"], [[1], [9], [], [8], [], [], [], [], [7], []]], "expected": [None, True, True, False, 9, 9, True, True, True, 7], "category": "Capacity 1", "edgeReason": "Verifies head == tail wrap-around with a single slot."},
        {"label": "Multiple wrap-arounds", "args": [["MyCircularQueue", "enQueue", "enQueue", "deQueue", "enQueue", "deQueue", "enQueue", "Front", "Rear"], [[2], [10], [20], [], [30], [], [40], [], []]], "expected": [None, True, True, True, True, True, True, 30, 40], "category": "Modulo Wrap", "edgeReason": "Ensures indices wrap cleanly across multiple full cycles."},
        {"label": "Zero values stored", "args": [["MyCircularQueue", "enQueue", "Front", "Rear", "isEmpty"], [[2], [0], [], [], []]], "expected": [None, True, 0, 0, False], "category": "Falsy Values", "edgeReason": "Value 0 must not be confused with empty (-1)."},
        {"label": "Drain completely then refill", "args": [["MyCircularQueue", "enQueue", "enQueue", "deQueue", "deQueue", "deQueue", "enQueue", "Rear"], [[2], [1], [2], [], [], [], [5], []]], "expected": [None, True, True, True, True, False, True, 5], "category": "Empty Recovery", "edgeReason": "Extra deQueue on empty queue must not corrupt count or head."},
        {"label": "Front unchanged on failed enQueue", "args": [["MyCircularQueue", "enQueue", "enQueue", "enQueue", "Front", "Rear"], [[2], [4], [5], [6], [], []]], "expected": [None, True, True, False, 4, 5], "category": "Overflow Guard", "edgeReason": "Full queue rejects new values without overwriting Front."},
    ],
    trap="Using a Python list with `pop(0)` shifts all elements in O(K) time, or tracking `head` and `tail` without `count` makes full and empty ambiguous.",
    pivot="Allocate a fixed ring buffer of size `k` and track only `(head, count)`. Tail index is always `(head + count) % cap`, giving O(1) time for every operation with zero ambiguity.",
    signal="Fixed-capacity FIFO ring buffer with O(1) enqueue/dequeue requires modulo indexing on a fixed array.",
    hints=[
        "Store a fixed list `buf = [0] * k`, a `head` pointer, and an integer `count`.",
        "When enqueuing, write to `(head + count) % cap` and increment `count`.",
        "When dequeuing, advance `head = (head + 1) % cap` and decrement `count`. `Rear` sits at `(head + count - 1) % cap`.",
    ],
    walkthrough="1. Preallocate `buf = [0] * k` with `head = 0`, `count = 0`.\n2. `enQueue` checks `count == cap`, writes to `(head + count) % cap`, and increments `count`.\n3. `deQueue` checks `count == 0`, advances `head = (head + 1) % cap`, and decrements `count`.\n4. `Front` reads `buf[head]` and `Rear` reads `buf[(head + count - 1) % cap]`.",
    trace_steps=[
        {"step": 1, "focus": "enQueue(1), enQueue(2), enQueue(3)", "stateVars": "buf=[1,2,3] | head=0 | count=3", "note": "Ring buffer is full; enQueue(4) returns False."},
        {"step": 2, "focus": "deQueue()", "stateVars": "buf=[1,2,3] | head=1 | count=2", "note": "head advances to 1 without shifting elements."},
        {"step": 3, "focus": "enQueue(4)", "stateVars": "tail=(1+2)%3=0 | buf=[4,2,3] | Rear=4", "note": "Index wraps cleanly around to slot 0."},
    ],
    brute_t="O(K) per deQueue",
    brute_s="O(K)",
    opt_t="O(1) per op",
    opt_s="O(K)",
    derivation="Every operation performs constant-time modulo arithmetic and direct array indexing.",
    followup_q="How would you make `MyCircularQueue` thread-safe in a single-producer single-consumer (SPSC) lock-free setting?",
    followup_a="Track monotonic atomic `head` and `tail` counters with acquire/release memory ordering and pad them onto separate cache lines to avoid false sharing.",
))


# Day 24: LC 432 - All O(1) Data Structure
_reg(_mk(
    day=24,
    func="AllOne",
    harness={"customDriver": "system-design", "className": "AllOne"},
    stmt=(
        "Design a data structure (`AllOne`) to store string counts with the ability to return the strings with minimum and maximum counts in `O(1)` average time.\n\n"
        "Implement the `AllOne` class:\n"
        "- `AllOne()`: Initialises the empty data structure.\n"
        "- `inc(key: str)`: Increments the count of `key` by 1 (inserts with count 1 if absent).\n"
        "- `dec(key: str)`: Decrements the count of `key` by 1 (removes `key` if its count reaches 0).\n"
        "- `getMaxKey() -> str`: Returns one key with the maximal count, or `\"\"` if empty.\n"
        "- `getMinKey() -> str`: Returns one key with the minimal count, or `\"\"` if empty."
    ),
    examples=[
        {
            "input": '["AllOne","inc","inc","getMaxKey","getMinKey","inc","getMaxKey","getMinKey"], [[],["hello"],["hello"],[],[],["leet"],[],[]]',
            "output": '[null, null, null, "hello", "hello", null, "hello", "leet"]',
            "explanation": "After two inc('hello') and one inc('leet'), max is 'hello' (2) and min is 'leet' (1).",
        }
    ],
    constraints=["1 <= len(key) <= 10", "All operations must run in O(1) average time complexity."],
    starter="""
class AllOne:
    def __init__(self):
        pass

    def inc(self, key: str) -> None:
        pass

    def dec(self, key: str) -> None:
        pass

    def getMaxKey(self) -> str:
        pass

    def getMinKey(self) -> str:
        pass
""",
    solution="""
class _Bucket:
    def __init__(self, count: int):
        self.count = count
        self.keys: set[str] = set()
        self.prev: "_Bucket | None" = None
        self.next: "_Bucket | None" = None


class AllOne:
    def __init__(self):
        self.head = _Bucket(0)
        self.tail = _Bucket(0)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.key_node: dict[str, _Bucket] = {}

    def _insert_after(self, node: _Bucket, new_node: _Bucket) -> _Bucket:
        nxt = node.next
        new_node.prev = node
        new_node.next = nxt
        node.next = new_node
        nxt.prev = new_node
        return new_node

    def _remove(self, node: _Bucket) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def inc(self, key: str) -> None:
        if key in self.key_node:
            cur = self.key_node[key]
            target_cnt = cur.count + 1
            nxt = cur.next
            if nxt is self.tail or nxt.count != target_cnt:
                nxt = self._insert_after(cur, _Bucket(target_cnt))
            nxt.keys.add(key)
            self.key_node[key] = nxt
            cur.keys.remove(key)
            if not cur.keys:
                self._remove(cur)
        else:
            first = self.head.next
            if first is self.tail or first.count != 1:
                first = self._insert_after(self.head, _Bucket(1))
            first.keys.add(key)
            self.key_node[key] = first

    def dec(self, key: str) -> None:
        if key not in self.key_node:
            return
        cur = self.key_node[key]
        if cur.count == 1:
            del self.key_node[key]
        else:
            target_cnt = cur.count - 1
            prv = cur.prev
            if prv is self.head or prv.count != target_cnt:
                prv = self._insert_after(prv, _Bucket(target_cnt))
            prv.keys.add(key)
            self.key_node[key] = prv
        cur.keys.remove(key)
        if not cur.keys:
            self._remove(cur)

    def getMaxKey(self) -> str:
        if self.tail.prev is self.head:
            return ""
        return next(iter(self.tail.prev.keys))

    def getMinKey(self) -> str:
        if self.head.next is self.tail:
            return ""
        return next(iter(self.head.next.keys))
""",
    visible=[
        {
            "label": "Basic inc/getMax/getMin",
            "args": [
                ["AllOne", "inc", "inc", "getMaxKey", "getMinKey", "inc", "getMaxKey", "getMinKey"],
                [[], ["hello"], ["hello"], [], [], ["leet"], [], []],
            ],
            "expected": [None, None, None, "hello", "hello", None, "hello", "leet"],
        },
        {
            "label": "Decrement to zero removes key",
            "args": [
                ["AllOne", "inc", "dec", "getMaxKey", "getMinKey"],
                [[], ["a"], ["a"], [], []],
            ],
            "expected": [None, None, None, "", ""],
        },
    ],
    hidden=[
        {"label": "Empty queries", "args": [["AllOne", "getMaxKey", "getMinKey"], [[], [], []]], "expected": [None, "", ""], "category": "Empty State", "edgeReason": "Empty structure must return empty strings."},
        {"label": "Remove middle bucket cleanly", "args": [["AllOne", "inc", "inc", "inc", "inc", "dec", "getMaxKey", "getMinKey"], [[], ["a"], ["b"], ["b"], ["b"], ["a"], [], []]], "expected": [None, None, None, None, None, None, "b", "b"], "category": "Bucket Pruning", "edgeReason": "Empty bucket for count 1 must be unlinked so getMinKey finds count 3."},
        {"label": "Swap min and max via dec", "args": [["AllOne", "inc", "inc", "inc", "dec", "dec", "getMaxKey", "getMinKey"], [[], ["x"], ["x"], ["y"], ["x"], ["x"], [], []]], "expected": [None, None, None, None, None, None, "y", "y"], "category": "Order Reversal", "edgeReason": "Decrementing former max removes it completely."},
        {"label": "Multiple increments then decrements", "args": [["AllOne", "inc", "inc", "inc", "inc", "inc", "dec", "getMaxKey", "getMinKey"], [[], ["a"], ["a"], ["a"], ["b"], ["b"], ["b"], [], []]], "expected": [None, None, None, None, None, None, None, "a", "b"], "category": "Adjacent Buckets", "edgeReason": "Decrements b from 2 to 1 while a stays at 3."},
        {"label": "Re-insert after removal", "args": [["AllOne", "inc", "dec", "inc", "getMaxKey", "getMinKey"], [[], ["k"], ["k"], ["k"], [], []]], "expected": [None, None, None, None, "k", "k"], "category": "Lifecycle Reuse", "edgeReason": "Key removed at 0 can be reinserted cleanly at count 1."},
    ],
    trap="Using a heap or sorted map takes O(log N) per `inc`/`dec`, or scanning a hash map for min/max takes O(N).",
    pivot="Maintain a doubly linked list of sorted frequency buckets (each holding a set of keys with that exact count) plus a hash map `key -> bucket`. Because counts change by +1 or -1, the destination bucket is always immediately adjacent.",
    signal="O(1) frequency increment/decrement paired with O(1) min/max lookup mirrors LFU Cache's frequency doubly-linked list.",
    hints=[
        "Group all keys with the same frequency into one doubly-linked list node (`_Bucket`).",
        "Keep a hash map `key_node[key] -> bucket`. Moving a key on `inc` only checks `cur.next`; moving on `dec` only checks `cur.prev`.",
        "Always unlink a bucket immediately once its `keys` set becomes empty so `head.next` is always the true min and `tail.prev` is always the true max.",
    ],
    walkthrough="1. Maintain sentinel `head` and `tail` nodes for frequency buckets in ascending order.\n2. On `inc(key)`, move `key` to `cur.next` (creating a `count + 1` bucket if missing), then remove `cur` if empty.\n3. On `dec(key)`, either remove `key` (if `count == 1`) or move it to `cur.prev` (creating `count - 1` if missing), then remove `cur` if empty.\n4. `getMinKey` reads from `head.next.keys` and `getMaxKey` reads from `tail.prev.keys`.",
    trace_steps=[
        {"step": 1, "focus": "inc('hello') twice", "stateVars": "head <-> [2:{hello}] <-> tail", "note": "Count-1 bucket is removed once empty; count-2 bucket holds 'hello'."},
        {"step": 2, "focus": "inc('leet')", "stateVars": "head <-> [1:{leet}] <-> [2:{hello}] <-> tail", "note": "New count-1 bucket inserted right after head."},
        {"step": 3, "focus": "getMaxKey / getMinKey", "stateVars": "tail.prev='hello' | head.next='leet'", "note": "Both queries finish in O(1) without scanning."},
    ],
    brute_t="O(N) or O(log N) per op",
    brute_s="O(N)",
    opt_t="O(1) per op",
    opt_s="O(N)",
    derivation="Hash-map lookup, set insert/remove, and adjacent doubly-linked list pointer updates are all O(1).",
    followup_q="How does this structure directly power an O(1) LFU Cache?",
    followup_a="Replace each bucket's `set` with an `OrderedDict` (or doubly-linked list of cache entries) so ties at the minimum frequency bucket evict the least recently used entry in O(1).",
))


# Day 28: LC 410 - Split Array Largest Sum
_reg(_mk(
    day=28,
    func="splitArray",
    stmt=(
        "Given an integer array `nums` and an integer `k`, split `nums` into `k` non-empty contiguous subarrays such that "
        "the largest sum of any subarray is minimised.\n\n"
        "Return the minimised largest sum of the split."
    ),
    examples=[
        {"input": "nums = [7, 2, 5, 10, 8], k = 2", "output": "18", "explanation": "Best split is [7, 2, 5] (sum 14) and [10, 8] (sum 18), giving minimised largest sum 18."},
        {"input": "nums = [1, 2, 3, 4, 5], k = 2", "output": "9", "explanation": "Split into [1, 2, 3] (6) and [4, 5] (9)."},
    ],
    constraints=["1 <= len(nums) <= 1000", "0 <= nums[i] <= 10^6", "1 <= k <= min(50, len(nums))"],
    starter="""
def splitArray(nums: list[int], k: int) -> int:
    # Write your O(N log(sum(nums))) Binary Search on Answer solution here
    pass
""",
    solution="""
def splitArray(nums: list[int], k: int) -> int:
    lo, hi = max(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        pieces = 1
        cur = 0
        for x in nums:
            if cur + x > mid:
                pieces += 1
                cur = x
            else:
                cur += x
        if pieces <= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
""",
    visible=[
        {"label": "Standard split k=2", "args": [[7, 2, 5, 10, 8], 2], "expected": 18},
        {"label": "Increasing array k=2", "args": [[1, 2, 3, 4, 5], 2], "expected": 9},
        {"label": "k equals length", "args": [[1, 4, 4], 3], "expected": 4},
    ],
    hidden=[
        {"label": "k = 1 (entire array)", "args": [[2, 3, 5, 7], 1], "expected": 17, "category": "Single Partition", "edgeReason": "Upper bound hi = sum(nums) must be reachable."},
        {"label": "All zeros", "args": [[0, 0, 0, 0], 2], "expected": 0, "category": "Zero Values", "edgeReason": "Handles lo == hi == 0 cleanly."},
        {"label": "Single element", "args": [[42], 1], "expected": 42, "category": "Minimum Length", "edgeReason": "Single element returns its own value."},
        {"label": "Heavy spike element", "args": [[1, 1, 100, 1, 1], 3], "expected": 100, "category": "Dominant Element", "edgeReason": "Lower bound lo = max(nums) prevents impossible splits."},
        {"label": "Even balanced split", "args": [[10, 5, 13, 4, 8, 4, 5, 11, 14, 9, 16, 10, 20, 8], 8], "expected": 25, "category": "Tight Packing", "edgeReason": "Verifies exact greedy feasibility threshold."},
    ],
    trap="Using 2D DP `dp[i][j]` costs O(N^2 * K) time, which is much slower than binary searching the monotonic answer space.",
    pivot="Binary search the candidate maximum subarray sum `mid` in `[max(nums), sum(nums)]`. A greedy linear pass checks whether `nums` can be partitioned into `<= k` pieces each summing to at most `mid`.",
    signal="'Minimise the maximum' (or 'maximise the minimum') over contiguous partitions with non-negative values signals Binary Search on the Answer.",
    hints=[
        "Because all elements are non-negative, increasing the allowed sum cap `mid` can only reduce or maintain the number of pieces needed.",
        "The answer must lie between `lo = max(nums)` and `hi = sum(nums)`.",
        "Greedily pack elements into the current subarray until adding `x` exceeds `mid`, then start a new subarray.",
    ],
    walkthrough="1. Set `lo = max(nums)` and `hi = sum(nums)`.\n2. While `lo < hi`, test `mid = (lo + hi) // 2` with a greedy left-to-right scan counting required subarrays.\n3. If `pieces <= k`, `mid` is feasible so shrink right (`hi = mid`); otherwise raise left (`lo = mid + 1`).\n4. Return `lo`.",
    trace_steps=[
        {"step": 1, "focus": "lo=10, hi=32 -> mid=21", "stateVars": "pieces=2 ([7,2,5], [10,8]) <= 2", "note": "21 is feasible, so narrow hi = 21."},
        {"step": 2, "focus": "lo=10, hi=21 -> mid=15", "stateVars": "pieces=3 ([7,2,5],[10],[8]) > 2", "note": "15 needs 3 pieces (> 2), so raise lo = 16."},
        {"step": 3, "focus": "Converge to lo=hi=18", "stateVars": "pieces=2 ([7,2,5]=14, [10,8]=18)", "note": "18 is the smallest feasible cap -> return 18."},
    ],
    brute_t="O(N^2 * K)",
    brute_s="O(N * K)",
    opt_t="O(N log S)",
    opt_s="O(1)",
    derivation="Each binary search iteration halves the sum range S = sum(nums) and executes one O(N) greedy check.",
    followup_q="Would binary search still work if `nums` could contain negative numbers?",
    followup_a="No, negative numbers break greedy prefix packing because extending a subarray could reduce its sum. With negatives you fall back to DP.",
))


# Day 30: LC 315 - Count of Smaller Numbers After Self
_reg(_mk(
    day=30,
    func="countSmaller",
    stmt=(
        "Given an integer array `nums`, return an integer array `counts` where `counts[i]` is the number of smaller elements "
        "to the right of `nums[i]`."
    ),
    examples=[
        {"input": "nums = [5, 2, 6, 1]", "output": "[2, 1, 1, 0]", "explanation": "Right of 5: 2 and 1 (2). Right of 2: 1 (1). Right of 6: 1 (1). Right of 1: none (0)."},
        {"input": "nums = [-1]", "output": "[0]", "explanation": "Single element has no elements to its right."},
    ],
    constraints=["1 <= len(nums) <= 10^5", "-10^4 <= nums[i] <= 10^4"],
    starter="""
def countSmaller(nums: list[int]) -> list[int]:
    # Write your O(N log N) Merge Sort / Fenwick Tree solution here
    pass
""",
    solution="""
def countSmaller(nums: list[int]) -> list[int]:
    n = len(nums)
    counts = [0] * n
    indexed = [(v, i) for i, v in enumerate(nums)]

    def sort_count(arr: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = sort_count(arr[:mid])
        right = sort_count(arr[mid:])
        merged: list[tuple[int, int]] = []
        i = j = 0
        right_smaller = 0
        while i < len(left) and j < len(right):
            if right[j][0] < left[i][0]:
                right_smaller += 1
                merged.append(right[j])
                j += 1
            else:
                counts[left[i][1]] += right_smaller
                merged.append(left[i])
                i += 1
        while i < len(left):
            counts[left[i][1]] += right_smaller
            merged.append(left[i])
            i += 1
        merged.extend(right[j:])
        return merged

    sort_count(indexed)
    return counts
""",
    visible=[
        {"label": "Standard mixed array", "args": [[5, 2, 6, 1]], "expected": [2, 1, 1, 0]},
        {"label": "Single negative", "args": [[-1]], "expected": [0]},
        {"label": "Duplicate negatives", "args": [[-1, -1]], "expected": [0, 0]},
    ],
    hidden=[
        {"label": "Strictly descending", "args": [[5, 4, 3, 2, 1]], "expected": [4, 3, 2, 1, 0], "category": "Worst-Case Inversions", "edgeReason": "Every element to the right is smaller."},
        {"label": "Strictly ascending", "args": [[1, 2, 3, 4, 5]], "expected": [0, 0, 0, 0, 0], "category": "Zero Inversions", "edgeReason": "No smaller elements exist to the right."},
        {"label": "Duplicates interleaved", "args": [[2, 0, 1, 2, 0]], "expected": [3, 0, 1, 1, 0], "category": "Strict Inequality", "edgeReason": "Equal values on the right must not be counted as strictly smaller."},
        {"label": "Negative and positive mix", "args": [[0, -5, 3, -5, 2]], "expected": [2, 0, 2, 0, 0], "category": "Negative Values", "edgeReason": "Verifies merge comparisons work cleanly with negatives."},
        {"label": "Two elements swapped", "args": [[9, 1]], "expected": [1, 0], "category": "Minimal Inversion", "edgeReason": "Smallest non-trivial inversion pair."},
    ],
    trap="Checking every pair `(i, j)` with `j > i` takes O(N^2) time and times out for `N = 10^5`.",
    pivot="Carry `(value, original_index)` pairs through Merge Sort. During the merge step, count how many elements from the right half move ahead of each left-half element (`right_smaller`) and add that count to `counts[orig_idx]`.",
    signal="Counting inversions or 'smaller elements to the right' per index is a textbook Divide-and-Conquer Merge Sort or Coordinate-Compressed Fenwick Tree problem.",
    hints=[
        "Pair each element with its original index `(val, idx)` before sorting so you know where to accumulate its count.",
        "When merging sorted `left` and `right` halves, every time `right[j] < left[i]`, increment `right_smaller`.",
        "Whenever `left[i]` is placed into `merged` (including when `right[j] == left[i]`!), add `right_smaller` to `counts[left[i][1]]`.",
    ],
    walkthrough="1. Tag each element with its original index `(v, i)`.\n2. Recursively split and merge-sort.\n3. Track `right_smaller` during each merge; add it to `counts[orig_idx]` whenever a left-half item is emitted.\n4. Return `counts`.",
    trace_steps=[
        {"step": 1, "focus": "Merge [5,2] and [6,1]", "stateVars": "left=[(2,1),(5,0)] | right=[(1,3),(6,2)]", "note": "Both halves are sorted while keeping original indices."},
        {"step": 2, "focus": "Emit (1,3) from right", "stateVars": "right_smaller = 1", "note": "1 is smaller than both 2 and 5."},
        {"step": 3, "focus": "Emit (2,1) and (5,0)", "stateVars": "counts = [2, 1, 1, 0]", "note": "Each left item picks up right_smaller=1 on top of its inner count."},
    ],
    brute_t="O(N^2)",
    brute_s="O(1)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Merge Sort splits log N levels deep and merges all N items linearly per level.",
    followup_q="How would you solve this with a Fenwick Tree (BIT) instead of Merge Sort?",
    followup_a="Coordinate-compress unique values into ranks `1..M`, iterate `nums` from right to left, query `bit.sum(rank - 1)` for smaller counts, then `bit.add(rank, 1)`.",
))


# Day 31: LC 1095 - Find in Mountain Array
_reg(_mk(
    day=31,
    func="findInMountainArray",
    stmt=(
        "A mountain array `mountainArr` strictly increases up to a peak index `peak` and strictly decreases afterwards "
        "(`len(mountainArr) >= 3`).\n\n"
        "Given `target` and `mountainArr`, return the minimum index `i` such that `mountainArr[i] == target`. "
        "If `target` does not exist in `mountainArr`, return `-1`. Solve it in `O(log N)` queries using binary search."
    ),
    examples=[
        {"input": "target = 3, mountainArr = [1, 2, 3, 4, 5, 3, 1]", "output": "2", "explanation": "3 appears at index 2 and index 5; return the minimum index 2."},
        {"input": "target = 3, mountainArr = [0, 1, 2, 4, 2, 1]", "output": "-1", "explanation": "3 is absent from the mountain array."},
    ],
    constraints=["3 <= len(mountainArr) <= 10^4", "0 <= target, mountainArr[i] <= 10^9", "Mountain array is strictly increasing then strictly decreasing."],
    starter="""
def findInMountainArray(target: int, mountainArr: list[int]) -> int:
    # Write your O(log N) Peak + Dual Binary Search solution here
    pass
""",
    solution="""
def findInMountainArray(target: int, mountainArr: list[int]) -> int:
    n = len(mountainArr)
    lo, hi = 1, n - 2
    while lo < hi:
        mid = (lo + hi) // 2
        if mountainArr[mid] < mountainArr[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    peak = lo

    # 1. Search strictly increasing left slope [0..peak]
    lo, hi = 0, peak
    while lo <= hi:
        mid = (lo + hi) // 2
        v = mountainArr[mid]
        if v == target:
            return mid
        if v < target:
            lo = mid + 1
        else:
            hi = mid - 1

    # 2. Search strictly decreasing right slope [peak+1..n-1]
    lo, hi = peak + 1, n - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        v = mountainArr[mid]
        if v == target:
            return mid
        if v > target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
    visible=[
        {"label": "Target on both slopes (return min)", "args": [3, [1, 2, 3, 4, 5, 3, 1]], "expected": 2},
        {"label": "Target absent", "args": [3, [0, 1, 2, 4, 2, 1]], "expected": -1},
        {"label": "Target only on right slope", "args": [0, [1, 5, 2, 0]], "expected": 3},
    ],
    hidden=[
        {"label": "Target is the peak", "args": [5, [1, 2, 5, 3, 1]], "expected": 2, "category": "Peak Target", "edgeReason": "Target located exactly at the peak index."},
        {"label": "Target at index 0", "args": [1, [1, 5, 2]], "expected": 0, "category": "Left Endpoint", "edgeReason": "Minimum length 3 mountain with target at index 0."},
        {"label": "Target at last index", "args": [2, [1, 5, 2]], "expected": 2, "category": "Right Endpoint", "edgeReason": "Target at the rightmost descending endpoint."},
        {"label": "Target greater than peak", "args": [9, [1, 3, 6, 4, 2]], "expected": -1, "category": "Out of Range", "edgeReason": "Value above peak cannot exist on either slope."},
        {"label": "Peak near right end", "args": [4, [1, 2, 3, 4, 10, 4]], "expected": 3, "category": "Skewed Peak", "edgeReason": "Must return index 3 on left slope rather than 5 on right slope."},
    ],
    trap="Linear scanning costs O(N) calls and exceeds the interactive 100-call budget on large arrays; searching the right slope before the left returns the wrong index when duplicates exist across slopes.",
    pivot="Run three O(log N) binary searches: (1) locate `peak` by comparing `arr[mid]` vs `arr[mid + 1]`, (2) binary search ascending `[0..peak]` first for the minimum index, (3) only if missing, binary search descending `[peak + 1..n - 1]`.",
    signal="Unimodal (bitonic) array with a minimum-index lookup decomposes into Peak Binary Search + two monotonic Binary Searches.",
    hints=[
        "First find the peak index: if `arr[mid] < arr[mid + 1]`, you are on the rising slope (`lo = mid + 1`), else `hi = mid`.",
        "Always binary search `[0..peak]` before `[peak + 1..n - 1]` so you return the smallest matching index.",
        "Remember the comparison sign flips on the descending right half (`if v > target: lo = mid + 1`).",
    ],
    walkthrough="1. Binary search `lo, hi = 1, n - 2` comparing `arr[mid] < arr[mid + 1]` to isolate `peak`.\n2. Binary search ascending `[0..peak]`; return immediately if found.\n3. Binary search descending `[peak + 1..n - 1]`; return index or `-1`.",
    trace_steps=[
        {"step": 1, "focus": "Find peak in [1,2,3,4,5,3,1]", "stateVars": "peak = 4 (value 5)", "note": "Splits array into ascending [1,2,3,4,5] and descending [3,1]."},
        {"step": 2, "focus": "Binary search [0..4] for 3", "stateVars": "mid=2 -> arr[2]=3 == target", "note": "Found on left slope at index 2; return 2 immediately."},
    ],
    brute_t="O(N)",
    brute_s="O(1)",
    opt_t="O(log N)",
    opt_s="O(1)",
    derivation="Three binary searches execute at most ~3 log2(N) element reads (~42 reads for N = 10,000).",
    followup_q="In the interactive LeetCode API where `mountainArr.get(i)` is capped at 100 calls, how do you cut redundant reads?",
    followup_a="Memoise `get(i)` in a small dictionary so overlapping indices queried during peak finding and slope search are never fetched twice.",
))


# Day 32: LC 240 - Search a 2D Matrix II
_reg(_mk(
    day=32,
    func="searchMatrix",
    stmt=(
        "Write an efficient algorithm that searches for a value `target` in an `m x n` integer `matrix`.\n\n"
        "This matrix has the following properties:\n"
        "- Integers in each row are sorted in ascending order from left to right.\n"
        "- Integers in each column are sorted in ascending order from top to bottom.\n\n"
        "Return `True` if `target` is in `matrix`, or `False` otherwise."
    ),
    examples=[
        {"input": "matrix = [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], target = 5", "output": "True", "explanation": "5 is located at row 1, column 1."},
        {"input": "matrix = [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], target = 20", "output": "False", "explanation": "20 does not appear in the matrix."},
    ],
    constraints=["1 <= m, n <= 300", "-10^9 <= matrix[i][j], target <= 10^9"],
    starter="""
def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    # Write your O(M + N) Staircase Search solution here
    pass
""",
    solution="""
def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        val = matrix[r][c]
        if val == target:
            return True
        if val > target:
            c -= 1
        else:
            r += 1
    return False
""",
    visible=[
        {"label": "Target present (5)", "args": [[[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 5], "expected": True},
        {"label": "Target absent (20)", "args": [[[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 20], "expected": False},
    ],
    hidden=[
        {"label": "1x1 match", "args": [[[-5]], -5], "expected": True, "category": "Minimal Grid", "edgeReason": "Single cell matrix match."},
        {"label": "1x1 miss", "args": [[[-5]], -10], "expected": False, "category": "Minimal Grid", "edgeReason": "Single cell matrix miss."},
        {"label": "Single row", "args": [[[1, 3, 5, 7, 9]], 7], "expected": True, "category": "Degenerate 1xN", "edgeReason": "Walks left across single row."},
        {"label": "Single column", "args": [[[1], [3], [5], [7]], 5], "expected": True, "category": "Degenerate Mx1", "edgeReason": "Walks down single column."},
        {"label": "Bottom-left corner target", "args": [[[1, 4, 7], [2, 5, 8], [3, 6, 9]], 3], "expected": True, "category": "Corner Boundary", "edgeReason": "Maximum O(M+N) staircase traversal path."},
    ],
    trap="Starting at top-left `(0, 0)` is ambiguous because both right and down increase; scanning all cells takes O(M * N).",
    pivot="Start at the top-right corner `(0, n - 1)` (saddle point): moving left strictly decreases values and moving down strictly increases them, eliminating an entire row or column on every comparison.",
    signal="Row-sorted AND column-sorted matrix without global flattening monotonicity signals Top-Right (or Bottom-Left) Staircase Search.",
    hints=[
        "At `(0, n - 1)`, every element to the left is smaller and every element below is larger.",
        "If `matrix[r][c] > target`, the entire column `c` below `r` is too big, so `c -= 1`.",
        "If `matrix[r][c] < target`, the entire row `r` to the left of `c` is too small, so `r += 1`.",
    ],
    walkthrough="1. Start at `r = 0, c = n - 1`.\n2. While inside bounds, compare `matrix[r][c]` to `target`.\n3. Step left if larger, step down if smaller, return `True` on match.\n4. Return `False` if either boundary is crossed.",
    trace_steps=[
        {"step": 1, "focus": "(r=0, c=4) val=15 > 5", "stateVars": "eliminate col 4 -> c=3", "note": "All values below 15 are >= 15, so column 4 cannot hold 5."},
        {"step": 2, "focus": "Walk left to (0,1) val=4 < 5", "stateVars": "eliminate row 0 -> r=1", "note": "4 < 5, so row 0 is exhausted; step down."},
        {"step": 3, "focus": "(r=1, c=1) val=5 == 5", "stateVars": "return True", "note": "Exact match found in 5 steps instead of 25."},
    ],
    brute_t="O(M * N)",
    brute_s="O(1)",
    opt_t="O(M + N)",
    opt_s="O(1)",
    derivation="Each iteration either decrements `c` or increments `r`, taking at most `m + n` steps.",
    followup_q="If `M = 10` and `N = 10^6`, is `O(M + N)` still fastest?",
    followup_a="No, when one dimension is tiny (`M << N`), binary searching each of the `M` rows takes `O(M log N)`, which beats `O(M + N)`.",
))


# Day 47: LC 218 - The Skyline Problem
_reg(_mk(
    day=47,
    func="getSkyline",
    stmt=(
        "A city's skyline is the outer contour of the silhouette formed by all buildings in `buildings`, where each building is "
        "`[left, right, height]`.\n\n"
        "Return the skyline as a list of key points `[[x1, y1], [x2, y2], ...]` sorted by x-coordinate, where each key point is "
        "the left endpoint of a horizontal segment in the contour. No two consecutive key points may share the same height."
    ),
    examples=[
        {
            "input": "buildings = [[2,9,10],[3,7,15],[5,12,12],[15,20,10],[19,24,8]]",
            "output": "[[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]",
            "explanation": "Key points trace the tallest active building at each start/end boundary.",
        },
        {"input": "buildings = [[0,2,3],[2,5,3]]", "output": "[[0,3],[5,0]]", "explanation": "Adjacent equal-height buildings merge into one segment."},
    ],
    constraints=["1 <= len(buildings) <= 10^4", "0 <= left < right <= 2^31 - 1", "1 <= height <= 2^31 - 1"],
    starter="""
def getSkyline(buildings: list[list[int]]) -> list[list[int]]:
    # Write your O(N log N) Event Sweep Line + Max-Heap solution here
    pass
""",
    solution="""
import heapq


def getSkyline(buildings: list[list[int]]) -> list[list[int]]:
    events: list[tuple[int, int, int]] = []
    for left, right, h in buildings:
        events.append((left, -h, right))
        events.append((right, 0, 0))
    events.sort()

    res: list[list[int]] = [[0, 0]]
    heap: list[tuple[int, int]] = [(0, float("inf"))]  # (-height, right_edge)
    for x, neg_h, r in events:
        while heap[0][1] <= x:
            heapq.heappop(heap)
        if neg_h != 0:
            heapq.heappush(heap, (neg_h, r))
        cur_max = -heap[0][0]
        if res[-1][1] != cur_max:
            res.append([x, cur_max])
    return res[1:]
""",
    visible=[
        {"label": "Classic multi-building skyline", "args": [[[2, 9, 10], [3, 7, 15], [5, 12, 12], [15, 20, 10], [19, 24, 8]]], "expected": [[2, 10], [3, 15], [7, 12], [12, 0], [15, 10], [20, 8], [24, 0]]},
        {"label": "Touching equal-height buildings", "args": [[[0, 2, 3], [2, 5, 3]]], "expected": [[0, 3], [5, 0]]},
    ],
    hidden=[
        {"label": "Single building", "args": [[[1, 5, 10]]], "expected": [[1, 10], [5, 0]], "category": "Single Interval", "edgeReason": "Minimal skyline starts at height and drops to 0."},
        {"label": "Same left edge different heights", "args": [[[1, 4, 5], [1, 4, 10]]], "expected": [[1, 10], [4, 0]], "category": "Tie-Breaking Start", "edgeReason": "Taller start (-10) must sort before shorter start (-5) at same x."},
        {"label": "Nested taller building", "args": [[[1, 10, 4], [3, 6, 9]]], "expected": [[1, 4], [3, 9], [6, 4], [10, 0]], "category": "Nested Containment", "edgeReason": "Height rises at 3 then returns cleanly to 4 at 6."},
        {"label": "Duplicate identical buildings", "args": [[[2, 5, 7], [2, 5, 7]]], "expected": [[2, 7], [5, 0]], "category": "Exact Duplicates", "edgeReason": "No duplicate horizontal key points allowed."},
        {"label": "Touching rising staircase", "args": [[[0, 2, 2], [2, 4, 4], [4, 6, 6]]], "expected": [[0, 2], [2, 4], [4, 6], [6, 0]], "category": "Touching Starts/Ends", "edgeReason": "Start (-h) sorts before end (0) at shared x boundary."},
    ],
    trap="Rasterising every x coordinate fails when coordinates reach 2^31 - 1, and sloppy tie-breaking at shared x boundaries produces spurious drops to 0.",
    pivot="Convert each building into a start event `(left, -h, right)` and an end checkpoint `(right, 0, 0)`. Sorting ascending places taller starts first (`-h < 0`), while a max-heap lazily pops expired buildings (`right <= x`).",
    signal="Merging overlapping weighted intervals to emit height-change events signals a Sweep Line + Lazy Max-Heap.",
    hints=[
        "Only building start (`left`) and end (`right`) x-coordinates can change the maximum height.",
        "Sorting `(x, -h, right)` ensures that at the same `x`, taller starts are processed before shorter starts and before ends (`0`).",
        "Keep a sentinel `(0, inf)` in the max-heap and lazily pop any top entry whose `right <= x` before reading `-heap[0][0]`.",
    ],
    walkthrough="1. Emit `(left, -h, right)` and `(right, 0, 0)` for each building and sort.\n2. Maintain a max-heap of `(-h, right)` seeded with `(0, inf)`.\n3. At each event `x`, pop expired heap tops (`right <= x`), push starts, and append `[x, cur_max]` whenever height changes.",
    trace_steps=[
        {"step": 1, "focus": "x=2 start h=10", "stateVars": "heap=[(-10,9),(0,inf)] | res=[[2,10]]", "note": "Max height changes 0 -> 10."},
        {"step": 2, "focus": "x=3 start h=15", "stateVars": "heap=[(-15,7),(-10,9),...] | res+=[3,15]", "note": "Taller building rises to 15."},
        {"step": 3, "focus": "x=7 end of h=15", "stateVars": "pop (-15,7) -> top=(-12,12) | res+=[7,12]", "note": "Lazy pop exposes next tallest active building (height 12)."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Each building enters and leaves the heap at most once, and sorting 2N events takes O(N log N).",
    followup_q="How can you also solve The Skyline Problem using Divide and Conquer?",
    followup_a="Recursively compute the left and right half skylines and merge them in linear time like Merge Sort, tracking `left_h` and `right_h` to emit `max(left_h, right_h)`.",
))


# Day 48: LC 729 - My Calendar I
_reg(_mk(
    day=48,
    func="MyCalendar",
    harness={"customDriver": "system-design", "className": "MyCalendar"},
    stmt=(
        "Implement a `MyCalendar` class to store half-open time intervals `[startTime, endTime)` without causing a double booking.\n\n"
        "A double booking happens when two events have a non-empty intersection (`max(s1, s2) < min(e1, e2)`).\n"
        "- `MyCalendar()`: Initialises the calendar.\n"
        "- `book(startTime: int, endTime: int) -> bool`: Returns `True` and adds the event if it does not overlap any existing event; otherwise returns `False`."
    ),
    examples=[
        {
            "input": '["MyCalendar","book","book","book"], [[],[10,20],[15,25],[20,30]]',
            "output": "[null, true, false, true]",
            "explanation": "[10,20) succeeds, [15,25) overlaps [10,20) so returns false, [20,30) touches at 20 without overlapping so returns true.",
        }
    ],
    constraints=["0 <= startTime < endTime <= 10^9", "At most 1000 calls to book."],
    starter="""
class MyCalendar:
    def __init__(self):
        pass

    def book(self, startTime: int, endTime: int) -> bool:
        pass
""",
    solution="""
import bisect


class MyCalendar:
    def __init__(self):
        self.events: list[tuple[int, int]] = []

    def book(self, startTime: int, endTime: int) -> bool:
        idx = bisect.bisect_left(self.events, (startTime, endTime))
        if idx > 0 and self.events[idx - 1][1] > startTime:
            return False
        if idx < len(self.events) and self.events[idx][0] < endTime:
            return False
        self.events.insert(idx, (startTime, endTime))
        return True
""",
    visible=[
        {
            "label": "Touching vs overlapping",
            "args": [["MyCalendar", "book", "book", "book"], [[], [10, 20], [15, 25], [20, 30]]],
            "expected": [None, True, False, True],
        },
        {
            "label": "Insert between existing bookings",
            "args": [["MyCalendar", "book", "book", "book", "book"], [[], [10, 15], [25, 30], [15, 25], [14, 16]]],
            "expected": [None, True, True, True, False],
        },
    ],
    hidden=[
        {"label": "Duplicate exact interval", "args": [["MyCalendar", "book", "book"], [[], [5, 10], [5, 10]]], "expected": [None, True, False], "category": "Exact Duplicate", "edgeReason": "Identical interval must be rejected."},
        {"label": "Contained inside existing", "args": [["MyCalendar", "book", "book"], [[], [10, 50], [20, 30]]], "expected": [None, True, False], "category": "Containment", "edgeReason": "Inner event overlaps outer event."},
        {"label": "Engulfing existing", "args": [["MyCalendar", "book", "book"], [[], [20, 30], [10, 50]]], "expected": [None, True, False], "category": "Engulfing Overlap", "edgeReason": "Outer event overlapping existing inner event must be rejected."},
        {"label": "Reverse chronological inserts", "args": [["MyCalendar", "book", "book", "book"], [[], [30, 40], [20, 30], [10, 20]]], "expected": [None, True, True, True], "category": "Left-Edge Touching", "edgeReason": "Adjacent half-open intervals booked backwards all succeed."},
        {"label": "Zero start boundary", "args": [["MyCalendar", "book", "book", "book"], [[], [0, 1], [1, 2], [0, 2]]], "expected": [None, True, True, False], "category": "Origin Boundary", "edgeReason": "Handles startTime = 0 cleanly."},
    ],
    trap="Checking overlap with `<=` instead of `<` rejects valid adjacent intervals like `[10, 20)` and `[20, 30)`.",
    pivot="Keep booked intervals sorted by start time and binary search `bisect_left` for the insertion slot `idx`. Because existing events are disjoint, you only need to check the immediate left neighbour `idx - 1` and right neighbour `idx`.",
    signal="Online non-overlapping interval booking calls for sorted boundary lookup (`bisect` / balanced BST).",
    hints=[
        "If existing intervals are disjoint and sorted, a new interval can only collide with its immediate predecessor or successor.",
        "Use `idx = bisect_left(self.events, (startTime, endTime))`.",
        "Reject if `events[idx - 1][1] > startTime` or `events[idx][0] < endTime`; otherwise insert at `idx`.",
    ],
    walkthrough="1. Binary search insertion index `idx` in sorted `self.events`.\n2. Check predecessor's end against `startTime` and successor's start against `endTime`.\n3. Insert if clear and return `True`, else return `False`.",
    trace_steps=[
        {"step": 1, "focus": "book(10, 20)", "stateVars": "events = [(10, 20)]", "note": "Empty calendar accepts [10, 20)."},
        {"step": 2, "focus": "book(15, 25)", "stateVars": "idx=1 | prev.end=20 > 15 -> False", "note": "Immediate predecessor ends after 15 -> overlap rejected."},
        {"step": 3, "focus": "book(20, 30)", "stateVars": "idx=1 | prev.end=20 <= 20 -> True", "note": "Half-open boundary touches without overlapping -> accepted."},
    ],
    brute_t="O(N) per book",
    brute_s="O(N)",
    opt_t="O(log N) lookup",
    opt_s="O(N)",
    derivation="Binary search locates the two candidate neighbours in O(log N); a balanced BST makes insertion O(log N) as well.",
    followup_q="How would you extend this to My Calendar III (returning the maximum k-booking overlap across all time)?",
    followup_a="Store boundary deltas (`delta[start] += 1`, `delta[end] -= 1`) in a sorted map and sweep running prefix sums to track the peak concurrent overlap.",
))


# Day 50: LC 857 - Minimum Cost to Hire K Workers
_reg(_mk(
    day=50,
    func="mincostToHireWorkers",
    stmt=(
        "There are `n` workers. You are given two integer arrays `quality` and `wage` of length `n`, and an integer `k`.\n\n"
        "You must hire exactly `k` workers to form a paid group satisfying:\n"
        "1. Every worker in the paid group is paid in direct proportion to their `quality`.\n"
        "2. Every worker receives at least their minimum wage expectation `wage[i]`.\n\n"
        "Return the least amount of money needed to form a valid paid group (answers within `10^-5` of the true value are accepted)."
    ),
    examples=[
        {"input": "quality = [10, 20, 5], wage = [70, 50, 30], k = 2", "output": "105.0", "explanation": "Hire worker 0 (paid 70) and worker 2 (paid 35) at rate 70/10 = 7 per quality unit -> total 105.0."},
        {"input": "quality = [3, 1, 10, 10, 1], wage = [4, 8, 2, 2, 7], k = 3", "output": "30.66667", "explanation": "Hire workers 0, 2, 3 at rate 4/3 -> (3+10+10)*(4/3) = 30.66667."},
    ],
    constraints=["1 <= k <= n <= 10^4", "1 <= quality[i], wage[i] <= 10^4"],
    starter="""
def mincostToHireWorkers(quality: list[int], wage: list[int], k: int) -> float:
    # Write your O(N log N) Ratio Sort + Max-Heap solution here
    pass
""",
    solution="""
import heapq


def mincostToHireWorkers(quality: list[int], wage: list[int], k: int) -> float:
    workers = sorted((w / q, q) for q, w in zip(quality, wage))
    max_heap: list[int] = []
    q_sum = 0
    best = float("inf")
    for ratio, q in workers:
        heapq.heappush(max_heap, -q)
        q_sum += q
        if len(max_heap) > k:
            q_sum += heapq.heappop(max_heap)  # pops negative largest quality
        if len(max_heap) == k:
            best = min(best, ratio * q_sum)
    return round(best, 5)
""",
    visible=[
        {"label": "Example 1 (k=2)", "args": [[10, 20, 5], [70, 50, 30], 2], "expected": 105.0},
        {"label": "Example 2 (k=3)", "args": [[3, 1, 10, 10, 1], [4, 8, 2, 2, 7], 3], "expected": 30.66667},
    ],
    hidden=[
        {"label": "k = 1 (pick cheapest wage)", "args": [[10, 5, 2], [100, 20, 30], 1], "expected": 20.0, "category": "k=1 Boundary", "edgeReason": "Single worker group simply pays the minimum individual wage."},
        {"label": "k = n (hire everyone)", "args": [[2, 4, 6], [6, 8, 12], 3], "expected": 36.0, "category": "All Workers", "edgeReason": "Max ratio 6/2=3 sets rate for total quality 12 -> 36.0."},
        {"label": "Equal ratios", "args": [[2, 4, 6], [10, 20, 30], 2], "expected": 30.0, "category": "Tied Ratios", "edgeReason": "All ratios equal 5; pick two smallest qualities (2 + 4) * 5."},
        {"label": "High quality low wage trap", "args": [[100, 1, 1], [10, 100, 100], 2], "expected": 200.0, "category": "Heap Eviction", "edgeReason": "Max-heap evicts quality 100 once ratio rises to 100."},
        {"label": "Single worker total", "args": [[7], [21], 1], "expected": 21.0, "category": "Minimum Input", "edgeReason": "Single worker returns their own wage."},
    ],
    trap="Trying all C(N, K) subsets is exponential, and sorting by wage alone ignores that the group's highest `wage/quality` ratio dictates everyone's pay.",
    pivot="For any chosen group, total cost equals `max(wage[i]/quality[i]) * sum(quality[i])`. Sort workers by ascending `wage/quality` ratio; as each worker sets the active rate, use a max-heap of size `k` to retain the `k` smallest qualities.",
    signal="Optimising `max(A) * sum(B)` over a size-`k` subset signals sorting by `A` + maintaining top/bottom `k` of `B` with a heap.",
    hints=[
        "If the group's pay-per-quality rate is `R`, every hired worker must satisfy `R >= wage[i] / quality[i]`.",
        "Sort workers by ascending `ratio = wage[i] / quality[i]`. When considering worker `j` as the captain setting `R = ratio[j]`, any earlier worker is eligible.",
        "To minimise `R * sum(quality)`, keep the `k` smallest qualities seen so far using a max-heap.",
    ],
    walkthrough="1. Pair each worker as `(wage/quality, quality)` and sort ascending by ratio.\n2. Push `-quality` into a max-heap and accumulate `q_sum`.\n3. Whenever heap size exceeds `k`, pop the largest quality.\n4. Whenever heap size equals `k`, update `best = min(best, ratio * q_sum)`.",
    trace_steps=[
        {"step": 1, "focus": "Sort by ratio", "stateVars": "[(2.5,20), (6.0,5), (7.0,10)]", "note": "Worker 1 (2.5), Worker 2 (6.0), Worker 0 (7.0)."},
        {"step": 2, "focus": "Add (2.5,20) & (6.0,5)", "stateVars": "heap=[-20,-5] | q_sum=25 | cost=6*25=150", "note": "First k=2 candidate costs 150."},
        {"step": 3, "focus": "Add (7.0,10), pop 20", "stateVars": "heap=[-10,-5] | q_sum=15 | cost=7*15=105", "note": "Evicting largest quality 20 drops total cost to 105.0."},
    ],
    brute_t="O(N^2 log N)",
    brute_s="O(N)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Sorting takes O(N log N) and each worker triggers at most one O(log K) heap push and pop.",
    followup_q="How is this exact same pattern used in LC 1383 (Maximum Performance of a Team)?",
    followup_a="LC 1383 maximises `min(efficiency) * sum(speed)`: sort descending by efficiency and keep the `k` largest speeds using a min-heap.",
))


# Day 56: LC 60 - Permutation Sequence
_reg(_mk(
    day=56,
    func="getPermutation",
    stmt=(
        "The set `[1, 2, 3, ..., n]` contains a total of `n!` unique permutations listed in lexicographical order.\n\n"
        "Given `n` and `k` (1-indexed), return the `k`-th permutation sequence as a string."
    ),
    examples=[
        {"input": "n = 3, k = 3", "output": '"213"', "explanation": "Permutations of [1,2,3]: 1:'123', 2:'132', 3:'213'."},
        {"input": "n = 4, k = 9", "output": '"2314"', "explanation": "9th permutation of [1,2,3,4] is '2314'."},
    ],
    constraints=["1 <= n <= 9", "1 <= k <= n!"],
    starter="""
def getPermutation(n: int, k: int) -> str:
    # Write your O(N^2) Factorial Number System solution here
    pass
""",
    solution="""
import math


def getPermutation(n: int, k: int) -> str:
    digits = [str(i) for i in range(1, n + 1)]
    k -= 1  # convert to 0-indexed
    out: list[str] = []
    for rem in range(n, 0, -1):
        block = math.factorial(rem - 1)
        idx = k // block
        k %= block
        out.append(digits.pop(idx))
    return "".join(out)
""",
    visible=[
        {"label": "n=3, k=3", "args": [3, 3], "expected": "213"},
        {"label": "n=4, k=9", "args": [4, 9], "expected": "2314"},
        {"label": "n=3, k=1", "args": [3, 1], "expected": "123"},
    ],
    hidden=[
        {"label": "n=1, k=1", "args": [1, 1], "expected": "1", "category": "Minimal Input", "edgeReason": "Smallest valid permutation."},
        {"label": "Last permutation n=4, k=24", "args": [4, 24], "expected": "4321", "category": "Upper Boundary", "edgeReason": "Exact k = n! must produce descending order."},
        {"label": "Block boundary k=6 (n=4)", "args": [4, 6], "expected": "1432", "category": "Zero-Index Boundary", "edgeReason": "Tests 0-indexing k -= 1 right at factorial boundary 3! = 6."},
        {"label": "Block boundary k=7 (n=4)", "args": [4, 7], "expected": "2134", "category": "Next Block Start", "edgeReason": "First permutation starting with digit 2."},
        {"label": "Larger n=9", "args": [9, 100000], "expected": "358926471", "category": "Scale Check", "edgeReason": "Runs instantaneously where backtracking O(k) would time out."},
    ],
    trap="Generating permutations one by one via backtracking until reaching the `k`-th takes O(k * N) time (up to 9! = 362,880).",
    pivot="Convert `k - 1` into the factorial number system: each leading digit governs a block of `(rem - 1)!` permutations, so `idx = k // (rem - 1)!` selects the exact digit directly.",
    signal="Finding the `k`-th lexicographical combinatorial object without enumerating all prior objects calls for Counting / Factorial Number System indexing.",
    hints=[
        "Decrement `k` by 1 so it is 0-indexed.",
        "With `n` digits left, there are `(n - 1)!` permutations starting with each candidate digit.",
        "Pick `digits.pop(k // (n - 1)!)` and replace `k` with `k % (n - 1)!`.",
    ],
    walkthrough="1. Create `digits = ['1', ..., str(n)]` and set `k -= 1`.\n2. For `rem` from `n` down to `1`, compute `block = (rem - 1)!`.\n3. Pop `digits[k // block]` into the answer and set `k %= block`.\n4. Join and return.",
    trace_steps=[
        {"step": 1, "focus": "n=3, k_0=2, block=2!", "stateVars": "idx=2//2=1 -> pop '2' | k_0=0", "note": "Digits left: ['1','3']. First char is '2'."},
        {"step": 2, "focus": "rem=2, k_0=0, block=1!", "stateVars": "idx=0//1=0 -> pop '1' | k_0=0", "note": "Digits left: ['3']. Prefix is '21'."},
        {"step": 3, "focus": "rem=1, k_0=0, block=0!", "stateVars": "pop '3' -> '213'", "note": "Final answer '213' computed in 3 divisions."},
    ],
    brute_t="O(N! * N)",
    brute_s="O(N)",
    opt_t="O(N^2)",
    opt_s="O(N)",
    derivation="Looping N times with an O(N) list pop gives O(N^2) total work (or O(N log N) with a Fenwick tree).",
    followup_q="How would you perform the inverse operation: given a permutation string, return its 1-indexed rank `k`?",
    followup_a="Sum `smaller_remaining_digits * (rem - 1)!` from left to right (Lehmer code) and add 1.",
))


# Day 57: LC 1755 - Closest Subsequence Sum
_reg(_mk(
    day=57,
    func="minAbsDifference",
    stmt=(
        "You are given an integer array `nums` and an integer `goal`.\n\n"
        "You want to choose a subsequence of `nums` such that the sum of its elements is as close as possible to `goal`. "
        "That is, if the sum of the subsequence's elements is `s`, you want to minimise `abs(s - goal)`.\n\n"
        "Return the minimum possible value of `abs(s - goal)`. Note that the empty subsequence has sum `0`."
    ),
    examples=[
        {"input": "nums = [5, -7, 3, 5], goal = 6", "output": "0", "explanation": "Choose the whole array [5, -7, 3, 5] with sum 6 -> |6 - 6| = 0."},
        {"input": "nums = [7, -9, 15, -2], goal = -5", "output": "1", "explanation": "Subsequence [7, -9, -2] sums to -4 -> |-4 - (-5)| = 1."},
    ],
    constraints=["1 <= len(nums) <= 40", "-10^7 <= nums[i] <= 10^7", "-10^9 <= goal <= 10^9"],
    starter="""
def minAbsDifference(nums: list[int], goal: int) -> int:
    # Write your O(2^(N/2) * N) Meet-in-the-Middle solution here
    pass
""",
    solution="""
import bisect


def minAbsDifference(nums: list[int], goal: int) -> int:
    def subset_sums(arr: list[int]) -> list[int]:
        sums = {0}
        for x in arr:
            sums |= {s + x for s in sums}
        return sorted(sums)

    mid = len(nums) // 2
    left_sums = subset_sums(nums[:mid])
    right_sums = subset_sums(nums[mid:])
    best = abs(goal)
    for ls in left_sums:
        need = goal - ls
        idx = bisect.bisect_left(right_sums, need)
        if idx < len(right_sums):
            best = min(best, abs(ls + right_sums[idx] - goal))
        if idx > 0:
            best = min(best, abs(ls + right_sums[idx - 1] - goal))
        if best == 0:
            return 0
    return best
""",
    visible=[
        {"label": "Exact match whole array", "args": [[5, -7, 3, 5], 6], "expected": 0},
        {"label": "Close negative goal", "args": [[7, -9, 15, -2], -5], "expected": 1},
        {"label": "Empty subsequence best", "args": [[1, 2, 3], -7], "expected": 7},
    ],
    hidden=[
        {"label": "Goal is 0 (empty wins)", "args": [[10, 20, 30], 0], "expected": 0, "category": "Empty Subsequence", "edgeReason": "Empty subsequence sums to 0."},
        {"label": "Single element", "args": [[15], 10], "expected": 5, "category": "Minimal Length", "edgeReason": "Chooses between empty (diff 10) and [15] (diff 5)."},
        {"label": "All negatives", "args": [[-5, -10, -3], -13], "expected": 0, "category": "Negative Sums", "edgeReason": "Subset [-10, -3] hits -13 exactly."},
        {"label": "Larger 20-element meet-in-middle", "args": [[1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, -1, -2, -4, -8, -16, -32, -64, -128], 1337], "expected": 0, "category": "Meet-in-Middle Scale", "edgeReason": "Binary representation hits 1337 cleanly across halves."},
        {"label": "Large unreachable goal", "args": [[1, 2, 3, 4], 100], "expected": 90, "category": "Upper Bound", "edgeReason": "Taking all elements gives sum 10, diff 90."},
    ],
    trap="Enumerating all 2^40 (~10^12) subsets times out, and standard DP fails because `nums[i]` ranges up to +/- 10^7.",
    pivot="Split `nums` into two halves of size <= 20 (`2^20 ~ 10^6` sums each). Generate all subset sums for both halves, sort the right half, and binary search `goal - left_sum` (checking both `idx` and `idx - 1`).",
    signal="`N <= 40` with huge value magnitudes (`10^7`) and subset-sum objective is the canonical Meet-in-the-Middle fingerprint.",
    hints=[
        "40 is too large for 2^N brute force, but `40 / 2 = 20` makes `2^20` manageable.",
        "Compute all subset sums for `nums[:n//2]` and `nums[n//2:]`.",
        "For each `ls` in `left_sums`, use `bisect_left(right_sums, goal - ls)` and inspect both `idx` and `idx - 1`.",
    ],
    walkthrough="1. Split `nums` at `n // 2`.\n2. Generate deduplicated sorted subset sums for each half.\n3. For each left sum `ls`, binary search `goal - ls` in `right_sums` and check adjacent candidates.\n4. Return the minimum absolute difference (short-circuiting on 0).",
    trace_steps=[
        {"step": 1, "focus": "Split [5,-7,3,5]", "stateVars": "L=[-7,-2,0,5] | R=[0,3,5,8]", "note": "Two tiny halves instead of 2^N combined search."},
        {"step": 2, "focus": "ls=-2 -> need=8", "stateVars": "bisect_left(R, 8) -> R[3]=8 | diff=0", "note": "Found -2 + 8 = 6 == goal -> short-circuit return 0."},
    ],
    brute_t="O(2^N)",
    brute_s="O(N)",
    opt_t="O(N * 2^(N/2))",
    opt_s="O(2^(N/2))",
    derivation="Each half produces at most 2^(N/2) sums; sorting and binary searching take O(2^(N/2) * N) total time.",
    followup_q="How can you eliminate the binary search log factor and combine the two sorted halves in linear time?",
    followup_a="Use two pointers (`i = 0` on ascending `left_sums`, `j = len - 1` on descending `right_sums`) after generating sorted sums via merge-without-sort.",
))


# Day 58: LC 2035 - Partition Array Into Two Arrays to Minimize Sum Difference
_reg(_mk(
    day=58,
    func="minimumDifference",
    stmt=(
        "You are given an integer array `nums` of length `2 * n`. You must partition `nums` into two arrays of equal length `n` "
        "to minimise the absolute difference of the sums of the two arrays.\n\n"
        "Return the minimum possible absolute difference."
    ),
    examples=[
        {"input": "nums = [3, 9, 7, 3]", "output": "2", "explanation": "Partition into [3, 9] (sum 12) and [7, 3] (sum 10) -> |12 - 10| = 2."},
        {"input": "nums = [-36, 36]", "output": "72", "explanation": "Only split is [-36] and [36] -> |-36 - 36| = 72."},
    ],
    constraints=["1 <= n <= 15", "len(nums) == 2 * n", "-10^7 <= nums[i] <= 10^7"],
    starter="""
def minimumDifference(nums: list[int]) -> int:
    # Write your Meet-in-the-Middle grouped by element count solution here
    pass
""",
    solution="""
import bisect


def minimumDifference(nums: list[int]) -> int:
    n = len(nums) // 2
    total = sum(nums)

    def grouped_sums(arr: list[int]) -> list[list[int]]:
        by_k: list[set[int]] = [set() for _ in range(len(arr) + 1)]
        by_k[0].add(0)
        for x in arr:
            for k in range(len(arr) - 1, -1, -1):
                if by_k[k]:
                    by_k[k + 1].update(s + x for s in by_k[k])
        return [sorted(s) for s in by_k]

    left_by_k = grouped_sums(nums[:n])
    right_by_k = grouped_sums(nums[n:])
    target = total / 2
    best = float("inf")
    for k in range(n + 1):
        r_list = right_by_k[n - k]
        for ls in left_by_k[k]:
            need = target - ls
            idx = bisect.bisect_left(r_list, need)
            if idx < len(r_list):
                s1 = ls + r_list[idx]
                best = min(best, abs(total - 2 * s1))
            if idx > 0:
                s1 = ls + r_list[idx - 1]
                best = min(best, abs(total - 2 * s1))
            if best == 0:
                return 0
    return int(best)
""",
    visible=[
        {"label": "n=2 standard", "args": [[3, 9, 7, 3]], "expected": 2},
        {"label": "n=1 opposites", "args": [[-36, 36]], "expected": 72},
        {"label": "n=3 exact zero diff", "args": [[2, -1, 0, 4, -2, -9]], "expected": 0},
    ],
    hidden=[
        {"label": "All equal elements", "args": [[5, 5, 5, 5]], "expected": 0, "category": "Symmetric Input", "edgeReason": "Equal halves give difference 0."},
        {"label": "All negative numbers", "args": [[-10, -2, -5, -3]], "expected": 4, "category": "Negative Values", "edgeReason": "Best split is [-10, -2] (-12) vs [-5, -3] (-8), giving absolute difference 4."},
        {"label": "Large magnitude mix", "args": [[76, 8, 45, 20, 74, 84, 28, 1]], "expected": 2, "category": "Count Matching", "edgeReason": "Must pick exactly n=4 items total across both halves."},
        {"label": "Zero and positive", "args": [[0, 0, 0, 10]], "expected": 10, "category": "Sparse Non-Zero", "edgeReason": "One half must take 10, giving difference 10."},
        {"label": "n=5 balanced", "args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], "expected": 1, "category": "Odd Total Sum", "edgeReason": "Total sum 55 is odd, so minimum possible difference is 1."},
    ],
    trap="Unconstrained subset-sum meet-in-the-middle fails because the chosen subset MUST contain exactly `n` elements (not any count `0..2n`).",
    pivot="Split into two halves of length `n` and bucket each half's subset sums by how many elements `k` were picked (`0..n`). Pair every sum in `left[k]` exclusively with `right[n - k]` using binary search towards `total / 2`.",
    signal="Equal-cardinality subset partitioning with `2n <= 30` and negative/large values calls for Cardinality-Bucketed Meet-in-the-Middle.",
    hints=[
        "If one half sum is `s1`, the other half is `total - s1`, so the difference is `abs(total - 2 * s1)`.",
        "Group subset sums of `nums[:n]` by size `k` (`0..n`), and do the same for `nums[n:]`.",
        "If you pick `k` items from the left half, you must pick `n - k` items from the right half.",
    ],
    walkthrough="1. Split `nums` into `nums[:n]` and `nums[n:]`.\n2. Compute sorted subset sums bucketed by chosen count `k = 0..n` for each half.\n3. For each `k` and `ls` in `left_by_k[k]`, binary search `total / 2 - ls` in `right_by_k[n - k]`.\n4. Track `min(abs(total - 2 * (ls + rs)))`.",
    trace_steps=[
        {"step": 1, "focus": "Split [3,9] | [7,3]", "stateVars": "L[1]=[3,9] | R[1]=[3,7] | total=22", "note": "Each half bucket tracks exact element count k."},
        {"step": 2, "focus": "k=1, ls=9 -> need=2", "stateVars": "R[1][0]=3 -> s1=12 | diff=|22-24|=2", "note": "Choosing 9 + 3 = 12 vs 3 + 7 = 10 gives minimum difference 2."},
    ],
    brute_t="O(C(2N, N))",
    brute_s="O(N)",
    opt_t="O(N * 2^N)",
    opt_s="O(2^N)",
    derivation="Each half has only 2^N <= 32,768 subsets; pairing bucket `k` with `n - k` via binary search runs in O(N * 2^N).",
    followup_q="Why is `best == 0` safe to short-circuit, and what is the tightest lower bound when `total` is odd?",
    followup_a="Absolute difference cannot be below 0 (or 1 when `total` is odd), so stopping as soon as `best <= (total & 1)` trims work further.",
))


# Day 67: LC 785 - Is Graph Bipartite?
_reg(_mk(
    day=67,
    func="isBipartite",
    stmt=(
        "There is an undirected graph with `n` nodes numbered `0` to `n - 1`, given as an adjacency list `graph` where "
        "`graph[u]` is the list of nodes adjacent to `u`.\n\n"
        "A graph is bipartite if its nodes can be partitioned into two independent sets `A` and `B` such that every edge "
        "connects a node in `A` to a node in `B`.\n\n"
        "Return `True` if and only if the graph is bipartite."
    ),
    examples=[
        {"input": "graph = [[1,2,3],[0,2],[0,1,3],[0,2]]", "output": "False", "explanation": "Nodes 0, 1, 2 form an odd cycle (triangle), so 2-colouring fails."},
        {"input": "graph = [[1,3],[0,2],[1,3],[0,2]]", "output": "True", "explanation": "Partition into {0, 2} and {1, 3}."},
    ],
    constraints=["1 <= n <= 100", "No self-edges or parallel edges; graph may be disconnected."],
    starter="""
def isBipartite(graph: list[list[int]]) -> bool:
    # Write your O(V + E) 2-Colouring BFS solution here
    pass
""",
    solution="""
from collections import deque


def isBipartite(graph: list[list[int]]) -> bool:
    n = len(graph)
    colour = [0] * n  # 0 = unvisited, 1 and -1 = two groups
    for start in range(n):
        if colour[start] != 0:
            continue
        colour[start] = 1
        q = deque([start])
        while q:
            u = q.popleft()
            for v in graph[u]:
                if colour[v] == 0:
                    colour[v] = -colour[u]
                    q.append(v)
                elif colour[v] == colour[u]:
                    return False
    return True
""",
    visible=[
        {"label": "Triangle odd cycle", "args": [[[1, 2, 3], [0, 2], [0, 1, 3], [0, 2]]], "expected": False},
        {"label": "4-cycle even bipartite", "args": [[[1, 3], [0, 2], [1, 3], [0, 2]]], "expected": True},
    ],
    hidden=[
        {"label": "Disconnected with odd component", "args": [[[1], [0], [3, 4], [2, 4], [2, 3]]], "expected": False, "category": "Disconnected Graph", "edgeReason": "BFS must restart from every unvisited node, not just node 0."},
        {"label": "Isolated nodes only", "args": [[[], [], []]], "expected": True, "category": "Zero Edges", "edgeReason": "Graph with no edges is trivially bipartite."},
        {"label": "Single node", "args": [[[]]], "expected": True, "category": "Minimal Graph", "edgeReason": "One node with no edges returns True."},
        {"label": "5-cycle odd cycle", "args": [[[1, 4], [0, 2], [1, 3], [2, 4], [3, 0]]], "expected": False, "category": "Odd Cycle", "edgeReason": "Odd cycle of length 5 cannot be 2-coloured."},
        {"label": "Disconnected even components", "args": [[[1], [0], [], [4], [3]]], "expected": True, "category": "Multiple Components", "edgeReason": "Every disconnected component is individually bipartite."},
    ],
    trap="Starting BFS only from node `0` misses odd cycles hidden in disconnected components.",
    pivot="Iterate through every node `0..n-1`. For each uncoloured node, run BFS assigning alternating colours `+1` and `-1` to neighbours; any edge joining two same-coloured nodes proves an odd cycle exists.",
    signal="Splitting nodes into two conflict-free groups or detecting odd cycles in an undirected graph signals 2-Colouring BFS/DFS.",
    hints=[
        "A graph is bipartite if and only if it can be 2-coloured without adjacent nodes sharing a colour.",
        "Loop over all `start in range(n)` because the graph may be disconnected.",
        "Assign `colour[v] = -colour[u]` on discovery; return `False` immediately if `colour[v] == colour[u]`.",
    ],
    walkthrough="1. Create `colour = [0] * n`.\n2. For each uncoloured node `start`, set `colour[start] = 1` and run BFS.\n3. Colour unvisited neighbours `-colour[u]`; if a visited neighbour already has `colour[u]`, return `False`.\n4. Return `True` if all components succeed.",
    trace_steps=[
        {"step": 1, "focus": "Colour node 0 -> +1", "stateVars": "colour=[1,0,0,0] | q=[0]", "note": "Start BFS from node 0."},
        {"step": 2, "focus": "Visit neighbours 1, 3", "stateVars": "colour=[1,-1,0,-1] | q=[1,3]", "note": "Assign opposite colour -1."},
        {"step": 3, "focus": "Visit neighbour 2 from 1", "stateVars": "colour=[1,-1,1,-1] | no conflict -> True", "note": "All edges cross between +1 and -1 groups."},
    ],
    brute_t="O(2^V * E)",
    brute_s="O(V)",
    opt_t="O(V + E)",
    opt_s="O(V)",
    derivation="Each vertex enters the queue once and each undirected edge is inspected twice.",
    followup_q="How can you solve Is Graph Bipartite using Union-Find instead of BFS?",
    followup_a="For each node `u`, union all of `u`'s neighbours together; if any neighbour `v` ends up in the same component as `u`, return `False`.",
))


# Day 68: LC 815 - Bus Routes
_reg(_mk(
    day=68,
    func="numBusesToDestination",
    stmt=(
        "You are given an array `routes` representing bus routes where `routes[i]` is a cyclic list of stops that bus `i` visits.\n\n"
        "You start at bus stop `source` (not initially on any bus) and want to reach `target`. You may transfer between buses at shared stops.\n\n"
        "Return the least number of buses you must take to travel from `source` to `target`, or `-1` if impossible."
    ),
    examples=[
        {"input": "routes = [[1,2,7],[3,6,7]], source = 1, target = 6", "output": "2", "explanation": "Board bus 0 at stop 1, transfer at stop 7 to bus 1, alight at stop 6."},
        {"input": "routes = [[7,12],[4,5,15],[6],[15,19],[9,12,13]], source = 15, target = 12", "output": "-1", "explanation": "No chain of bus routes links stop 15 to stop 12."},
    ],
    constraints=["1 <= len(routes) <= 500", "Sum of len(routes[i]) <= 10^5", "0 <= source, target < 10^6"],
    starter="""
def numBusesToDestination(routes: list[list[int]], source: int, target: int) -> int:
    # Write your Route-Node BFS solution here
    pass
""",
    solution="""
from collections import defaultdict, deque


def numBusesToDestination(routes: list[list[int]], source: int, target: int) -> int:
    if source == target:
        return 0
    stop_to_routes: dict[int, list[int]] = defaultdict(list)
    for r_idx, stops in enumerate(routes):
        for s in stops:
            stop_to_routes[s].append(r_idx)

    visited_stops = {source}
    visited_routes: set[int] = set()
    q = deque([(source, 0)])
    while q:
        stop, buses = q.popleft()
        for r_idx in stop_to_routes.get(stop, ()):
            if r_idx in visited_routes:
                continue
            visited_routes.add(r_idx)
            for nxt_stop in routes[r_idx]:
                if nxt_stop == target:
                    return buses + 1
                if nxt_stop not in visited_stops:
                    visited_stops.add(nxt_stop)
                    q.append((nxt_stop, buses + 1))
    return -1
""",
    visible=[
        {"label": "Two-bus transfer", "args": [[[1, 2, 7], [3, 6, 7]], 1, 6], "expected": 2},
        {"label": "Disconnected routes", "args": [[[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]], 15, 12], "expected": -1},
    ],
    hidden=[
        {"label": "Source equals target", "args": [[[1, 2, 3]], 2, 2], "expected": 0, "category": "Zero Transfers", "edgeReason": "Already at destination requires 0 buses, even if stop is not on any route."},
        {"label": "Source == target absent from routes", "args": [[[1, 2]], 99, 99], "expected": 0, "category": "Zero-Cost Guard", "edgeReason": "Must check source == target before looking up routes."},
        {"label": "Direct single bus", "args": [[[1, 2, 3, 4], [4, 5]], 1, 4], "expected": 1, "category": "Single Bus", "edgeReason": "Target reachable on the first bus returns 1."},
        {"label": "Three-hop chain", "args": [[[1, 2], [2, 3], [3, 4], [1, 5]], 1, 4], "expected": 3, "category": "Multi-Hop Shortest", "edgeReason": "BFS guarantees minimum number of transfers."},
        {"label": "Unreachable target stop", "args": [[[1, 2, 3]], 1, 9], "expected": -1, "category": "Missing Target", "edgeReason": "Returns -1 cleanly when target is unreachable."},
    ],
    trap="Building an all-pairs stop-to-stop adjacency list creates O(S^2) edges when a single route has thousands of stops, blowing up memory and time.",
    pivot="Treat each bus route as a hyperedge via `stop_to_routes[stop] -> [route_ids]`. Mark BOTH `visited_routes` and `visited_stops` in BFS so every route's stop list is scanned at most once.",
    signal="Shortest path measured in 'number of groups/routes/lines used' rather than individual stops signals Hypergraph Route-Node BFS.",
    hints=[
        "First handle `if source == target: return 0`.",
        "Build an inverted index `stop_to_routes[stop] = [route indices]`.",
        "Track `visited_routes` so once you board bus `r`, you never scan `routes[r]` again.",
    ],
    walkthrough="1. Return 0 immediately if `source == target`.\n2. Map each stop to all route indices passing through it.\n3. BFS from `(source, 0)`; for each unvisited route at `stop`, mark it visited and enqueue all unvisited stops on that route with `buses + 1`.\n4. Return `buses + 1` as soon as `target` is reached, or `-1` if BFS exhausts.",
    trace_steps=[
        {"step": 1, "focus": "Build stop_to_routes", "stateVars": "stop 7 -> [route 0, route 1]", "note": "Stop 7 bridges bus 0 and bus 1."},
        {"step": 2, "focus": "BFS pop (stop=1, buses=0)", "stateVars": "board route 0 -> enqueue stops 2, 7 (buses=1)", "note": "Route 0 marked visited."},
        {"step": 3, "focus": "BFS pop (stop=7, buses=1)", "stateVars": "board route 1 -> hits target 6 -> return 2", "note": "Minimum 2 buses found."},
    ],
    brute_t="O(R * S^2)",
    brute_s="O(S^2)",
    opt_t="O(sum(len(routes[i])))",
    opt_s="O(sum(len(routes[i])))",
    derivation="Every route is expanded at most once and every stop is enqueued at most once.",
    followup_q="How would you adapt this if each bus route had a different ticket cost instead of uniform cost 1?",
    followup_a="Replace the FIFO queue with a min-heap (Dijkstra) keyed by cumulative fare paid so far.",
))


# Day 71: LC 1631 - Path With Minimum Effort
_reg(_mk(
    day=71,
    func="minimumEffortPath",
    stmt=(
        "You are given a 2D `heights` grid of size `rows x cols`, where `heights[r][c]` is the elevation of cell `(r, c)`.\n\n"
        "You start at top-left `(0, 0)` and want to travel to bottom-right `(rows - 1, cols - 1)` moving up, down, left, or right. "
        "A path's effort is the maximum absolute elevation difference between any two consecutive cells along the path.\n\n"
        "Return the minimum effort required to travel from `(0, 0)` to `(rows - 1, cols - 1)`."
    ),
    examples=[
        {"input": "heights = [[1,2,2],[3,8,2],[5,3,5]]", "output": "2", "explanation": "Path 1 -> 3 -> 5 -> 3 -> 5 has consecutive differences <= 2."},
        {"input": "heights = [[1,2,3],[3,8,4],[5,3,5]]", "output": "1", "explanation": "Path 1 -> 2 -> 3 -> 4 -> 5 has maximum step difference 1."},
    ],
    constraints=["1 <= rows, cols <= 100", "1 <= heights[r][c] <= 10^6"],
    starter="""
def minimumEffortPath(heights: list[list[int]]) -> int:
    # Write your O(R*C log(R*C)) Minimax Dijkstra solution here
    pass
""",
    solution="""
import heapq


def minimumEffortPath(heights: list[list[int]]) -> int:
    rows, cols = len(heights), len(heights[0])
    dist = [[float("inf")] * cols for _ in range(rows)]
    dist[0][0] = 0
    heap: list[tuple[int, int, int]] = [(0, 0, 0)]
    while heap:
        effort, r, c = heapq.heappop(heap)
        if effort > dist[r][c]:
            continue
        if r == rows - 1 and c == cols - 1:
            return effort
        cur_h = heights[r][c]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nxt_eff = max(effort, abs(heights[nr][nc] - cur_h))
                if nxt_eff < dist[nr][nc]:
                    dist[nr][nc] = nxt_eff
                    heapq.heappush(heap, (nxt_eff, nr, nc))
    return 0
""",
    visible=[
        {"label": "Effort 2 around cliff", "args": [[[1, 2, 2], [3, 8, 2], [5, 3, 5]]], "expected": 2},
        {"label": "Effort 1 smooth ridge", "args": [[[1, 2, 3], [3, 8, 4], [5, 3, 5]]], "expected": 1},
        {"label": "Zero-effort flat path", "args": [[[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]]], "expected": 0},
    ],
    hidden=[
        {"label": "1x1 grid", "args": [[[7]]], "expected": 0, "category": "Minimal Grid", "edgeReason": "Start equals end -> effort 0."},
        {"label": "Single row", "args": [[[1, 10, 6, 7, 9, 10, 4, 9]]], "expected": 9, "category": "1D Corridor", "edgeReason": "Only one path exists; max adjacent diff is 9."},
        {"label": "Single column", "args": [[[1], [5], [2], [10]]], "expected": 8, "category": "1D Column", "edgeReason": "Must climb 2 -> 10 (diff 8)."},
        {"label": "Requires moving up/left detour", "args": [[[1, 100, 1, 1, 1], [1, 100, 1, 100, 1], [1, 1, 1, 100, 1]]], "expected": 0, "category": "Non-Monotonic Path", "edgeReason": "Simple DP (only right/down) fails because optimal path moves upward."},
        {"label": "Large jump cliff", "args": [[[1, 1000000], [1000000, 1]]], "expected": 999999, "category": "Large Magnitude", "edgeReason": "Tests large elevation differences cleanly."},
    ],
    trap="Using top-down or bottom-up grid DP assuming you only move right and down fails when the minimum-effort route detours up or left around a cliff.",
    pivot="Run Minimax Dijkstra: treat each edge weight as `abs(h[nr][nc] - h[r][c])` and relax `new_effort = max(cur_effort, edge_weight)`. Popping `(rows - 1, cols - 1)` guarantees global optimality.",
    signal="Minimising the maximum edge weight along a 4-directional grid path signals Minimax Dijkstra (or Binary Search + BFS).",
    hints=[
        "Standard grid DP fails because paths can snake up and left.",
        "Dijkstra works for ANY monotonic path cost, including `max(path_effort, step_diff)`.",
        "Skip stale heap entries (`if effort > dist[r][c]: continue`) and return immediately when popping `(rows - 1, cols - 1)`.",
    ],
    walkthrough="1. Initialise `dist[0][0] = 0` and push `(0, 0, 0)` into a min-heap.\n2. Pop the cell with minimum bottleneck effort so far; if it is the target cell, return immediately.\n3. Relax all 4 neighbours using `max(effort, abs(heights[nr][nc] - heights[r][c]))`.",
    trace_steps=[
        {"step": 1, "focus": "Pop (0,0) eff=0", "stateVars": "push (1,0,1) & (2,1,0)", "note": "Neighbours have elevation diffs 1 and 2."},
        {"step": 2, "focus": "Explore ridge eff<=2", "stateVars": "dist[2][2] updated via (2,1)->(2,2) eff=2", "note": "Avoids cliff cell (1,1)=8."},
        {"step": 3, "focus": "Pop (2,2) eff=2", "stateVars": "return 2", "note": "First time target is popped is guaranteed optimal."},
    ],
    brute_t="O(4^(R*C))",
    brute_s="O(R*C)",
    opt_t="O(R*C log(R*C))",
    opt_s="O(R*C)",
    derivation="Each cell and its 4 edges relax at most O(R*C) heap operations costing O(log(R*C)) each.",
    followup_q="How can Kruskal's Union-Find also solve this problem?",
    followup_a="Sort all grid edges by elevation difference ascending and union endpoints until `(0, 0)` and `(rows - 1, cols - 1)` become connected; that edge's weight is the answer.",
))


# Day 72: LC 1368 - Minimum Cost to Make at Least One Valid Path in a Grid
_reg(_mk(
    day=72,
    func="minCost",
    stmt=(
        "Given an `m x n` `grid`, each cell has a sign pointing to the next cell:\n"
        "- `1`: go right (`c + 1`)\n"
        "- `2`: go left (`c - 1`)\n"
        "- `3`: go down (`r + 1`)\n"
        "- `4`: go up (`r - 1`)\n\n"
        "You start at `(0, 0)` and want to reach `(m - 1, n - 1)`. Following a cell's existing arrow costs `0`, while changing "
        "a cell's arrow to another direction costs `1`. Return the minimum total cost to create at least one valid path."
    ),
    examples=[
        {"input": "grid = [[1,1,1,1],[2,2,2,2],[1,1,1,1],[2,2,2,2]]", "output": "3", "explanation": "Change the arrow at the end of rows 0, 1, and 2 to move down -> cost 3."},
        {"input": "grid = [[1,1,3],[3,2,2],[1,1,4]]", "output": "0", "explanation": "Existing arrows already lead from (0,0) to (2,2) with cost 0."},
    ],
    constraints=["1 <= m, n <= 100", "1 <= grid[i][j] <= 4"],
    starter="""
def minCost(grid: list[list[int]]) -> int:
    # Write your O(M * N) 0-1 BFS (Deque) solution here
    pass
""",
    solution="""
from collections import deque


def minCost(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    dirs = ((1, 0, 1), (2, 0, -1), (3, 1, 0), (4, -1, 0))
    dist = [[float("inf")] * n for _ in range(m)]
    dist[0][0] = 0
    dq = deque([(0, 0)])
    while dq:
        r, c = dq.popleft()
        cur_d = dist[r][c]
        if r == m - 1 and c == n - 1:
            return cur_d
        sign = grid[r][c]
        for code, dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n:
                w = 0 if code == sign else 1
                if cur_d + w < dist[nr][nc]:
                    dist[nr][nc] = cur_d + w
                    if w == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))
    return int(dist[m - 1][n - 1])
""",
    visible=[
        {"label": "Three row drops needed", "args": [[[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1], [2, 2, 2, 2]]], "expected": 3},
        {"label": "Zero-cost valid path", "args": [[[1, 1, 3], [3, 2, 2], [1, 1, 4]]], "expected": 0},
        {"label": "Single flip needed", "args": [[[1, 2], [4, 3]]], "expected": 1},
    ],
    hidden=[
        {"label": "1x1 grid", "args": [[[4]]], "expected": 0, "category": "Minimal Grid", "edgeReason": "Already at destination -> cost 0."},
        {"label": "All pointing away", "args": [[[2, 2], [4, 4]]], "expected": 2, "category": "Full Override", "edgeReason": "Must flip two arrows to reach (1,1)."},
        {"label": "Single row mixed arrows", "args": [[[1, 2, 1, 2, 1]]], "expected": 2, "category": "1D Row", "edgeReason": "Must flip both left-pointing arrows to right."},
        {"label": "Single column mixed arrows", "args": [[[3], [4], [3], [4]]], "expected": 1, "category": "1D Column", "edgeReason": "Only cell (1,0) needs flipping (destination arrow irrelevant)."},
        {"label": "Spiral zero-cost path", "args": [[[1, 1, 3], [1, 3, 3], [4, 2, 2]]], "expected": 0, "category": "Zero-Cost Detour", "edgeReason": "0-weight edges popped from front of deque first."},
    ],
    trap="Using standard Dijkstra works in O(MN log(MN)) but overlooks that edge weights are strictly binary `{0, 1}`, and standard BFS fails because 0-cost moves and 1-cost moves mix.",
    pivot="Use 0-1 BFS with a `deque`: push 0-cost (matching arrow) neighbours to the FRONT (`appendleft`) and 1-cost (modified arrow) neighbours to the BACK (`append`), keeping the deque sorted by distance in O(1) per edge.",
    signal="Shortest path on a graph whose edge weights are strictly `0` or `1` signals 0-1 BFS with a deque.",
    hints=[
        "Model each cell as a node with 4 directed edges: weight `0` in `grid[r][c]`'s direction, weight `1` in the other 3 directions.",
        "In 0-1 BFS, relax neighbours just like Dijkstra, pushing weight-0 transitions to `deque.appendleft` and weight-1 transitions to `deque.append`.",
        "Because every edge adds 0 or 1, the deque stays monotonically non-decreasing without needing a heap.",
    ],
    walkthrough="1. Set `dist[0][0] = 0` and initialise `dq = deque([(0, 0)])`.\n2. Pop `(r, c)` from the left; stop early if `(m - 1, n - 1)` is reached.\n3. For each of the 4 directions, compute `w = 0 if code == grid[r][c] else 1`; if `dist[r][c] + w < dist[nr][nc]`, update and push left (if 0) or right (if 1).",
    trace_steps=[
        {"step": 1, "focus": "Start (0,0) sign=1 (right)", "stateVars": "dist[0][1]=0 (front) | dist[1][0]=1 (back)", "note": "Zero-cost move right jumps to front of deque."},
        {"step": 2, "focus": "Follow row 0 at cost 0", "stateVars": "dist[0][0..3] = 0", "note": "Entire free chain explored before any cost-1 change."},
        {"step": 3, "focus": "Pay cost 1 at (0,3) down", "stateVars": "dist[1][3] = 1 -> reaches (3,3) cost 3", "note": "0-1 BFS finishes in linear O(M * N) time."},
    ],
    brute_t="O(MN log(MN))",
    brute_s="O(MN)",
    opt_t="O(M * N)",
    opt_s="O(M * N)",
    derivation="Each cell's distance improves at most once via 0-weight and once via 1-weight deque transitions, giving O(M * N) time.",
    followup_q="What if edge weights were small integers in `{0, 1, 2, ..., K}` instead of just `{0, 1}`?",
    followup_a="Generalise 0-1 BFS to Dial's Algorithm using `K + 1` circular buckets to keep O(V + E + K) time without heap overhead.",
))


# Day 75: LC 2097 - Valid Arrangement of Pairs
_reg(_mk(
    day=75,
    func="validArrangement",
    stmt=(
        "You are given a 2D integer array `pairs` where `pairs[i] = [start_i, end_i]`. An arrangement of `pairs` is valid if "
        "for every index `i` from `1` to `len(pairs) - 1`, `end_{i-1} == start_i`.\n\n"
        "Return a valid arrangement of `pairs`. Every test case has a unique valid Eulerian path arrangement (or deterministic sorted-edge tour)."
    ),
    examples=[
        {"input": "pairs = [[5,1],[4,5],[11,9],[9,4]]", "output": "[[11,9],[9,4],[4,5],[5,1]]", "explanation": "Each pair's end matches the next pair's start: 11->9->4->5->1."},
        {"input": "pairs = [[1,2],[2,3],[3,4]]", "output": "[[1,2],[2,3],[3,4]]", "explanation": "Linear directed Eulerian path."},
    ],
    constraints=["1 <= len(pairs) <= 10^5", "0 <= start_i, end_i <= 10^9", "A valid arrangement always exists."],
    starter="""
def validArrangement(pairs: list[list[int]]) -> list[list[int]]:
    # Write your O(E) Hierholzer Directed Eulerian Path solution here
    pass
""",
    solution="""
from collections import defaultdict


def validArrangement(pairs: list[list[int]]) -> list[list[int]]:
    adj: dict[int, list[int]] = defaultdict(list)
    out_deg: dict[int, int] = defaultdict(int)
    in_deg: dict[int, int] = defaultdict(int)
    for u, v in pairs:
        adj[u].append(v)
        out_deg[u] += 1
        in_deg[v] += 1
    for u in adj:
        adj[u].sort(reverse=True)

    start = pairs[0][0]
    for node in sorted(out_deg):
        if out_deg[node] - in_deg[node] == 1:
            start = node
            break

    stack = [start]
    path: list[int] = []
    while stack:
        while adj[stack[-1]]:
            stack.append(adj[stack[-1]].pop())
        path.append(stack.pop())
    path.reverse()
    return [[path[i], path[i + 1]] for i in range(len(path) - 1)]
""",
    visible=[
        {"label": "Scrambled 4-pair chain", "args": [[[5, 1], [4, 5], [11, 9], [9, 4]]], "expected": [[11, 9], [9, 4], [4, 5], [5, 1]]},
        {"label": "Already ordered", "args": [[[1, 2], [2, 3], [3, 4]]], "expected": [[1, 2], [2, 3], [3, 4]]},
    ],
    hidden=[
        {"label": "Single pair", "args": [[[7, 8]]], "expected": [[7, 8]], "category": "Minimal Input", "edgeReason": "Single directed edge returns itself."},
        {"label": "Chain with side loop", "args": [[[1, 2], [2, 2], [2, 3]]], "expected": [[1, 2], [2, 2], [2, 3]], "category": "Self-Loop Detour", "edgeReason": "Hierholzer post-order absorbs the 2->2 loop before heading to 3."},
        {"label": "Eulerian circuit", "args": [[[1, 2], [2, 3], [3, 1]]], "expected": [[1, 2], [2, 3], [3, 1]], "category": "Closed Circuit", "edgeReason": "When all nodes have out_deg == in_deg, start from a valid vertex."},
        {"label": "Bridge with inner cycle", "args": [[[1, 2], [2, 3], [3, 2], [2, 4]]], "expected": [[1, 2], [2, 3], [3, 2], [2, 4]], "category": "Backtracking Trap", "edgeReason": "Greedy DFS taking 2->4 first gets stuck; Hierholzer splices 2->3->2 cleanly."},
        {"label": "Large node IDs", "args": [[[1000000000, 500000000], [500000000, 0]]], "expected": [[1000000000, 500000000], [500000000, 0]], "category": "Sparse IDs", "edgeReason": "Adjacency dict handles sparse 10^9 node IDs cleanly."},
    ],
    trap="Greedy DFS fails when it enters the terminal dead-end edge before traversing a side cycle attached to an intermediate vertex.",
    pivot="Model each pair `[u, v]` as a directed edge `u -> v` and find a Directed Eulerian Path via Hierholzer's iterative post-order stack algorithm, starting at the unique vertex with `out_deg - in_deg == 1` (or any node if it is a closed circuit).",
    signal="Chaining every directed pair/domino end-to-end exactly once is a Directed Eulerian Path problem (Hierholzer's Algorithm).",
    hints=[
        "Count `out_deg[u]` and `in_deg[v]` for all vertices. The start node has `out_deg[u] - in_deg[u] == 1`.",
        "Use an explicit stack: while `adj[stack[-1]]` is non-empty, pop an outgoing edge and push the neighbour.",
        "When stuck (no outgoing edges left), pop `stack[-1]` into `path`, then reverse `path` at the end and zip consecutive pairs.",
    ],
    walkthrough="1. Build adjacency lists and `in_deg` / `out_deg` maps.\n2. Pick the unique start node with `out_deg - in_deg == 1` (fallback to `pairs[0][0]` for closed circuits).\n3. Run iterative Hierholzer post-order traversal popping consumed edges.\n4. Reverse `path` and emit `[[path[i], path[i+1]]]`.",
    trace_steps=[
        {"step": 1, "focus": "Compute degrees", "stateVars": "out-in: 11->+1, 1->-1, others->0", "note": "Unique Eulerian start is vertex 11."},
        {"step": 2, "focus": "Consume edges on stack", "stateVars": "stack=[11,9,4,5,1]", "note": "Walk until dead end at vertex 1."},
        {"step": 3, "focus": "Pop post-order & reverse", "stateVars": "path=[11,9,4,5,1] -> [[11,9],[9,4],[4,5],[5,1]]", "note": "Every directed edge used exactly once in O(E) time."},
    ],
    brute_t="O(E!)",
    brute_s="O(E)",
    opt_t="O(E log E)",
    opt_s="O(E)",
    derivation="Each edge is pushed and popped from `adj` and `stack` once; sorting edges for deterministic order adds O(E log E) (or pure O(E) unsorted).",
    followup_q="Why is iterative Hierholzer strongly preferred over recursive DFS when `len(pairs) == 10^5`?",
    followup_a="A chain of 10^5 pairs exceeds Python's default recursion depth (~1000) and crashes with `RecursionError`; an explicit stack runs safely in O(E) heap space.",
))


# Day 88: LC 1547 - Minimum Cost to Cut a Stick
_reg(_mk(
    day=88,
    func="minCostCutStick",
    stmt=(
        "Given a wooden stick of length `n` units labelled from `0` to `n`, and an integer array `cuts` denoting positions "
        "where you must perform cuts (in any order).\n\n"
        "The cost of one cut is the length of the stick currently being cut, and the total cost is the sum of costs of all cuts. "
        "Return the minimum total cost of the cuts."
    ),
    examples=[
        {"input": "n = 7, cuts = [1, 3, 4, 5]", "output": "16", "explanation": "Cut in order [3, 5, 1, 4]: 7 + 4 + 3 + 2 = 16."},
        {"input": "n = 9, cuts = [5, 6, 1, 4, 2]", "output": "22", "explanation": "Optimal cut ordering achieves total cost 22."},
    ],
    constraints=["2 <= n <= 10^6", "1 <= len(cuts) <= min(n - 1, 100)", "All cuts are distinct and in [1, n - 1]."],
    starter="""
def minCostCutStick(n: int, cuts: list[int]) -> int:
    # Write your O(C^3) Interval DP solution here
    pass
""",
    solution="""
def minCostCutStick(n: int, cuts: list[int]) -> int:
    pts = [0] + sorted(cuts) + [n]
    m = len(pts)
    dp = [[0] * m for _ in range(m)]
    for length in range(2, m):
        for i in range(m - length):
            j = i + length
            span = pts[j] - pts[i]
            best = float("inf")
            for k in range(i + 1, j):
                cost = dp[i][k] + dp[k][j] + span
                if cost < best:
                    best = cost
            dp[i][j] = best
    return dp[0][m - 1]
""",
    visible=[
        {"label": "n=7, cuts=[1,3,4,5]", "args": [7, [1, 3, 4, 5]], "expected": 16},
        {"label": "n=9, cuts=[5,6,1,4,2]", "args": [9, [5, 6, 1, 4, 2]], "expected": 22},
    ],
    hidden=[
        {"label": "Single cut", "args": [10, [4]], "expected": 10, "category": "Single Cut", "edgeReason": "One cut always costs the full stick length n."},
        {"label": "Two cuts", "args": [10, [2, 8]], "expected": 18, "category": "Minimal Choice", "edgeReason": "Cutting at 2 then 8 costs 10 + 8 = 18."},
        {"label": "Large n small cuts", "args": [1000000, [100000, 500000, 900000]], "expected": 2000000, "category": "Coordinate Compression", "edgeReason": "DP must index by cut positions (<= 102), never by stick length n = 10^6."},
        {"label": "Unsorted cuts input", "args": [6, [5, 1, 3]], "expected": 12, "category": "Unsorted Input", "edgeReason": "Must sort cuts before building interval DP."},
        {"label": "Tight adjacent cuts", "args": [5, [1, 2, 3, 4]], "expected": 12, "category": "Every Unit Cut", "edgeReason": "Balanced binary split minimises total cost."},
    ],
    trap="Indexing DP by raw stick coordinates `dp[0..n][0..n]` blows up memory when `n = 10^6`, and greedy midpoint cutting fails on asymmetric cut spacing.",
    pivot="Pad and sort cut coordinates `pts = [0] + sorted(cuts) + [n]`. Define `dp[i][j]` as the minimum cost to perform all cuts strictly inside `(pts[i], pts[j])`: try every first cut `k` in `(i, j)` paying `(pts[j] - pts[i]) + dp[i][k] + dp[k][j]`.",
    signal="Choosing the optimal split order on an interval where cost depends on current segment length signals O(C^3) Interval DP.",
    hints=[
        "Never index DP by `n` (up to 10^6); index by the sorted array `pts = [0] + sorted(cuts) + [n]` of size `C + 2 <= 102`.",
        "Any stick segment `(pts[i], pts[j])` with `j - i == 1` has no cuts left inside, so `dp[i][j] = 0`.",
        "Fill `dp` in increasing order of interval span `length = j - i` from `2` to `m - 1`.",
    ],
    walkthrough="1. Build `pts = [0] + sorted(cuts) + [n]`.\n2. Base case: adjacent indices `j - i < 2` have cost 0.\n3. For `length` from `2` to `m - 1`, compute `dp[i][j] = (pts[j] - pts[i]) + min(dp[i][k] + dp[k][j])`.\n4. Return `dp[0][m - 1]`.",
    trace_steps=[
        {"step": 1, "focus": "pts = [0,1,3,4,5,7]", "stateVars": "m=6 | base dp[i][i+1]=0", "note": "Compressed from n=7 into 6 boundary points."},
        {"step": 2, "focus": "length=2 intervals", "stateVars": "dp[0][2]=3, dp[1][3]=3, dp[2][4]=2, dp[3][5]=3", "note": "Each length-2 interval contains exactly one cut."},
        {"step": 3, "focus": "Full span dp[0][5]", "stateVars": "best first cut k=2 (pos 3) -> 7 + 3 + 6 = 16", "note": "Returns optimal total cost 16."},
    ],
    brute_t="O(C!)",
    brute_s="O(C)",
    opt_t="O(C^3)",
    opt_s="O(C^2)",
    derivation="There are O(C^2) sub-intervals and each tries O(C) split points.",
    followup_q="Can O(C^3) be optimised further to O(C^2) for this exact recurrence?",
    followup_a="Yes! Because the cost function `pts[j] - pts[i]` satisfies the quadrangle inequality, Knuth's Optimisation bounds `opt[i][j-1] <= opt[i][j] <= opt[i+1][j]`, reducing total time to O(C^2).",
))


# Day 89: LC 847 - Shortest Path Visiting All Nodes
_reg(_mk(
    day=89,
    func="shortestPathLength",
    stmt=(
        "You have an undirected, connected graph of `n` nodes labelled from `0` to `n - 1`, given as an adjacency list `graph`.\n\n"
        "Return the length of the shortest path that visits every node. You may start and stop at any node, revisit nodes "
        "multiple times, and reuse edges."
    ),
    examples=[
        {"input": "graph = [[1,2,3],[0],[0],[0]]", "output": "4", "explanation": "One shortest path is [1, 0, 2, 0, 3] of length 4."},
        {"input": "graph = [[1],[0,2,4],[1,3,4],[2],[1,2]]", "output": "4", "explanation": "One shortest path is [0, 1, 4, 2, 3] of length 4."},
    ],
    constraints=["1 <= n <= 12", "graph is undirected and connected."],
    starter="""
def shortestPathLength(graph: list[list[int]]) -> int:
    # Write your O(N * 2^N) Bitmask BFS solution here
    pass
""",
    solution="""
from collections import deque


def shortestPathLength(graph: list[list[int]]) -> int:
    n = len(graph)
    if n <= 1:
        return 0
    full_mask = (1 << n) - 1
    q = deque((i, 1 << i, 0) for i in range(n))
    visited = {(i, 1 << i) for i in range(n)}
    while q:
        u, mask, steps = q.popleft()
        for v in graph[u]:
            nmask = mask | (1 << v)
            if nmask == full_mask:
                return steps + 1
            if (v, nmask) not in visited:
                visited.add((v, nmask))
                q.append((v, nmask, steps + 1))
    return 0
""",
    visible=[
        {"label": "Star graph n=4", "args": [[[1, 2, 3], [0], [0], [0]]], "expected": 4},
        {"label": "5-node graph", "args": [[[1], [0, 2, 4], [1, 3, 4], [2], [1, 2]]], "expected": 4},
    ],
    hidden=[
        {"label": "Single node", "args": [[[]]], "expected": 0, "category": "Minimal Graph", "edgeReason": "1 node is already visited in 0 steps."},
        {"label": "Two connected nodes", "args": [[[1], [0]]], "expected": 1, "category": "Single Edge", "edgeReason": "Single edge visits both nodes in 1 step."},
        {"label": "Complete graph K4", "args": [[[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]], "expected": 3, "category": "Hamiltonian Path", "edgeReason": "Visits all 4 nodes in n - 1 = 3 steps."},
        {"label": "Line path n=5", "args": [[[1], [0, 2], [1, 3], [2, 4], [3]]], "expected": 4, "category": "Multi-Source Start", "edgeReason": "Starting at endpoints 0 or 4 achieves 4 steps (starting in middle takes more)."},
        {"label": "Double-star tree", "args": [[[1, 2, 3], [0], [0], [0, 4, 5], [3], [3]]], "expected": 7, "category": "Tree Revisit", "edgeReason": "Requires backtracking out of dead-end leaves."},
    ],
    trap="Marking only visited nodes (without tracking which subset of nodes has been seen) blocks legal revisits needed on star/tree graphs.",
    pivot="Represent each BFS state as `(current_node, visited_bitmask)`. Seed the queue with ALL `(i, 1 << i, 0)` simultaneously (multi-source BFS) so the first state reaching `mask == (1 << n) - 1` is guaranteed shortest.",
    signal="`n <= 12` plus 'visit every node with revisits allowed' in an unweighted graph is a textbook Bitmask Multi-Source BFS.",
    hints=[
        "Because `n <= 12`, a bitmask of visited nodes fits in just `2^12 = 4096` states.",
        "Start BFS from every node `(i, 1 << i, 0)` simultaneously since any starting node is allowed.",
        "Track visited `(node, mask)` pairs so you can revisit a node whenever you arrive with a strictly richer set of visited nodes.",
    ],
    walkthrough="1. Guard `n <= 1` returning 0.\n2. Seed a deque and visited set with `(i, 1 << i, 0)` for all `i`.\n3. Pop `(u, mask, steps)`, expand neighbours `v` with `nmask = mask | (1 << v)`.\n4. Return `steps + 1` as soon as `nmask == (1 << n) - 1`.",
    trace_steps=[
        {"step": 1, "focus": "Seed all 4 nodes", "stateVars": "q=[(0,0001,0),(1,0010,0),(2,0100,0),(3,1000,0)]", "note": "Multi-source BFS tries every starting node in lockstep."},
        {"step": 2, "focus": "Expand steps 1..3", "stateVars": "masks grow to 3 bits set (e.g. (0, 0111, 3))", "note": "Revisits centre node 0 with richer masks."},
        {"step": 3, "focus": "Step 4: 0 -> 3", "stateVars": "nmask = 1111 == full_mask -> return 4", "note": "First full-mask state is globally shortest."},
    ],
    brute_t="O(N! * N)",
    brute_s="O(N)",
    opt_t="O(N^2 * 2^N)",
    opt_s="O(N * 2^N)",
    derivation="There are `N * 2^N` unique `(node, mask)` states, each examining at most `N` outgoing edges.",
    followup_q="How does this change if edges have positive weights instead of unit length 1?",
    followup_a="Run Floyd-Warshall for all-pairs shortest distances, then solve Travelling Salesman Bitmask DP `dp[mask][u]` in O(N^2 * 2^N).",
))


# Day 90: LC 1125 - Smallest Sufficient Team
_reg(_mk(
    day=90,
    func="smallestSufficientTeam",
    stmt=(
        "In a project, you have a list of required skills `req_skills` and a list of `people`, where `people[i]` is the list "
        "of skills person `i` possesses.\n\n"
        "A sufficient team is a subset of people such that for every required skill, at least one person on the team has it. "
        "Return the sorted list of indices of the smallest sufficient team (every test case has a unique minimum team size and tie-broken lexicographically earliest answer)."
    ),
    examples=[
        {
            "input": 'req_skills = ["java","nodejs","reactjs"], people = [["java"],["nodejs"],["nodejs","reactjs"]]',
            "output": "[0, 2]",
            "explanation": "Person 0 covers 'java' and Person 2 covers 'nodejs' + 'reactjs'.",
        }
    ],
    constraints=["1 <= len(req_skills) <= 16", "1 <= len(people) <= 60", "A sufficient team always exists."],
    starter="""
def smallestSufficientTeam(req_skills: list[str], people: list[list[str]]) -> list[int]:
    # Write your O(P * 2^S) Bitmask Set-Cover DP solution here
    pass
""",
    solution="""
def smallestSufficientTeam(req_skills: list[str], people: list[list[str]]) -> list[int]:
    skill_idx = {s: i for i, s in enumerate(req_skills)}
    full_mask = (1 << len(req_skills)) - 1
    dp: dict[int, list[int]] = {0: []}
    for i, skills in enumerate(people):
        pmask = 0
        for s in skills:
            if s in skill_idx:
                pmask |= 1 << skill_idx[s]
        if pmask == 0:
            continue
        for mask, team in list(dp.items()):
            nmask = mask | pmask
            if nmask == mask:
                continue
            cand = team + [i]
            if nmask not in dp or len(cand) < len(dp[nmask]):
                dp[nmask] = cand
    return sorted(dp[full_mask])
""",
    visible=[
        {
            "label": "3 skills 3 people",
            "args": [["java", "nodejs", "reactjs"], [["java"], ["nodejs"], ["nodejs", "reactjs"]]],
            "expected": [0, 2],
        },
        {
            "label": "Single generalist covers all",
            "args": [["a", "b", "c"], [["a"], ["b"], ["a", "b", "c"]]],
            "expected": [2],
        },
    ],
    hidden=[
        {"label": "People with empty skill lists", "args": [["a", "b"], [[], ["a"], [], ["b"]]], "expected": [1, 3], "category": "Zero-Skill Pruning", "edgeReason": "Skip people with pmask == 0 cleanly."},
        {"label": "One skill one person", "args": [["python"], [["python"]]], "expected": [0], "category": "Minimal Input", "edgeReason": "Single skill covered by person 0."},
        {"label": "Disjoint required specialists", "args": [["a", "b", "c"], [["a"], ["b"], ["c"]]], "expected": [0, 1, 2], "category": "All Required", "edgeReason": "All 3 people are needed."},
        {"label": "Subset dominance pruning", "args": [["a", "b", "c", "d"], [["a", "b"], ["c"], ["d"], ["a", "b", "c"]]], "expected": [2, 3], "category": "Optimal Cover", "edgeReason": "Unique 2-person cover [2, 3] beats 3-person cover [0, 1, 2]."},
        {"label": "Extra irrelevant skills", "args": [["x", "y"], [["z", "x"], ["w", "y"]]], "expected": [0, 1], "category": "Unknown Skills", "edgeReason": "Skills outside req_skills must be ignored without KeyError."},
    ],
    trap="Greedy set cover (always picking the person with the most uncovered skills) can pick 3 people when a 2-person exact cover exists.",
    pivot="Encode the `<= 16` required skills as a bitmask (`2^16 = 65,536` states). Run 0/1 Knapsack-style DP `dp[mask] = smallest team covering mask` iterating over each person's bitmask.",
    signal="Minimum Set Cover with universe size `<= 16` signals Bitmask DP over reachable masks.",
    hints=[
        "Map each required skill name to bit `0..S-1` and encode each person as an integer bitmask `pmask`.",
        "Maintain a dictionary `dp[mask] = best_team_list` starting with `{0: []}` so unreachable masks are never iterated.",
        "For each person with `pmask != 0`, combine with every existing `(mask, team)` in `list(dp.items())` and keep the shorter team for `mask | pmask`.",
    ],
    walkthrough="1. Map `req_skills` to bit positions `0..S-1`.\n2. Compute `pmask` for each person (skipping `pmask == 0`).\n3. Update `dp[mask | pmask]` whenever `len(team) + 1 < len(dp[mask | pmask])`.\n4. Return `sorted(dp[(1 << S) - 1])`.",
    trace_steps=[
        {"step": 1, "focus": "Person 0 (java -> 001)", "stateVars": "dp = {0:[], 001:[0]}", "note": "Covers bit 0."},
        {"step": 2, "focus": "Person 1 (nodejs -> 010)", "stateVars": "dp adds 010:[1], 011:[0,1]", "note": "Two-person partial cover."},
        {"step": 3, "focus": "Person 2 (nodejs+react -> 110)", "stateVars": "001 | 110 = 111 -> [0,2]", "note": "Full mask 111 achieved with size 2 -> [0, 2]."},
    ],
    brute_t="O(2^P)",
    brute_s="O(P)",
    opt_t="O(P * 2^S)",
    opt_s="O(2^S)",
    derivation="Each of P people updates at most 2^S bitmask states.",
    followup_q="How can you store `dp[mask]` as a single 64-bit integer instead of a Python list to cut memory and copying overhead?",
    followup_a="Since `len(people) <= 60`, store each team itself as a 60-bit person bitmask and compare `team_mask.bit_count()` in O(1).",
))


# Day 91: LC 486 - Predict the Winner
_reg(_mk(
    day=91,
    func="predictTheWinner",
    stmt=(
        "You are given an integer array `nums`. Players 1 and 2 take turns picking either the first or last number from the "
        "remaining array and adding it to their score (both start at 0).\n\n"
        "Return `True` if Player 1 can win or tie (`score1 >= score2`), assuming both players play optimally."
    ),
    examples=[
        {"input": "nums = [1, 5, 2]", "output": "False", "explanation": "Whether Player 1 takes 1 or 2, Player 2 takes 5 and wins 5 vs 3."},
        {"input": "nums = [1, 5, 233, 7]", "output": "True", "explanation": "Player 1 takes 1, forces Player 2 to expose 233, and wins 234 vs 12."},
    ],
    constraints=["1 <= len(nums) <= 20", "0 <= nums[i] <= 10^7"],
    starter="""
def predictTheWinner(nums: list[int]) -> bool:
    # Write your O(N^2) Minimax Interval DP solution here
    pass
""",
    solution="""
def predictTheWinner(nums: list[int]) -> bool:
    n = len(nums)
    dp = list(nums)
    for i in range(n - 2, -1, -1):
        for j in range(i + 1, n):
            dp[j] = max(nums[i] - dp[j], nums[j] - dp[j - 1])
    return dp[n - 1] >= 0
""",
    visible=[
        {"label": "Player 2 wins", "args": [[1, 5, 2]], "expected": False},
        {"label": "Player 1 wins", "args": [[1, 5, 233, 7]], "expected": True},
    ],
    hidden=[
        {"label": "Single element", "args": [[0]], "expected": True, "category": "Minimal Input", "edgeReason": "Player 1 takes the only element and wins/ties."},
        {"label": "Tie counts as win", "args": [[5, 5]], "expected": True, "category": "Tie Rule", "edgeReason": "Score 5 vs 5 is a tie, so Player 1 returns True."},
        {"label": "Even length always True", "args": [[1, 100, 1, 2]], "expected": True, "category": "Even Parity", "edgeReason": "With even length, Player 1 can force all odd or all even indices."},
        {"label": "Odd length middle spike", "args": [[2, 4, 55, 6, 8]], "expected": False, "category": "Odd Parity Trap", "edgeReason": "Player 2 captures 55 regardless of Player 1's opening move."},
        {"label": "All zeros", "args": [[0, 0, 0]], "expected": True, "category": "Zero Values", "edgeReason": "0 >= 0 returns True."},
    ],
    trap="Exploring both choices recursively without memoisation costs O(2^N), and tracking both players' absolute scores separately doubles state complexity unnecessarily.",
    pivot="Model the zero-sum score lead `dp[i][j]` = maximum `(current_player - opponent)` advantage on `nums[i..j]`: `dp[i][j] = max(nums[i] - dp[i+1][j], nums[j] - dp[i][j-1])`, compressed to O(N) space.",
    signal="Two-player zero-sum optimal play taking from either end of an array signals Minimax Interval DP on relative score difference.",
    hints=[
        "Define `dp[i][j]` as the best net lead the active player can achieve over the opponent on subarray `nums[i..j]`.",
        "If you take `nums[i]`, the opponent gets optimal lead `dp[i+1][j]` on the remainder, so your lead is `nums[i] - dp[i+1][j]`.",
        "Rolling `i` from `n - 2` down to `0` lets a 1D array `dp[j]` hold the table in O(N) space.",
    ],
    walkthrough="1. Initialise 1D `dp = list(nums)` representing length-1 intervals `dp[i][i] = nums[i]`.\n2. Loop `i` downwards from `n - 2` to `0`, and `j` from `i + 1` to `n - 1`.\n3. Update `dp[j] = max(nums[i] - dp[j], nums[j] - dp[j - 1])`.\n4. Return `dp[n - 1] >= 0`.",
    trace_steps=[
        {"step": 1, "focus": "nums = [1, 5, 2]", "stateVars": "dp = [1, 5, 2]", "note": "Base single-element leads."},
        {"step": 2, "focus": "i=1, j=2 ([5,2])", "stateVars": "dp[2] = max(5-2, 2-5) = 3", "note": "On [5,2], active player wins by 3."},
        {"step": 3, "focus": "i=0, j=2 ([1,5,2])", "stateVars": "dp[1]=4, dp[2]=max(1-3, 2-4)=-2 < 0 -> False", "note": "Player 1 loses by 2 under optimal play."},
    ],
    brute_t="O(2^N)",
    brute_s="O(N)",
    opt_t="O(N^2)",
    opt_s="O(N)",
    derivation="There are N*(N+1)/2 sub-intervals, each computed in O(1) using only the previous row.",
    followup_q="Can you immediately return `True` in O(1) whenever `len(nums)` is even?",
    followup_a="Yes! Colour indices alternating red/blue; Player 1 sums red vs blue and can always force taking every element of the higher-sum colour.",
))


# Day 92: LC 1140 - Stone Game II
_reg(_mk(
    day=92,
    func="stoneGameII",
    stmt=(
        "Alice and Bob continue their games with piles of stones. There are a number of piles arranged in a row, and each pile "
        "has a positive integer number of stones `piles[i]`.\n\n"
        "Alice and Bob take turns, with Alice starting first. Initially `M = 1`. On each player's turn, that player can take "
        "all the stones in the first `X` remaining piles, where `1 <= X <= 2 * M`. Then `M = max(M, X)`.\n\n"
        "Assuming both players play optimally, return the maximum number of stones Alice can get."
    ),
    examples=[
        {"input": "piles = [2, 7, 9, 4, 4]", "output": "10", "explanation": "Alice takes 1 pile (2), Bob takes 2 piles (7+9=16) or 1 pile (7) -> optimal play gives Alice 10."},
        {"input": "piles = [1, 2, 3, 4, 5, 100]", "output": "104", "explanation": "Alice takes 1 pile (1), forcing a sequence where she captures the 100 pile."},
    ],
    constraints=["1 <= len(piles) <= 100", "1 <= piles[i] <= 10^4"],
    starter="""
def stoneGameII(piles: list[int]) -> int:
    # Write your O(N^3) Suffix-Sum Minimax DP solution here
    pass
""",
    solution="""
from functools import lru_cache


def stoneGameII(piles: list[int]) -> int:
    n = len(piles)
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + piles[i]

    @lru_cache(maxsize=None)
    def dfs(i: int, m: int) -> int:
        if i + 2 * m >= n:
            return suffix[i]
        min_opp = float("inf")
        for x in range(1, 2 * m + 1):
            opp = dfs(i + x, max(m, x))
            if opp < min_opp:
                min_opp = opp
        return suffix[i] - min_opp

    return dfs(0, 1)
""",
    visible=[
        {"label": "Standard 5 piles", "args": [[2, 7, 9, 4, 4]], "expected": 10},
        {"label": "Heavy tail pile", "args": [[1, 2, 3, 4, 5, 100]], "expected": 104},
    ],
    hidden=[
        {"label": "Single pile", "args": [[42]], "expected": 42, "category": "Base Case", "edgeReason": "Alice takes the entire pile immediately since i + 2*M >= n."},
        {"label": "Two piles (take both)", "args": [[3, 9]], "expected": 12, "category": "Immediate Sweep", "edgeReason": "With M=1, Alice can take X=2 piles on turn 1."},
        {"label": "Three equal piles", "args": [[5, 5, 5]], "expected": 10, "category": "Equal Weights", "edgeReason": "Alice takes 2 piles (10), leaving 1 pile (5) for Bob."},
        {"label": "Descending piles", "args": [[100, 50, 10, 1]], "expected": 150, "category": "Greedy Trap", "edgeReason": "Alice takes 2 piles (150) leaving 11 for Bob."},
        {"label": "Alternating spikes", "args": [[1, 100, 1, 100, 1]], "expected": 102, "category": "Parity Strategy", "edgeReason": "Optimal X selection prevents Bob from sweeping both 100s."},
    ],
    trap="Evaluating moves greedily or tracking both Alice's and Bob's totals separately blows up the state space.",
    pivot="Precompute `suffix[i] = sum(piles[i:])`. Because total remaining stones is fixed, maximising your stones from state `(i, M)` is identical to `suffix[i] - min_{1<=x<=2M} dfs(i + x, max(M, x))`.",
    signal="Two-player zero-sum turn game over a suffix with variable step bound `M` signals Suffix-Sum Minimax Memoisation `dfs(i, M)`.",
    hints=[
        "Precompute `suffix[i]` so you know the exact sum of all remaining stones from index `i` onward in O(1).",
        "If `i + 2 * m >= n`, the active player can take ALL remaining piles, immediately returning `suffix[i]`.",
        "Otherwise choose `x` in `1..2*m` to minimise the opponent's best score `dfs(i + x, max(m, x))`.",
    ],
    walkthrough="1. Build `suffix[i] = sum(piles[i:])`.\n2. Memoise `dfs(i, m)` returning the maximum stones the current player can claim from `piles[i:]`.\n3. Short-circuit `suffix[i]` when `i + 2*m >= n`, otherwise return `suffix[i] - min(dfs(i + x, max(m, x)))`.",
    trace_steps=[
        {"step": 1, "focus": "suffix for [2,7,9,4,4]", "stateVars": "suffix = [26, 24, 17, 8, 4, 0]", "note": "Total stones remaining from every index."},
        {"step": 2, "focus": "Try x=1 vs x=2 at (0, 1)", "stateVars": "x=1 -> 26 - dfs(1,1)=10 | x=2 -> 26 - dfs(2,2)=9", "note": "Taking 1 pile leaves Bob with max 16, giving Alice 10."},
    ],
    brute_t="O(2^N)",
    brute_s="O(N)",
    opt_t="O(N^3)",
    opt_s="O(N^2)",
    derivation="There are O(N^2) `(i, M)` states (since `M <= N`) and each loops over up to `2M <= N` choices.",
    followup_q="How can you tighten the upper bound on `M` in the memo table?",
    followup_a="Whenever `i + 2*m >= n` we return `suffix[i]` immediately, so `m` only needs to be stored up to `(n - i) // 2`.",
))


# Day 93: LC 877 - Stone Game
_reg(_mk(
    day=93,
    func="stoneGame",
    stmt=(
        "Alice and Bob play a game with an even number of piles of stones `piles`, arranged in a row. "
        "Each pile has a positive integer number of stones `piles[i]`, and the total number of stones across all piles is odd, "
        "so there are no ties.\n\n"
        "Alice goes first. On each turn, a player takes the entire pile from either the beginning or the end of the row. "
        "Assuming both players play optimally, return `True` if Alice wins, or `False` if Bob wins."
    ),
    examples=[
        {"input": "piles = [5, 3, 4, 5]", "output": "True", "explanation": "Alice can take all even-indexed piles (5+4=9) or all odd-indexed piles (3+5=8) and always wins."},
        {"input": "piles = [3, 7, 2, 3]", "output": "True", "explanation": "Alice forces odd-indexed piles (7+3=10 > 3+2=5)."},
    ],
    constraints=["2 <= len(piles) <= 500", "len(piles) is even", "sum(piles) is odd"],
    starter="""
def stoneGame(piles: list[int]) -> bool:
    # Write your Interval DP or O(1) Parity Invariant solution here
    pass
""",
    solution="""
def stoneGame(piles: list[int]) -> bool:
    n = len(piles)
    dp = list(piles)
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i] = max(piles[i] - dp[i + 1], piles[j] - dp[i])
    return dp[0] > 0
""",
    visible=[
        {"label": "Standard 4 piles", "args": [[5, 3, 4, 5]], "expected": True},
        {"label": "Hidden spike in middle", "args": [[3, 7, 2, 3]], "expected": True},
    ],
    hidden=[
        {"label": "Two piles", "args": [[1, 2]], "expected": True, "category": "Minimal Even Length", "edgeReason": "Alice takes the larger of two piles."},
        {"label": "Heavy inner odd index", "args": [[1, 100, 1, 1]], "expected": True, "category": "Parity Forcing", "edgeReason": "Alice takes right end (index 3), forcing Bob to expose index 1 (100)."},
        {"label": "Heavy inner even index", "args": [[1, 1, 100, 1]], "expected": True, "category": "Mirror Parity", "edgeReason": "Alice takes left end (index 0), forcing Bob to expose index 2 (100)."},
        {"label": "Six piles", "args": [[2, 9, 4, 1, 8, 3]], "expected": True, "category": "Larger Even Row", "edgeReason": "Even-length odd-sum invariant holds for any even N."},
        {"label": "Alternating high low", "args": [[10, 1, 10, 1, 10, 2]], "expected": True, "category": "Parity Proof Check", "edgeReason": "Even indices sum 30 vs odd indices sum 4; Alice forces all even indices."},
    ],
    trap="Assuming Alice must greedily pick the larger endpoint (`max(piles[0], piles[-1])`) fails on `[3, 7, 2, 3]` if you pick the wrong `3`, even though Alice can ALWAYS win with parity control.",
    pivot="Either prove the O(1) Parity Invariant (Alice colours indices even/odd; since `sum` is odd, one parity strictly exceeds the other and Alice can force every pile of that colour) or run general O(N^2) Minimax Interval DP `dp[i][j] = max(piles[i] - dp[i+1][j], piles[j] - dp[i][j-1])` that also handles odd-length follow-ups.",
    signal="Even number of piles with odd total sum and endpoint removal has an exact colouring invariant (`return True`), while the general version uses Minimax Interval DP.",
    hints=[
        "Label indices alternating Even (`0, 2, 4...`) and Odd (`1, 3, 5...`). Because `len(piles)` is even, index `0` is Even and `n - 1` is Odd.",
        "If Alice picks index `0` (Even), both exposed ends for Bob are Odd; whichever Bob picks, Alice gets another Even pile!",
        "Writing the Interval DP `dp[i][j]` is great practice because interviewers immediately ask 'what if N is odd?' (LC 486).",
    ],
    walkthrough="1. Define `dp[i][j]` as the maximum lead `(active - opponent)` over `piles[i..j]`.\n2. Transition `dp[i][j] = max(piles[i] - dp[i+1][j], piles[j] - dp[i][j-1])`.\n3. Return `dp[0][n - 1] > 0` (which mathematically always evaluates to `True` for even `N` and odd sum).",
    trace_steps=[
        {"step": 1, "focus": "Colour [3, 7, 2, 3]", "stateVars": "even sum = 3+2 = 5 | odd sum = 7+3 = 10", "note": "Odd indices beat even indices (10 > 5)."},
        {"step": 2, "focus": "Alice picks index 3 (Odd)", "stateVars": "remaining [3, 7, 2] -> ends are both Even!", "note": "Bob is forced to take an Even pile, handing Alice the 7."},
    ],
    brute_t="O(2^N)",
    brute_s="O(N)",
    opt_t="O(1) parity / O(N^2) general DP",
    opt_s="O(1) / O(N)",
    derivation="The colouring proof runs in O(1); the general DP evaluates O(N^2) subarrays in O(N) rolling space.",
    followup_q="Why does the O(1) `return True` proof break down if `len(piles)` is odd?",
    followup_a="With odd `N`, both ends `0` and `n - 1` have Even index, so Alice cannot force Bob into a single colour parity, requiring full Interval DP.",
))


# Day 94: LC 843 - Guess the Word
_reg(_mk(
    day=94,
    func="minimaxGuessWord",
    stmt=(
        "You are given a list of unique 6-letter lowercase strings `words` and a hidden `secret` word inside `words`.\n\n"
        "On each turn, you select a candidate word `w` from the remaining pool using deterministic Minimax Entropy Elimination:\n"
        "- For each candidate `w` in the current pool, group all words in the pool by their positional character match count `0..6` against `w`, and compute `worst_bucket(w)` = maximum group size.\n"
        "- Choose the candidate `w` that minimises `worst_bucket(w)` (breaking ties by lexicographically smallest word).\n"
        "- Query the oracle for `matches = sum(a == b for a, b in zip(w, secret))`. If `matches == 6`, stop.\n"
        "- Otherwise filter the pool to only words that share exactly `matches` positional characters with `w` and repeat.\n\n"
        "Return the exact number of guesses taken to find `secret`."
    ),
    examples=[
        {"input": 'words = ["acckzz","ccbazz","eiowzz","abcczz"], secret = "ccbazz"', "output": "2", "explanation": "Minimax picks 'acckzz' (max bucket 1 across all 4 words), gets 3 matches -> narrows directly to 'ccbazz' on guess 2."},
        {"input": 'words = ["hamada","khaled"], secret = "hamada"', "output": "1", "explanation": "Lex smallest minimax candidate is 'hamada', matching immediately in 1 guess."},
    ],
    constraints=["1 <= len(words) <= 100", "len(words[i]) == 6", "secret is guaranteed to be in words."],
    starter="""
def minimaxGuessWord(words: list[str], secret: str) -> int:
    # Write your Minimax Candidate Partitioning solution here
    pass
""",
    solution="""
def minimaxGuessWord(words: list[str], secret: str) -> int:
    def match_count(a: str, b: str) -> int:
        return sum(x == y for x, y in zip(a, b))

    pool = sorted(words)
    guesses = 0
    while pool:
        best_word = pool[0]
        best_worst = len(pool) + 1
        for cand in pool:
            buckets = [0] * 7
            for other in pool:
                buckets[match_count(cand, other)] += 1
            worst = max(buckets)
            if worst < best_worst:
                best_worst = worst
                best_word = cand
        guesses += 1
        m = match_count(best_word, secret)
        if m == 6:
            return guesses
        pool = [w for w in pool if match_count(w, best_word) == m]
    return guesses
""",
    visible=[
        {"label": "Classic 4-word pool", "args": [["acckzz", "ccbazz", "eiowzz", "abcczz"], "ccbazz"], "expected": 2},
        {"label": "Two-word immediate hit", "args": [["hamada", "khaled"], "hamada"], "expected": 1},
    ],
    hidden=[
        {"label": "Single word pool", "args": [["abcdef"], "abcdef"], "expected": 1, "category": "Minimal Pool", "edgeReason": "Pool of 1 always finds secret on guess 1."},
        {"label": "Two-word second pick", "args": [["hamada", "khaled"], "khaled"], "expected": 2, "category": "Tie-Break Order", "edgeReason": "Lex smallest 'hamada' is picked first, then 'khaled' on guess 2."},
        {"label": "Shared suffix family", "args": [["aaaaaa", "baaaaa", "caaaaa", "daaaaa", "eaaaaa", "faaaaa", "gaaaaa"], "gaaaaa"], "expected": 7, "category": "Worst-Case Star", "edgeReason": "All pairs share 5 matches, demonstrating the adversarial lower bound."},
        {"label": "Disjoint alphabet clusters", "args": [["abcdef", "abcxyz", "abpqrs", "mnopqr", "mnostu", "uvwxyz"], "uvwxyz"], "expected": 3, "category": "Entropy Split", "edgeReason": "Minimax narrows across disjoint clusters deterministically in 3 guesses."},
        {"label": "Mixed overlap 8 words", "args": [["gaxckt", "trlccr", "jxwhkz", "ycbfps", "peayuf", "yiejjw", "ldzccp", "nqsjoa"], "nqsjoa"], "expected": 2, "category": "Zero-Match Pruning", "edgeReason": "Eliminates words with non-matching overlap cleanly."},
    ],
    trap="Picking the first word in `words` blindly can repeatedly hit 0-match outliers and waste all 10 guesses; picking a word with too many 0-match neighbours leaves a giant surviving bucket.",
    pivot="Score every remaining candidate by its worst-case partition bucket size `max(count of words with k matches)` and choose the candidate that minimises that worst-case survivor count (Minimax Elimination).",
    signal="Interactive guessing game with a tight probe budget and feedback score signals Minimax worst-case bucket shrinking.",
    hints=[
        "Sort `pool` lexicographically so tie-breaking happens automatically when using strict `<`.",
        "For each `cand`, count how many words in `pool` have `0, 1, 2, 3, 4, 5, 6` positional matches with `cand`.",
        "Pick the `cand` minimising `max(buckets)`, query `m = match_count(best_word, secret)`, and keep only words matching `best_word` at `m` positions.",
    ],
    walkthrough="1. Sort `pool = sorted(words)`.\n2. On each round, compute a 7-bin match histogram for every candidate against `pool` and pick the candidate with smallest peak bin.\n3. Compare against `secret`; stop on 6 matches, else filter `pool` to words with exact match count `m`.",
    trace_steps=[
        {"step": 1, "focus": "Evaluate 4 candidates", "stateVars": "acckzz: max bucket=1 | abcczz: max bucket=2", "note": "Minimax strictly selects 'acckzz' because its worst bucket is 1."},
        {"step": 2, "focus": "Query 'acckzz' vs 'ccbazz'", "stateVars": "matches = 3 -> pool = ['ccbazz']", "note": "Only 'ccbazz' shares 3 matches with 'acckzz'; guess 2 wins."},
    ],
    brute_t="O(N) guesses",
    brute_s="O(N)",
    opt_t="O(G * N^2)",
    opt_s="O(N)",
    derivation="Each guess evaluates pairwise matches over the shrinking pool (`N <= 100`), finishing in G <= 10 rounds.",
    followup_q="Why is picking a candidate from the FULL original `words` list sometimes even better than restricting guesses to `pool`?",
    followup_a="An already-eliminated word can still act as a balanced discriminator that splits the surviving `pool` into smaller sub-buckets than any word inside `pool` itself.",
))


# Day 95: LC 307 - Range Sum Query - Mutable
_reg(_mk(
    day=95,
    func="NumArray",
    harness={"customDriver": "system-design", "className": "NumArray"},
    stmt=(
        "Given an integer array `nums`, implement the `NumArray` class to handle interleaved point updates and range sum queries:\n"
        "- `NumArray(nums: list[int])`: Initialises the object with `nums`.\n"
        "- `update(index: int, val: int) -> None`: Updates `nums[index]` to `val`.\n"
        "- `sumRange(left: int, right: int) -> int`: Returns the sum of elements between indices `left` and `right` inclusive."
    ),
    examples=[
        {
            "input": '["NumArray","sumRange","update","sumRange"], [[[1,3,5]],[0,2],[1,2],[0,2]]',
            "output": "[null, 9, null, 8]",
            "explanation": "sum(1,3,5)=9, update index 1 to 2 -> [1,2,5], sum(1,2,5)=8.",
        }
    ],
    constraints=["1 <= len(nums) <= 3 * 10^4", "-100 <= nums[i], val <= 100", "At most 3 * 10^4 calls to update and sumRange."],
    starter="""
class NumArray:
    def __init__(self, nums: list[int]):
        pass

    def update(self, index: int, val: int) -> None:
        pass

    def sumRange(self, left: int, right: int) -> int:
        pass
""",
    solution="""
class NumArray:
    def __init__(self, nums: list[int]):
        self.n = len(nums)
        self.nums = list(nums)
        self.bit = [0] * (self.n + 1)
        for i, v in enumerate(nums, 1):
            self.bit[i] += v
            parent = i + (i & -i)
            if parent <= self.n:
                self.bit[parent] += self.bit[i]

    def update(self, index: int, val: int) -> None:
        delta = val - self.nums[index]
        self.nums[index] = val
        i = index + 1
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i

    def _prefix(self, i: int) -> int:
        total = 0
        while i > 0:
            total += self.bit[i]
            i -= i & -i
        return total

    def sumRange(self, left: int, right: int) -> int:
        return self._prefix(right + 1) - self._prefix(left)
""",
    visible=[
        {
            "label": "Classic update and range query",
            "args": [["NumArray", "sumRange", "update", "sumRange"], [[[1, 3, 5]], [0, 2], [1, 2], [0, 2]]],
            "expected": [None, 9, None, 8],
        },
        {
            "label": "Multiple partial slices",
            "args": [["NumArray", "sumRange", "sumRange", "update", "sumRange"], [[[2, 4, 6, 8]], [1, 3], [0, 0], [3, -2], [1, 3]]],
            "expected": [None, 18, 2, None, 8],
        },
    ],
    hidden=[
        {"label": "Single element updates", "args": [["NumArray", "sumRange", "update", "sumRange"], [[[-1]], [0, 0], [0, 1], [0, 0]]], "expected": [None, -1, None, 1], "category": "Length 1", "edgeReason": "1-indexed Fenwick Tree handles index 0 cleanly."},
        {"label": "Multiple updates same index", "args": [["NumArray", "update", "update", "sumRange"], [[[1, 2, 3]], [1, 10], [1, 20], [0, 2]]], "expected": [None, None, None, 24], "category": "Delta Tracking", "edgeReason": "Must update self.nums[index] so the second delta is 20-10, not 20-2."},
        {"label": "All negatives", "args": [["NumArray", "sumRange", "update", "sumRange"], [[[-5, -10, -15]], [0, 2], [2, 15], [1, 2]]], "expected": [None, -30, None, 5], "category": "Negative Values", "edgeReason": "Handles negative deltas and sums cleanly."},
        {"label": "Power of two length 8", "args": [["NumArray", "sumRange", "update", "sumRange"], [[[1, 1, 1, 1, 1, 1, 1, 1]], [0, 7], [7, 9], [4, 7]]], "expected": [None, 8, None, 12], "category": "LSB Bit Boundary", "edgeReason": "Verifies i + (i & -i) propagation across powers of two."},
        {"label": "Repeated single-cell ranges", "args": [["NumArray", "sumRange", "sumRange", "sumRange"], [[[9, 8, 7]], [0, 0], [1, 1], [2, 2]]], "expected": [None, 9, 8, 7], "category": "Point Queries", "edgeReason": "prefix(i+1) - prefix(i) isolates individual elements."},
    ],
    trap="Using a plain prefix-sum array makes `update` O(N), while summing directly makes `sumRange` O(N), both timing out under 30,000 interleaved operations.",
    pivot="Maintain a 1-indexed Binary Indexed Tree (Fenwick Tree) where `bit[i]` stores the partial sum ending at `i` of length `i & -i`. Point delta updates climb `i += i & -i` and prefix queries descend `i -= i & -i`, both in O(log N).",
    signal="Dynamic point updates interleaved with associative range-sum queries signals a Fenwick Tree (BIT) or Segment Tree.",
    hints=[
        "Remember Fenwick Trees are 1-indexed (`bit` has length `n + 1`), and `update(index, val)` adds `delta = val - self.nums[index]`.",
        "You can build the entire BIT in O(N) time by propagating `bit[i]` directly into its immediate parent `i + (i & -i)`.",
        "`sumRange(left, right)` is simply `_prefix(right + 1) - _prefix(left)`.",
    ],
    walkthrough="1. Build `bit[1..n]` in O(N) by adding `bit[i]` into `bit[i + (i & -i)]`.\n2. On `update(index, val)`, compute `delta = val - nums[index]`, update `nums[index]`, and add `delta` along `i += i & -i`.\n3. On `sumRange(left, right)`, subtract `_prefix(left)` from `_prefix(right + 1)`.",
    trace_steps=[
        {"step": 1, "focus": "Build BIT for [1, 3, 5]", "stateVars": "bit = [0, 1, 4, 5]", "note": "bit[2]=1+3=4 covers [1..2]; bit[3]=5 covers [3..3]."},
        {"step": 2, "focus": "sumRange(0, 2)", "stateVars": "prefix(3) = bit[3]+bit[2] = 5+4 = 9", "note": "Uses 3 -> 2 -> 0 in two additions."},
        {"step": 3, "focus": "update(1, 2)", "stateVars": "delta = -1 | bit[2]=3 -> sumRange(0,2)=8", "note": "Only affected ancestors update in O(log N)."},
    ],
    brute_t="O(N) per query or update",
    brute_s="O(N)",
    opt_t="O(log N) per op (O(N) init)",
    opt_s="O(N)",
    derivation="Each `i & -i` bit step clears or carries the lowest set bit, visiting at most floor(log2(N)) + 1 slots.",
    followup_q="When must you switch from a Fenwick Tree to a Segment Tree?",
    followup_a="When the query operation lacks an inverse (like range minimum/maximum) or when you need range-assign / range-add lazy propagation.",
))


# Day 96: LC 493 - Reverse Pairs
_reg(_mk(
    day=96,
    func="reversePairs",
    stmt=(
        "Given an integer array `nums`, return the number of reverse pairs in the array.\n\n"
        "A reverse pair is a pair `(i, j)` where `0 <= i < j < len(nums)` and `nums[i] > 2 * nums[j]`."
    ),
    examples=[
        {"input": "nums = [1, 3, 2, 3, 1]", "output": "2", "explanation": "Reverse pairs are (1, 4) -> 3 > 2*1 and (3, 4) -> 3 > 2*1."},
        {"input": "nums = [2, 4, 3, 5, 1]", "output": "3", "explanation": "Pairs: (1, 4) 4>2, (2, 4) 3>2, (3, 4) 5>2."},
    ],
    constraints=["1 <= len(nums) <= 5 * 10^4", "-2^31 <= nums[i] <= 2^31 - 1"],
    starter="""
def reversePairs(nums: list[int]) -> int:
    # Write your O(N log N) Merge Sort / Coordinate-Compressed BIT solution here
    pass
""",
    solution="""
def reversePairs(nums: list[int]) -> int:
    arr = list(nums)

    def sort_count(lo: int, hi: int) -> int:
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        cnt = sort_count(lo, mid) + sort_count(mid, hi)
        j = mid
        for i in range(lo, mid):
            while j < hi and arr[i] > 2 * arr[j]:
                j += 1
            cnt += j - mid
        arr[lo:hi] = sorted(arr[lo:hi])
        return cnt

    return sort_count(0, len(arr))
""",
    visible=[
        {"label": "Standard array", "args": [[1, 3, 2, 3, 1]], "expected": 2},
        {"label": "Three reverse pairs", "args": [[2, 4, 3, 5, 1]], "expected": 3},
    ],
    hidden=[
        {"label": "Negative numbers trap", "args": [[-5, -5]], "expected": 1, "category": "Negative Inequality", "edgeReason": "-5 > 2 * (-5) = -10 is True! Equal negative numbers form reverse pairs."},
        {"label": "Single element", "args": [[10]], "expected": 0, "category": "Minimal Length", "edgeReason": "Fewer than 2 elements has 0 pairs."},
        {"label": "Strictly ascending positive", "args": [[1, 2, 3, 4, 5]], "expected": 0, "category": "Zero Pairs", "edgeReason": "No earlier positive element exceeds twice a later positive element."},
        {"label": "Large 32-bit integers", "args": [[2147483647, 2147483647, -2147483647, -2147483647]], "expected": 5, "category": "Overflow Safety", "edgeReason": "Python handles 2 * 2^31 safely; pairs include all (+,-) and (-,-)."},
        {"label": "Zero boundary", "args": [[0, 0, -1]], "expected": 2, "category": "Zero Threshold", "edgeReason": "0 > 2*0 is False, while 0 > 2*(-1) is True."},
    ],
    trap="Counting `nums[i] > 2 * nums[j]` directly inside the merge comparison loop breaks because `nums[i] > nums[j]` and `nums[i] > 2 * nums[j]` do not align at the same pointer position, especially with negative numbers.",
    pivot="Decouple counting from merging inside Divide-and-Conquer Merge Sort: once `arr[lo:mid]` and `arr[mid:hi]` are sorted, run a dedicated monotonic two-pointer sweep (`while arr[i] > 2 * arr[j]: j += 1`) before merging the two halves.",
    signal="Counting cross-index pairs `(i < j)` satisfying a scaled linear inequality (`nums[i] > k * nums[j]`) signals decoupled Merge Sort Counting or Coordinate-Compressed BIT.",
    hints=[
        "Notice `-5 > 2 * (-5)` is True! Never assume equal elements cannot form a reverse pair.",
        "Recursively sort left half `[lo, mid)` and right half `[mid, hi)` first.",
        "Because both halves are sorted, as `i` advances across `[lo, mid)`, the cutoff `j` in `[mid, hi)` only ever moves forward -> O(N) counting pass per level.",
    ],
    walkthrough="1. Recursively count inside `[lo, mid)` and `[mid, hi)`.\n2. With both halves sorted, advance `j` while `arr[i] > 2 * arr[j]` and add `j - mid` for each `i`.\n3. Merge/sort `arr[lo:hi]` so the parent call sees sorted halves.",
    trace_steps=[
        {"step": 1, "focus": "Count across [1, 3] and [1, 2, 3]", "stateVars": "i=0(1): j stops at 1 (0 pairs) | i=1(3): 3>2*1 -> +1", "note": "Monotonic j never resets across the loop."},
        {"step": 2, "focus": "Negative check [-5] vs [-5]", "stateVars": "-5 > 2 * -5 (-10) -> cnt += 1", "note": "Two-pointer sweep handles negatives identically to positives."},
    ],
    brute_t="O(N^2)",
    brute_s="O(1)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Each of the log N recursion levels performs a linear two-pointer count and a Timsort merge of two already-sorted runs.",
    followup_q="Why is `sorted(arr[lo:hi])` still O(N) in Python's Timsort here?",
    followup_a="Timsort detects the two pre-sorted runs `arr[lo:mid]` and `arr[mid:hi]` and merges them in C in O(hi - lo) time.",
))


# Day 97: LC 327 - Count of Range Sum
_reg(_mk(
    day=97,
    func="countRangeSum",
    stmt=(
        "Given an integer array `nums` and two integers `lower` and `upper`, return the number of contiguous range sums "
        "`S(i, j) = sum(nums[i..j])` (`0 <= i <= j < len(nums)`) that lie in `[lower, upper]` inclusive."
    ),
    examples=[
        {"input": "nums = [-2, 5, -1], lower = -2, upper = 2", "output": "3", "explanation": "Valid ranges: [0,0] (-2), [2,2] (-1), and [0,2] (2)."},
        {"input": "nums = [0], lower = 0, upper = 0", "output": "1", "explanation": "Single element 0 lies in [0, 0]."},
    ],
    constraints=["1 <= len(nums) <= 10^5", "-2^31 <= nums[i] <= 2^31 - 1", "-10^5 <= lower <= upper <= 10^5"],
    starter="""
def countRangeSum(nums: list[int], lower: int, upper: int) -> int:
    # Write your O(N log N) Prefix Sum + Merge Sort solution here
    pass
""",
    solution="""
def countRangeSum(nums: list[int], lower: int, upper: int) -> int:
    prefix = [0]
    for x in nums:
        prefix.append(prefix[-1] + x)

    def sort_count(lo: int, hi: int) -> int:
        if hi - lo <= 1:
            return 0
        mid = (lo + hi) // 2
        cnt = sort_count(lo, mid) + sort_count(mid, hi)
        left_ptr = right_ptr = mid
        for p in prefix[lo:mid]:
            while left_ptr < hi and prefix[left_ptr] - p < lower:
                left_ptr += 1
            while right_ptr < hi and prefix[right_ptr] - p <= upper:
                right_ptr += 1
            cnt += right_ptr - left_ptr
        prefix[lo:hi] = sorted(prefix[lo:hi])
        return cnt

    return sort_count(0, len(prefix))
""",
    visible=[
        {"label": "Mixed sign array", "args": [[-2, 5, -1], -2, 2], "expected": 3},
        {"label": "Single zero", "args": [[0], 0, 0], "expected": 1},
    ],
    hidden=[
        {"label": "All zeros", "args": [[0, 0, 0], 0, 0], "expected": 6, "category": "All Subarrays Match", "edgeReason": "All n*(n+1)/2 = 6 subarrays sum to 0."},
        {"label": "No matching subarray", "args": [[5, 6, 7], -10, 4], "expected": 0, "category": "Empty Result", "edgeReason": "Every subarray sum exceeds upper bound 4."},
        {"label": "Negative bounds only", "args": [[-3, 1, 2, -2, 2, -1], -3, -1], "expected": 7, "category": "Negative Window", "edgeReason": "Sliding window fails with negative values; prefix merge sort succeeds."},
        {"label": "Exact point bound lower == upper", "args": [[1, -1, 1, -1], 0, 0], "expected": 4, "category": "Zero-Width Band", "edgeReason": "Counts subarrays summing to exactly 0."},
        {"label": "Large prefix values", "args": [[2147483647, -2147483647, -1, 0], -1, 0], "expected": 6, "category": "Large Magnitude", "edgeReason": "Cancelling extremes produce 6 subarrays summing to -1 or 0."},
    ],
    trap="Sliding window fails immediately because negative values in `nums` destroy prefix-sum monotonicity; checking all O(N^2) subarrays times out.",
    pivot="Transform subarray sums into prefix-sum pairs `lower <= prefix[j] - prefix[i] <= upper` (`i < j`). During Merge Sort on `prefix`, both `left_ptr` (first `prefix[k] >= p + lower`) and `right_ptr` (first `prefix[k] > p + upper`) advance monotonically across the sorted right half.",
    signal="Counting contiguous subarrays whose sum falls in `[lower, upper]` when elements can be negative signals Prefix Sum + Merge Sort (or Coordinate-Compressed BIT).",
    hints=[
        "Build `prefix` of length `n + 1` starting with `0` so every subarray `[i..j]` corresponds to `prefix[j + 1] - prefix[i]`.",
        "Recursively solve left half `[lo, mid)` and right half `[mid, hi)` so both halves are sorted.",
        "For each `p` in the sorted left half, advance `left_ptr` and `right_ptr` through the sorted right half to count valid `prefix[k] - p` in `[lower, upper]`.",
    ],
    walkthrough="1. Build `prefix = [0, nums[0], ...]`.\n2. Recursively divide `[lo, hi)` at `mid`.\n3. With left and right halves sorted, slide two pointers `left_ptr` and `right_ptr` over `[mid, hi)` for each `p` in `[lo, mid)` adding `right_ptr - left_ptr`.\n4. Merge-sort `prefix[lo:hi]`.",
    trace_steps=[
        {"step": 1, "focus": "Build prefix for [-2, 5, -1]", "stateVars": "prefix = [0, -2, 3, 2]", "note": "Need pairs (i < j) with -2 <= prefix[j] - prefix[i] <= 2."},
        {"step": 2, "focus": "Merge [-2, 0] and [2, 3]", "stateVars": "p=-2 -> none | p=0 -> [2] (+1) | plus inner pairs (+2) = 3", "note": "Total valid range sums = 3."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Every recursion level scans `[lo, hi)` linearly with monotonic pointers and merges two sorted runs.",
    followup_q="How does the Coordinate-Compressed Fenwick Tree alternative work for LC 327?",
    followup_a="Collect all `prefix[j]`, `prefix[j] - lower`, and `prefix[j] - upper` values into a sorted rank array, then iterate `prefix[j]` left-to-right querying `bit.sum(rank(p - lower)) - bit.sum(rank(p - upper) - 1)` before inserting `rank(p)`.",
))


# Day 98: LC 699 - Falling Squares
_reg(_mk(
    day=98,
    func="fallingSquares",
    stmt=(
        "There are several squares being dropped onto the X-axis of a 2D plane. You are given a 2D integer array `positions` "
        "where `positions[i] = [left_i, sideLength_i]` means the `i`-th square has side length `sideLength_i` and is dropped "
        "covering the open-closed interval `[left_i, left_i + sideLength_i)`.\n\n"
        "Each square falls straight down until it lands on top of another square or on the X-axis. Grazing only a vertical edge "
        "(e.g. `[1, 3)` and `[3, 5)`) does NOT stack.\n\n"
        "Return an integer array `ans` where `ans[i]` is the tallest stack height anywhere on the X-axis after dropping the `i`-th square."
    ),
    examples=[
        {"input": "positions = [[1, 2], [2, 3], [6, 1]]", "output": "[2, 5, 5]", "explanation": "Square 0 lands at height 2 on [1,3); Square 1 overlaps [2,3) and stacks to 2+3=5; Square 2 lands at height 1 on [6,7), max stays 5."},
        {"input": "positions = [[100, 100], [200, 100]]", "output": "[100, 100]", "explanation": "Touching at x=200 does not overlap, so both land at height 100."},
    ],
    constraints=["1 <= len(positions) <= 1000", "1 <= left_i <= 10^8", "1 <= sideLength_i <= 10^6"],
    starter="""
def fallingSquares(positions: list[list[int]]) -> list[int]:
    # Write your Coordinate-Compressed Segment Tree (Range Max + Range Assign) solution here
    pass
""",
    solution="""
def fallingSquares(positions: list[list[int]]) -> list[int]:
    coords = sorted({x for left, size in positions for x in (left, left + size)})
    idx_map = {x: i for i, x in enumerate(coords)}
    m = len(coords) - 1  # number of elementary intervals [coords[i], coords[i+1])
    tree = [0] * (4 * m)
    lazy = [0] * (4 * m)

    def push(node: int) -> None:
        if lazy[node]:
            v = lazy[node]
            tree[2 * node] = lazy[2 * node] = v
            tree[2 * node + 1] = lazy[2 * node + 1] = v
            lazy[node] = 0

    def query(node: int, l: int, r: int, ql: int, qr: int) -> int:
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return tree[node]
        push(node)
        mid = (l + r) // 2
        return max(query(2 * node, l, mid, ql, qr), query(2 * node + 1, mid + 1, r, ql, qr))

    def update(node: int, l: int, r: int, ql: int, qr: int, val: int) -> None:
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            tree[node] = lazy[node] = val
            return
        push(node)
        mid = (l + r) // 2
        update(2 * node, l, mid, ql, qr, val)
        update(2 * node + 1, mid + 1, r, ql, qr, val)
        tree[node] = max(tree[2 * node], tree[2 * node + 1])

    ans: list[int] = []
    best = 0
    for left, size in positions:
        ql = idx_map[left]
        qr = idx_map[left + size] - 1
        base = query(1, 0, m - 1, ql, qr)
        new_h = base + size
        update(1, 0, m - 1, ql, qr, new_h)
        if new_h > best:
            best = new_h
        ans.append(best)
    return ans
""",
    visible=[
        {"label": "Overlapping then disjoint", "args": [[[1, 2], [2, 3], [6, 1]]], "expected": [2, 5, 5]},
        {"label": "Touching boundary no stack", "args": [[[100, 100], [200, 100]]], "expected": [100, 100]},
    ],
    hidden=[
        {"label": "Single square", "args": [[[5, 7]]], "expected": [7], "category": "Minimal Input", "edgeReason": "Single square lands at its side length."},
        {"label": "Tower on exact same x", "args": [[[1, 2], [1, 3], [1, 4]]], "expected": [2, 5, 9], "category": "Vertical Stacking", "edgeReason": "Repeated drops accumulate height 2 -> 5 -> 9."},
        {"label": "Wide square bridges gap", "args": [[[1, 2], [5, 3], [1, 6]]], "expected": [2, 3, 9], "category": "Bridge Over Valley", "edgeReason": "Wide square rests on the taller of [1,3) (2) and [5,8) (3) -> 3 + 6 = 9."},
        {"label": "Large coordinates 10^8", "args": [[[100000000, 1000000], [100500000, 500000]]], "expected": [1000000, 1500000], "category": "Coordinate Compression", "edgeReason": "Raw coordinate array would OOM; compressed tree uses 3 slots."},
        {"label": "Small square hidden under overhang", "args": [[[1, 5], [1, 1], [3, 1]]], "expected": [5, 6, 6], "category": "Partial Overhang", "edgeReason": "Both small squares sit at height 5+1=6 without overlapping each other."},
    ],
    trap="Allocating a segment tree directly over `10^8` X-coordinates blows up memory, and using inclusive `[left, right]` wrongly stacks squares that only brush along a vertical edge.",
    pivot="Coordinate-compress all unique `left` and `left + size` endpoints into at most `2N` elementary half-open intervals `[coords[i], coords[i+1])`, then run a Lazy Propagation Max Segment Tree supporting Range Max Query + Range Assign Update in O(log N).",
    signal="Range Maximum Query + Range Overwrite over huge sparse coordinates (`10^8`) signals Coordinate Compression + Lazy Segment Tree.",
    hints=[
        "Collect all unique `left` and `left + size` coordinates and map each square to elementary interval indices `[idx[left], idx[left + size] - 1]`.",
        "Because we stop at `idx[left + size] - 1`, adjacent squares like `[100, 200)` and `[200, 300)` map to disjoint leaf ranges.",
        "Each drop performs `h = query_max(ql, qr) + size`, then `range_assign(ql, qr, h)` with lazy propagation.",
    ],
    walkthrough="1. Coordinate-compress all square start and end X coordinates into `m <= 2N - 1` elementary segments.\n2. For each square, query the maximum existing height across `[ql, qr]`.\n3. Range-assign `base + size` across `[ql, qr]` using lazy propagation and record the running global max.",
    trace_steps=[
        {"step": 1, "focus": "Compress [[1,2],[2,3],[6,1]]", "stateVars": "coords=[1,2,3,5,6,7] -> 5 elementary segments", "note": "Square [1,3) -> [0,1]; [2,5) -> [1,2]; [6,7) -> [4,4]."},
        {"step": 2, "focus": "Drop [2, 3] on [1, 2]", "stateVars": "query([1,2])=2 -> assign 2+3=5 on [1,2]", "note": "Overlaps segment [2,3) at height 2, stacking to 5."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Coordinate compression shrinks coordinates to <= 2N, making every lazy segment tree query and range assign O(log N).",
    followup_q="Why is `lazy[node] = val` (overwrite) valid here instead of `lazy[node] += val`?",
    followup_a="Every newly dropped square flattens its entire footprint to a uniform higher plateau `base + size`, strictly replacing any previous heights underneath.",
))


# Day 99: LC 715 - Range Module
_reg(_mk(
    day=99,
    func="RangeModule",
    harness={"customDriver": "system-design", "className": "RangeModule"},
    stmt=(
        "A Range Module tracks half-open integer intervals `[left, right)`.\n\n"
        "Implement the `RangeModule` class:\n"
        "- `RangeModule()`: Initialises the tracker with no intervals.\n"
        "- `addRange(left: int, right: int) -> None`: Adds `[left, right)`, merging with any overlapping or touching tracked ranges.\n"
        "- `queryRange(left: int, right: int) -> bool`: Returns `True` if every real number in `[left, right)` is currently tracked, else `False`.\n"
        "- `removeRange(left: int, right: int) -> None`: Stops tracking every real number in `[left, right)` (splitting existing intervals if needed)."
    ),
    examples=[
        {
            "input": '["RangeModule","addRange","removeRange","queryRange","queryRange","queryRange"], [[],[10,20],[14,16],[10,14],[13,15],[16,17]]',
            "output": "[null, null, null, true, false, true]",
            "explanation": "[10,20) minus [14,16) leaves [10,14) and [16,20). [10,14) and [16,17) are covered; [13,15) crosses the gap.",
        }
    ],
    constraints=["1 <= left < right <= 10^9", "At most 10^4 calls to addRange, queryRange, and removeRange."],
    starter="""
class RangeModule:
    def __init__(self):
        pass

    def addRange(self, left: int, right: int) -> None:
        pass

    def queryRange(self, left: int, right: int) -> bool:
        pass

    def removeRange(self, left: int, right: int) -> None:
        pass
""",
    solution="""
import bisect


class RangeModule:
    def __init__(self):
        # Flat sorted alternating list [l0, r0, l1, r1, ...] of disjoint non-touching intervals
        self.track: list[int] = []

    def addRange(self, left: int, right: int) -> None:
        i = bisect.bisect_left(self.track, left)
        j = bisect.bisect_right(self.track, right)
        sub: list[int] = []
        if i % 2 == 0:
            sub.append(left)
        if j % 2 == 0:
            sub.append(right)
        self.track[i:j] = sub

    def queryRange(self, left: int, right: int) -> bool:
        i = bisect.bisect_right(self.track, left)
        j = bisect.bisect_left(self.track, right)
        return i == j and i % 2 == 1

    def removeRange(self, left: int, right: int) -> None:
        i = bisect.bisect_left(self.track, left)
        j = bisect.bisect_right(self.track, right)
        sub: list[int] = []
        if i % 2 == 1:
            sub.append(left)
        if j % 2 == 1:
            sub.append(right)
        self.track[i:j] = sub
""",
    visible=[
        {
            "label": "Split middle and query edges",
            "args": [
                ["RangeModule", "addRange", "removeRange", "queryRange", "queryRange", "queryRange"],
                [[], [10, 20], [14, 16], [10, 14], [13, 15], [16, 17]],
            ],
            "expected": [None, None, None, True, False, True],
        },
        {
            "label": "Merge touching ranges",
            "args": [
                ["RangeModule", "addRange", "addRange", "queryRange", "queryRange"],
                [[], [10, 15], [15, 25], [10, 25], [9, 25]],
            ],
            "expected": [None, None, None, True, False],
        },
    ],
    hidden=[
        {"label": "Query empty tracker", "args": [["RangeModule", "queryRange"], [[], [1, 5]]], "expected": [None, False], "category": "Empty State", "edgeReason": "Empty module must return False."},
        {"label": "Remove entire range", "args": [["RangeModule", "addRange", "removeRange", "queryRange"], [[], [10, 20], [5, 25], [10, 11]]], "expected": [None, None, None, False], "category": "Full Wipe", "edgeReason": "Superset removal deletes interval completely."},
        {"label": "Bridge multiple intervals", "args": [["RangeModule", "addRange", "addRange", "addRange", "addRange", "queryRange"], [[], [1, 3], [5, 7], [9, 11], [2, 10], [1, 11]]], "expected": [None, None, None, None, None, True], "category": "Multi-Merge", "edgeReason": "Single addRange collapses three intervals into [1, 11)."},
        {"label": "Trim both ends of interval", "args": [["RangeModule", "addRange", "removeRange", "removeRange", "queryRange", "queryRange"], [[], [10, 30], [10, 15], [25, 30], [15, 25], [14, 25]]], "expected": [None, None, None, None, True, False], "category": "Edge Trimming", "edgeReason": "Left and right trims leave [15, 25) exact."},
        {"label": "Query across touching boundary after split", "args": [["RangeModule", "addRange", "removeRange", "addRange", "queryRange"], [[], [1, 10], [4, 6], [4, 6], [1, 10]]], "expected": [None, None, None, None, True], "category": "Hole Patching", "edgeReason": "Re-adding exact removed hole merges back seamlessly."},
    ],
    trap="Manually juggling overlap cases (contained, left-overlap, right-overlap, multi-span, touching) leads to dozens of fragile boundary bugs.",
    pivot="Store merged disjoint intervals as a flat sorted boundary list `[l0, r0, l1, r1, ...]`. Even indices are interval starts (entering tracked space) and odd indices are interval ends (leaving tracked space), making `addRange`, `removeRange`, and `queryRange` clean `bisect` parity checks.",
    signal="Online union, difference, and full-containment queries on continuous 1D intervals signals an Ordered Interval Set / Flat Parity Array (or Dynamic Segment Tree).",
    hints=[
        "In a flat array `[l0, r0, l1, r1, ...]`, any coordinate whose insertion index is ODD lies strictly inside a tracked interval.",
        "For `queryRange(l, r)`: `i = bisect_right(track, l)` and `j = bisect_left(track, r)`. The entire span `[l, r)` is covered iff `i == j` and `i % 2 == 1`.",
        "For `addRange`, keep `left` only if `i` is even (outside) and `right` only if `j` is even; for `removeRange`, flip the parity check to odd!",
    ],
    walkthrough="1. Maintain `self.track = [l0, r0, l1, r1, ...]` strictly increasing with no touching intervals.\n2. `addRange` replaces `track[i:j]` with `[left]` (if `i` even) + `[right]` (if `j` even).\n3. `removeRange` replaces `track[i:j]` with `[left]` (if `i` odd) + `[right]` (if `j` odd).\n4. `queryRange` returns `bisect_right(track, left) == bisect_left(track, right)` and parity odd.",
    trace_steps=[
        {"step": 1, "focus": "addRange(10, 20)", "stateVars": "track = [10, 20]", "note": "Indices 0 (start), 1 (end)."},
        {"step": 2, "focus": "removeRange(14, 16)", "stateVars": "i=1 (odd), j=1 (odd) -> track = [10, 14, 16, 20]", "note": "Both endpoints lie inside [10, 20), splitting cleanly into two intervals."},
        {"step": 3, "focus": "queryRange(13, 15)", "stateVars": "i=1, j=2 -> i != j -> False", "note": "Boundary 14 separates 13 and 15, exposing the gap."},
    ],
    brute_t="O(N) scan",
    brute_s="O(N)",
    opt_t="O(log N) query / amortised O(log N) in balanced BST",
    opt_s="O(N)",
    derivation="Every interval added is deleted at most once; `bisect` locates slice boundaries in O(log N).",
    followup_q="How would you guarantee strict worst-case O(log U) per call without Python list slicing?",
    followup_a="Use a Dynamic Lazy Segment Tree (allocating child nodes on demand up to `U = 10^9`) or a C++ `std::map` / Python `SortedDict`.",
))


# Day 100: LC 2407 - Longest Increasing Subsequence II
_reg(_mk(
    day=100,
    func="lengthOfLISII",
    stmt=(
        "You are given an integer array `nums` and an integer `k`.\n\n"
        "Find the longest strictly increasing subsequence of `nums` such that the difference between every pair of adjacent "
        "elements in the subsequence is at most `k` (`0 < sub[i] - sub[i-1] <= k`).\n\n"
        "Return the length of the longest such subsequence."
    ),
    examples=[
        {"input": "nums = [4, 2, 1, 4, 3, 4, 5, 8, 15], k = 3", "output": "5", "explanation": "Longest valid subsequence is [1, 3, 4, 5, 8] (adjacent diffs <= 3) of length 5."},
        {"input": "nums = [7, 4, 5, 1, 8, 12, 4, 7], k = 5", "output": "4", "explanation": "Subsequence [4, 5, 8, 12] has length 4."},
    ],
    constraints=["1 <= len(nums) <= 10^5", "1 <= nums[i], k <= 10^5"],
    starter="""
def lengthOfLISII(nums: list[int], k: int) -> int:
    # Write your O(N log V) Iterative Max Segment Tree DP solution here
    pass
""",
    solution="""
def lengthOfLISII(nums: list[int], k: int) -> int:
    max_v = max(nums) + 1
    tree = [0] * (2 * max_v)

    def query(l: int, r: int) -> int:
        # max on [l, r)
        l += max_v
        r += max_v
        res = 0
        while l < r:
            if l & 1:
                if tree[l] > res:
                    res = tree[l]
                l += 1
            if r & 1:
                r -= 1
                if tree[r] > res:
                    res = tree[r]
            l >>= 1
            r >>= 1
        return res

    def update(pos: int, val: int) -> None:
        i = pos + max_v
        if val <= tree[i]:
            return
        tree[i] = val
        while i > 1:
            i >>= 1
            tree[i] = tree[2 * i] if tree[2 * i] >= tree[2 * i + 1] else tree[2 * i + 1]

    best = 0
    for x in nums:
        lo = max(0, x - k)
        cur = query(lo, x) + 1
        update(x, cur)
        if cur > best:
            best = cur
    return best
""",
    visible=[
        {"label": "Standard bounded gap k=3", "args": [[4, 2, 1, 4, 3, 4, 5, 8, 15], 3], "expected": 5},
        {"label": "Bounded gap k=5", "args": [[7, 4, 5, 1, 8, 12, 4, 7], 5], "expected": 4},
        {"label": "Single step k=1", "args": [[1, 5], 1], "expected": 1},
    ],
    hidden=[
        {"label": "Strictly consecutive k=1", "args": [[1, 2, 3, 4, 5], 1], "expected": 5, "category": "Exact Step 1", "edgeReason": "Difference 1 satisfies <= k=1 across entire array."},
        {"label": "All equal elements", "args": [[4, 4, 4, 4], 3], "expected": 1, "category": "Strict Inequality", "edgeReason": "Query interval [x-k, x) excludes x itself so duplicates cannot chain."},
        {"label": "Single element", "args": [[10], 1], "expected": 1, "category": "Minimal Length", "edgeReason": "Single element always forms LIS of length 1."},
        {"label": "Gap too wide for patience sorting", "args": [[1, 10, 2, 3, 4], 2], "expected": 4, "category": "Bounded Jump", "edgeReason": "10 cannot link to 1 (diff 9 > 2), so optimal is [1,2,3,4]."},
        {"label": "Strictly descending", "args": [[9, 7, 5, 3, 1], 5], "expected": 1, "category": "Descending Input", "edgeReason": "No strictly increasing pair exists."},
    ],
    trap="Classic Patience Sorting (`bisect_left` on tails) breaks completely because an element can only extend predecessors inside the bounded value window `[x - k, x - 1]`, not any smaller tail.",
    pivot="Index an iterative bottom-up Max Segment Tree by VALUE `v` storing `dp[v]` = longest valid subsequence ending at value `v`. For each `x` in `nums`, query `max(dp[max(0, x-k) .. x-1]) + 1` and point-update `dp[x]` in O(log V).",
    signal="DP transition `dp[x] = 1 + max(dp[v] for v in [x - k, x - 1])` over `N = 10^5` is the flagship Segment Tree DP pattern.",
    hints=[
        "Why does standard LIS binary search fail? Because a smaller tail might be MORE than `k` below `x`!",
        "Store `dp[val]` in a Max Segment Tree indexed by element values `0..max(nums)`.",
        "For each `x`, query the half-open value range `[max(0, x - k), x)` (strictly `< x`), add 1, and update `dp[x] = max(dp[x], cur)`.",
    ],
    walkthrough="1. Allocate an iterative Max Segment Tree of size `2 * (max(nums) + 1)`.\n2. Scan `x` left-to-right in `nums`: query `best_prev = query(max(0, x - k), x)`.\n3. Update `tree[x]` with `best_prev + 1` if larger and track global maximum.",
    trace_steps=[
        {"step": 1, "focus": "Process 4, 2, 1 (k=3)", "stateVars": "dp[4]=1, dp[2]=1, dp[1]=1", "note": "No smaller predecessor in [x-3, x) yet."},
        {"step": 2, "focus": "Process 4 -> 3 -> 4 -> 5 -> 8", "stateVars": "dp[3]=dp[1]+1=2 -> dp[4]=3 -> dp[5]=4 -> dp[8]=5", "note": "Each step queries [x-3, x) in O(log V) and chains to length 5."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N log(max(nums)))",
    opt_s="O(max(nums))",
    derivation="Each of the N elements performs one O(log V) range-max query and one O(log V) point update on the iterative segment tree.",
    followup_q="What if `nums[i]` could be up to `10^9` instead of `10^5`?",
    followup_a="Coordinate-compress the distinct values of `nums` into `0..M-1` and binary search `bisect_left(uniq, x - k)` to map `[x - k, x)` into compressed segment tree indices.",
))


# Day 102: LC 214 - Shortest Palindrome
_reg(_mk(
    day=102,
    func="shortestPalindrome",
    stmt=(
        "You are given a string `s`. You can convert `s` to a palindrome by adding characters in front of it.\n\n"
        "Return the shortest palindrome you can find by performing this transformation."
    ),
    examples=[
        {"input": 's = "aacecaaa"', "output": '"aaacecaaa"', "explanation": "Longest palindromic prefix is 'aacecaa' (length 7); prepend reverse of remaining 'a'."},
        {"input": 's = "abcd"', "output": '"dcbabcd"', "explanation": "Longest palindromic prefix is 'a'; prepend reverse of 'bcd' -> 'dcb'."},
    ],
    constraints=["0 <= len(s) <= 5 * 10^4", "s consists of lowercase English letters."],
    starter="""
def shortestPalindrome(s: str) -> str:
    # Write your O(N) KMP Prefix Function (LPS) solution here
    pass
""",
    solution="""
def shortestPalindrome(s: str) -> str:
    if len(s) <= 1:
        return s
    rev = s[::-1]
    combined = s + "#" + rev
    lps = [0] * len(combined)
    j = 0
    for i in range(1, len(combined)):
        while j > 0 and combined[i] != combined[j]:
            j = lps[j - 1]
        if combined[i] == combined[j]:
            j += 1
        lps[i] = j
    longest_pal_prefix = lps[-1]
    return rev[: len(s) - longest_pal_prefix] + s
""",
    visible=[
        {"label": "Near-palindrome prefix", "args": ["aacecaaa"], "expected": "aaacecaaa"},
        {"label": "No multi-char palindrome prefix", "args": ["abcd"], "expected": "dcbabcd"},
    ],
    hidden=[
        {"label": "Empty string", "args": [""], "expected": "", "category": "Empty Input", "edgeReason": "Empty string is already a palindrome."},
        {"label": "Single character", "args": ["z"], "expected": "z", "category": "Length 1", "edgeReason": "Single character requires no prefix addition."},
        {"label": "Already a palindrome", "args": ["racecar"], "expected": "racecar", "category": "Zero Prepends", "edgeReason": "lps[-1] == len(s), so nothing is prepended."},
        {"label": "Separator prevents overlap bug", "args": ["aaaa"], "expected": "aaaa", "category": "Sentinel Guard", "edgeReason": "Without '#' sentinel, LPS on 'aaaaaaaa' would exceed len(s)."},
        {"label": "Even palindrome prefix", "args": ["abbacd"], "expected": "dcabbacd", "category": "Even Length Prefix", "edgeReason": "Longest palindromic prefix 'abba' has even length 4."},
    ],
    trap="Checking every prefix for palindromicity takes O(N^2) and times out on `50,000` characters; concatenating `s + rev` without a sentinel `#` lets LPS overshoot `len(s)` on repeated characters like `'aaaa'`.",
    pivot="To minimise prepended characters, maximise the longest palindromic PREFIX of `s`. Run the KMP LPS table on `s + '#' + reverse(s)`: `lps[-1]` gives the exact length of the longest prefix of `s` that equals a suffix of `reverse(s)`.",
    signal="Finding the longest palindromic prefix in linear O(N) time signals KMP Prefix Function on `s + '#' + reverse(s)`.",
    hints=[
        "Adding characters only in front means keeping the longest possible palindromic PREFIX untouched and prepending the reversed leftover suffix.",
        "A prefix of `s` is a palindrome iff it matches a suffix of `s[::-1]` of the same length.",
        "Build the KMP `lps` array on `s + '#' + s[::-1]`; the sentinel `'#'` guarantees `lps[-1] <= len(s)`.",
    ],
    walkthrough="1. Construct `combined = s + '#' + s[::-1]`.\n2. Compute standard KMP `lps` array in O(N) time.\n3. `longest_pal_prefix = lps[-1]`; prepend `rev[:len(s) - longest_pal_prefix]` to `s`.",
    trace_steps=[
        {"step": 1, "focus": "Build combined string", "stateVars": "combined = 'aacecaaa#aaacecaa'", "note": "Sentinel '#' caps maximum border length at len(s)."},
        {"step": 2, "focus": "Compute KMP lps[-1]", "stateVars": "lps[-1] = 7 ('aacecaa')", "note": "Only 1 trailing char ('a') lies outside the palindromic prefix."},
        {"step": 3, "focus": "Prepend reversed suffix", "stateVars": "rev[:1] + s = 'a' + 'aacecaaa' = 'aaacecaaa'", "note": "Guaranteed shortest possible palindrome."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N)",
    opt_s="O(N)",
    derivation="KMP's pointer `j` increases at most `2N + 1` times total, bounding inner fallback iterations to O(N) overall.",
    followup_q="How can you solve Shortest Palindrome in O(N) time using Rolling Hash instead of KMP?",
    followup_a="Scan `i` from `0` to `n - 1` updating both a forward polynomial hash `fwd = fwd * base + c` and reverse hash `rev = rev + c * power`; whenever `fwd == rev`, record `i` as the longest palindromic prefix (using double moduli to eliminate collisions).",
))


# Day 103: LC 1392 - Longest Happy Prefix
_reg(_mk(
    day=103,
    func="longestPrefix",
    stmt=(
        "A string is called a happy prefix if it is a non-empty prefix which is also a suffix (excluding the entire string itself).\n\n"
        "Given a string `s`, return the longest happy prefix of `s`. Return an empty string `\"\"` if no such prefix exists."
    ),
    examples=[
        {"input": 's = "level"', "output": '"l"', "explanation": "Prefixes: l, le, lev, leve; Suffixes: l, el, vel, evel. Longest match is 'l'."},
        {"input": 's = "ababab"', "output": '"abab"', "explanation": "'abab' is both a proper prefix and proper suffix (overlapping allowed)."},
    ],
    constraints=["1 <= len(s) <= 10^5", "s contains only lowercase English letters."],
    starter="""
def longestPrefix(s: str) -> str:
    # Write your O(N) KMP Failure Function (LPS) solution here
    pass
""",
    solution="""
def longestPrefix(s: str) -> str:
    n = len(s)
    lps = [0] * n
    j = 0
    for i in range(1, n):
        while j > 0 and s[i] != s[j]:
            j = lps[j - 1]
        if s[i] == s[j]:
            j += 1
        lps[i] = j
    return s[: lps[-1]]
""",
    visible=[
        {"label": "Single char border", "args": ["level"], "expected": "l"},
        {"label": "Overlapping periodic border", "args": ["ababab"], "expected": "abab"},
    ],
    hidden=[
        {"label": "No happy prefix", "args": ["abcdef"], "expected": "", "category": "No Match", "edgeReason": "All characters distinct -> lps[-1] == 0 -> empty string."},
        {"label": "Single character", "args": ["a"], "expected": "", "category": "Proper Prefix Rule", "edgeReason": "Full string is excluded, so length-1 string returns ''."},
        {"label": "All identical characters", "args": ["aaaaa"], "expected": "aaaa", "category": "Max Overlap", "edgeReason": "Longest proper border has length n - 1."},
        {"label": "Fallback chain needed", "args": ["aabaaab"], "expected": "aab", "category": "KMP Backtrack", "edgeReason": "Verifies while j > 0: j = lps[j - 1] fallback (cannot just reset j = 0!)."},
        {"label": "Full double repeat", "args": ["abcabc"], "expected": "abc", "category": "Exact Half Period", "edgeReason": "Clean non-overlapping border of length n / 2."},
    ],
    trap="Resetting `j = 0` on mismatch instead of falling back through `j = lps[j - 1]` misses valid shorter borders on inputs like `'aabaaab'`.",
    pivot="The problem literally asks for the final entry of KMP's Longest Proper Prefix-Suffix (`lps`) table: compute `lps[0..n-1]` in O(N) and return `s[:lps[-1]]`.",
    signal="'Longest proper prefix that is also a suffix' IS the exact mathematical definition of KMP's failure function `lps[-1]`.",
    hints=[
        "`lps[i]` stores the length of the longest proper prefix of `s[:i+1]` that is also a suffix of `s[:i+1]`.",
        "When `s[i] != s[j]`, fall back using `while j > 0 and s[i] != s[j]: j = lps[j - 1]`.",
        "After the single linear pass, the answer is simply `s[:lps[-1]]`.",
    ],
    walkthrough="1. Initialise `lps = [0] * n` and `j = 0`.\n2. For `i` from `1` to `n - 1`, rewind `j = lps[j - 1]` while mismatching, then increment `j` on match and store `lps[i] = j`.\n3. Return `s[:lps[-1]]`.",
    trace_steps=[
        {"step": 1, "focus": "Scan 'ababab'", "stateVars": "lps = [0, 0, 1, 2, 3, 4]", "note": "Overlapping prefix 'abab' matches suffix 'abab' cleanly."},
        {"step": 2, "focus": "Slice result", "stateVars": "s[:4] = 'abab'", "note": "Single O(N) pass returns exact answer."},
    ],
    brute_t="O(N^2)",
    brute_s="O(1)",
    opt_t="O(N)",
    opt_s="O(N)",
    derivation="Amortised analysis proves the `while` loop executes fewer than N total fallbacks across the entire string.",
    followup_q="How can you find the smallest repeating period of a string `s` directly from `lps[-1]`?",
    followup_a="The shortest period candidate is `p = n - lps[-1]`. If `n % p == 0`, `s` is an exact repetition of `s[:p]` (used directly in LC 459).",
))


# Day 104: LC 1044 - Longest Duplicate Substring
_reg(_mk(
    day=104,
    func="longestDupSubstring",
    stmt=(
        "Given a string `s`, consider all duplicated substrings: contiguous substrings of `s` that occur `2` or more times "
        "(occurrences may overlap).\n\n"
        "Return any duplicated substring that has the longest possible length. If `s` does not have a duplicated substring, "
        "return `\"\"`."
    ),
    examples=[
        {"input": 's = "banana"', "output": '"ana"', "explanation": "'ana' appears at index 1 and index 3 (overlapping)."},
        {"input": 's = "abcd"', "output": '""', "explanation": "No character repeats, so return empty string."},
    ],
    constraints=["2 <= len(s) <= 3 * 10^4", "s consists of lowercase English letters."],
    starter="""
def longestDupSubstring(s: str) -> str:
    # Write your O(N log N) Binary Search + Rabin-Karp Rolling Hash solution here
    pass
""",
    solution="""
def longestDupSubstring(s: str) -> str:
    n = len(s)
    nums = [ord(c) - 97 for c in s]
    mod1, mod2 = 1_000_000_007, 1_000_000_009
    base1, base2 = 31, 37

    def find_dup(length: int) -> int:
        if length == 0:
            return 0
        h1 = h2 = 0
        p1 = pow(base1, length, mod1)
        p2 = pow(base2, length, mod2)
        for i in range(length):
            h1 = (h1 * base1 + nums[i]) % mod1
            h2 = (h2 * base2 + nums[i]) % mod2
        seen = {(h1, h2)}
        for i in range(length, n):
            h1 = (h1 * base1 - nums[i - length] * p1 + nums[i]) % mod1
            h2 = (h2 * base2 - nums[i - length] * p2 + nums[i]) % mod2
            key = (h1, h2)
            if key in seen:
                return i - length + 1
            seen.add(key)
        return -1

    lo, hi = 1, n - 1
    best_start, best_len = 0, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        pos = find_dup(mid)
        if pos != -1:
            best_start, best_len = pos, mid
            lo = mid + 1
        else:
            hi = mid - 1
    return s[best_start : best_start + best_len]
""",
    visible=[
        {"label": "Overlapping 'ana'", "args": ["banana"], "expected": "ana"},
        {"label": "All unique chars", "args": ["abcd"], "expected": ""},
    ],
    hidden=[
        {"label": "All identical characters", "args": ["aaaaa"], "expected": "aaaa", "category": "Max Overlap", "edgeReason": "Length n-1 duplicate overlaps at indices 0 and 1."},
        {"label": "Minimum length duplicate", "args": ["aa"], "expected": "a", "category": "Length 2", "edgeReason": "Shortest string with a duplicate substring."},
        {"label": "Non-overlapping repeat", "args": ["abcxyzabc"], "expected": "abc", "category": "Separated Repeat", "edgeReason": "Finds 'abc' across a gap cleanly."},
        {"label": "Single character repeat only", "args": ["abca"], "expected": "a", "category": "Length 1 Match", "edgeReason": "Binary search converges cleanly down to length 1."},
        {"label": "Longer inner repeat", "args": ["mississippi"], "expected": "issi", "category": "Overlapping Middle", "edgeReason": "'issi' overlaps at indices 1 and 4 (beats 'ss' and 'pp')."},
    ],
    trap="Using a single 32-bit rolling hash suffers birthday-paradox collisions on `N = 30,000` strings, while checking all substrings naively takes O(N^3).",
    pivot="Binary search the answer length `mid` (monotonic: if a duplicate of length `L` exists, duplicates of all lengths `< L` also exist). For each `mid`, run a double-modulus Rabin-Karp rolling hash in O(N) to detect any repeated window.",
    signal="Maximising the length of a repeated contiguous substring over `N = 3 * 10^4` signals Binary Search on Length + Double Rolling Hash (or Suffix Array + LCP).",
    hints=[
        "Monotonicity check: if there is a duplicate substring of length `mid`, try longer (`lo = mid + 1`); otherwise try shorter (`hi = mid - 1`).",
        "Compute the rolling window hash in O(1) per shift: `h = (h * base - out_char * base^L + in_char) % mod`.",
        "Use TWO independent large primes (`10^9 + 7` and `10^9 + 9`) so collision probability drops below `10^-10`.",
    ],
    walkthrough="1. Binary search candidate duplicate length `mid` in `[1, n - 1]`.\n2. Slide a length-`mid` window across `s`, maintaining a pair of polynomial rolling hashes `(h1, h2)` in a set.\n3. Whenever `(h1, h2)` repeats, record the start index and search larger lengths; return `s[best_start : best_start + best_len]`.",
    trace_steps=[
        {"step": 1, "focus": "mid=3 on 'banana'", "stateVars": "windows: ban, ana, nan, ana -> HIT at idx 3!", "note": "Length 3 succeeds ('ana'), so push lo = 4."},
        {"step": 2, "focus": "mid=4 on 'banana'", "stateVars": "windows: bana, anan, nana -> all unique", "note": "Length 4 fails, so hi = 3 -> loop ends, return 'ana'."},
    ],
    brute_t="O(N^3)",
    brute_s="O(N^2)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Binary search executes O(log N) probes and each Rabin-Karp scan runs in O(N) time and O(N) hash-set space.",
    followup_q="How does Suffix Array + Kasai's LCP array solve this deterministically with zero hash collision risk?",
    followup_a="Sort all suffixes lexicographically into a Suffix Array and compute adjacent Longest Common Prefixes (LCP); the maximum entry in the LCP array directly identifies the longest duplicate substring.",
))


# Day 105: LC 1163 - Last Substring in Lexicographical Order
_reg(_mk(
    day=105,
    func="lastSubstring",
    stmt=(
        "Given a string `s`, return the last substring of `s` in lexicographical order."
    ),
    examples=[
        {"input": 's = "abab"', "output": '"bab"', "explanation": "Substrings are 'a','ab','aba','abab','b','ba','bab'; max is 'bab'."},
        {"input": 's = "leetcode"', "output": '"tcode"', "explanation": "Lexicographically largest substring starts at 't' and runs to the end."},
    ],
    constraints=["1 <= len(s) <= 4 * 10^5", "s contains only lowercase English letters."],
    starter="""
def lastSubstring(s: str) -> str:
    # Write your O(N) Time / O(1) Space Two-Pointer Suffix Comparison solution here
    pass
""",
    solution="""
def lastSubstring(s: str) -> str:
    n = len(s)
    i, j, k = 0, 1, 0
    while j + k < n:
        if s[i + k] == s[j + k]:
            k += 1
        elif s[i + k] < s[j + k]:
            i = max(i + k + 1, j)
            j = i + 1
            k = 0
        else:
            j = j + k + 1
            k = 0
    return s[i:]
""",
    visible=[
        {"label": "Alternating string", "args": ["abab"], "expected": "bab"},
        {"label": "Classic word", "args": ["leetcode"], "expected": "tcode"},
    ],
    hidden=[
        {"label": "Single character", "args": ["a"], "expected": "a", "category": "Minimal Input", "edgeReason": "Single character returns itself."},
        {"label": "All identical characters", "args": ["zzzzz"], "expected": "zzzzz", "category": "Quadratic Trap", "edgeReason": "Naive suffix comparison degrades to O(N^2) on 'zzzz...'; two-pointer jump stays O(N)."},
        {"label": "Overlapping prefix jump", "args": ["cacacb"], "expected": "cb", "category": "Pointer Skip Invariant", "edgeReason": "Tests i = max(i + k + 1, j) skipping already-beaten intermediate starts."},
        {"label": "Max char at very end", "args": ["abcdz"], "expected": "z", "category": "Right Endpoint", "edgeReason": "Last single character 'z' beats every earlier suffix."},
        {"label": "Max char at very start", "args": ["zabcd"], "expected": "zabcd", "category": "Left Endpoint", "edgeReason": "Full string is already the lexicographical maximum."},
    ],
    trap="Comparing every suffix starting at `max(s)` takes O(N^2) on adversarial strings like `'zzzz...z'` or `'zazaz...zb'`.",
    pivot="First observe the answer MUST be a full suffix `s[i:]` (extending any substring to the right only makes it larger). Maintain two competing candidate starts `i < j` and match offset `k`: on the first mismatch, eliminate ALL intermediate indices `i..i+k` (if `s[i+k] < s[j+k]`) or `j..j+k` (otherwise) in one O(1) jump.",
    signal="Finding the lexicographically largest suffix/substring in O(N) time and O(1) space signals Duval / Minimum-Maximum Representation Two Pointers `(i, j, k)`.",
    hints=[
        "Why must the lexicographically last substring always extend all the way to the end of `s`?",
        "Compare `s[i + k]` and `s[j + k]`. If they match, advance `k += 1`.",
        "If `s[i + k] < s[j + k]`, not only does `i` lose to `j`, every `i + t` (`0 <= t <= k`) loses to `j + t`! Jump `i = max(i + k + 1, j)` and set `j = i + 1, k = 0`.",
    ],
    walkthrough="1. Track best suffix candidate `i = 0`, challenger `j = 1`, and matched prefix length `k = 0`.\n2. While `j + k < n`: advance `k` on equality; if `i` loses, jump `i = max(i + k + 1, j)`, `j = i + 1`; if `j` loses, jump `j = j + k + 1` and reset `k = 0`.\n3. Return `s[i:]`.",
    trace_steps=[
        {"step": 1, "focus": "s = 'abab': i=0, j=1, k=0", "stateVars": "s[0]='a' < s[1]='b'", "note": "i loses immediately -> i=1, j=2, k=0."},
        {"step": 2, "focus": "i=1 ('bab') vs j=2 ('ab')", "stateVars": "s[1]='b' > s[2]='a' -> j=3", "note": "j advances past 'a'."},
        {"step": 3, "focus": "i=1 ('bab') vs j=3 ('b')", "stateVars": "k=1 hits j+k == 4 -> return s[1:]='bab'", "note": "Longest winning suffix wins."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N)",
    opt_s="O(1)",
    derivation="Every mismatch advances `i + j` by at least `k + 1`, so `i + j + k` increases strictly and cannot exceed `3N`.",
    followup_q="How does this exact `(i, j, k)` pointer technique also find the lexicographically smallest cyclic rotation of a string (Booth's / Duval's Algorithm)?",
    followup_a="Duplicate the string `t = s + s` and run the same two-pointer elimination flipping `<` to `>` while stopping once `i` or `j` reaches `n`.",
))


# Day 106: LC 718 - Maximum Length of Repeated Subarray
_reg(_mk(
    day=106,
    func="findLength",
    stmt=(
        "Given two integer arrays `nums1` and `nums2`, return the maximum length of a contiguous subarray that appears in both arrays."
    ),
    examples=[
        {"input": "nums1 = [1, 2, 3, 2, 1], nums2 = [3, 2, 1, 4, 7]", "output": "3", "explanation": "Longest repeated contiguous subarray is [3, 2, 1] of length 3."},
        {"input": "nums1 = [0, 0, 0, 0, 0], nums2 = [0, 0, 0, 0, 0]", "output": "5", "explanation": "Entire array repeats identically."},
    ],
    constraints=["1 <= len(nums1), len(nums2) <= 1000", "0 <= nums1[i], nums2[i] <= 100"],
    starter="""
def findLength(nums1: list[int], nums2: list[int]) -> int:
    # Write your O(M * N) Space-Optimised DP (or Binary Search + Rolling Hash) solution here
    pass
""",
    solution="""
def findLength(nums1: list[int], nums2: list[int]) -> int:
    m, n = len(nums1), len(nums2)
    dp = [0] * (n + 1)
    best = 0
    for i in range(m - 1, -1, -1):
        prev = 0
        for j in range(n - 1, -1, -1):
            tmp = dp[j]
            if nums1[i] == nums2[j]:
                dp[j] = prev + 1
                if dp[j] > best:
                    best = dp[j]
            else:
                dp[j] = 0
            prev = tmp
    return best
""",
    visible=[
        {"label": "Shared length-3 subarray", "args": [[1, 2, 3, 2, 1], [3, 2, 1, 4, 7]], "expected": 3},
        {"label": "All identical zeros", "args": [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]], "expected": 5},
    ],
    hidden=[
        {"label": "Completely disjoint arrays", "args": [[1, 2, 3], [4, 5, 6]], "expected": 0, "category": "Zero Overlap", "edgeReason": "Must return 0 when no element matches."},
        {"label": "Contiguous vs subsequence trap", "args": [[1, 2, 9, 3, 4], [1, 2, 8, 3, 4]], "expected": 2, "category": "Reset on Mismatch", "edgeReason": "Unlike LCS, mismatch must hard-reset dp[j] = 0 instead of max(left, up)."},
        {"label": "Single matching element", "args": [[7], [1, 2, 7, 3]], "expected": 1, "category": "Asymmetric Lengths", "edgeReason": "Handles m = 1 cleanly."},
        {"label": "Match at very end", "args": [[9, 8, 1, 2, 3], [4, 5, 1, 2, 3]], "expected": 3, "category": "Suffix Match", "edgeReason": "Longest match touches both right boundaries."},
        {"label": "Multiple partial overlaps", "args": [[0, 1, 1, 1, 1], [1, 0, 1, 0, 1]], "expected": 2, "category": "Shifted Overlap", "edgeReason": "[0, 1] matches with length 2."},
    ],
    trap="Confusing contiguous subarray with subsequence (writing `max(dp[i+1][j], dp[i][j+1])` on mismatch instead of resetting to `0`) gives LCS instead of Longest Common Subarray.",
    pivot="Define `dp[i][j]` as the longest common subarray starting at `nums1[i]` and `nums2[j]`: if `nums1[i] == nums2[j]`, `dp[i][j] = 1 + dp[i+1][j+1]`, else `0`. Track the global maximum across the table in O(N) rolling space.",
    signal="'Longest common contiguous subarray/substring' of two sequences is 2D Diagonal DP (or O((M+N) log min(M,N)) Binary Search + Rolling Hash).",
    hints=[
        "Unlike Longest Common Subsequence (LC 1143), any mismatch breaks contiguity immediately (`dp[i][j] = 0`).",
        "Because `dp[i][j]` only depends on the diagonal `dp[i+1][j+1]`, you only need a single 1D row plus one `prev` variable.",
        "Always track `best = max(best, dp[j])` inside the loop because the longest match can start anywhere, not just `(0, 0)`.",
    ],
    walkthrough="1. Initialise 1D `dp = [0] * (n + 1)`.\n2. Sweep `i` from `m - 1` down to `0` and `j` from `n - 1` down to `0`, preserving old `dp[j]` in `prev` for the diagonal.\n3. Set `dp[j] = prev + 1` on match (updating `best`) or `0` on mismatch.",
    trace_steps=[
        {"step": 1, "focus": "Match 3, 2, 1 diagonally", "stateVars": "(4,2)=1 -> (3,1)=2 -> (2,0)=3", "note": "Diagonal run builds length 3 cleanly."},
        {"step": 2, "focus": "Mismatch resets to 0", "stateVars": "nums1[1]=2 != nums2[0]=3 -> dp=0", "note": "Global best stays 3."},
    ],
    brute_t="O(M * N * min(M, N))",
    brute_s="O(1)",
    opt_t="O(M * N) DP / O((M+N) log min) Rolling Hash",
    opt_s="O(min(M, N))",
    derivation="Each `(i, j)` pair is evaluated in O(1) using only a 1D rolling array.",
    followup_q="If `M, N = 10^5`, how do you beat O(M * N) time?",
    followup_a="Binary search the answer length `L` and verify in O(M + N) using a double-modulus Rabin-Karp rolling hash comparing length-`L` window hash sets between `nums1` and `nums2`.",
))


# Day 109: LC 587 - Erect the Fence
_reg(_mk(
    day=109,
    func="outerTrees",
    harness={"methodName": "outerTrees", "orderMatters": False},
    stmt=(
        "You are given an array `trees` where `trees[i] = [x_i, y_i]` represents the location of a tree in a 2D garden.\n\n"
        "Fence the entire garden using the minimum length of rope so that every tree is enclosed. "
        "Return the coordinates of ALL trees that lie exactly on the fence perimeter (including collinear points on the hull edges), "
        "in any order without duplicates."
    ),
    examples=[
        {
            "input": "trees = [[1,1],[2,2],[2,0],[2,4],[3,3],[4,2]]",
            "output": "[[1,1],[2,0],[4,2],[3,3],[2,4]]",
            "explanation": "All trees except interior point [2,2] lie on the convex hull boundary.",
        },
        {
            "input": "trees = [[1,2],[2,2],[4,2]]",
            "output": "[[1,2],[2,2],[4,2]]",
            "explanation": "All three collinear trees lie along the perimeter rope.",
        },
    ],
    constraints=["1 <= len(trees) <= 3000", "0 <= x_i, y_i <= 100", "All given points are unique."],
    starter="""
def outerTrees(trees: list[list[int]]) -> list[list[int]]:
    # Write your O(N log N) Andrew's Monotone Chain Convex Hull solution here
    pass
""",
    solution="""
def outerTrees(trees: list[list[int]]) -> list[list[int]]:
    pts = sorted(map(tuple, trees))
    if len(pts) <= 1:
        return [list(p) for p in pts]

    def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[int, int]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) < 0:
            lower.pop()
        lower.append(p)

    upper: list[tuple[int, int]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) < 0:
            upper.pop()
        upper.append(p)

    return [list(p) for p in set(lower + upper)]
""",
    visible=[
        {"label": "Standard polygon with 1 interior tree", "args": [[[1, 1], [2, 2], [2, 0], [2, 4], [3, 3], [4, 2]]], "expected": [[1, 1], [2, 0], [4, 2], [3, 3], [2, 4]]},
        {"label": "All collinear horizontal line", "args": [[[1, 2], [2, 2], [4, 2]]], "expected": [[1, 2], [2, 2], [4, 2]]},
    ],
    hidden=[
        {"label": "Single tree", "args": [[[5, 5]]], "expected": [[5, 5]], "category": "Minimal Input", "edgeReason": "One point forms a degenerate hull containing itself."},
        {"label": "Two trees", "args": [[[0, 0], [3, 4]]], "expected": [[0, 0], [3, 4]], "category": "Two Points", "edgeReason": "Both points lie on the fence."},
        {"label": "Square with collinear edge midpoints", "args": [[[0, 0], [0, 1], [0, 2], [1, 0], [2, 0], [2, 1], [2, 2], [1, 2], [1, 1]]], "expected": [[0, 0], [0, 1], [0, 2], [1, 0], [2, 0], [2, 1], [2, 2], [1, 2]], "category": "Collinear Boundary", "edgeReason": "Strict cross < 0 retains all collinear edge points while excluding interior [1, 1]."},
        {"label": "All collinear vertical line", "args": [[[3, 0], [3, 5], [3, 2], [3, 9]]], "expected": [[3, 0], [3, 2], [3, 5], [3, 9]], "category": "Vertical Collinearity", "edgeReason": "Deduplication set prevents double-counting points appearing on both upper and lower hulls."},
        {"label": "Triangle with multiple interior points", "args": [[[0, 0], [6, 0], [3, 6], [3, 2], [2, 1], [4, 1]]], "expected": [[0, 0], [6, 0], [3, 6]], "category": "Interior Pruning", "edgeReason": "Only the three triangle vertices belong to the perimeter."},
    ],
    trap="Popping on `cross <= 0` drops collinear points lying along the fence edges, and failing to deduplicate `lower + upper` returns endpoints twice (or every point twice on collinear inputs).",
    pivot="Run Andrew's Monotone Chain: sort points by `(x, y)`, build lower hull left-to-right and upper hull right-to-left popping ONLY strictly clockwise turns (`cross < 0`), then deduplicate `set(lower + upper)`.",
    signal="Minimum-perimeter 2D enclosure around points is Convex Hull (Andrew's Monotone Chain avoids polar-angle floating-point precision issues).",
    hints=[
        "Sort points lexicographically by `(x, y)` so no trigonometry or `atan2` floats are needed.",
        "Use the 2D cross product `(a.x - o.x)*(b.y - o.y) - (a.y - o.y)*(b.x - o.x)`: `< 0` means a clockwise right turn (concave indentation).",
        "Keep `cross == 0` (do NOT pop collinear points) and return `set(lower + upper)` to deduplicate shared endpoints.",
    ],
    walkthrough="1. Sort unique points by `(x, y)`.\n2. Sweep left-to-right building `lower`, popping whenever `cross(lower[-2], lower[-1], p) < 0`.\n3. Sweep right-to-left building `upper` with the same rule.\n4. Return deduplicated `set(lower + upper)`.",
    trace_steps=[
        {"step": 1, "focus": "Sort points by (x, y)", "stateVars": "[(1,1),(2,0),(2,2),(2,4),(3,3),(4,2)]", "note": "Lexicographical order enables two linear passes."},
        {"step": 2, "focus": "Build lower & upper hulls", "stateVars": "lower=[(1,1),(2,0),(4,2)] | upper=[(4,2),(3,3),(2,4),(1,1)]", "note": "Interior point (2,2) causes clockwise turn and is popped."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N log N)",
    opt_s="O(N)",
    derivation="Sorting points costs O(N log N); each point is pushed and popped from each stack at most once in O(N).",
    followup_q="Why is Andrew's Monotone Chain generally safer than Graham Scan in interviews?",
    followup_a="Monotone Chain uses pure integer sorting and integer cross products, avoiding polar-angle division/trigonometry edge cases and collinear tie-breaking traps on the final edge.",
))


# Day 110: LC 528 - Random Pick with Weight
_reg(_mk(
    day=110,
    func="pickIndices",
    stmt=(
        "You are given a 0-indexed array of positive integer weights `w` where `w[i]` describes the weight of index `i` "
        "(so index `i` should be selected with probability `w[i] / sum(w)`).\n\n"
        "To keep execution deterministic and verifiable, you are also given `targets`, a list of 1-indexed integer rolls each in "
        "`[1, sum(w)]`. For each roll `t` in `targets`, return the 0-indexed bucket `i` whose cumulative weight interval "
        "`(prefix[i - 1], prefix[i]]` contains `t`."
    ),
    examples=[
        {"input": "w = [1, 3], targets = [1, 2, 3, 4]", "output": "[0, 1, 1, 1]", "explanation": "Prefix CDF is [1, 4]: roll 1 maps to index 0; rolls 2, 3, 4 map to index 1."},
        {"input": "w = [2, 5, 3], targets = [1, 2, 3, 7, 8, 10]", "output": "[0, 0, 1, 1, 2, 2]", "explanation": "Prefix CDF is [2, 7, 10]."},
    ],
    constraints=["1 <= len(w) <= 10^4", "1 <= w[i] <= 10^5", "1 <= targets[j] <= sum(w)"],
    starter="""
def pickIndices(w: list[int], targets: list[int]) -> list[int]:
    # Write your O(N + Q log N) Prefix CDF + Binary Search solution here
    pass
""",
    solution="""
import bisect


def pickIndices(w: list[int], targets: list[int]) -> list[int]:
    prefix: list[int] = []
    running = 0
    for weight in w:
        running += weight
        prefix.append(running)
    return [bisect.bisect_left(prefix, t) for t in targets]
""",
    visible=[
        {"label": "25% / 75% split", "args": [[1, 3], [1, 2, 3, 4]], "expected": [0, 1, 1, 1]},
        {"label": "Three weighted buckets", "args": [[2, 5, 3], [1, 2, 3, 7, 8, 10]], "expected": [0, 0, 1, 1, 2, 2]},
    ],
    hidden=[
        {"label": "Single weight bucket", "args": [[10], [1, 5, 10]], "expected": [0, 0, 0], "category": "Single Bucket", "edgeReason": "Every roll maps to index 0."},
        {"label": "All unit weights", "args": [[1, 1, 1, 1], [1, 2, 3, 4]], "expected": [0, 1, 2, 3], "category": "Uniform Distribution", "edgeReason": "Exact 1-to-1 boundary match verifies bisect_left vs bisect_right."},
        {"label": "Boundary transitions", "args": [[3, 1, 4], [3, 4, 5, 8]], "expected": [0, 1, 2, 2], "category": "Inclusive Right Edge", "edgeReason": "Roll equal to prefix[i] must stay in index i (bisect_left, NOT bisect_right!)."},
        {"label": "Large skew weight", "args": [[1, 100000, 1], [1, 2, 100001, 100002]], "expected": [0, 1, 1, 2], "category": "Extreme Skew", "edgeReason": "Tiny edge buckets remain reachable at rolls 1 and 100002."},
        {"label": "Empty query list", "args": [[5, 5], []], "expected": [], "category": "Zero Queries", "edgeReason": "Handles empty targets list cleanly."},
    ],
    trap="Expanding weights into a repeated array `[0, 1, 1, 1]` blows up memory when `sum(w) = 10^9`, and using `bisect_right` instead of `bisect_left` shifts exact boundary rolls into the next bucket (causing `IndexError` on `t == sum(w)`).",
    pivot="Build a strictly increasing Cumulative Distribution Function (prefix sums) `prefix` in O(N), then answer each draw in O(log N) via `bisect_left(prefix, target)` (since each bucket covers `(prefix[i-1], prefix[i]]`).",
    signal="Sampling discrete indices proportional to arbitrary positive weights signals Prefix-Sum CDF + `bisect_left` (Inverse Transform Sampling).",
    hints=[
        "Compute `prefix[i] = w[0] + ... + w[i]` so bucket `i` owns `w[i]` integer slots `(prefix[i-1], prefix[i]]`.",
        "For a 1-indexed roll `t in [1, total]`, we want the FIRST index `i` where `prefix[i] >= t`.",
        "`bisect.bisect_left(prefix, t)` returns that exact index in O(log N) time.",
    ],
    walkthrough="1. Build `prefix` via running sum of `w`.\n2. For each `t` in `targets`, run `bisect.bisect_left(prefix, t)`.\n3. Return the mapped index list.",
    trace_steps=[
        {"step": 1, "focus": "Build prefix CDF for [2, 5, 3]", "stateVars": "prefix = [2, 7, 10]", "note": "Buckets own [1..2], [3..7], and [8..10]."},
        {"step": 2, "focus": "Query t=7 vs t=8", "stateVars": "bisect_left([2,7,10], 7)=1 | bisect_left([2,7,10], 8)=2", "note": "Exact boundary 7 stays in bucket 1; 8 crosses into bucket 2."},
    ],
    brute_t="O(N * Q) or O(sum(w)) space",
    brute_s="O(sum(w))",
    opt_t="O(N + Q log N)",
    opt_s="O(N)",
    derivation="Prefix construction is O(N) once and every weighted lookup runs one binary search in O(log N).",
    followup_q="How can you answer weighted random picks in O(1) time per draw if weights are static?",
    followup_a="Use Vose's Alias Method: preprocess weights into `prob[]` and `alias[]` tables in O(N) time so every subsequent sample needs only one uniform random draw and one array lookup.",
))


# Day 111: LC 382 - Reservoir Sampling (Algorithm R)
_reg(_mk(
    day=111,
    func="reservoirSample",
    stmt=(
        "You are given a data stream `stream` of unknown length (represented as a list), a sample capacity `k`, and a "
        "deterministic sequence of random draws `randIndices`.\n\n"
        "Implement Vitter's Algorithm R (Reservoir Sampling):\n"
        "1. Fill `reservoir` with the first `k` items `stream[0..k-1]`.\n"
        "2. For each subsequent item `stream[i]` (`i >= k`), read `j = randIndices[i - k]` (a draw in `[0, i]`). "
        "If `j < k`, replace `reservoir[j] = stream[i]`; otherwise discard `stream[i]`.\n\n"
        "Return the final `reservoir` of length `min(k, len(stream))`."
    ),
    examples=[
        {"input": "stream = [10, 20, 30, 40, 50], k = 2, randIndices = [1, 3, 0]", "output": "[50, 30]", "explanation": "Start [10,20]; i=2 j=1 -> [10,30]; i=3 j=3 (>=2 skip); i=4 j=0 -> [50,30]."},
        {"input": "stream = [7, 8, 9], k = 1, randIndices = [0, 2]", "output": "[8]", "explanation": "Start [7]; i=1 j=0 -> [8]; i=2 j=2 (>=1 skip) -> [8]."},
    ],
    constraints=["1 <= k <= len(stream) <= 10^5", "len(randIndices) == len(stream) - k", "0 <= randIndices[t] <= t + k"],
    starter="""
def reservoirSample(stream: list[int], k: int, randIndices: list[int]) -> list[int]:
    # Write your O(N) Time / O(K) Space Reservoir Sampling (Algorithm R) solution here
    pass
""",
    solution="""
def reservoirSample(stream: list[int], k: int, randIndices: list[int]) -> list[int]:
    reservoir = list(stream[:k])
    for offset, j in enumerate(randIndices):
        val = stream[k + offset]
        if j < k:
            reservoir[j] = val
    return reservoir
""",
    visible=[
        {"label": "k=2 stream of 5", "args": [[10, 20, 30, 40, 50], 2, [1, 3, 0]], "expected": [50, 30]},
        {"label": "k=1 (LC 382 classic)", "args": [[7, 8, 9], 1, [0, 2]], "expected": [8]},
    ],
    hidden=[
        {"label": "k equals stream length", "args": [[1, 2, 3], 3, []], "expected": [1, 2, 3], "category": "Full Retention", "edgeReason": "No replacement loop runs when k == len(stream)."},
        {"label": "No replacements occur", "args": [[1, 2, 3, 4, 5], 2, [2, 3, 4]], "expected": [1, 2], "category": "Strict Inequality j < k", "edgeReason": "j == k must NOT replace (only j < k)."},
        {"label": "Every item replaces slot 0", "args": [[1, 2, 3, 4], 1, [0, 0, 0]], "expected": [4], "category": "Repeated Overwrite", "edgeReason": "Latest item overwrites reservoir[0] cleanly."},
        {"label": "Negative and duplicate values", "args": [[-5, 0, -5, 9, 9], 3, [2, 1]], "expected": [-5, 9, 9], "category": "Value Agnostic", "edgeReason": "Sampling depends solely on stream indices, never on value uniqueness."},
        {"label": "Single element k=1", "args": [[42], 1, []], "expected": [42], "category": "Minimal Stream", "edgeReason": "Single item stream always retains that item."},
    ],
    trap="Caching the entire stream into an array to measure `N` first uses O(N) memory, which fails on unbounded streams or linked lists larger than RAM.",
    pivot="Keep only `k` items in memory (`reservoir`). For the `(i + 1)`-th stream item (0-indexed `i >= k`), draw `j in [0, i]` uniformly and overwrite `reservoir[j]` iff `j < k`. By induction, every item seen so far survives with exact probability `k / N`.",
    signal="Uniformly sampling `k` items from a single-pass stream or linked list of unknown length `N` in O(K) space is Reservoir Sampling (Algorithm R).",
    hints=[
        "Seed `reservoir` with the first `k` items from the stream.",
        "Induction proof: after item `i` (total `i + 1` items), the new item enters with probability `k / (i + 1)`, and each existing item survives with `(k / i) * (1 - 1 / (i + 1)) = k / (i + 1)`.",
        "Only overwrite `reservoir[j]` when `j < k` (strict `<`, not `<=`).",
    ],
    walkthrough="1. Initialise `reservoir = stream[:k]`.\n2. Stream remaining items `i = k .. n - 1`: if random draw `j < k`, set `reservoir[j] = stream[i]`.\n3. Return `reservoir` in O(N) time and O(K) auxiliary space.",
    trace_steps=[
        {"step": 1, "focus": "Seed k=2", "stateVars": "reservoir = [10, 20]", "note": "First 2 items enter unconditionally."},
        {"step": 2, "focus": "i=2 (30), j=1 < 2", "stateVars": "reservoir = [10, 30]", "note": "30 replaces slot 1."},
        {"step": 3, "focus": "i=3 (40), j=3 skip | i=4 (50), j=0", "stateVars": "reservoir = [50, 30]", "note": "Every element of the 5-item stream had exact 2/5 survival probability."},
    ],
    brute_t="O(N)",
    brute_s="O(N)",
    opt_t="O(N)",
    opt_s="O(K)",
    derivation="Single pass over the stream with O(1) work per element and O(K) fixed reservoir buffer.",
    followup_q="How do you merge reservoirs computed independently on distributed shards of sizes `N1` and `N2`?",
    followup_a="Weight each shard's reservoir proportional to its stream count `N_s` (or use Algorithm A-Res with random keys `u^(1/w)` in a size-`k` min-heap, where distributed merge is simply taking the global top-`k` keys).",
))


# Day 112: LC 470 - Implement Rand10() Using Rand7()
_reg(_mk(
    day=112,
    func="rand10FromStream",
    stmt=(
        "Given a uniform random generator `rand7()` producing integers in `[1, 7]`, simulate `rand10()` producing uniform "
        "integers in `[1, 10]` via exact Rejection Sampling.\n\n"
        "You are given `rolls`, a deterministic stream of `rand7()` outcomes (`1..7`). Repeatedly consume pairs `(a, b)`:\n"
        "- Compute `idx = (a - 1) * 7 + b` (uniform in `1..49`).\n"
        "- If `idx <= 40`, emit `(idx - 1) % 10 + 1` (uniform in `1..10`).\n"
        "- If `idx > 40`, reject the pair and draw the next pair from `rolls`.\n\n"
        "Stop once fewer than 2 rolls remain and return the list of all emitted `rand10` values."
    ),
    examples=[
        {"input": "rolls = [1, 1, 7, 7, 2, 3]", "output": "[1, 10]", "explanation": "(1,1)->idx=1->emit 1; (7,7)->idx=49>40 reject; (2,3)->idx=10->emit 10."},
        {"input": "rolls = [6, 5, 6, 6]", "output": "[10]", "explanation": "(6,5)->idx=40->emit 10; (6,6)->idx=41>40 reject."},
    ],
    constraints=["0 <= len(rolls) <= 10^4", "1 <= rolls[i] <= 7"],
    starter="""
def rand10FromStream(rolls: list[int]) -> list[int]:
    # Write your Rejection Sampling (Base-7 -> [1..49] -> accept <= 40) solution here
    pass
""",
    solution="""
def rand10FromStream(rolls: list[int]) -> list[int]:
    out: list[int] = []
    i = 0
    n = len(rolls)
    while i + 1 < n:
        a, b = rolls[i], rolls[i + 1]
        i += 2
        idx = (a - 1) * 7 + b
        if idx <= 40:
            out.append((idx - 1) % 10 + 1)
    return out
""",
    visible=[
        {"label": "Accept, reject 49, accept 10", "args": [[1, 1, 7, 7, 2, 3]], "expected": [1, 10]},
        {"label": "Exact threshold 40 vs 41", "args": [[6, 5, 6, 6]], "expected": [10]},
    ],
    hidden=[
        {"label": "All rejected pairs", "args": [[6, 6, 7, 1, 7, 7]], "expected": [], "category": "100% Rejection", "edgeReason": "Indices 41, 43, 49 are all > 40 so nothing is emitted."},
        {"label": "Trailing odd roll ignored", "args": [[1, 5, 3]], "expected": [5], "category": "Incomplete Pair", "edgeReason": "Single leftover roll cannot form a pair."},
        {"label": "Empty stream", "args": [[]], "expected": [], "category": "Empty Input", "edgeReason": "Returns empty list cleanly."},
        {"label": "All 10 outputs uniform sweep", "args": [[1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1, 7, 2, 1, 2, 2, 2, 3]], "expected": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "category": "Full Range [1..10]", "edgeReason": "Verifies mapping (idx - 1) % 10 + 1 covers 1 through 10 without 0."},
        {"label": "Wrap-around 31 -> 1 and 40 -> 10", "args": [[5, 3, 6, 5]], "expected": [1, 10], "category": "Modulo Boundary", "edgeReason": "(5-1)*7+3 = 31 -> 1; (6-1)*7+5 = 40 -> 10."},
    ],
    trap="Summing `rand7() + rand7()` produces a non-uniform triangular distribution (7 is 6x more likely than 2), and using `idx % 10` on `[1..49]` without rejecting `41..49` biases outputs `1..9` over `10`.",
    pivot="Expand the uniform sample space via base-7 encoding: two independent calls give `idx = (a - 1) * 7 + b` uniformly across `[1..49]`. Reject the 9 leftover outcomes (`41..49`) so the remaining 40 outcomes divide evenly by 10 (`4` slots per output).",
    signal="Constructing a uniform `RandM()` from `RandN()` (`M > N`) requires base-`N` expansion + Rejection Sampling at the largest multiple of `M`.",
    hints=[
        "Two calls `(a, b)` create a 7x7 uniform grid of `49` equally likely cells `idx = (a - 1) * 7 + b`.",
        "The largest multiple of `10` that fits inside `49` is `40`; reject `idx > 40` so every output `1..10` has exact probability `4 / 40 = 1/10`.",
        "Use `(idx - 1) % 10 + 1` (not `idx % 10`) so `idx = 10, 20, 30, 40` map cleanly to `10` instead of `0`.",
    ],
    walkthrough="1. Consume pairs `(a, b)` from `rolls` while `i + 1 < len(rolls)`.\n2. Map to `idx = (a - 1) * 7 + b` in `[1..49]`.\n3. If `idx <= 40`, emit `(idx - 1) % 10 + 1`; otherwise reject and advance.",
    trace_steps=[
        {"step": 1, "focus": "Pair (1, 1)", "stateVars": "idx = 0*7 + 1 = 1 <= 40 -> emit 1", "note": "Accepted inside [1..40]."},
        {"step": 2, "focus": "Pair (7, 7)", "stateVars": "idx = 6*7 + 7 = 49 > 40 -> REJECT", "note": "Discarded to keep uniformity exact."},
        {"step": 3, "focus": "Pair (2, 3)", "stateVars": "idx = 1*7 + 3 = 10 <= 40 -> emit 10", "note": "Maps to 10 without bias."},
    ],
    brute_t="Unbounded without rejection",
    brute_s="O(1)",
    opt_t="Expected 2.45 calls per rand10 (O(N) stream)",
    opt_s="O(1)",
    derivation="Each pair succeeds with probability 40/49, so expected calls per `rand10()` is `2 / (40/49) = 2.45`.",
    followup_q="How can you reduce expected `rand7()` calls even further from 2.45 down to ~2.21?",
    followup_a="Recycle the rejected remainder `r = idx - 40` (uniform in `1..9`) by pairing it with ONE extra `rand7()` call to form `[1..63]` (accept `<= 60`), and if rejected (`61..63`, uniform `1..3`) pair with one more `rand7()` to form `[1..21]` (accept `<= 20`)!",
))


# Day 114: LC 1188 - Design Bounded Blocking Queue
_reg(_mk(
    day=114,
    func="BoundedBlockingQueue",
    harness={"customDriver": "system-design", "className": "BoundedBlockingQueue"},
    stmt=(
        "Design a fixed-capacity `BoundedBlockingQueue` supporting producer-consumer flow control.\n\n"
        "Implement the `BoundedBlockingQueue` class (using non-blocking boolean/sentinel returns for deterministic single-thread testing, "
        "plus consider how you would guard the same invariants with `Condition`/`Semaphore` in multi-threaded code):\n"
        "- `BoundedBlockingQueue(capacity: int)`: Initialises an empty FIFO queue holding at most `capacity` elements.\n"
        "- `enqueue(element: int) -> bool`: Appends `element` at the tail and returns `True` if `size < capacity`; otherwise rejects and returns `False`.\n"
        "- `dequeue() -> int`: Removes and returns the front element if non-empty; otherwise returns `-1`.\n"
        "- `size() -> int`: Returns the current number of items in the queue."
    ),
    examples=[
        {
            "input": '["BoundedBlockingQueue","enqueue","enqueue","enqueue","size","dequeue","enqueue","dequeue"], [[2],[10],[20],[30],[],[],[30],[]]',
            "output": "[null, true, true, false, 2, 10, true, 20]",
            "explanation": "Capacity 2 accepts 10 and 20, rejects 30 while full; after dequeuing 10, 30 is accepted.",
        }
    ],
    constraints=["1 <= capacity <= 10^4", "0 <= element <= 10^6", "All operations must run in O(1) time."],
    starter="""
class BoundedBlockingQueue:
    def __init__(self, capacity: int):
        pass

    def enqueue(self, element: int) -> bool:
        pass

    def dequeue(self) -> int:
        pass

    def size(self) -> int:
        pass
""",
    solution="""
from collections import deque


class BoundedBlockingQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buf: deque[int] = deque()

    def enqueue(self, element: int) -> bool:
        if len(self.buf) >= self.capacity:
            return False
        self.buf.append(element)
        return True

    def dequeue(self) -> int:
        if not self.buf:
            return -1
        return self.buf.popleft()

    def size(self) -> int:
        return len(self.buf)
""",
    visible=[
        {
            "label": "Backpressure at capacity=2",
            "args": [
                ["BoundedBlockingQueue", "enqueue", "enqueue", "enqueue", "size", "dequeue", "enqueue", "dequeue"],
                [[2], [10], [20], [30], [], [], [30], []],
            ],
            "expected": [None, True, True, False, 2, 10, True, 20],
        },
        {
            "label": "Empty dequeue returns -1",
            "args": [["BoundedBlockingQueue", "dequeue", "size", "enqueue", "dequeue", "dequeue"], [[1], [], [], [7], [], []]],
            "expected": [None, -1, 0, True, 7, -1],
        },
    ],
    hidden=[
        {"label": "Capacity 1 alternating ping-pong", "args": [["BoundedBlockingQueue", "enqueue", "enqueue", "dequeue", "enqueue", "dequeue"], [[1], [1], [2], [], [3], []]], "expected": [None, True, False, 1, True, 3], "category": "Capacity 1", "edgeReason": "Single-slot buffer blocks second enqueue until consumer drains."},
        {"label": "FIFO ordering under refill", "args": [["BoundedBlockingQueue", "enqueue", "enqueue", "enqueue", "dequeue", "enqueue", "dequeue", "dequeue", "dequeue"], [[3], [1], [2], [3], [], [4], [], [], []]], "expected": [None, True, True, True, 1, True, 2, 3, 4], "category": "Strict FIFO", "edgeReason": "Verifies head-to-tail wraparound preserves FIFO order."},
        {"label": "Zero element value preserved", "args": [["BoundedBlockingQueue", "enqueue", "dequeue"], [[2], [0], []]], "expected": [None, True, 0], "category": "Falsy Zero Value", "edgeReason": "Element 0 must be returned as 0, never confused with empty sentinel -1."},
        {"label": "Drain completely then refill", "args": [["BoundedBlockingQueue", "enqueue", "enqueue", "dequeue", "dequeue", "size", "enqueue", "size"], [[2], [5], [6], [], [], [], [9], []]], "expected": [None, True, True, 5, 6, 0, True, 1], "category": "Reset After Drain", "edgeReason": "Queue transitions cleanly from full -> empty -> active."},
        {"label": "Multiple rejected writes do not corrupt", "args": [["BoundedBlockingQueue", "enqueue", "enqueue", "enqueue", "size", "dequeue"], [[1], [99], [100], [101], [], []]], "expected": [None, True, False, False, 1, 99], "category": "Overflow Protection", "edgeReason": "Rejected enqueues must never overwrite existing items or grow size past capacity."},
    ],
    trap="Using a Python `list` with `pop(0)` makes `dequeue` O(N) under load; in multi-threaded Python/Java, checking `if full:` instead of `while full:` on a condition variable causes spurious-wakeup corruption.",
    pivot="Back the bounded queue with an O(1) `deque` (or circular ring buffer). In concurrent multi-threaded runtimes, guard mutations with a mutex + two condition variables (`not_full`, `not_empty`) or two semaphores (`slots = Semaphore(capacity)`, `items = Semaphore(0)`).",
    signal="Fixed-capacity producer/consumer buffer with backpressure signals a Ring Buffer / `deque` paired with `Condition` or dual `Semaphore` synchronisation.",
    hints=[
        "Use `collections.deque` (or a fixed circular array with `head`, `tail`, `count`) for guaranteed O(1) `enqueue` and `dequeue`.",
        "Always check `len(self.buf) >= self.capacity` before enqueuing and `not self.buf` before dequeuing.",
        "For the concurrency interview discussion: always wrap `cond.wait()` inside a `while` loop (not `if`) to defend against spurious wakeups.",
    ],
    walkthrough="1. Store `self.capacity` and `self.buf = deque()`.\n2. `enqueue` rejects if `len(buf) >= capacity`, else appends in O(1).\n3. `dequeue` returns `-1` if empty, else `popleft()` in O(1).\n4. In multi-threaded Python, wrap with `threading.Condition` using `while len(buf) == capacity: not_full.wait()` and `not_empty.notify()`.",
    trace_steps=[
        {"step": 1, "focus": "enqueue(10), enqueue(20) (cap=2)", "stateVars": "buf = deque([10, 20]) | size = 2", "note": "Buffer reaches full capacity."},
        {"step": 2, "focus": "enqueue(30) rejected", "stateVars": "len(buf) == 2 -> returns False", "note": "Backpressure protects bounded memory."},
        {"step": 3, "focus": "dequeue() -> 10, enqueue(30)", "stateVars": "buf = deque([20, 30])", "note": "Free slot immediately allows 30 to enter."},
    ],
    brute_t="O(N) with list.pop(0)",
    brute_s="O(capacity)",
    opt_t="O(1) per op",
    opt_s="O(capacity)",
    derivation="Deque/circular-buffer head and tail updates execute in strict O(1) time with fixed O(capacity) memory.",
    followup_q="How do you implement the blocking multi-threaded version cleanly using two `threading.Semaphore` objects?",
    followup_a="Initialise `slots = Semaphore(capacity)`, `items = Semaphore(0)`, and a `Lock()`. `enqueue` acquires `slots`, appends under `lock`, and releases `items`; `dequeue` acquires `items`, pops under `lock`, and releases `slots`.",
))


# Day 116: LC 192 - Word Frequency & Log Pipeline
_reg(_mk(
    day=116,
    func="wordFrequency",
    stmt=(
        "Given a multi-line log string `text` containing lowercase words separated by one or more spaces or newlines, "
        "implement the frequency aggregation stage of a Unix log pipeline (`tr -s ' ' '\\n' | sort | uniq -c | sort -rn`).\n\n"
        "Return a list of `[word, count]` pairs sorted by:\n"
        "1. Descending frequency `count`.\n"
        "2. Ascending alphabetical order of `word` on ties."
    ),
    examples=[
        {
            "input": 'text = "the day is sunny the the\\nthe sunny is is"',
            "output": '[["the", 4], ["is", 3], ["sunny", 2], ["day", 1]]',
            "explanation": "'the' appears 4 times, 'is' 3 times, 'sunny' 2 times, 'day' 1 time.",
        },
        {
            "input": 'text = "err warn err info warn"',
            "output": '[["err", 2], ["warn", 2], ["info", 1]]',
            "explanation": "Tied count 2 sorts alphabetically ('err' before 'warn').",
        },
    ],
    constraints=["0 <= len(text) <= 10^5", "Words consist of lowercase ASCII letters separated by whitespace."],
    starter="""
def wordFrequency(text: str) -> list[list]:
    # Write your O(N + U log U) Streaming Token Counter + Multi-Key Sort solution here
    pass
""",
    solution="""
from collections import Counter


def wordFrequency(text: str) -> list[list]:
    counts = Counter(text.split())
    return [[w, c] for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
""",
    visible=[
        {"label": "Classic LC 192 poem", "args": ["the day is sunny the the\nthe sunny is is"], "expected": [["the", 4], ["is", 3], ["sunny", 2], ["day", 1]]},
        {"label": "Frequency tie alphabetical break", "args": ["err warn err info warn"], "expected": [["err", 2], ["warn", 2], ["info", 1]]},
    ],
    hidden=[
        {"label": "Whitespace-only input", "args": ["   \n\t  \n "], "expected": [], "category": "Blank Input", "edgeReason": "split() with no argument skips leading, trailing, and repeated whitespace cleanly."},
        {"label": "Single word repeated", "args": ["ok   ok\nok"], "expected": [["ok", 3]], "category": "Extra Whitespace", "edgeReason": "Multiple spaces and newlines must not produce empty-string tokens."},
        {"label": "All ties sorted alphabetically", "args": ["zebra apple mango banana"], "expected": [["apple", 1], ["banana", 1], ["mango", 1], ["zebra", 1]], "category": "Tie-Breaking Sort", "edgeReason": "Equal counts sort strictly lexicographically ascending."},
        {"label": "Single word", "args": ["timeout"], "expected": [["timeout", 1]], "category": "Minimal Token", "edgeReason": "Single token returns count 1."},
        {"label": "Mixed tabs and newlines", "args": ["a\tb\na  b\ta"], "expected": [["a", 3], ["b", 2]], "category": "Mixed Delimiters", "edgeReason": "Handles tabs, spaces, and newlines uniformly."},
    ],
    trap="Using `text.split(' ')` instead of `text.split()` leaves empty strings `''` on repeated spaces and fails to split across newlines or tabs.",
    pivot="Tokenise with whitespace-normalising `text.split()`, aggregate counts in O(N) via `Counter`, and sort the `U` unique keys with composite key `(-count, word)` in O(U log U) (or use `tr -s '[:space:]' '\\n' | sort | uniq -c | sort -k1,1nr -k2,2` in Bash).",
    signal="Counting tokens from messy multi-line logs and ranking by descending frequency with deterministic tie-breaking maps directly to `Counter` + composite sort key (and Unix `sort | uniq -c`).",
    hints=[
        "`text.split()` (with no separator argument) collapses arbitrary runs of spaces, tabs, and newlines automatically.",
        "Aggregate into `collections.Counter` in one linear pass.",
        "Sort items with `key=lambda kv: (-kv[1], kv[0])` to get descending count and ascending alphabetical tie-breaking.",
    ],
    walkthrough="1. Tokenise `text.split()` to skip blank whitespace.\n2. Count word occurrences in `Counter`.\n3. Sort `(word, count)` by `(-count, word)` and format as `[word, count]`.",
    trace_steps=[
        {"step": 1, "focus": "Tokenise & count", "stateVars": "counts = {'the':4, 'is':3, 'sunny':2, 'day':1}", "note": "Linear O(N) aggregation."},
        {"step": 2, "focus": "Sort by (-count, word)", "stateVars": "[['the',4], ['is',3], ['sunny',2], ['day',1]]", "note": "Deterministic descending frequency order."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N + U log U)",
    opt_s="O(U)",
    derivation="Scanning tokens takes O(N) and sorting `U` unique words takes O(U log U).",
    followup_q="How would you find only the Top-K words across a 100 GB log file that cannot fit in RAM?",
    followup_a="Hash-partition words across `P` disk shards (`hash(w) % P`) so identical words land in the same shard, count each shard independently, and merge per-shard top-K results with a size-`K` min-heap (or use Count-Min Sketch + min-heap for streaming approximate heavy hitters).",
))


# Day 118: FDE-2 - Token-Bucket Rate Limiter & Per-Tenant Quota Engine
_reg(_mk(
    day=118,
    func="evaluateRateLimits",
    stmt=(
        "You are building a multi-tenant API Gateway rate limiter using the Token-Bucket algorithm.\n\n"
        "Every tenant starts with a full bucket of `capacity` tokens upon their first request. "
        "Tokens refill continuously at `refillPerSec` tokens per second, capped at `capacity`.\n\n"
        "You are given `requests`, a list of `[tenant_id, timestamp_sec, cost]` entries sorted in non-decreasing order of `timestamp_sec`:\n"
        "1. If `tenant_id` is new, initialise `tokens = capacity`, `last_ts = timestamp_sec`.\n"
        "2. Otherwise refill `tokens = min(capacity, tokens + (timestamp_sec - last_ts) * refillPerSec)` and set `last_ts = timestamp_sec`.\n"
        "3. If `tokens >= cost`, deduct `tokens -= cost` and append `True` (request allowed). Otherwise leave `tokens` unchanged and append `False` (HTTP 429 throttled).\n\n"
        "Return the boolean decision list for all requests."
    ),
    examples=[
        {
            "input": 'capacity = 5, refillPerSec = 1, requests = [["t1",0,3],["t1",1,4],["t1",2,3],["t2",2,5]]',
            "output": "[True, False, True, True]",
            "explanation": "t1@0: 5-3=2 (True); t1@1: min(5,2+1)=3 < 4 (False, stays 3); t1@2: min(5,3+1)=4 >= 3 -> 1 (True); t2@2: fresh bucket 5-5=0 (True).",
        }
    ],
    constraints=["1 <= capacity <= 10^6", "0 <= refillPerSec <= 10^4", "0 <= len(requests) <= 10^5", "Timestamps are non-decreasing integers."],
    starter="""
def evaluateRateLimits(capacity: int, refillPerSec: int, requests: list[list]) -> list[bool]:
    # Write your O(R) Per-Tenant Lazy Token-Bucket Rate Limiter here
    pass
""",
    solution="""
def evaluateRateLimits(capacity: int, refillPerSec: int, requests: list[list]) -> list[bool]:
    # state[tenant] = [tokens, last_ts]
    state: dict[str, list[int]] = {}
    out: list[bool] = []
    for tenant, ts, cost in requests:
        if tenant not in state:
            tokens = capacity
        else:
            prev_tokens, last_ts = state[tenant]
            tokens = min(capacity, prev_tokens + (ts - last_ts) * refillPerSec)
        if tokens >= cost:
            tokens -= cost
            out.append(True)
        else:
            out.append(False)
        state[tenant] = [tokens, ts]
    return out
""",
    visible=[
        {
            "label": "Multi-tenant burst, throttle, refill",
            "args": [5, 1, [["t1", 0, 3], ["t1", 1, 4], ["t1", 2, 3], ["t2", 2, 5]]],
            "expected": [True, False, True, True],
        },
        {
            "label": "Refill caps at capacity",
            "args": [4, 2, [["a", 0, 4], ["a", 100, 4], ["a", 100, 1]]],
            "expected": [True, True, False],
        },
    ],
    hidden=[
        {"label": "Rejected request still advances last_ts after refill", "args": [5, 1, [["a", 0, 5], ["a", 3, 4], ["a", 4, 4]]], "expected": [True, False, True], "category": "Refill State Persistence", "edgeReason": "At ts=3 bucket refills to 3 (rejected), then at ts=4 refills +1 to 4 (allowed)."},
        {"label": "Cost exceeds capacity (always rejected)", "args": [5, 10, [["a", 0, 6], ["a", 10, 6], ["a", 10, 5]]], "expected": [False, False, True], "category": "Oversized Cost", "edgeReason": "Bucket never exceeds capacity 5, so cost 6 fails without burning tokens."},
        {"label": "Zero refill static quota", "args": [3, 0, [["u", 0, 2], ["u", 50, 1], ["u", 100, 1]]], "expected": [True, True, False], "category": "Zero Refill", "edgeReason": "refillPerSec = 0 behaves as a fixed lifetime quota."},
        {"label": "Same timestamp burst", "args": [6, 1, [["u", 5, 2], ["u", 5, 2], ["u", 5, 2], ["u", 5, 1]]], "expected": [True, True, True, False], "category": "Zero Elapsed Delta", "edgeReason": "Multiple requests at identical timestamp share the burst budget cleanly."},
        {"label": "Empty request log", "args": [10, 2, []], "expected": [], "category": "Empty Input", "edgeReason": "Handles empty request list gracefully."},
    ],
    trap="Running a background timer per tenant wastes CPU when millions of tenants are idle; deducting tokens on rejected requests or forgetting to cap refills at `capacity` breaks burst isolation.",
    pivot="Compute refills LAZILY on demand per tenant using only two numbers `[tokens, last_ts]`: `tokens = min(capacity, prev + (ts - last_ts) * refillPerSec)`. Always persist the refilled `[tokens, ts]` even when a request is rejected so elapsed time is never double-counted.",
    signal="Per-tenant burst allowance + sustained refill rate in O(1) per request signals a Lazy Token-Bucket hash map.",
    hints=[
        "Store only `[tokens, last_ts]` per tenant; you never need a per-second timer loop.",
        "Always cap refilled tokens with `min(capacity, ...)` before checking `tokens >= cost`.",
        "If `tokens < cost`, append `False` WITHOUT subtracting `cost`, while still saving `[tokens, ts]`.",
    ],
    walkthrough="1. Maintain `state[tenant] = [tokens, last_ts]`.\n2. On each `[tenant, ts, cost]`, lazily refill up to `capacity` (or start at `capacity` if unseen).\n3. Deduct `cost` and append `True` if `tokens >= cost`, else append `False` without deducting.\n4. Save `[tokens, ts]` back into `state[tenant]`.",
    trace_steps=[
        {"step": 1, "focus": "['t1', 0, 3]", "stateVars": "t1: 5 - 3 = 2 @ ts=0 -> True", "note": "Fresh bucket starts at capacity 5."},
        {"step": 2, "focus": "['t1', 1, 4]", "stateVars": "t1: refill 2+1=3 < 4 -> False (stays 3 @ ts=1)", "note": "Rejected without burning tokens."},
        {"step": 3, "focus": "['t1', 2, 3]", "stateVars": "t1: refill 3+1=4 >= 3 -> 1 @ ts=2 -> True", "note": "Sufficient tokens after 1 more second."},
    ],
    brute_t="O(T * max_timestamp)",
    brute_s="O(T)",
    opt_t="O(R)",
    opt_s="O(T)",
    derivation="Each request updates one tenant hash-map entry in O(1) time and O(1) space per active tenant.",
    followup_q="How do you make this token bucket atomic across 50 distributed API gateway replicas?",
    followup_a="Execute the read-refill-deduct-write sequence inside a single atomic Redis Lua script keyed by `tenant_id` (using Redis `TIME` or logical monotonic clocks) and attach a Redis `EXPIRE` equal to `capacity / refillPerSec` so idle tenants self-evict.",
))


# Day 119: FDE-3 - In-Memory Transactional KV Store with TTL & Rollback
_reg(_mk(
    day=119,
    func="runTransactionalKV",
    stmt=(
        "Design an in-memory transactional Key-Value Store supporting TTL expiration and nested transactions (`BEGIN` / `COMMIT` / `ROLLBACK`).\n\n"
        "You are given a list of commands `ops` with non-decreasing integer timestamps `ts`:\n"
        "- `[\"SET\", key, val, ts, ttl]`: Sets `key = val`. If `ttl == 0`, the key never expires; otherwise it is valid strictly while `now < ts + ttl`.\n"
        "- `[\"GET\", key, ts]`: Appends the active value of `key` at time `ts` to the output list, or `None` if absent/deleted/expired.\n"
        "- `[\"DELETE\", key, ts]`: Removes `key` in the current scope.\n"
        "- `[\"BEGIN\"]`: Starts a new nested transaction layer.\n"
        "- `[\"COMMIT\"]`: Merges the innermost transaction's changes into its parent layer (no-op if no active transaction).\n"
        "- `[\"ROLLBACK\"]`: Discards the innermost transaction's changes (no-op if no active transaction).\n\n"
        "Return the list of all `GET` results in execution order."
    ),
    examples=[
        {
            "input": '[["SET","a",1,0,10],["BEGIN"],["SET","a",2,2,10],["GET","a",5],["ROLLBACK"],["GET","a",5],["GET","a",10]]',
            "output": "[2, 1, None]",
            "explanation": "Inside tx a=2; after ROLLBACK a reverts to 1 (expires at ts=10); at ts=10 it has expired -> None.",
        }
    ],
    constraints=["1 <= len(ops) <= 10^4", "Timestamps ts are non-decreasing non-negative integers; ttl >= 0."],
    starter="""
def runTransactionalKV(ops: list[list]) -> list:
    # Write your Stacked Delta-Overlay Transactional KV Store with TTL here
    pass
""",
    solution="""
def runTransactionalKV(ops: list[list]) -> list:
    # Each layer maps key -> (val, expiry_or_None) or _TOMBSTONE for deletion
    _TOMBSTONE = object()
    layers: list[dict[str, object]] = [{}]
    out: list[object] = []

    def lookup(key: str, ts: int) -> object:
        for layer in reversed(layers):
            if key in layer:
                entry = layer[key]
                if entry is _TOMBSTONE:
                    return None
                val, expiry = entry  # type: ignore[misc]
                if expiry is not None and ts >= expiry:
                    return None
                return val
        return None

    for op in ops:
        cmd = op[0]
        if cmd == "SET":
            _, key, val, ts, ttl = op
            expiry = None if ttl == 0 else ts + ttl
            layers[-1][key] = (val, expiry)
        elif cmd == "DELETE":
            _, key, _ts = op
            layers[-1][key] = _TOMBSTONE
        elif cmd == "GET":
            _, key, ts = op
            out.append(lookup(key, ts))
        elif cmd == "BEGIN":
            layers.append({})
        elif cmd == "ROLLBACK":
            if len(layers) > 1:
                layers.pop()
        elif cmd == "COMMIT":
            if len(layers) > 1:
                top = layers.pop()
                layers[-1].update(top)
    return out
""",
    visible=[
        {
            "label": "Rollback & exact TTL expiry boundary",
            "args": [[["SET", "a", 1, 0, 10], ["BEGIN"], ["SET", "a", 2, 2, 10], ["GET", "a", 5], ["ROLLBACK"], ["GET", "a", 5], ["GET", "a", 10]]],
            "expected": [2, 1, None],
        },
        {
            "label": "Nested commit + tombstone delete",
            "args": [[["SET", "k", "v1", 0, 0], ["BEGIN"], ["DELETE", "k", 1], ["GET", "k", 2], ["BEGIN"], ["SET", "k", "v2", 3, 5], ["COMMIT"], ["GET", "k", 4], ["ROLLBACK"], ["GET", "k", 4]]],
            "expected": [None, "v2", "v1"],
        },
    ],
    hidden=[
        {"label": "COMMIT persists tombstone delete", "args": [[["SET", "x", 9, 0, 0], ["BEGIN"], ["DELETE", "x", 1], ["COMMIT"], ["GET", "x", 2]]], "expected": [None], "category": "Tombstone Commit", "edgeReason": "Deleting a key in a child tx must mask the parent's key via a tombstone sentinel."},
        {"label": "TTL=0 never expires", "args": [[["SET", "perm", 42, 0, 0], ["GET", "perm", 999999]]], "expected": [42], "category": "Infinite TTL", "edgeReason": "ttl == 0 means no expiration regardless of large ts."},
        {"label": "ROLLBACK / COMMIT outside tx is safe no-op", "args": [[["ROLLBACK"], ["COMMIT"], ["SET", "a", 1, 0, 0], ["ROLLBACK"], ["GET", "a", 1]]], "expected": [1], "category": "Empty Tx Stack Guard", "edgeReason": "Base layer (layers[0]) must never be popped."},
        {"label": "Shadow expired parent with fresh inner SET", "args": [[["SET", "a", 1, 0, 5], ["BEGIN"], ["SET", "a", 2, 4, 10], ["GET", "a", 8], ["COMMIT"], ["GET", "a", 8], ["GET", "a", 14]]], "expected": [2, 2, None], "category": "TTL Override", "edgeReason": "Committed inner entry extends expiry to 4+10=14."},
        {"label": "Delete inside tx then rollback restores", "args": [[["SET", "a", "alive", 0, 0], ["BEGIN"], ["DELETE", "a", 1], ["GET", "a", 2], ["ROLLBACK"], ["GET", "a", 3]]], "expected": [None, "alive"], "category": "Delete Rollback", "edgeReason": "Discarding the tombstone layer restores the base value cleanly."},
    ],
    trap="Cloning the entire KV dictionary on every `BEGIN` costs O(K) per transaction (slow on large databases), and deleting a key with `del layers[-1][k]` fails to hide a key that still exists in a parent layer!",
    pivot="Maintain a stack of delta overlay dicts `layers = [base, tx1, tx2, ...]`. Writes touch only `layers[-1]`, deletes write a unique `_TOMBSTONE` sentinel into `layers[-1]` to shadow outer layers, `ROLLBACK` pops in O(1), and `COMMIT` merges `layers.pop()` into `layers[-1]`.",
    signal="Nested `BEGIN`/`COMMIT`/`ROLLBACK` over a KV store signals a Stack of Delta Overlays with Tombstone Deletion Sentinels.",
    hints=[
        "Never `dict.copy()` the whole database on `BEGIN`; push an empty overlay dict `{}` instead.",
        "Use a unique `_TOMBSTONE = object()` sentinel for `DELETE` so `GET` stops searching parent layers instead of leaking the old value.",
        "On `GET`, walk `reversed(layers)` from top to bottom; the FIRST layer containing `key` decides the answer (including checking `ts >= expiry`).",
    ],
    walkthrough="1. Represent state as a stack `layers = [{}]` where each value is `(val, expiry_or_None)` or `_TOMBSTONE`.\n2. `BEGIN` appends `{}`; `ROLLBACK` pops (keeping base `layers[0]`); `COMMIT` pops and `layers[-1].update(top)`.\n3. `GET` searches `reversed(layers)` and returns `None` on tombstone or `ts >= expiry`.",
    trace_steps=[
        {"step": 1, "focus": "SET a=1 (ttl=10) -> BEGIN -> SET a=2", "stateVars": "layers = [{'a':(1,10)}, {'a':(2,12)}]", "note": "Top overlay shadows base without copying unrelated keys."},
        {"step": 2, "focus": "ROLLBACK", "stateVars": "layers = [{'a':(1,10)}]", "note": "O(1) stack pop reverts instantly."},
        {"step": 3, "focus": "GET a @ ts=10", "stateVars": "10 >= expiry(10) -> None", "note": "Half-open TTL boundary expires cleanly at ts=10."},
    ],
    brute_t="O(N * K) full copy per BEGIN",
    brute_s="O(D * K)",
    opt_t="O(D) lookup / O(1) BEGIN & ROLLBACK",
    opt_s="O(total written deltas)",
    derivation="Only modified keys are stored per transaction layer; depth `D` lookups and O(1) rollback avoid cloning the entire store.",
    followup_q="How would you also support O(1) `GET` even when nesting depth `D` is huge (e.g. 10,000 nested `BEGIN` calls)?",
    followup_a="Apply updates directly to one live `store` dictionary and push an UNDO LOG `(key, prev_entry_or_ABSENT)` per transaction frame: `GET` is always O(1), `COMMIT` merges the undo log into the parent frame, and `ROLLBACK` replays the undo log in reverse!",
))


# Day 120: FDE-4 - Streaming Top-K Anomaly Detector Under Memory Bounds
_reg(_mk(
    day=120,
    func="detectTopKAnomalies",
    stmt=(
        "You are building a real-time SRE error-spike detector processing a stream of service error `events`.\n\n"
        "Each event is `[timestamp_sec, service_id]`, arriving in non-decreasing order of `timestamp_sec`. "
        "Given integers `k` and `windowSec`, after ingesting each event at time `ts`:\n"
        "1. Evict all earlier events whose timestamp falls strictly outside the inclusive sliding window `[ts - windowSec, ts]` (i.e. `old_ts < ts - windowSec`), "
        "deleting any service whose count drops to `0` so memory stays strictly bounded by active window events.\n"
        "2. Compute the Top-`k` active service IDs ranked by descending error count in the window, breaking ties alphabetically ascending by `service_id`.\n\n"
        "Return a list of Top-`k` service-ID lists, one snapshot after every ingested event."
    ),
    examples=[
        {
            "input": 'events = [[1,"auth"],[2,"pay"],[3,"auth"],[7,"pay"],[8,"db"]], k = 2, windowSec = 4',
            "output": '[["auth"],["auth","pay"],["auth","pay"],["auth","pay"],["db","pay"]]',
            "explanation": "At ts=7 window [3,7] evicts ts=1,2 leaving auth:1, pay:1 (tie breaks alphabetically -> ['auth','pay']); at ts=8 window [4,8] evicts ts=3 leaving pay:1, db:1 -> ['db','pay'].",
        }
    ],
    constraints=["0 <= len(events) <= 5 * 10^4", "1 <= k <= 50", "0 <= windowSec <= 10^6", "Timestamps are non-decreasing integers."],
    starter="""
def detectTopKAnomalies(events: list[list], k: int, windowSec: int) -> list[list[str]]:
    # Write your Bounded Sliding-Window Queue + Active Frequency Counter Top-K solution here
    pass
""",
    solution="""
from collections import deque
import heapq


def detectTopKAnomalies(events: list[list], k: int, windowSec: int) -> list[list[str]]:
    window: deque[tuple[int, str]] = deque()
    counts: dict[str, int] = {}
    snapshots: list[list[str]] = []

    for ts, svc in events:
        window.append((ts, svc))
        counts[svc] = counts.get(svc, 0) + 1
        cutoff = ts - windowSec
        while window and window[0][0] < cutoff:
            _, old_svc = window.popleft()
            rem = counts[old_svc] - 1
            if rem == 0:
                del counts[old_svc]
            else:
                counts[old_svc] = rem
        top_k = heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))
        snapshots.append([svc_id for svc_id, _ in top_k])
    return snapshots
""",
    visible=[
        {
            "label": "Sliding eviction and alphabetical tie-break",
            "args": [[[1, "auth"], [2, "pay"], [3, "auth"], [7, "pay"], [8, "db"]], 2, 4],
            "expected": [["auth"], ["auth", "pay"], ["auth", "pay"], ["auth", "pay"], ["db", "pay"]],
        },
        {
            "label": "Lead overtake inside window",
            "args": [[[1, "a"], [2, "b"], [3, "b"], [4, "a"], [5, "a"]], 1, 10],
            "expected": [["a"], ["a"], ["b"], ["a"], ["a"]],
        },
    ],
    hidden=[
        {"label": "Zero-width window (same timestamp only)", "args": [[[1, "x"], [1, "y"], [2, "z"]], 2, 0], "expected": [["x"], ["x", "y"], ["z"]], "category": "Zero Window", "edgeReason": "windowSec = 0 keeps only events matching exact current ts."},
        {"label": "k larger than active services", "args": [[[1, "api"], [2, "api"]], 5, 10], "expected": [["api"], ["api"]], "category": "Sparse Active Set", "edgeReason": "Returns fewer than k items when fewer unique services are active."},
        {"label": "Complete window flush between bursts", "args": [[[1, "old"], [2, "old"], [100, "new"]], 2, 5], "expected": [["old"], ["old"], ["new"]], "category": "Memory Pruning", "edgeReason": "Zero-count 'old' service must be deleted from counts dict completely."},
        {"label": "Exact inclusive boundary ts - windowSec kept", "args": [[[10, "a"], [15, "b"], [16, "c"]], 3, 5], "expected": [["a"], ["a", "b"], ["b", "c"]], "category": "Inclusive Boundary", "edgeReason": "At ts=15, ts=10 equals cutoff 15-5=10 so 'a' stays; at ts=16 cutoff is 11 so 'a' evicts."},
        {"label": "Empty stream", "args": [[], 3, 10], "expected": [], "category": "Empty Stream", "edgeReason": "Empty event stream produces empty snapshot list."},
    ],
    trap="Retaining zero-count keys in `counts` causes an unbounded memory leak over long-running streams (and pollutes Top-K snapshots with evicted services).",
    pivot="Pair a FIFO `deque` holding active `(ts, service_id)` window events with an active `counts` hash map that deletes keys immediately when their count reaches `0`. Use `heapq.nsmallest(k, counts.items(), key=lambda kv: (-count, svc))` to extract Top-K cleanly.",
    signal="Time-bounded streaming heavy hitters with memory cleanup combines a Sliding Window FIFO Deque + Active Frequency Map + Top-K Heap.",
    hints=[
        "Append `(ts, svc)` to a FIFO `deque` and increment `counts[svc]`.",
        "Evict from the front while `window[0][0] < ts - windowSec`, and ALWAYS `del counts[old_svc]` when its count hits `0`!",
        "Rank with composite key `(-count, service_id)` via `heapq.nsmallest(k, ...)` so higher count wins and ties sort alphabetically.",
    ],
    walkthrough="1. Push `(ts, svc)` into `window` deque and increment `counts[svc]`.\n2. Pop all events with `old_ts < ts - windowSec`, decrementing and deleting zero-count keys from `counts`.\n3. Extract top `k` services using `heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))`.",
    trace_steps=[
        {"step": 1, "focus": "ts=1..3 ingest auth, pay, auth", "stateVars": "counts={'auth':2, 'pay':1} -> top2=['auth','pay']", "note": "All 3 events inside window."},
        {"step": 2, "focus": "ts=7 ingest pay (cutoff=3)", "stateVars": "evict ts=1,2 -> counts={'auth':1, 'pay':1} -> ['auth','pay']", "note": "Tie breaks alphabetically 'auth' < 'pay'."},
        {"step": 3, "focus": "ts=8 ingest db (cutoff=4)", "stateVars": "evict ts=3 -> delete 'auth' -> counts={'pay':1, 'db':1} -> ['db','pay']", "note": "Zero-count 'auth' pruned cleanly from memory."},
    ],
    brute_t="O(N^2)",
    brute_s="O(N)",
    opt_t="O(N * U log K) (or O(N log U) with lazy indexed heap)",
    opt_s="O(W)",
    derivation="Each event enters and leaves the FIFO deque once, and active map memory is strictly bounded by active window events `W`.",
    followup_q="How would you scale this to 10 million distinct services per minute when even `counts` exceeds RAM?",
    followup_a="Replace exact `counts` with a time-bucketed Count-Min Sketch (rotating fixed-size sub-window sketches every `windowSec / B` seconds) combined with a bounded Heavy-Hitter min-heap of size `K`.",
))
