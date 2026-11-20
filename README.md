# Algo Studio

Offline coding interview workbench built for Chromebooks (zero Terminal required) as well as Windows, macOS, and Linux. Practise all 406 problems across 6 structured courses with no account sign-in and no package installs.

## Quick start on Chromebook (no Terminal needed)

If your Chromebook does not have Linux Terminal access, use the single self-contained file `AlgoStudio.html` (under 1 MB) directly in Chrome:

1. Open this repository (`https://github.com/elim316/algo-studio`) in Chrome on your Chromebook and click `AlgoStudio.html` in the file list.
2. Click the Download raw file icon at the top right of the file view (or press `Ctrl+S` on the Raw view) to save `AlgoStudio.html` into your Chromebook `Downloads` folder.
3. Open the ChromeOS Files app, go to `Downloads`, and double-click `AlgoStudio.html`. It opens straight in Chrome with zero setup.

How single-file mode works:
- Instant offline browsing and study: all 406 problems, 6 courses, 601 hidden edge cases, 9-domain edge-case playbook, Guided Coaching, Pressure Recall Drills, and native TypeScript execution load immediately from the file itself.
- In-browser Python 3 and SQLite 3: the first time you run a Python or SQL 50 solution (or click Analyse / AI Co-Pilot), Chrome loads the Pyodide WebAssembly Python 3 and SQLite 3 runtime (~12 MB) directly inside the browser tab and caches it automatically for subsequent runs.
- Persistent Chromebook progress: solved questions, passed submission history, course positions, code drafts, bookmarks, notes, drill high scores, and mock/OA history save automatically in browser `localStorage`. Click `Export` in the top toolbar anytime to download a JSON backup to `Downloads`, or `Import` to restore it on another device.

## Courses included

Switch courses anytime from the Course dropdown next to the problem selector. Solved progress stays synchronised across every course by LeetCode problem number.

- Our 120-Day List: 120 progressive SWE and FDE interview problems across 16 phases covering 86 algorithmic and systems topics, paired with 601 hidden edge-case tests and a 9-domain edge-case playbook.
- LeetCode Top 150: all 150 official interview problems organised across 23 categories.
- Grind 75 and Grind 70 (Core): Tech Interview Handbook's 8-week schedule with a direct Grind 70 Core course option.
- NeetCode 150 Skill-Tree: all 150 problems across 18 modules with an interactive SVG prerequisite graph.
- SQL 50 Relational Mastery: all 50 relational SQL problems executed against seeded SQLite 3 schemas with side-by-side Expected vs Your Query Output tables.

## Built-in practice tools

- Live code execution: Python 3 (including `ListNode`, `TreeNode`, Graph `Node`, `QuadTree`, and class-design harnesses), TypeScript, and SQLite 3 run directly in Chrome in single-file mode, or locally via the Python 3 server (plus optional Go when installed).
- Passed submissions history and Practise Again: only solutions that pass all tests and are submitted are saved under `Submissions (N)` (synchronised across courses by LeetCode problem number). Click `Practise Again` to reset to starter code without losing your saved answers, and click `Revert to Latest Passed` or `Revert to Editor` on any past accepted submission to restore it anytime.
- Resizable Python Tutor memory visualiser: side-by-side traced code pane, call stack frames, heap object tables, pointer arrows, clickable gutter breakpoints, `Fit Code`, font/wrap controls, drag handles, and full-window `Expand` mode.
- Guided Coaching and 20-check rubric scorer: 3-tier progressive hints, mental-model pivots, and a transparent 100-point rubric explaining how to earn full marks.
- Timed Pressure Recall Drills: Line Recall, Token Blitz, and Blind Master drills with countdown timers, lives, streak multipliers, and saved high scores.
- Mock Interview and 75-minute OA Simulator: 4-stage 45-minute technical interview simulator and 3-question 75-minute online assessment simulator (Easy DSA, Medium DSA, and SQL 50).
- Offline AST mentor and Copy for AI: built-in offline debugging assistant with 5 structured prompt modes (`Full Tutor`, `Hints Only`, `Debug Bug`, `Big-O Only`, `Trace Table`), plus optional `GEMINI_API_KEY` support when running the local Python server online.

## Optional: local server mode (100% air-gapped offline + Go support)

If you have Terminal access on Windows, macOS, Linux, or ChromeOS Linux and want 100% air-gapped Python 3 execution from the very first run (plus local Go compilation and `data/progress.json` file storage):

### Chromebook with Linux enabled

1. Open ChromeOS Settings, go to About ChromeOS, open Developers, and turn on Linux development environment.
2. Open the Terminal app (Penguin) and run:

```bash
git clone https://github.com/elim316/algo-studio.git
cd algo-studio
./start.sh
```

3. Optional: run `./install-chromebook-app.sh` once inside `algo-studio` to add Algo Studio to your Chromebook Launcher.

### Windows

1. Install Python 3 from https://www.python.org/downloads/ (tick "Add python.exe to PATH") and Git.
2. Clone the repository and double-click `Algo Studio.bat`.

### macOS or Linux

1. Clone the repository and run `./start.sh` (or double-click `Algo Studio.command` on macOS).

## Rebuilding the single-file bundle and running tests

After editing any backend or frontend file, regenerate `AlgoStudio.html` and run the verification suite:

```bash
python3 build_single_html.py
python3 test_server.py -v
```
