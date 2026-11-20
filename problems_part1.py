#!/usr/bin/env python3
"""Curriculum Problems Part 1: Phases 1 to 5 (Days 1 to 42).

Covers Phase 1 (Arrays, Strings, Hashing, Prefix Sum), Phase 2 (Two Pointers,
Sliding Windows, Linear Sorting), Phase 3 (Stacks, Monotonic Stacks, Queues,
Linked Lists), Phase 4 (Binary Search, Divide & Conquer), and Phase 5 (Trees,
BST, Tries, Recursion).
"""

from __future__ import annotations

from typing import Any

# Detailed flagship problems with custom multi-language solutions + trace tables
DETAILED_PART1: dict[int, dict[str, Any]] = {
    1: {
        "leetcodeId": "LC 1",
        "title": "Two Sum",
        "difficulty": "Easy",
        "phase": 1,
        "tags": ["Array", "Hash Table", "Ambiguity & Constraint Clarification", "Space-Time Trade-Off & Amortised Analysis"],
        "url": "https://leetcode.com/problems/two-sum/",
        "statement": (
            "Given an array of integers `nums` and an integer `target`, return the indices of the two numbers "
            "such that they add up to `target`.\n\n"
            "You may assume that each input has exactly one valid solution, and you may not use the same element twice. "
            "Return the answer in ascending index order `[i, j]` where `i < j`."
        ),
        "examples": [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]", "explanation": "nums[0] + nums[1] == 2 + 7 == 9."},
            {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]", "explanation": "nums[1] + nums[2] == 2 + 4 == 6."},
            {"input": "nums = [3, 3], target = 6", "output": "[0, 1]", "explanation": "Duplicate values at distinct indices are valid."},
        ],
        "constraints": ["2 <= len(nums) <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9", "Target Complexity: O(N) time, O(N) space"],
        "clarifyingQuestions": [
            "Can `nums` contain negative numbers, zero, or duplicate values? (Yes, so we cannot prune values larger than `target`.)",
            "Is the input array sorted, or must we preserve original indices? (Unsorted, and we must return original indices, so sorting directly would scramble indices.)",
            "Could `nums[i] + nums[j]` overflow a 32-bit signed integer in typed languages like Go? (Within +/-2*10^9, fits in 32-bit signed int, though 64-bit `int` is safer.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Scanning every pair `(i, j)` with two nested loops (`for i ... for j = i+1 ...`). That asks: 'Given `nums[i]`, let me search the rest of the array for `target - nums[i]`', costing O(N) per element and O(N^2) overall.",
            "optimalPivot": "Invert the question from 'search the future' to 'query the past in O(1)'. As you visit `nums[i]`, ask: 'Have I already seen `complement = target - nums[i]` at some earlier index?' A hash map `seen[value] = index` answers that question in O(1) amortised time.",
            "triggerSignal": "Whenever a problem asks for a pair `(i, j)` satisfying an algebraic relation `f(a[i], a[j]) = target`, isolate `a[i]` on one side (`a[i] = g(target, a[j])`) and store seen values of `a[i]` in a hash table.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Instead of checking all pairs in O(N^2), what exact value do you need to pair with the current number `x` to reach `target`?",
            "Tier 2 (State & Invariant): Maintain a dictionary `seen` mapping each previously visited number `num` to its index `i`.",
            "Tier 3 (Transition Blueprint): For each `(i, x)` in `nums`, compute `need = target - x`. Check if `need` is in `seen` BEFORE inserting `seen[x] = i` (this cleanly handles duplicate numbers like `[3, 3]` with `target = 6`).",
        ],
        "funcName": "twoSum",
        "starterCode": {
            "python": "def twoSum(nums: list[int], target: int) -> list[int]:\n    # Write your O(N) hash-table solution here\n    pass\n",
            "go": "package main\n\nfunc twoSum(nums []int, target int) []int {\n\t// Write your O(N) hash-table solution here\n\treturn nil\n}\n",
            "typescript": "function twoSum(nums: number[], target: number): number[] {\n  // Write your O(N) hash-table solution here\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "def twoSum(nums: list[int], target: int) -> list[int]:\n"
                "    seen: dict[int, int] = {}\n"
                "    for i, x in enumerate(nums):\n"
                "        need = target - x\n"
                "        if need in seen:\n"
                "            return [seen[need], i]\n"
                "        seen[x] = i\n"
                "    return []\n"
            ),
            "go": (
                "package main\n\n"
                "func twoSum(nums []int, target int) []int {\n"
                "\tseen := make(map[int]int, len(nums))\n"
                "\tfor i, x := range nums {\n"
                "\t\tif prevIdx, ok := seen[target-x]; ok {\n"
                "\t\t\treturn []int{prevIdx, i}\n"
                "\t\t}\n"
                "\t\tseen[x] = i\n"
                "\t}\n"
                "\treturn nil\n"
                "}\n"
            ),
            "typescript": (
                "function twoSum(nums: number[], target: number): number[] {\n"
                "  const seen = new Map<number, number>();\n"
                "  for (let i = 0; i < nums.length; i++) {\n"
                "    const need = target - nums[i];\n"
                "    if (seen.has(need)) {\n"
                "      return [seen.get(need)!, i];\n"
                "    }\n"
                "    seen.set(nums[i], i);\n"
                "  }\n"
                "  return [];\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Initialise an empty hash map `seen` that maps `number -> index`.\n"
            "2. Iterate through `nums` with index `i` and value `x`.\n"
            "3. Calculate the required complement `need = target - x`.\n"
            "4. Check if `need` is already a key in `seen`. If so, we found the earlier element at `seen[need]`, so return `[seen[need], i]` immediately.\n"
            "5. Otherwise, record `seen[x] = i` and advance. Checking before inserting guarantees we never pair an element with itself and handles duplicate values like `[3, 3]` seamlessly."
        ),
        "traceSteps": [
            {"step": 1, "focus": "i=0, x=2 (target=9)", "stateVars": "need = 7 | seen = {}", "note": "7 is not in seen. Store seen[2] = 0."},
            {"step": 2, "focus": "i=1, x=7 (target=9)", "stateVars": "need = 2 | seen = {2: 0}", "note": "2 is in seen at index 0! Return [0, 1]."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(N)",
            "derivation": "We visit each of the N elements at most once, performing O(1) amortised hash table lookup and insertion per element. The hash table stores at most N keys.",
        },
        "interviewFollowUp": {
            "question": "Suppose `nums` is streaming from a network socket (10 million integers per minute) and you need to support `add(num)` and `find(target)` where `find` is called 100x less frequently than `add`. How do you optimise?",
            "answer": "Maintain a frequency hash map `counts[num]` in O(1) per `add(num)`. On `find(target)`, iterate over keys `x` in `counts` and check if `target - x` exists (or `counts[x] >= 2` when `x == target - x`). Never precompute all pairwise sums on `add`, which would blow up memory to O(N^2).",
        },
        "testCases": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1], "label": "Standard pair"},
            {"args": [[3, 2, 4], 6], "expected": [1, 2], "label": "Non-zero start index"},
            {"args": [[3, 3], 6], "expected": [0, 1], "label": "Duplicate elements"},
            {"args": [[-1, -2, -3, -4, -5], -8], "expected": [2, 4], "label": "Negative numbers"},
        ],
    },
    2: {
        "leetcodeId": "LC 242",
        "title": "Valid Anagram",
        "difficulty": "Easy",
        "phase": 1,
        "tags": ["String", "Hash Table", "Sorting", "Counting", "Adversarial Edge-Case Synthesis"],
        "url": "https://leetcode.com/problems/valid-anagram/",
        "statement": (
            "Given two strings `s` and `t`, return `True` if `t` is an anagram of `s`, and `False` otherwise.\n\n"
            "An anagram is a word or phrase formed by rearranging the letters of a different word or phrase, "
            "using all the original letters exactly once."
        ),
        "examples": [
            {"input": 's = "anagram", t = "nagaram"', "output": "True", "explanation": "Both strings have identical character frequencies."},
            {"input": 's = "rat", t = "car"', "output": "False", "explanation": "'t' and 'c' differ."},
        ],
        "constraints": ["1 <= len(s), len(t) <= 5 * 10^4", "s and t consist of lowercase English letters", "Target Complexity: O(N) time, O(1) space (26-bucket array)"],
        "clarifyingQuestions": [
            "Are the strings guaranteed to be ASCII lowercase letters `'a'-'z'`, or can they contain arbitrary UTF-8 / Unicode runes? (Start with 26 lowercase letters, then discuss Unicode hash map for follow-up.)",
            "Does whitespace or letter casing matter? (All lowercase letters with no whitespace per constraints.)",
            "Can we exit immediately if `len(s) != len(t)`? (Yes, that is an O(1) guard clause that saves all work on mismatched lengths.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Sorting both strings (`sorted(s) == sorted(t)`), which costs O(N log N) time and O(N) auxiliary copy space.",
            "optimalPivot": "Two strings are anagrams if and only if they have the same canonical multiset signature. Over a fixed alphabet of size Sigma=26, a 26-integer frequency array is a canonical O(1)-space signature computable in one O(N) pass.",
            "triggerSignal": "Whenever order does not matter (permutations, anagrams, rearrangements), replace the sequence with its canonical frequency count vector.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): If two strings have different lengths, can they ever be anagrams? Check `len(s) != len(t)` first.",
            "Tier 2 (State & Invariant): Allocate a fixed array `freq` of 26 zeros representing counts for `'a'` through `'z'`.",
            "Tier 3 (Transition Blueprint): Increment `freq[ord(c) - ord('a')]` for characters in `s` and decrement for characters in `t`. Verify all 26 entries end at zero.",
        ],
        "funcName": "isAnagram",
        "starterCode": {
            "python": "def isAnagram(s: str, t: str) -> bool:\n    # Write your O(N) frequency-counting solution here\n    pass\n",
            "go": "package main\n\nfunc isAnagram(s string, t string) bool {\n\t// Write your O(N) frequency-counting solution here\n\treturn false\n}\n",
            "typescript": "function isAnagram(s: string, t: string): boolean {\n  // Write your O(N) frequency-counting solution here\n  return false;\n}\n",
        },
        "solutionCode": {
            "python": (
                "def isAnagram(s: str, t: str) -> bool:\n"
                "    if len(s) != len(t):\n"
                "        return False\n"
                "    freq = [0] * 26\n"
                "    base = ord('a')\n"
                "    for ch_s, ch_t in zip(s, t):\n"
                "        freq[ord(ch_s) - base] += 1\n"
                "        freq[ord(ch_t) - base] -= 1\n"
                "    return all(c == 0 for c in freq)\n"
            ),
            "go": (
                "package main\n\n"
                "func isAnagram(s string, t string) bool {\n"
                "\tif len(s) != len(t) {\n"
                "\t\treturn false\n"
                "\t}\n"
                "\tvar freq [26]int\n"
                "\tfor i := 0; i < len(s); i++ {\n"
                "\t\tfreq[s[i]-'a']++\n"
                "\t\tfreq[t[i]-'a']--\n"
                "\t}\n"
                "\tfor _, c := range freq {\n"
                "\t\tif c != 0 {\n"
                "\t\t\treturn false\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn true\n"
                "}\n"
            ),
            "typescript": (
                "function isAnagram(s: string, t: string): boolean {\n"
                "  if (s.length !== t.length) return false;\n"
                "  const freq = new Int32Array(26);\n"
                "  for (let i = 0; i < s.length; i++) {\n"
                "    freq[s.charCodeAt(i) - 97]++;\n"
                "    freq[t.charCodeAt(i) - 97]--;\n"
                "  }\n"
                "  return freq.every((c) => c === 0);\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Guard clause: if `len(s) != len(t)`, immediately return `False`.\n"
            "2. Create a 26-slot integer array `freq` initialised to 0.\n"
            "3. Iterate through both strings simultaneously, adding 1 for each character in `s` and subtracting 1 for each character in `t`.\n"
            "4. Return `True` if and only if every slot in `freq` equals 0."
        ),
        "traceSteps": [
            {"step": 1, "focus": "s='ab', t='ba'", "stateVars": "len(s)==2, len(t)==2 | freq=[0..0]", "note": "Lengths match; start single-pass balance."},
            {"step": 2, "focus": "i=0: s[0]='a', t[0]='b'", "stateVars": "freq['a']=+1, freq['b']=-1", "note": "Increment 'a', decrement 'b'."},
            {"step": 3, "focus": "i=1: s[1]='b', t[1]='a'", "stateVars": "freq['a']=0, freq['b']=0", "note": "All counts cancel to 0 -> return True."},
        ],
        "complexity": {
            "bruteTime": "O(N log N)",
            "bruteSpace": "O(N)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(1)",
            "derivation": "A single pass over N characters with a fixed 26-integer array uses O(N) time and O(1) auxiliary space.",
        },
        "interviewFollowUp": {
            "question": "What if the inputs contain arbitrary Unicode characters (emojis, CJK ideographs, combining accents)?",
            "answer": "Replace the fixed 26-element array with a hash map `dict[rune, int]` (after applying Unicode NFC normalisation so composed and decomposed accents compare equal). Time remains O(N) and space becomes O(U) where U is the number of distinct Unicode code points.",
        },
        "testCases": [
            {"args": ["anagram", "nagaram"], "expected": True, "label": "Valid anagram"},
            {"args": ["rat", "car"], "expected": False, "label": "Different characters"},
            {"args": ["a", "ab"], "expected": False, "label": "Different lengths"},
            {"args": ["listen", "silent"], "expected": True, "label": "Classic pair"},
        ],
    },
    3: {
        "leetcodeId": "LC 49",
        "title": "Group Anagrams",
        "difficulty": "Medium",
        "phase": 1,
        "tags": ["Array", "String", "Hash Table", "Sorting", "Counting", "Hash Function"],
        "url": "https://leetcode.com/problems/group-anagrams/",
        "statement": (
            "Given an array of strings `strs`, group the anagrams together. "
            "For deterministic testing, return the groups sorted by their smallest member, with each group sorted alphabetically."
        ),
        "examples": [
            {"input": 'strs = ["eat","tea","tan","ate","nat","bat"]', "output": '[["ate","eat","tea"],["bat"],["nat","tan"]]', "explanation": "Strings sharing the same character count signature map to the same bucket."},
        ],
        "constraints": ["1 <= len(strs) <= 10^4", "0 <= len(strs[i]) <= 100", "Target Complexity: O(N * K) time where K is max string length"],
        "clarifyingQuestions": [
            "Can `strs` contain empty strings `\"\"` or duplicate strings? (Yes, empty strings group together and duplicates stay in the same group.)",
            "What is the maximum string length `K` vs array length `N`? (`K <= 100`, `N <= 10^4`; a 26-tuple count key avoids `O(K log K)` sorting per string.)",
            "Does output group order matter in the real interview? (Usually any order is fine, though sorting inside tests makes verification deterministic.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Comparing every pair of strings for anagram equivalence in O(N^2 * K) time.",
            "optimalPivot": "Design a custom hash function `canonicalKey(s)` such that `canonicalKey(a) == canonicalKey(b)` if and only if `a` and `b` are anagrams. A 26-integer tuple `tuple(counts)` is computed in O(K) time and hashes in O(26) = O(1) time.",
            "triggerSignal": "When asked to partition items into equivalence classes, define a canonical invariant key for each equivalence class and bucket items in a hash map.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): What property is identical across all anagrams in a group?",
            "Tier 2 (State & Invariant): Use a hash map `groups[key] = list_of_strings` where `key` is the 26-letter frequency tuple of each word.",
            "Tier 3 (Transition Blueprint): For each word, build `counts = [0]*26`, convert to `tuple(counts)` (or `[26]int` in Go, which is directly comparable as a map key!), and append the word to `groups[key]`.",
        ],
        "funcName": "groupAnagrams",
        "starterCode": {
            "python": "def groupAnagrams(strs: list[str]) -> list[list[str]]:\n    # Group anagrams using a 26-count canonical key\n    pass\n",
            "go": "package main\n\nfunc groupAnagrams(strs []string) [][]string {\n\t// Group anagrams using a [26]int canonical map key\n\treturn nil\n}\n",
            "typescript": "function groupAnagrams(strs: string[]): string[][] {\n  // Group anagrams using a canonical frequency key\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "from collections import defaultdict\n\n"
                "def groupAnagrams(strs: list[str]) -> list[list[str]]:\n"
                "    groups: dict[tuple[int, ...], list[str]] = defaultdict(list)\n"
                "    for s in strs:\n"
                "        count = [0] * 26\n"
                "        for ch in s:\n"
                "            count[ord(ch) - 97] += 1\n"
                "        groups[tuple(count)].append(s)\n"
                "    res = [sorted(g) for g in groups.values()]\n"
                "    res.sort(key=lambda g: g[0])\n"
                "    return res\n"
            ),
            "go": (
                "package main\n\nimport \"sort\"\n\n"
                "func groupAnagrams(strs []string) [][]string {\n"
                "\tgroups := make(map[[26]int][]string)\n"
                "\tfor _, s := range strs {\n"
                "\t\tvar key [26]int\n"
                "\t\tfor i := 0; i < len(s); i++ {\n"
                "\t\t\tkey[s[i]-'a']++\n"
                "\t\t}\n"
                "\t\tgroups[key] = append(groups[key], s)\n"
                "\t}\n"
                "\tres := make([][]string, 0, len(groups))\n"
                "\tfor _, g := range groups {\n"
                "\t\tsort.Strings(g)\n"
                "\t\tres = append(res, g)\n"
                "\t}\n"
                "\tsort.Slice(res, func(i, j int) bool { return res[i][0] < res[j][0] })\n"
                "\treturn res\n"
                "}\n"
            ),
            "typescript": (
                "function groupAnagrams(strs: string[]): string[][] {\n"
                "  const groups = new Map<string, string[]>();\n"
                "  for (const s of strs) {\n"
                "    const count = new Int32Array(26);\n"
                "    for (let i = 0; i < s.length; i++) count[s.charCodeAt(i) - 97]++;\n"
                "    const key = count.join('#');\n"
                "    const bucket = groups.get(key) ?? [];\n"
                "    bucket.push(s);\n"
                "    groups.set(key, bucket);\n"
                "  }\n"
                "  const res = Array.from(groups.values()).map((g) => g.sort());\n"
                "  res.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));\n"
                "  return res;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Map each string `s` to a 26-element frequency vector representing counts of `'a'` through `'z'`.\n"
            "2. Use that immutable vector (`tuple(count)` in Python, `[26]int` value array in Go, or `'#'`-joined string in TS) as a dictionary key.\n"
            "3. Append `s` to its bucket in O(1) time.\n"
            "4. Collect the dictionary values."
        ),
        "traceSteps": [
            {"step": 1, "focus": "s='eat'", "stateVars": "key=(1,0,0,0,1,...,1,...) | groups[key]=['eat']", "note": "First word creates bucket for {a:1, e:1, t:1}."},
            {"step": 2, "focus": "s='tea'", "stateVars": "key=(1,0,0,0,1,...,1,...) | groups[key]=['eat','tea']", "note": "Matches existing bucket key in O(1)."},
            {"step": 3, "focus": "s='bat'", "stateVars": "key=(1,1,0,...,1,...) | groups[key]=['bat']", "note": "Creates separate bucket for {a:1, b:1, t:1}."},
        ],
        "complexity": {
            "bruteTime": "O(N^2 * K)",
            "bruteSpace": "O(N * K)",
            "optimalTime": "O(N * K)",
            "optimalSpace": "O(N * K)",
            "derivation": "Counting characters for N strings of length at most K takes O(N * K) time, avoiding the O(N * K log K) cost of sorting each string.",
        },
        "interviewFollowUp": {
            "question": "In TypeScript or JavaScript, why would joining counts without a delimiter (`count.join('')`) be a subtle bug?",
            "answer": "Without a delimiter like `'#'`, `10` `'a'`s and `1` `'b'` (`[10, 1, 0...]`) produces the same string prefix `'101'` as `1` `'a'`, `0` `'b'`s, and `1` `'c'` (`[1, 0, 1...]`). Always separate variable-width integers with a delimiter when serialising a composite hash key.",
        },
        "testCases": [
            {"args": [["eat", "tea", "tan", "ate", "nat", "bat"]], "expected": [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]], "label": "Standard 6 words"},
            {"args": [[""]], "expected": [[""]], "label": "Empty string"},
            {"args": [["a"]], "expected": [["a"]], "label": "Single char"},
        ],
    },
    4: {
        "leetcodeId": "LC 560",
        "title": "Subarray Sum Equals K",
        "difficulty": "Medium",
        "phase": 1,
        "tags": ["Array", "Hash Table", "Prefix Sum", "Space-Time Trade-Off & Amortised Analysis"],
        "url": "https://leetcode.com/problems/subarray-sum-equals-k/",
        "statement": (
            "Given an array of integers `nums` and an integer `k`, return the total number of contiguous subarrays "
            "whose sum equals `k`."
        ),
        "examples": [
            {"input": "nums = [1, 1, 1], k = 2", "output": "2", "explanation": "Subarrays [1, 1] at indices (0..1) and (1..2) both sum to 2."},
            {"input": "nums = [1, 2, 3], k = 3", "output": "2", "explanation": "Subarrays [1, 2] and [3] both sum to 3."},
        ],
        "constraints": ["1 <= len(nums) <= 2 * 10^4", "-1000 <= nums[i] <= 1000", "-10^7 <= k <= 10^7", "Target Complexity: O(N) time, O(N) space"],
        "clarifyingQuestions": [
            "Can `nums[i]` be negative or zero? (Yes! `-1000 <= nums[i] <= 1000`. That means the running sum is NOT monotonic, so a two-pointer sliding window WILL FAIL.)",
            "Does a single element equal to `k` count as a valid subarray? (Yes, a subarray of length 1 is contiguous.)",
            "Why do we initialise `prefix_counts = {0: 1}` before iterating? (Because a prefix `nums[0..i]` whose sum equals `k` needs `current_sum - k == 0` to match the empty prefix before index 0.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Trying to use a sliding window `[L..R]` and shrinking `L` when `sum > k`. Because `nums` can contain negative numbers, shrinking `L` might increase or decrease `sum` unpredictably, missing valid subarrays.",
            "optimalPivot": "Express any contiguous subarray sum `sum(L..R)` as the difference of two prefixes: `prefix[R] - prefix[L-1] = k`. Rearranging gives `prefix[L-1] = prefix[R] - k`. That turns 'count subarrays ending at R with sum k' into 'how many earlier prefixes had sum equal to `current_sum - k`?'",
            "triggerSignal": "Contiguous subarray sum/XOR query + negative numbers allowed -> Prefix Sum + Frequency Hash Map (`prefix_counts = {0: 1}`).",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Since `nums` has negative numbers, sliding window does not work. How can you express `sum(nums[L..R])` using running prefix sums?",
            "Tier 2 (State & Invariant): Maintain `running_sum` and a hash map `prefix_counts` recording how many times each prefix sum has occurred so far, seeded with `{0: 1}`.",
            "Tier 3 (Transition Blueprint): At each `x`, add `x` to `running_sum`, add `prefix_counts.get(running_sum - k, 0)` to `ans`, and then increment `prefix_counts[running_sum] += 1`.",
        ],
        "funcName": "subarraySum",
        "starterCode": {
            "python": "def subarraySum(nums: list[int], k: int) -> int:\n    # Count subarrays summing to k using prefix sum frequencies\n    pass\n",
            "go": "package main\n\nfunc subarraySum(nums []int, k int) int {\n\t// Count subarrays summing to k using prefix sum frequencies\n\treturn 0\n}\n",
            "typescript": "function subarraySum(nums: number[], k: number): number {\n  // Count subarrays summing to k using prefix sum frequencies\n  return 0;\n}\n",
        },
        "solutionCode": {
            "python": (
                "def subarraySum(nums: list[int], k: int) -> int:\n"
                "    prefix_counts: dict[int, int] = {0: 1}\n"
                "    running = 0\n"
                "    ans = 0\n"
                "    for x in nums:\n"
                "        running += x\n"
                "        ans += prefix_counts.get(running - k, 0)\n"
                "        prefix_counts[running] = prefix_counts.get(running, 0) + 1\n"
                "    return ans\n"
            ),
            "go": (
                "package main\n\n"
                "func subarraySum(nums []int, k int) int {\n"
                "\tprefixCounts := map[int]int{0: 1}\n"
                "\trunning, ans := 0, 0\n"
                "\tfor _, x := range nums {\n"
                "\t\trunning += x\n"
                "\t\tans += prefixCounts[running-k]\n"
                "\t\tprefixCounts[running]++\n"
                "\t}\n"
                "\treturn ans\n"
                "}\n"
            ),
            "typescript": (
                "function subarraySum(nums: number[], k: number): number {\n"
                "  const prefixCounts = new Map<number, number>([[0, 1]]);\n"
                "  let running = 0;\n"
                "  let ans = 0;\n"
                "  for (const x of nums) {\n"
                "    running += x;\n"
                "    ans += prefixCounts.get(running - k) ?? 0;\n"
                "    prefixCounts.set(running, (prefixCounts.get(running) ?? 0) + 1);\n"
                "  }\n"
                "  return ans;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Seed `prefix_counts = {0: 1}` to represent the empty prefix of sum 0 before index 0.\n"
            "2. For each number `x`, update `running += x`.\n"
            "3. Any earlier prefix with sum `running - k` forms a subarray ending at the current index with sum `k`. Add `prefix_counts[running - k]` to `ans`.\n"
            "4. Increment `prefix_counts[running]` AFTER querying (so `k = 0` does not falsely match the current empty subarray of length 0)."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Init (k=3)", "stateVars": "running=0, ans=0 | counts={0: 1}", "note": "Empty prefix sum 0 occurs once."},
            {"step": 2, "focus": "x=1", "stateVars": "running=1, need=-2 | ans=0 | counts={0:1, 1:1}", "note": "-2 not in counts; record prefix 1."},
            {"step": 3, "focus": "x=2", "stateVars": "running=3, need=0 | ans=1 | counts={0:1, 1:1, 3:1}", "note": "need=0 found in counts! ans becomes 1 ([1,2])."},
            {"step": 4, "focus": "x=3", "stateVars": "running=6, need=3 | ans=2 | counts={0:1, 1:1, 3:1, 6:1}", "note": "need=3 found in counts! ans becomes 2 ([3])."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(N)",
            "derivation": "One pass over N elements with O(1) hash map lookups and updates per step.",
        },
        "interviewFollowUp": {
            "question": "How does your solution change if we ask whether there exists a subarray of length >= 2 whose sum is a multiple of `k` (LeetCode 523)?",
            "answer": "Store the earliest index of each remainder `running % k` in `seen = {0: -1}`. If `rem` was seen at `prev_idx` and `i - prev_idx >= 2`, return `True`.",
        },
        "testCases": [
            {"args": [[1, 1, 1], 2], "expected": 2, "label": "Overlapping ones"},
            {"args": [[1, 2, 3], 3], "expected": 2, "label": "Prefix and single element"},
            {"args": [[1, -1, 0], 0], "expected": 3, "label": "Negative and zero values"},
        ],
    },
    5: {
        "leetcodeId": "LC 238",
        "title": "Product of Array Except Self",
        "difficulty": "Medium",
        "phase": 1,
        "tags": ["Array", "Prefix Sum", "Dry-Run State Table Tracing"],
        "url": "https://leetcode.com/problems/product-of-array-except-self/",
        "statement": (
            "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product "
            "of all the elements of `nums` except `nums[i]`.\n\n"
            "You must write an algorithm that runs in O(N) time and without using the division operation."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3, 4]", "output": "[24, 12, 8, 6]", "explanation": "Products excluding self: [2*3*4, 1*3*4, 1*2*4, 1*2*3]."},
            {"input": "nums = [-1, 1, 0, -3, 3]", "output": "[0, 0, 9, 0, 0]", "explanation": "Only index 2 excludes the zero."},
        ],
        "constraints": ["2 <= len(nums) <= 10^5", "-30 <= nums[i] <= 30", "Target Complexity: O(N) time, O(1) extra space beyond output array"],
        "clarifyingQuestions": [
            "Why is computing `total_product / nums[i]` dangerous even if division were allowed? (A single `0` in `nums` causes division by zero, and two or more `0`s make every entry `0`.)",
            "Does the output array count toward auxiliary space complexity? (No, by convention the returned array is excluded from extra space, allowing O(1) auxiliary workspace.)",
            "Are all prefix and suffix products guaranteed to fit in a 32-bit signed integer? (Yes, guaranteed by problem specification.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Computing the product of all elements except `i` from scratch for each index (O(N^2)), or dividing total product by `nums[i]` (which breaks on zeros).",
            "optimalPivot": "Decompose 'everything except index `i`' into two disjoint halves: `product(0..i-1) * product(i+1..N-1)`. Pass 1 sweeps left-to-right writing prefix products into `out[i]`. Pass 2 sweeps right-to-left multiplying `out[i]` by a single scalar `suffix` accumulator.",
            "triggerSignal": "'Compute aggregate of all elements except index i' -> Left Prefix Aggregate * Right Suffix Aggregate.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): For index `i`, `answer[i]` is the product of everything to the left of `i` multiplied by everything to the right of `i`.",
            "Tier 2 (State & Invariant): Use the output array `out` to store left prefix products on pass 1, then maintain a scalar `right_prod = 1` on pass 2.",
            "Tier 3 (Transition Blueprint): Left-to-right: `out[i] = left_prod; left_prod *= nums[i]`. Right-to-left: `out[i] *= right_prod; right_prod *= nums[i]`.",
        ],
        "funcName": "productExceptSelf",
        "starterCode": {
            "python": "def productExceptSelf(nums: list[int]) -> list[int]:\n    # O(N) time, O(1) extra space without division\n    pass\n",
            "go": "package main\n\nfunc productExceptSelf(nums []int) []int {\n\t// O(N) time, O(1) extra space without division\n\treturn nil\n}\n",
            "typescript": "function productExceptSelf(nums: number[]): number[] {\n  // O(N) time, O(1) extra space without division\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "def productExceptSelf(nums: list[int]) -> list[int]:\n"
                "    n = len(nums)\n"
                "    out = [1] * n\n"
                "    left = 1\n"
                "    for i in range(n):\n"
                "        out[i] = left\n"
                "        left *= nums[i]\n"
                "    right = 1\n"
                "    for i in range(n - 1, -1, -1):\n"
                "        out[i] *= right\n"
                "        right *= nums[i]\n"
                "    return out\n"
            ),
            "go": (
                "package main\n\n"
                "func productExceptSelf(nums []int) []int {\n"
                "\tn := len(nums)\n"
                "\tout := make([]int, n)\n"
                "\tleft := 1\n"
                "\tfor i := 0; i < n; i++ {\n"
                "\t\tout[i] = left\n"
                "\t\tleft *= nums[i]\n"
                "\t}\n"
                "\tright := 1\n"
                "\tfor i := n - 1; i >= 0; i-- {\n"
                "\t\tout[i] *= right\n"
                "\t\tright *= nums[i]\n"
                "\t}\n"
                "\treturn out\n"
                "}\n"
            ),
            "typescript": (
                "function productExceptSelf(nums: number[]): number[] {\n"
                "  const n = nums.length;\n"
                "  const out = new Array<number>(n).fill(1);\n"
                "  let left = 1;\n"
                "  for (let i = 0; i < n; i++) {\n"
                "    out[i] = left;\n"
                "    left *= nums[i];\n"
                "  }\n"
                "  let right = 1;\n"
                "  for (let i = n - 1; i >= 0; i--) {\n"
                "    out[i] = out[i] * right + 0;\n"
                "    right *= nums[i];\n"
                "  }\n"
                "  return out;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Allocate `out` of length `n`.\n"
            "2. Sweep `i` from `0` to `n-1`: set `out[i] = left`, then update `left *= nums[i]`. Now `out[i]` holds the product of `nums[0..i-1]`.\n"
            "3. Sweep `i` from `n-1` down to `0`: multiply `out[i] *= right`, then update `right *= nums[i]`. Now `out[i]` holds `left_product * right_product`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Pass 1 (Left Prefixes) on [1,2,3,4]", "stateVars": "out = [1, 1, 2, 6]", "note": "Each slot holds product of elements strictly to its left."},
            {"step": 2, "focus": "Pass 2 i=3..2 (Right Suffixes)", "stateVars": "right=1->4->12 | out=[1, 1, 8, 6]", "note": "Multiply out[3]*=1, out[2]*=4."},
            {"step": 3, "focus": "Pass 2 i=1..0 (Right Suffixes)", "stateVars": "right=12->24 | out=[24, 12, 8, 6]", "note": "Multiply out[1]*=12, out[0]*=24. Done!"},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(1) auxiliary",
            "derivation": "Two linear passes over N elements using only two scalar accumulators (`left` and `right`).",
        },
        "interviewFollowUp": {
            "question": "Where does this exact Prefix + Suffix decomposition show up in harder SWE & FDE interview problems?",
            "answer": "Trapping Rain Water (`min(leftMax[i], rightMax[i]) - height[i]`), Candy distribution (`max(leftRun[i], rightRun[i])`), and Prefix/Suffix DP where one outlier element is skipped or modified.",
        },
        "testCases": [
            {"args": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6], "label": "Positive sequence"},
            {"args": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0], "label": "Contains zero"},
            {"args": [[0, 0]], "expected": [0, 0], "label": "Two zeros"},
        ],
    },
    9: {
        "leetcodeId": "LC 15",
        "title": "3Sum",
        "difficulty": "Medium",
        "phase": 2,
        "tags": ["Array", "Two Pointers", "Sorting", "Adversarial Edge-Case Synthesis"],
        "url": "https://leetcode.com/problems/3sum/",
        "statement": (
            "Given an integer array `nums`, return all unique triplets `[nums[i], nums[j], nums[k]]` such that "
            "`i != j`, `i != k`, `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.\n\n"
            "Notice that the solution set must not contain duplicate triplets. Return triplets sorted lexicographically."
        ),
        "examples": [
            {"input": "nums = [-1, 0, 1, 2, -1, -4]", "output": "[[-1, -1, 2], [-1, 0, 1]]", "explanation": "Unique triplets summing to 0."},
            {"input": "nums = [0, 0, 0]", "output": "[[0, 0, 0]]", "explanation": "Single all-zero triplet."},
        ],
        "constraints": ["3 <= len(nums) <= 3000", "-10^5 <= nums[i] <= 10^5", "Target Complexity: O(N^2) time, O(1) extra space beyond sorting"],
        "clarifyingQuestions": [
            "How should duplicate values in `nums` be handled? (Duplicate values can appear within a triplet like `[-1, -1, 2]`, but the output list must not repeat `[-1, -1, 2]` twice.)",
            "Can we mutate/sort `nums` in-place? (Yes, sorting in O(N log N) is dwarfed by O(N^2) and makes both two-pointer search and duplicate skipping trivial.)",
            "What early termination is possible once `nums` is sorted? (If `nums[i] > 0`, no two elements to its right can sum with it to 0, so we can `break` immediately.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Using three nested loops O(N^3) plus a `set` of tuples to deduplicate, or trying to use an unsorted hash map where deduplicating triplets becomes error-prone.",
            "optimalPivot": "Sort the array first. Once sorted, fixing `nums[i]` reduces the remaining subarray `nums[i+1..N-1]` to a monotonic Two-Pointer search (`L = i+1`, `R = N-1`): if `sum < 0`, only `L++` can increase the sum; if `sum > 0`, only `R--` can decrease the sum.",
            "triggerSignal": "Find unique K-tuples summing to target -> Sort first + fix K-2 elements + inward Two Pointers `L, R` with duplicate skipping (`nums[i] == nums[i-1]`).",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Sort `nums` in ascending order first. If `nums[i] > 0`, you can stop immediately.",
            "Tier 2 (State & Invariant): For each anchor `i` (skipping `i > 0 and nums[i] == nums[i-1]`), place `L = i + 1` and `R = n - 1`.",
            "Tier 3 (Transition Blueprint): When `nums[i] + nums[L] + nums[R] == 0`, record the triplet, advance both `L` and `R`, and skip consecutive duplicate values at `L` and `R`.",
        ],
        "funcName": "threeSum",
        "starterCode": {
            "python": "def threeSum(nums: list[int]) -> list[list[int]]:\n    # Sort + Two Pointers in O(N^2) time\n    pass\n",
            "go": "package main\n\nfunc threeSum(nums []int) [][]int {\n\t// Sort + Two Pointers in O(N^2) time\n\treturn nil\n}\n",
            "typescript": "function threeSum(nums: number[]): number[][] {\n  // Sort + Two Pointers in O(N^2) time\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "def threeSum(nums: list[int]) -> list[list[int]]:\n"
                "    nums.sort()\n"
                "    n = len(nums)\n"
                "    res: list[list[int]] = []\n"
                "    for i in range(n - 2):\n"
                "        if nums[i] > 0:\n"
                "            break\n"
                "        if i > 0 and nums[i] == nums[i - 1]:\n"
                "            continue\n"
                "        l, r = i + 1, n - 1\n"
                "        while l < r:\n"
                "            s = nums[i] + nums[l] + nums[r]\n"
                "            if s < 0:\n"
                "                l += 1\n"
                "            elif s > 0:\n"
                "                r -= 1\n"
                "            else:\n"
                "                res.append([nums[i], nums[l], nums[r]])\n"
                "                l += 1\n"
                "                r -= 1\n"
                "                while l < r and nums[l] == nums[l - 1]:\n"
                "                    l += 1\n"
                "                while l < r and nums[r] == nums[r + 1]:\n"
                "                    r -= 1\n"
                "    return res\n"
            ),
            "go": (
                "package main\n\nimport \"sort\"\n\n"
                "func threeSum(nums []int) [][]int {\n"
                "\tsort.Ints(nums)\n"
                "\tn := len(nums)\n"
                "\tres := [][]int{}\n"
                "\tfor i := 0; i < n-2; i++ {\n"
                "\t\tif nums[i] > 0 {\n"
                "\t\t\tbreak\n"
                "\t\t}\n"
                "\t\tif i > 0 && nums[i] == nums[i-1] {\n"
                "\t\t\tcontinue\n"
                "\t\t}\n"
                "\t\tl, r := i+1, n-1\n"
                "\t\tfor l < r {\n"
                "\t\t\ts := nums[i] + nums[l] + nums[r]\n"
                "\t\t\tif s < 0 {\n"
                "\t\t\t\tl++\n"
                "\t\t\t} else if s > 0 {\n"
                "\t\t\t\tr--\n"
                "\t\t\t} else {\n"
                "\t\t\t\tres = append(res, []int{nums[i], nums[l], nums[r]})\n"
                "\t\t\t\tl++\n"
                "\t\t\t\tr--\n"
                "\t\t\t\tfor l < r && nums[l] == nums[l-1] {\n"
                "\t\t\t\t\tl++\n"
                "\t\t\t\t}\n"
                "\t\t\t\tfor l < r && nums[r] == nums[r+1] {\n"
                "\t\t\t\t\tr--\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn res\n"
                "}\n"
            ),
            "typescript": (
                "function threeSum(nums: number[]): number[][] {\n"
                "  nums.sort((a, b) => a - b);\n"
                "  const n = nums.length;\n"
                "  const res: number[][] = [];\n"
                "  for (let i = 0; i < n - 2; i++) {\n"
                "    if (nums[i] > 0) break;\n"
                "    if (i > 0 && nums[i] === nums[i - 1]) continue;\n"
                "    let l = i + 1;\n"
                "    let r = n - 1;\n"
                "    while (l < r) {\n"
                "      const s = nums[i] + nums[l] + nums[r];\n"
                "      if (s < 0) l++;\n"
                "      else if (s > 0) r--;\n"
                "      else {\n"
                "        res.push([nums[i], nums[l], nums[r]]);\n"
                "        l++;\n"
                "        r--;\n"
                "        while (l < r && nums[l] === nums[l - 1]) l++;\n"
                "        while (l < r && nums[r] === nums[r + 1]) r--;\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "  return res;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Sort `nums` ascending in O(N log N) time.\n"
            "2. Loop anchor `i` from `0` to `n-3`. Break early if `nums[i] > 0`. Skip duplicate anchors `nums[i] == nums[i-1]`.\n"
            "3. Sweep `l = i + 1` and `r = n - 1` inward. Each step eliminates either column `l` or row `r` from the 2D search matrix in O(1) time.\n"
            "4. When a zero-sum triplet is found, advance both pointers past any duplicate values."
        ),
        "traceSteps": [
            {"step": 1, "focus": "Sorted: [-4, -1, -1, 0, 1, 2]", "stateVars": "i=0 (-4), l=1 (-1), r=5 (2)", "note": "Max possible sum with -4 is -4+1+2 = -1 < 0; l reaches r."},
            {"step": 2, "focus": "i=1 (-1), l=2 (-1), r=5 (2)", "stateVars": "s = -1 + (-1) + 2 = 0", "note": "Match [-1, -1, 2]! Advance l=3, r=4."},
            {"step": 3, "focus": "i=1 (-1), l=3 (0), r=4 (1)", "stateVars": "s = -1 + 0 + 1 = 0", "note": "Match [-1, 0, 1]! Advance l=4, r=3 (loop ends)."},
            {"step": 4, "focus": "i=2 (-1)", "stateVars": "nums[2] == nums[1] (-1)", "note": "Skipped to prevent duplicate triplets."},
        ],
        "complexity": {
            "bruteTime": "O(N^3)",
            "bruteSpace": "O(N)",
            "optimalTime": "O(N^2)",
            "optimalSpace": "O(1) or O(log N) sort stack",
            "derivation": "Sorting takes O(N log N). For each of N anchors, `l` and `r` take at most N steps combined, yielding O(N^2) time.",
        },
        "interviewFollowUp": {
            "question": "How would you generalise this to `kSum` for an arbitrary `k >= 2`?",
            "answer": "Write a recursive helper `kSum(start, k, target)` that fixes one element and calls `kSum(i + 1, k - 1, target - nums[i])`, terminating at `k == 2` with the O(N) two-pointer base case. Overall time is O(N^(k-1)).",
        },
        "testCases": [
            {"args": [[-1, 0, 1, 2, -1, -4]], "expected": [[-1, -1, 2], [-1, 0, 1]], "label": "Standard mix"},
            {"args": [[0, 1, 1]], "expected": [], "label": "No valid triplet"},
            {"args": [[0, 0, 0, 0]], "expected": [[0, 0, 0]], "label": "All zeros"},
        ],
    },
    11: {
        "leetcodeId": "LC 42",
        "title": "Trapping Rain Water",
        "difficulty": "Hard",
        "phase": 2,
        "tags": ["Array", "Two Pointers", "Dynamic Programming", "Stack", "Monotonic Stack"],
        "url": "https://leetcode.com/problems/trapping-rain-water/",
        "statement": (
            "Given `n` non-negative integers representing an elevation map where the width of each bar is 1, "
            "compute how much water it can trap after raining."
        ),
        "examples": [
            {"input": "height = [0,1,0,2,1,0,1,3,2,1,2,1]", "output": "6", "explanation": "6 units of rain water are trapped between the bars."},
            {"input": "height = [4,2,0,3,2,5]", "output": "9", "explanation": "Water fills up to level min(4, 5) = 4 across the interior."},
        ],
        "constraints": ["1 <= len(height) <= 2 * 10^4", "0 <= height[i] <= 10^5", "Target Complexity: O(N) time, O(1) space"],
        "clarifyingQuestions": [
            "Can water sit on the very first or very last bar? (No, there is no outer wall beyond index `0` or `n-1`.)",
            "What determines the water depth above a single column `i`? (`max(0, min(maxLeft[i], maxRight[i]) - height[i])`.)",
            "Can we avoid storing the `O(N)` `maxLeft` and `maxRight` arrays? (Yes, two inward pointers `l` and `r` need only the smaller of `leftMax` and `rightMax` at each step!)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Trying to find matching peak pairs and integrating water horizontally between peaks, which gets tangled when inner peaks are shorter than outer peaks.",
            "optimalPivot": "Switch from 'horizontal ponds' to 'vertical 1-unit columns'. Column `i` traps `min(leftMax, rightMax) - height[i]`. Furthermore, if `leftMax <= rightMax`, we ALREADY know `min(leftMax, trueRightMaxForL) == leftMax` regardless of any taller wall unseen in `(l, r)`, so we can settle column `l` immediately in O(1) space!",
            "triggerSignal": "Whenever a per-index quantity depends on `min(prefixMax[i], suffixMax[i])`, inward two pointers can always resolve whichever side currently has the smaller boundary.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): How much water sits directly above column `i` if you know the tallest bar to its left and the tallest bar to its right?",
            "Tier 2 (State & Invariant): Keep pointers `l = 0, r = n - 1` and running walls `left_max = height[l], right_max = height[r]`.",
            "Tier 3 (Transition Blueprint): Always advance the pointer with the smaller wall (`if left_max <= right_max: l += 1`), update its `left_max`, and add `left_max - height[l]` to `water`.",
        ],
        "funcName": "trap",
        "starterCode": {
            "python": "def trap(height: list[int]) -> int:\n    # O(N) time, O(1) space two-pointer water calculation\n    pass\n",
            "go": "package main\n\nfunc trap(height []int) int {\n\t// O(N) time, O(1) space two-pointer water calculation\n\treturn 0\n}\n",
            "typescript": "function trap(height: number[]): number {\n  // O(N) time, O(1) space two-pointer water calculation\n  return 0;\n}\n",
        },
        "solutionCode": {
            "python": (
                "def trap(height: list[int]) -> int:\n"
                "    if not height:\n"
                "        return 0\n"
                "    l, r = 0, len(height) - 1\n"
                "    left_max, right_max = height[l], height[r]\n"
                "    water = 0\n"
                "    while l < r:\n"
                "        if left_max <= right_max:\n"
                "            l += 1\n"
                "            left_max = max(left_max, height[l])\n"
                "            water += left_max - height[l]\n"
                "        else:\n"
                "            r -= 1\n"
                "            right_max = max(right_max, height[r])\n"
                "            water += right_max - height[r]\n"
                "    return water\n"
            ),
            "go": (
                "package main\n\n"
                "func trap(height []int) int {\n"
                "\tif len(height) == 0 {\n"
                "\t\treturn 0\n"
                "\t}\n"
                "\tl, r := 0, len(height)-1\n"
                "\tleftMax, rightMax := height[l], height[r]\n"
                "\twater := 0\n"
                "\tfor l < r {\n"
                "\t\tif leftMax <= rightMax {\n"
                "\t\t\tl++\n"
                "\t\t\tif height[l] > leftMax {\n"
                "\t\t\t\tleftMax = height[l]\n"
                "\t\t\t}\n"
                "\t\t\twater += leftMax - height[l]\n"
                "\t\t} else {\n"
                "\t\t\tr--\n"
                "\t\t\tif height[r] > rightMax {\n"
                "\t\t\t\trightMax = height[r]\n"
                "\t\t\t}\n"
                "\t\t\twater += rightMax - height[r]\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn water\n"
                "}\n"
            ),
            "typescript": (
                "function trap(height: number[]): number {\n"
                "  if (height.length === 0) return 0;\n"
                "  let l = 0, r = height.length - 1;\n"
                "  let leftMax = height[l], rightMax = height[r];\n"
                "  let water = 0;\n"
                "  while (l < r) {\n"
                "    if (leftMax <= rightMax) {\n"
                "      l++;\n"
                "      leftMax = Math.max(leftMax, height[l]);\n"
                "      water += leftMax - height[l];\n"
                "    } else {\n"
                "      r--;\n"
                "      rightMax = Math.max(rightMax, height[r]);\n"
                "      water += rightMax - height[r];\n"
                "    }\n"
                "  }\n"
                "  return water;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Start pointers `l = 0` and `r = n - 1` with `left_max = height[0]` and `right_max = height[n-1]`.\n"
            "2. While `l < r`, compare `left_max` and `right_max`.\n"
            "3. If `left_max <= right_max`, the water level at `l + 1` is bottlenecked by `left_max` (since `right_max` on the right is already at least as tall). Advance `l`, update `left_max`, and accumulate `left_max - height[l]`.\n"
            "4. Symmetrically advance `r` when `right_max < left_max`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "height=[4,2,0,3,2,5]", "stateVars": "l=0(4), r=5(5) | leftMax=4, rightMax=5 | water=0", "note": "leftMax(4) <= rightMax(5), so left side is the bottleneck."},
            {"step": 2, "focus": "l=1 (height=2)", "stateVars": "leftMax=4 | water += 4-2 = 2", "note": "Column 1 traps 2 units."},
            {"step": 3, "focus": "l=2 (height=0)", "stateVars": "leftMax=4 | water += 4-0 = 6", "note": "Column 2 traps 4 units (total 6)."},
            {"step": 4, "focus": "l=3..4 (heights 3, 2)", "stateVars": "leftMax=4 | water = 6 + 1 + 2 = 9", "note": "Columns 3 and 4 add 1 and 2 units. Total = 9."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(1)",
            "derivation": "Each iteration moves either `l` right or `r` left by 1, terminating in exactly N - 1 steps with O(1) scalar variables.",
        },
        "interviewFollowUp": {
            "question": "How does this generalise to a 2D elevation grid `heightMap[R][C]` (Trapping Rain Water II, LC 407)?",
            "answer": "In 2D, the boundary is a closed ring of cells rather than two endpoints `l` and `r`. Push all border cells into a Min-Heap, and repeatedly pop the lowest boundary cell `(h, r, c)` (the 'lowest plank in the barrel'), relaxing unvisited neighbours with water level `max(h, heightMap[nr][nc])` in O(R*C log(R*C)) time.",
        },
        "testCases": [
            {"args": [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], "expected": 6, "label": "Classic elevation map"},
            {"args": [[4, 2, 0, 3, 2, 5]], "expected": 9, "label": "Deep basin"},
            {"args": [[3, 2, 1]], "expected": 0, "label": "Monotonic descending"},
        ],
    },
    12: {
        "leetcodeId": "LC 3",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "phase": 2,
        "tags": ["String", "Hash Table", "Sliding Window"],
        "url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
        "statement": "Given a string `s`, find the length of the longest contiguous substring without repeating characters.",
        "examples": [
            {"input": 's = "abcabcbb"', "output": "3", "explanation": "The answer is 'abc', with length 3."},
            {"input": 's = "bbbbb"', "output": "1", "explanation": "The answer is 'b', with length 1."},
            {"input": 's = "pwwkew"', "output": "3", "explanation": "The answer is 'wke', with length 3."},
        ],
        "constraints": ["0 <= len(s) <= 5 * 10^4", "s consists of English letters, digits, symbols and spaces", "Target Complexity: O(N) time, O(min(N, Sigma)) space"],
        "clarifyingQuestions": [
            "Is the problem asking for a contiguous substring or a subsequence? (Substring: characters must be contiguous.)",
            "Can `s` be empty `\"\"`? (Yes, `0 <= len(s)`, so return `0` for empty input.)",
            "Why must we do `left = max(left, last_seen[ch] + 1)` instead of `left = last_seen[ch] + 1`? (Because `last_seen[ch]` might lie to the left of `left` from an old window, e.g., `'abba'` at the second `'a'`!)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Restarting the scan from `left + 1` whenever a duplicate is hit (O(N^2)), or moving `left` backward to an expired index.",
            "optimalPivot": "Maintain a sliding window `[left..right]` whose invariant is 'all characters inside `[left..right]` are unique'. When `s[right]` was previously seen at index `prev >= left`, jump `left` directly to `prev + 1`.",
            "triggerSignal": "Longest/shortest contiguous subarray or substring satisfying a monotonic validity condition -> Sliding Window `[left..right]`.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): For each right endpoint `r`, what is the furthest left endpoint `l` such that `s[l..r]` has no duplicates?",
            "Tier 2 (State & Invariant): Store `last_idx[ch] = most_recent_index` in a dictionary and track window start `left = 0`.",
            "Tier 3 (Transition Blueprint): When `ch` is in `last_idx` and `last_idx[ch] >= left`, advance `left = last_idx[ch] + 1`. Update `best = max(best, r - left + 1)`.",
        ],
        "funcName": "lengthOfLongestSubstring",
        "starterCode": {
            "python": "def lengthOfLongestSubstring(s: str) -> int:\n    # O(N) sliding window with last-seen index map\n    pass\n",
            "go": "package main\n\nfunc lengthOfLongestSubstring(s string) int {\n\t// O(N) sliding window with last-seen index map\n\treturn 0\n}\n",
            "typescript": "function lengthOfLongestSubstring(s: string): number {\n  // O(N) sliding window with last-seen index map\n  return 0;\n}\n",
        },
        "solutionCode": {
            "python": (
                "def lengthOfLongestSubstring(s: str) -> int:\n"
                "    last_idx: dict[str, int] = {}\n"
                "    left = 0\n"
                "    best = 0\n"
                "    for right, ch in enumerate(s):\n"
                "        if ch in last_idx and last_idx[ch] >= left:\n"
                "            left = last_idx[ch] + 1\n"
                "        last_idx[ch] = right\n"
                "        if right - left + 1 > best:\n"
                "            best = right - left + 1\n"
                "    return best\n"
            ),
            "go": (
                "package main\n\n"
                "func lengthOfLongestSubstring(s string) int {\n"
                "\tlastIdx := make(map[byte]int)\n"
                "\tleft, best := 0, 0\n"
                "\tfor right := 0; right < len(s); right++ {\n"
                "\t\tch := s[right]\n"
                "\t\tif prev, ok := lastIdx[ch]; ok && prev >= left {\n"
                "\t\t\tleft = prev + 1\n"
                "\t\t}\n"
                "\t\tlastIdx[ch] = right\n"
                "\t\tif right-left+1 > best {\n"
                "\t\t\tbest = right - left + 1\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn best\n"
                "}\n"
            ),
            "typescript": (
                "function lengthOfLongestSubstring(s: string): number {\n"
                "  const lastIdx = new Map<string, number>();\n"
                "  let left = 0;\n"
                "  let best = 0;\n"
                "  for (let right = 0; right < s.length; right++) {\n"
                "    const ch = s[right];\n"
                "    const prev = lastIdx.get(ch);\n"
                "    if (prev !== undefined && prev >= left) {\n"
                "      left = prev + 1;\n"
                "    }\n"
                "    lastIdx.set(ch, right);\n"
                "    best = Math.max(best, right - left + 1);\n"
                "  }\n"
                "  return best;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Track the window start `left = 0` and a map `last_idx` from character to its most recent index.\n"
            "2. For each `(right, ch)`, if `last_idx[ch] >= left`, the current window contains a duplicate `ch`, so jump `left` to `last_idx[ch] + 1`.\n"
            "3. Record `last_idx[ch] = right` and update `best = max(best, right - left + 1)`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "s='abba', r=0..1 ('a','b')", "stateVars": "left=0 | last={'a':0, 'b':1} | best=2", "note": "Window 'ab' has length 2."},
            {"step": 2, "focus": "r=2 ('b')", "stateVars": "prev('b')=1 >= left(0) -> left=2 | best=2", "note": "Duplicate 'b' jumps left to index 2."},
            {"step": 3, "focus": "r=3 ('a')", "stateVars": "prev('a')=0 < left(2) -> left stays 2! | best=2", "note": "Old 'a' at 0 is outside [2..3]; window 'ba' has length 2."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(Sigma)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(min(N, Sigma))",
            "derivation": "Single pass over `s` with O(1) hash map lookups per character.",
        },
        "interviewFollowUp": {
            "question": "What if you are allowed at most `k` distinct characters in the window (LC 340)?",
            "answer": "Instead of jumping on any duplicate, store either counts inside the window or the rightmost index of each distinct character in the window. When `len(window_map) > k`, evict the character with the minimum `last_idx` and set `left = min_idx + 1`.",
        },
        "testCases": [
            {"args": ["abcabcbb"], "expected": 3, "label": "Repeating pattern"},
            {"args": ["bbbbb"], "expected": 1, "label": "All identical"},
            {"args": ["abba"], "expected": 2, "label": "Stale index trap ('abba')"},
            {"args": [""], "expected": 0, "label": "Empty string"},
        ],
    },
    18: {
        "leetcodeId": "LC 739",
        "title": "Daily Temperatures",
        "difficulty": "Medium",
        "phase": 3,
        "tags": ["Array", "Stack", "Monotonic Stack"],
        "url": "https://leetcode.com/problems/daily-temperatures/",
        "statement": (
            "Given an array of integers `temperatures` represents the daily temperatures, return an array `answer` "
            "such that `answer[i]` is the number of days you have to wait after the `i`-th day to get a warmer temperature. "
            "If there is no future day for which this is possible, keep `answer[i] == 0`."
        ),
        "examples": [
            {"input": "temperatures = [73,74,75,71,69,72,76,73]", "output": "[1,1,4,2,1,1,0,0]", "explanation": "For 75 at index 2, the next warmer day is 76 at index 6 (6 - 2 = 4 days)."},
        ],
        "constraints": ["1 <= len(temperatures) <= 10^5", "30 <= temperatures[i] <= 100", "Target Complexity: O(N) time, O(N) space"],
        "clarifyingQuestions": [
            "Does 'warmer' mean strictly greater (`>`) or greater than or equal (`>=`)? (Strictly greater: `temperatures[j] > temperatures[i]`.)",
            "Should the stack store temperature values or array indices? (Array indices `i`, because we need `i - prev_i` for the wait duration AND can still read `temperatures[stack[-1]]`.)",
            "Why is a loop with a nested `while` over the stack still O(N) overall? (Amortised analysis: each index is pushed onto the stack once and popped at most once.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "For each day `i`, scanning forward `j = i+1..n-1` until `temperatures[j] > temperatures[i]`, which degrades to O(N^2) on decreasing arrays like `[90, 89, 88, ..., 30]`.",
            "optimalPivot": "Instead of each day searching forward for its warmer future, let each new day `i` look backward and resolve all waiting colder days on top of a Monotonic Decreasing Stack.",
            "triggerSignal": "'Next Greater Element' or 'Next Smaller Element' to the left or right -> Monotonic Stack storing unresolved indices.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): Which previous days get their answer resolved as soon as today's temperature `temp` arrives?",
            "Tier 2 (State & Invariant): Maintain a stack of indices `stack` whose temperatures are strictly non-increasing from bottom to top.",
            "Tier 3 (Transition Blueprint): While `stack` is non-empty and `temperatures[i] > temperatures[stack[-1]]`, pop `prev = stack.pop()` and set `ans[prev] = i - prev`. Then push `i`.",
        ],
        "funcName": "dailyTemperatures",
        "starterCode": {
            "python": "def dailyTemperatures(temperatures: list[int]) -> list[int]:\n    # Monotonic decreasing stack in O(N) amortised time\n    pass\n",
            "go": "package main\n\nfunc dailyTemperatures(temperatures []int) []int {\n\t// Monotonic decreasing stack in O(N) amortised time\n\treturn nil\n}\n",
            "typescript": "function dailyTemperatures(temperatures: number[]): number[] {\n  // Monotonic decreasing stack in O(N) amortised time\n  return [];\n}\n",
        },
        "solutionCode": {
            "python": (
                "def dailyTemperatures(temperatures: list[int]) -> list[int]:\n"
                "    n = len(temperatures)\n"
                "    ans = [0] * n\n"
                "    stack: list[int] = []\n"
                "    for i, t in enumerate(temperatures):\n"
                "        while stack and t > temperatures[stack[-1]]:\n"
                "            prev = stack.pop()\n"
                "            ans[prev] = i - prev\n"
                "        stack.append(i)\n"
                "    return ans\n"
            ),
            "go": (
                "package main\n\n"
                "func dailyTemperatures(temperatures []int) []int {\n"
                "\tn := len(temperatures)\n"
                "\tans := make([]int, n)\n"
                "\tstack := make([]int, 0, n)\n"
                "\tfor i, t := range temperatures {\n"
                "\t\tfor len(stack) > 0 && t > temperatures[stack[len(stack)-1]] {\n"
                "\t\t\tprev := stack[len(stack)-1]\n"
                "\t\t\tstack = stack[:len(stack)-1]\n"
                "\t\t\tans[prev] = i - prev\n"
                "\t\t}\n"
                "\t\tstack = append(stack, i)\n"
                "\t}\n"
                "\treturn ans\n"
                "}\n"
            ),
            "typescript": (
                "function dailyTemperatures(temperatures: number[]): number[] {\n"
                "  const n = temperatures.length;\n"
                "  const ans = new Array<number>(n).fill(0);\n"
                "  const stack: number[] = [];\n"
                "  for (let i = 0; i < n; i++) {\n"
                "    while (stack.length > 0 && temperatures[i] > temperatures[stack[stack.length - 1]]) {\n"
                "      const prev = stack.pop()!;\n"
                "      ans[prev] = i - prev;\n"
                "    }\n"
                "    stack.push(i);\n"
                "  }\n"
                "  return ans;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Initialise `ans = [0] * n` and an empty index stack `stack`.\n"
            "2. For each day `(i, t)`, pop every index `prev` from the top of `stack` whose temperature is strictly less than `t`, setting `ans[prev] = i - prev`.\n"
            "3. Push `i` onto `stack`. Any indices remaining on `stack` at the end never saw a warmer day and keep `ans[idx] = 0`."
        ),
        "traceSteps": [
            {"step": 1, "focus": "i=0..1: 73, 74", "stateVars": "74 > 73 -> pop 0, ans[0]=1 | stack=[1(74)]", "note": "74 resolves day 0 immediately."},
            {"step": 2, "focus": "i=2..4: 75, 71, 69", "stateVars": "ans=[1,1,0,0,0...] | stack=[2(75), 3(71), 4(69)]", "note": "Colder days stack in decreasing order."},
            {"step": 3, "focus": "i=5: 72", "stateVars": "72 pops 4(69) & 3(71) -> ans[4]=1, ans[3]=2 | stack=[2(75), 5(72)]", "note": "Single day 72 resolves two waiting days at once."},
        ],
        "complexity": {
            "bruteTime": "O(N^2)",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N)",
            "optimalSpace": "O(N)",
            "derivation": "Each index is pushed once and popped at most once across the entire loop (2N stack operations max).",
        },
        "interviewFollowUp": {
            "question": "Can you solve this in O(1) extra space (excluding the output array `ans`)?",
            "answer": "Yes! Iterate backward from `i = n - 2` down to `0` while tracking `hottest`. If `temperatures[i] < hottest`, jump forward using the already-computed `ans` array (`j += ans[j]`) until `temperatures[j] > temperatures[i]`. That uses `ans` itself as an implicit monotonic jump table in O(N) amortised time and O(1) extra space.",
        },
        "testCases": [
            {"args": [[73, 74, 75, 71, 69, 72, 76, 73]], "expected": [1, 1, 4, 2, 1, 1, 0, 0], "label": "Standard forecast"},
            {"args": [[30, 40, 50, 60]], "expected": [1, 1, 1, 0], "label": "Strictly increasing"},
            {"args": [[60, 50, 40]], "expected": [0, 0, 0], "label": "Strictly decreasing"},
        ],
    },
    27: {
        "leetcodeId": "LC 875",
        "title": "Koko Eating Bananas",
        "difficulty": "Medium",
        "phase": 4,
        "tags": ["Array", "Binary Search"],
        "url": "https://leetcode.com/problems/koko-eating-bananas/",
        "statement": (
            "Koko loves to eat bananas. There are `n` piles of bananas, the `i`-th pile has `piles[i]` bananas. "
            "The guards have gone and will come back in `h` hours.\n\n"
            "Koko can decide her bananas-per-hour eating speed of `k`. Each hour, she chooses a pile and eats `k` bananas from it. "
            "If the pile has less than `k` bananas, she eats all of them and will not eat any more bananas during that hour.\n\n"
            "Return the minimum integer `k` such that she can eat all the bananas within `h` hours."
        ),
        "examples": [
            {"input": "piles = [3,6,7,11], h = 8", "output": "4", "explanation": "At speed 4, hours needed = ceil(3/4)+ceil(6/4)+ceil(7/4)+ceil(11/4) = 1+2+2+3 = 8."},
            {"input": "piles = [30,11,23,4,20], h = 5", "output": "30", "explanation": "With h == len(piles), she must finish the largest pile in 1 hour."},
        ],
        "constraints": ["1 <= len(piles) <= 10^4", "len(piles) <= h <= 10^9", "1 <= piles[i] <= 10^9", "Target Complexity: O(N log(max(piles))) time, O(1) space"],
        "clarifyingQuestions": [
            "Why is `h >= len(piles)` guaranteed? (Because she can eat from at most one pile per hour; if `h < len(piles)`, no finite speed `k` could ever finish in time.)",
            "What is the tightest upper bound on `k`? (`max(piles)`, because eating faster than the largest pile still takes 1 full hour per pile.)",
            "How do we compute `ceil(p / k)` using integer arithmetic without floating-point precision bugs? (`(p + k - 1) // k`.)",
        ],
        "mentalModel": {
            "instinctiveTrap": "Trying to derive a closed-form algebraic formula for `k`, or testing `k = 1, 2, 3, ...` linearly up to `10^9` (which TLEs).",
            "optimalPivot": "Notice that `canFinish(k)` is a MONOTONIC boolean function: for small `k` it is `False, False, ..., False`, and starting at some threshold `k*` it becomes `True, True, ..., True` forever. Binary search the answer range `[1, max(piles)]` to find the first `True`!",
            "triggerSignal": "'Minimum maximum' or 'Maximum minimum' where checking a candidate answer `mid` takes O(N) time and feasibility is monotonic -> Binary Search on Answer Space.",
        },
        "hints": [
            "Tier 1 (Pattern Cue): If Koko can finish in `h` hours at speed `k`, she can also finish at any speed `k' > k`. That monotonicity enables binary search.",
            "Tier 2 (State & Invariant): Search range `lo = 1, hi = max(piles)`. Write helper `hoursNeeded(k) = sum((p + k - 1) // k for p in piles)`.",
            "Tier 3 (Transition Blueprint): If `hoursNeeded(mid) <= h`, `mid` is feasible so set `hi = mid`; otherwise `mid` is too slow so set `lo = mid + 1`.",
        ],
        "funcName": "minEatingSpeed",
        "starterCode": {
            "python": "def minEatingSpeed(piles: list[int], h: int) -> int:\n    # Binary search on the answer space [1, max(piles)]\n    pass\n",
            "go": "package main\n\nfunc minEatingSpeed(piles []int, h int) int {\n\t// Binary search on the answer space [1, max(piles)]\n\treturn 0\n}\n",
            "typescript": "function minEatingSpeed(piles: number[], h: number): number {\n  // Binary search on the answer space [1, max(piles)]\n  return 0;\n}\n",
        },
        "solutionCode": {
            "python": (
                "def minEatingSpeed(piles: list[int], h: int) -> int:\n"
                "    lo, hi = 1, max(piles)\n"
                "    while lo < hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        hours = sum((p + mid - 1) // mid for p in piles)\n"
                "        if hours <= h:\n"
                "            hi = mid\n"
                "        else:\n"
                "            lo = mid + 1\n"
                "    return lo\n"
            ),
            "go": (
                "package main\n\n"
                "func minEatingSpeed(piles []int, h int) int {\n"
                "\tlo, hi := 1, 0\n"
                "\tfor _, p := range piles {\n"
                "\t\tif p > hi {\n"
                "\t\t\thi = p\n"
                "\t\t}\n"
                "\t}\n"
                "\tfor lo < hi {\n"
                "\t\tmid := lo + (hi-lo)/2\n"
                "\t\thours := 0\n"
                "\t\tfor _, p := range piles {\n"
                "\t\t\thours += (p + mid - 1) / mid\n"
                "\t\t}\n"
                "\t\tif hours <= h {\n"
                "\t\t\thi = mid\n"
                "\t\t} else {\n"
                "\t\t\tlo = mid + 1\n"
                "\t\t}\n"
                "\t}\n"
                "\treturn lo\n"
                "}\n"
            ),
            "typescript": (
                "function minEatingSpeed(piles: number[], h: number): number {\n"
                "  let lo = 1;\n"
                "  let hi = Math.max(...piles);\n"
                "  while (lo < hi) {\n"
                "    const mid = lo + Math.floor((hi - lo) / 2);\n"
                "    let hours = 0;\n"
                "    for (const p of piles) hours += Math.ceil(p / mid);\n"
                "    if (hours <= h) hi = mid;\n"
                "    else lo = mid + 1;\n"
                "  }\n"
                "  return lo;\n"
                "}\n"
            ),
        },
        "walkthrough": (
            "1. Bound the answer space: minimum possible speed `lo = 1`, maximum necessary speed `hi = max(piles)`.\n"
            "2. While `lo < hi`, test midpoint `mid = (lo + hi) // 2`.\n"
            "3. Sum ceiling divisions `(p + mid - 1) // mid` across all piles.\n"
            "4. If total hours `<= h`, `mid` works, so the minimum feasible speed is in `[lo, mid]` (`hi = mid`). Otherwise it is in `[mid + 1, hi]` (`lo = mid + 1`)."
        ),
        "traceSteps": [
            {"step": 1, "focus": "piles=[3,6,7,11], h=8", "stateVars": "lo=1, hi=11 -> mid=6", "note": "hours(6) = 1+1+2+2 = 6 <= 8 (feasible -> hi=6)."},
            {"step": 2, "focus": "lo=1, hi=6 -> mid=3", "stateVars": "hours(3) = 1+2+3+4 = 10 > 8", "note": "Too slow -> lo=4."},
            {"step": 3, "focus": "lo=4, hi=6 -> mid=5", "stateVars": "hours(5) = 1+2+2+3 = 8 <= 8", "note": "Feasible -> hi=5."},
            {"step": 4, "focus": "lo=4, hi=5 -> mid=4", "stateVars": "hours(4) = 1+2+2+3 = 8 <= 8", "note": "Feasible -> hi=4. lo==hi==4, return 4!"},
        ],
        "complexity": {
            "bruteTime": "O(N * max(piles))",
            "bruteSpace": "O(1)",
            "optimalTime": "O(N log(max(piles)))",
            "optimalSpace": "O(1)",
            "derivation": "At most log2(10^9) ~= 30 binary search iterations, each doing an O(N) scan of `piles`.",
        },
        "interviewFollowUp": {
            "question": "Can we tighten the lower bound `lo` from `1` before starting the binary search?",
            "answer": "Yes! Even if Koko never wastes a partial hour on any pile, she eats at most `k * h` bananas in `h` hours, so `lo = max(1, (sum(piles) + h - 1) // h)` is a tighter lower bound.",
        },
        "testCases": [
            {"args": [[3, 6, 7, 11], 8], "expected": 4, "label": "Standard 4 piles"},
            {"args": [[30, 11, 23, 4, 20], 5], "expected": 30, "label": "Tight hour limit"},
            {"args": [[30, 11, 23, 4, 20], 6], "expected": 23, "label": "One extra hour"},
        ],
    },
}

# Compact blueprint specifications for the remaining problems in Phases 1 to 5 (Days 1 to 42)
BLUEPRINTS_PART1: list[dict[str, Any]] = [
    # Phase 1 (Days 1-8)
    {"day": 6, "lc": "LC 128", "title": "Longest Consecutive Sequence", "diff": "Medium", "phase": 1, "tags": ["Array", "Hash Table", "Union-Find"], "url": "https://leetcode.com/problems/longest-consecutive-sequence/", "trap": "Sorting the array in O(N log N) time or starting a streak scan from every element (O(N^2)).", "pivot": "Put all numbers into a `set` and ONLY start counting a streak from `x` if `x - 1` is NOT in the set (meaning `x` is the true start of a streak).", "signal": "Unordered set + 'only start traversal at sequence roots (`x - 1 not in set`)' guarantees O(N) total work.", "func": "longestConsecutive", "type": "longest_consecutive"},
    {"day": 7, "lc": "LC 54", "title": "Spiral Matrix", "diff": "Medium", "phase": 1, "tags": ["Array", "Matrix", "Simulation"], "url": "https://leetcode.com/problems/spiral-matrix/", "trap": "Tracking complex corner state flags and direction vectors with ad-hoc index corrections.", "pivot": "Maintain 4 shrinking boundary walls (`top, bottom, left, right`). After sweeping each wall, increment/decrement that wall and check `top <= bottom and left <= right`.", "signal": "2D layer-by-layer traversal -> 4 explicit shrinking boundary pointers.", "func": "spiralOrder", "type": "spiral_matrix"},
    {"day": 8, "lc": "LC 204", "title": "Count Primes (Enumeration & Sieve)", "diff": "Medium", "phase": 1, "tags": ["Array", "Math", "Enumeration", "Number Theory"], "url": "https://leetcode.com/problems/count-primes/", "trap": "Testing primality of each number `k < n` individually in O(N * sqrt(N)).", "pivot": "Instead of testing if `k` is divisible by primes, enumerate multiples `p*p, p*p + p, ...` of each prime `p <= sqrt(n)` and cross them out in a boolean sieve.", "signal": "Bulk property across `1..N` -> Sieve / forward multiple enumeration starting at `p * p`.", "func": "countPrimes", "type": "count_primes"},
    # Phase 2 (Days 9-16)
    {"day": 10, "lc": "LC 11", "title": "Container With Most Water", "diff": "Medium", "phase": 2, "tags": ["Array", "Two Pointers", "Greedy"], "url": "https://leetcode.com/problems/container-with-most-water/", "trap": "Checking all N*(N-1)/2 pairs of vertical lines.", "pivot": "Start at maximum width `[0, n-1]`. Since area is limited by `min(height[l], height[r])`, keeping the shorter wall while shrinking width can never beat the current area, so greedily advance the shorter wall.", "signal": "Max product of `(r - l) * min(h[l], h[r])` -> Inward greedy two pointers discarding the shorter boundary.", "func": "maxArea", "type": "max_area"},
    {"day": 13, "lc": "LC 76", "title": "Minimum Window Substring", "diff": "Hard", "phase": 2, "tags": ["String", "Hash Table", "Sliding Window"], "url": "https://leetcode.com/problems/minimum-window-substring/", "trap": "Re-checking all 52 character counts on every step of the sliding window.", "pivot": "Track a single integer `formed` (how many distinct required characters have met their target frequency). Expand `r` until `formed == required`, then shrink `l` while keeping `formed == required`.", "signal": "Shortest substring containing a target multiset -> Expand `r` to satisfy, shrink `l` to minimise, track `formed == required` in O(1).", "func": "minWindow", "type": "min_window"},
    {"day": 14, "lc": "LC 239", "title": "Sliding Window Maximum", "diff": "Hard", "phase": 2, "tags": ["Array", "Queue", "Sliding Window", "Heap (Priority Queue)", "Monotonic Queue"], "url": "https://leetcode.com/problems/sliding-window-maximum/", "trap": "Calling `max(nums[i:i+k])` on every window in O(N*k) time.", "pivot": "Any older element in the window that is `<= nums[i]` can NEVER be the maximum of this or any future window. Maintain a Monotonic Decreasing Deque of indices.", "signal": "Max/min over a moving sliding window -> Monotonic Deque (pop expired from front, pop dominated from back).", "func": "maxSlidingWindow", "type": "max_sliding_window"},
    {"day": 15, "lc": "LC 347", "title": "Top K Frequent Elements (Bucket Sort)", "diff": "Medium", "phase": 2, "tags": ["Array", "Hash Table", "Sorting", "Heap (Priority Queue)", "Counting", "Bucket Sort", "Quickselect"], "url": "https://leetcode.com/problems/top-k-frequent-elements/", "trap": "Sorting all unique elements by frequency in O(N log N) time.", "pivot": "Since any element's frequency is bounded between `1` and `N`, allocate `N + 1` frequency buckets `buckets[freq]` and sweep from `N` down to `1` in O(N) time.", "signal": "Sorting keys whose values are bounded integers `1..N` -> Bucket Sort / Counting Sort in O(N).", "func": "topKFrequent", "type": "top_k_frequent"},
    {"day": 16, "lc": "LC 164", "title": "Maximum Gap (Radix & Counting Sort)", "diff": "Medium", "phase": 2, "tags": ["Array", "Sorting", "Bucket Sort", "Counting Sort", "Radix Sort"], "url": "https://leetcode.com/problems/maximum-gap/", "trap": "Comparison sorting in O(N log N) when the problem asks for linear O(N) time.", "pivot": "By the Pigeonhole Principle, the maximum gap across N elements spanning `[minV, maxV]` must be at least `ceil((maxV - minV) / (N - 1))`, or use base-10 Radix Sort via stable Counting Sort passes.", "signal": "Linear-time sorting of integers or adjacent gap extremes -> Radix Sort / Pigeonhole Bucket Sort.", "func": "maximumGap", "type": "maximum_gap"},
    # Phase 3 (Days 17-24)
    {"day": 17, "lc": "LC 20", "title": "Valid Parentheses", "diff": "Easy", "phase": 3, "tags": ["String", "Stack"], "url": "https://leetcode.com/problems/valid-parentheses/", "trap": "Counting total open vs closed brackets without checking LIFO nesting order (`([)]`).", "pivot": "Every closing bracket must match the most recently opened unclosed bracket, which is the exact invariant of a LIFO Stack.", "signal": "Nested matching delimiters or recursive grammar parsing -> LIFO Stack.", "func": "isValidParentheses", "type": "valid_parentheses"},
    {"day": 19, "lc": "LC 84", "title": "Largest Rectangle in Histogram", "diff": "Hard", "phase": 3, "tags": ["Array", "Stack", "Monotonic Stack"], "url": "https://leetcode.com/problems/largest-rectangle-in-histogram/", "trap": "Expanding left and right from each bar `i` in O(N^2) time.", "pivot": "Bar `h` can extend right until the first bar strictly shorter than `h`, and left back to the previous bar on a Monotonic Increasing Stack. Append a sentinel height `0` to flush all bars cleanly.", "signal": "Max rectangle / subarray where element `i` is the minimum -> Monotonic Increasing Stack finding previous & next smaller indices.", "func": "largestRectangleArea", "type": "largest_rectangle"},
    {"day": 20, "lc": "LC 206", "title": "Reverse Linked List & In-Place Pointer Surgery", "diff": "Easy", "phase": 3, "tags": ["Linked List", "Recursion"], "url": "https://leetcode.com/problems/reverse-linked-list/", "trap": "Allocating a new list or losing the `next` pointer before rewiring `curr.next = prev`.", "pivot": "Maintain a 3-pointer sliding window (`prev, curr, nxt`) across the linked list: save `nxt = curr.next`, flip `curr.next = prev`, advance `prev = curr, curr = nxt`.", "signal": "In-place linked list reversal -> 3-pointer state transition (`prev, curr, nxt`).", "func": "reverseListArray", "type": "reverse_list"},
    {"day": 21, "lc": "LC 143", "title": "Reorder List (Fast/Slow Midpoint + Merge)", "diff": "Medium", "phase": 3, "tags": ["Linked List", "Two Pointers", "Stack", "Recursion"], "url": "https://leetcode.com/problems/reorder-list/", "trap": "Indexing from the tail repeatedly in O(N^2) time.", "pivot": "Compose three O(N) linked-list primitives: (1) Floyd's tortoise-and-hare to find the middle, (2) in-place reverse of the second half, and (3) alternating zipper merge.", "signal": "Folding a linked list from both ends in O(1) space -> Split at midpoint + Reverse second half + Zipper merge.", "func": "reorderListArray", "type": "reorder_list"},
    {"day": 22, "lc": "LC 287", "title": "Find the Duplicate Number (Floyd Cycle Detection)", "diff": "Medium", "phase": 3, "tags": ["Array", "Two Pointers", "Binary Search", "Bit Manipulation"], "url": "https://leetcode.com/problems/find-the-duplicate-number/", "trap": "Sorting/modifying the read-only array or using an O(N) hash set when O(1) space is required.", "pivot": "Treat array values in `[1..n]` as next-node pointers `f(x) = nums[x]`. Two indices pointing to the same value create a cycle entry point detectable via Floyd's Tortoise & Hare in O(1) space.", "signal": "Array of N+1 integers in `[1..N]` with O(1) space -> Pointer-graph cycle detection (`slow = nums[slow], fast = nums[nums[fast]]`).", "func": "findDuplicate", "type": "find_duplicate"},
    {"day": 23, "lc": "LC 622", "title": "Design Circular Queue & Flatten Nested Iterator", "diff": "Medium", "phase": 3, "tags": ["Array", "Linked List", "Design", "Queue", "Iterator"], "url": "https://leetcode.com/problems/design-circular-queue/", "trap": "Shifting array elements on `dequeue` in O(N) time or eagerly flattening an entire stream in the constructor.", "pivot": "Use a fixed ring buffer with `head` and `(head + count) % capacity` for O(1) queueing, and lazy stack-top preparation inside `hasNext()` for iterators.", "signal": "Bounded FIFO buffer -> Ring Buffer (`(head + size) % cap`); Lazy tree/list iterator -> Normalise top of stack in `hasNext()`.", "func": "simulateCircularQueue", "type": "circular_queue"},
    {"day": 24, "lc": "LC 432", "title": "All O(1) Data Structure (Doubly-Linked Frequency Buckets)", "diff": "Hard", "phase": 3, "tags": ["Hash Table", "Linked List", "Design", "Doubly-Linked List"], "url": "https://leetcode.com/problems/all-oone-data-structure/", "trap": "Using a heap or balanced BST for min/max frequency, which costs O(log N) instead of strict O(1).", "pivot": "Maintain a Doubly-Linked List of frequency nodes sorted by count (`1 <-> 2 <-> 5`). When a key's count changes by +/-1, it only ever moves to an adjacent node in O(1) time!", "signal": "Strict O(1) min and max under +/-1 count updates -> Hash Map + Doubly-Linked List of frequency buckets.", "func": "simulateAllOne", "type": "all_one"},
    # Phase 4 (Days 25-32)
    {"day": 25, "lc": "LC 33", "title": "Search in Rotated Sorted Array", "diff": "Medium", "phase": 4, "tags": ["Array", "Binary Search"], "url": "https://leetcode.com/problems/search-in-rotated-sorted-array/", "trap": "Doing a linear scan to find the rotation pivot before binary searching.", "pivot": "Whenever you split a rotated sorted array at `mid`, AT LEAST ONE half (`[lo..mid]` or `[mid..hi]`) is guaranteed to be strictly sorted. Check which half is sorted, then check if `target` lies inside that sorted half.", "signal": "Rotated sorted array -> Identify the intact sorted half (`nums[lo] <= nums[mid]`), test range membership, and halve.", "func": "searchRotated", "type": "search_rotated"},
    {"day": 26, "lc": "LC 4", "title": "Median of Two Sorted Arrays", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer"], "url": "https://leetcode.com/problems/median-of-two-sorted-arrays/", "trap": "Merging both arrays in O(M + N) time instead of O(log(min(M, N))).", "pivot": "Binary search the partition cut `i` in the smaller array `A`; that automatically fixes the cut `j = half - i` in `B`. Valid median cut iff `A[i-1] <= B[j]` and `B[j-1] <= A[i]`.", "signal": "K-th element or median of two sorted arrays in logarithmic time -> Binary search the partition cut on the shorter array.", "func": "findMedianSortedArrays", "type": "median_two_sorted"},
    {"day": 28, "lc": "LC 410", "title": "Split Array Largest Sum", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Dynamic Programming", "Greedy", "Prefix Sum"], "url": "https://leetcode.com/problems/split-array-largest-sum/", "trap": "Writing an O(N^2 * K) dynamic programming table when N*K is large.", "pivot": "Flip the problem: 'Given a maximum allowed subarray sum `cap`, how many subarrays do we greedily need?' If `needed <= k`, `cap` is feasible. Binary search `cap` in `[max(nums), sum(nums)]`.", "signal": "Minimise the maximum contiguous partition sum into K parts -> Binary search the cap + greedy linear check.", "func": "splitArray", "type": "split_array"},
    {"day": 29, "lc": "LC 215", "title": "Kth Largest Element (Three-Way Quickselect)", "diff": "Medium", "phase": 4, "tags": ["Array", "Divide and Conquer", "Sorting", "Heap (Priority Queue)", "Quickselect", "Randomized"], "url": "https://leetcode.com/problems/kth-largest-element-in-an-array/", "trap": "Full O(N log N) sort or 2-way partition that degrades to O(N^2) on all-equal inputs.", "pivot": "Use randomised 3-way Dutch National Flag partitioning (`< pivot`, `== pivot`, `> pivot`) and recurse ONLY into the single partition containing index `k`, achieving O(N) expected time.", "signal": "Selection of rank K without sorting the remaining elements -> Randomised 3-Way Quickselect.", "func": "findKthLargest", "type": "kth_largest"},
    {"day": 30, "lc": "LC 315", "title": "Count of Smaller Numbers After Self (Merge Sort Tree)", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer", "Binary Indexed Tree", "Segment Tree", "Merge Sort"], "url": "https://leetcode.com/problems/count-of-smaller-numbers-after-self/", "trap": "Scanning right for every element in O(N^2) time.", "pivot": "During Merge Sort, whenever an element from the left half is placed after `right_cnt` elements from the right half have already been merged, those `right_cnt` elements were originally to its right and strictly smaller!", "signal": "Counting inversions or smaller-after-self pairs -> Divide & Conquer Merge Sort counting cross-half jumps.", "func": "countSmaller", "type": "count_smaller"},
    {"day": 31, "lc": "LC 1095", "title": "Find in Mountain Array (Interactive Binary Search)", "diff": "Hard", "phase": 4, "tags": ["Array", "Binary Search", "Interactive"], "url": "https://leetcode.com/problems/find-in-mountain-array/", "trap": "Querying `MountainArray.get(i)` linearly and exceeding the strict 100-call interactive API budget.", "pivot": "Cache API calls and run three binary searches: (1) find the peak index where `get(m) < get(m+1)` flips, (2) ascending binary search on `[0..peak]`, (3) descending binary search on `[peak+1..n-1]`.", "signal": "Bitonic / unimodal array or interactive query budget -> Binary search derivative sign `f(m) < f(m+1)` for peak.", "func": "findInMountainArray", "type": "mountain_array"},
    {"day": 32, "lc": "LC 240", "title": "Search a 2D Matrix II (Staircase Elimination)", "diff": "Medium", "phase": 4, "tags": ["Array", "Binary Search", "Divide and Conquer", "Matrix"], "url": "https://leetcode.com/problems/search-a-2d-matrix-ii/", "trap": "Starting at top-left `(0, 0)` where both right and down increase, leaving you unable to eliminate a row or column.", "pivot": "Start at top-right `(0, cols - 1)` (the saddle point): going down increases values and going left decreases values, so every comparison eliminates an entire row or column in O(R + C) time.", "signal": "Row-sorted and column-sorted 2D matrix -> Start at saddle corner `(0, C-1)` or `(R-1, 0)`.", "func": "searchMatrix", "type": "search_matrix"},
    # Phase 5 (Days 33-42)
    {"day": 33, "lc": "LC 104", "title": "Maximum Depth & Balanced Binary Tree Contract", "diff": "Easy", "phase": 5, "tags": ["Tree", "Depth-First Search", "Breadth-First Search", "Binary Tree", "Recursion"], "url": "https://leetcode.com/problems/maximum-depth-of-binary-tree/", "trap": "Recomputing `height(node)` at every node in O(N^2) on skewed trees.", "pivot": "Use a bottom-up postorder DFS where each child returns its height (or `-1` if unbalanced) in a single O(N) pass.", "signal": "Subtree property depends on left and right child heights -> Postorder bottom-up DFS returning height.", "func": "maxDepthLevelOrder", "type": "max_depth_tree"},
    {"day": 34, "lc": "LC 543", "title": "Diameter of Binary Tree", "diff": "Easy", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/diameter-of-binary-tree/", "trap": "Assuming the longest path must pass through the root node.", "pivot": "Distinguish between what a node updates globally (`best = max(best, left_h + right_h)` when acting as the highest bend point) vs what it returns upward to its parent (`1 + max(left_h, right_h)`).", "signal": "Tree path that can bend at any node -> Update global answer with `left + right`, return single-branch `1 + max(left, right)`.", "func": "diameterOfBinaryTree", "type": "diameter_tree"},
    {"day": 35, "lc": "LC 124", "title": "Binary Tree Maximum Path Sum", "diff": "Hard", "phase": 5, "tags": ["Dynamic Programming", "Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/binary-tree-maximum-path-sum/", "trap": "Forgetting to clamp negative downward branches to `0`, or returning a split V-path upward to the parent (which would create an invalid branched Y-path).", "pivot": "Clamp child gains with `left_gain = max(0, dfs(node.left))`. At `node`, candidate split path is `node.val + left_gain + right_gain`, while upward return value is `node.val + max(left_gain, right_gain)`.", "signal": "Weighted tree path maximisation -> Postorder DFS with `max(0, child_gain)` clamping.", "func": "maxPathSum", "type": "max_path_sum"},
    {"day": 36, "lc": "LC 102", "title": "Binary Tree Level Order & Right Side View", "diff": "Medium", "phase": 5, "tags": ["Tree", "Breadth-First Search", "Binary Tree", "Queue"], "url": "https://leetcode.com/problems/binary-tree-level-order-traversal/", "trap": "Mixing nodes from different depths in the BFS queue without snapshotting `level_size = len(queue)`.", "pivot": "Snapshot `level_size = len(queue)` at the start of each `while queue:` iteration so you process one complete depth layer per outer loop.", "signal": "Depth-by-depth tree processing -> BFS queue with inner `for _ in range(len(queue)):` loop.", "func": "levelOrder", "type": "level_order"},
    {"day": 37, "lc": "LC 98", "title": "Validate Binary Search Tree", "diff": "Medium", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Search Tree", "Binary Tree"], "url": "https://leetcode.com/problems/validate-binary-search-tree/", "trap": "Only checking `node.left.val < node.val < node.right.val` locally, missing a grandchild in the right subtree that is smaller than the root.", "pivot": "Pass down the valid open interval `(low, high)` to each recursive call: going left tightens the upper bound to `(low, node.val)`, going right tightens the lower bound to `(node.val, high)`.", "signal": "Global ancestor constraint on tree nodes -> Top-down DFS passing tightened `(min_bound, max_bound)`.", "func": "isValidBST", "type": "valid_bst"},
    {"day": 38, "lc": "LC 236", "title": "Lowest Common Ancestor of a Binary Tree", "diff": "Medium", "phase": 5, "tags": ["Tree", "Depth-First Search", "Binary Tree"], "url": "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/", "trap": "Building explicit root-to-node path arrays and parent hash maps when a single postorder traversal suffices.", "pivot": "If `root` is `None`, `p`, or `q`, return `root`. Recurse left and right: if both return non-null, `root` is the exact split point (LCA); otherwise bubble up whichever side is non-null.", "signal": "Find join point of two targets in a tree -> Postorder bubble-up DFS.", "func": "lowestCommonAncestor", "type": "lca_tree"},
    {"day": 39, "lc": "LC 297", "title": "Serialize and Deserialize Binary Tree", "diff": "Hard", "phase": 5, "tags": ["String", "Tree", "Depth-First Search", "Breadth-First Search", "Design", "Binary Tree"], "url": "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/", "trap": "Using inorder + preorder without unique values (which fails when duplicate node values exist).", "pivot": "Preorder traversal with explicit `'#'` null markers uniquely encodes tree topology in O(N) tokens without needing inorder, and reconstructs cleanly via a shared token iterator.", "signal": "Lossless tree serialisation -> Preorder DFS with explicit null sentinels (`'#'`).", "func": "codecRoundTrip", "type": "serialize_tree"},
    {"day": 40, "lc": "LC 208", "title": "Implement Prefix Trie", "diff": "Medium", "phase": 5, "tags": ["String", "Hash Table", "Design", "Trie"], "url": "https://leetcode.com/problems/implement-trie-prefix-tree/", "trap": "Scanning a list of all words for `startsWith(prefix)` in O(N * L) time.", "pivot": "Represent shared string prefixes as shared paths from the root of a 26-way character tree (`TrieNode`), making both `search(word)` and `startsWith(prefix)` depend only on query length `O(L)`.", "signal": "Prefix queries, autocomplete, or dictionary word search -> Prefix Trie with `is_end` boolean flag.", "func": "simulateTrie", "type": "trie_ops"},
    {"day": 41, "lc": "LC 212", "title": "Word Search II (Trie + Grid Backtracking Pruning)", "diff": "Hard", "phase": 5, "tags": ["Array", "String", "Backtracking", "Trie", "Matrix"], "url": "https://leetcode.com/problems/word-search-ii/", "trap": "Running a separate grid DFS for each of the 30,000 dictionary words.", "pivot": "Insert all dictionary words into one Trie, then run a single DFS from each board cell walking the board and the Trie simultaneously, pruning dead Trie leaves once matched!", "signal": "Matching many patterns against a 2D board -> Build one Trie of patterns and walk board + Trie together.", "func": "findWords", "type": "word_search_ii"},
]
