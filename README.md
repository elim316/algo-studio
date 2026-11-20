# Algo Studio

Offline coding interview workbench built with pure Python 3 standard library and zero external dependencies. Runs directly on your laptop (Chromebook via ChromeOS Linux, Windows, macOS, or Linux) with no internet connection, no account sign-in, and no package installs required.

## Courses included

Switch courses anytime from the Course dropdown next to the problem selector. Solved progress stays synchronised across every course by LeetCode problem number and saves locally to `data/progress.json`.

- Our 120-Day List: 120 progressive SWE and FDE interview problems across 16 phases covering 86 algorithmic and systems topics, paired with 601 hidden edge-case tests and a 9-domain edge-case playbook.
- LeetCode Top 150: all 150 official interview problems organised across 23 categories.
- Grind 75 and Grind 70 (Core): Tech Interview Handbook's 8-week schedule with a direct Grind 70 Core course option.
- NeetCode 150 Skill-Tree: all 150 problems across 18 modules with an interactive SVG prerequisite graph.
- SQL 50 Relational Mastery: all 50 relational SQL problems executed locally against seeded SQLite 3 schemas with side-by-side Expected vs Your Query Output tables.

## Built-in practice tools

- Live local code execution: Python 3 (including `ListNode`, `TreeNode`, Graph `Node`, `QuadTree`, and class-design harnesses) and SQLite 3 work out of the box, with optional Go and TypeScript execution whenever `go` or `node` are installed.
- Python Tutor step-by-step memory visualiser: side-by-side traced code pane, call stack frames, heap object tables, pointer arrows, and clickable gutter breakpoints.
- Guided Coaching and 20-check rubric scorer: 3-tier progressive hints, mental-model pivots, and a transparent 100-point rubric explaining how to earn full marks.
- Timed Pressure Recall Drills: Line Recall, Token Blitz, and Blind Master drills with countdown timers, lives, streak multipliers, and saved high scores.
- Mock Interview and 75-minute OA Simulator: 4-stage 45-minute technical interview simulator and 3-question 75-minute online assessment simulator (Easy DSA, Medium DSA, and SQL 50).
- Offline AST mentor and Copy for AI: built-in offline debugging assistant with 5 structured prompt modes (`Full Tutor`, `Hints Only`, `Debug Bug`, `Big-O Only`, `Trace Table`), plus optional `GEMINI_API_KEY` support when online.

## Setup on Chromebook (ChromeOS)

Chromebooks run ChromeOS, which includes a built-in Linux environment with Python 3 and Git ready to use.

1. Enable Linux (one-time step if not already enabled):
   Open ChromeOS Settings, go to About ChromeOS, open Developers, and turn on Linux development environment.
2. Open the Terminal app (Penguin) and clone this repository:

```bash
git clone https://github.com/elim316/algo-studio.git
cd algo-studio
```

3. Launch Algo Studio:

```bash
./start.sh
```

ChromeOS automatically forwards `http://127.0.0.1:8788` and opens Algo Studio in Chrome.

4. Pin as a standalone Chromebook app (optional, recommended):
   - Run `./install-chromebook-app.sh` once inside `algo-studio` so Algo Studio appears directly inside your Chromebook Launcher under Linux apps (right-click it and choose Pin to shelf).
   - While Algo Studio is open in Chrome, you can also click the Install icon in the right side of the Chrome address bar to open it in its own frameless app window.

## Setup on Windows

1. Install Python 3 from https://www.python.org/downloads/ (tick "Add python.exe to PATH") and Git.
2. Clone the repository:

```powershell
git clone https://github.com/elim316/algo-studio.git
```

3. Double-click `Algo Studio.bat` inside the `algo-studio` folder. It starts the local offline server and opens Algo Studio in a standalone Chrome or Edge app window.

## Setup on macOS or Linux

1. Clone the repository:

```bash
git clone https://github.com/elim316/algo-studio.git
cd algo-studio
```

2. On macOS, double-click `Algo Studio.command` (or run `./start.sh` in Terminal). On Linux, run `./start.sh` or run `./install-chromebook-app.sh` to add a desktop app shortcut.

## Optional settings and backups

- Offline progress file: all solved problems, course positions, code drafts, bookmarks, notes, drill high scores, and mock/OA history are stored in `data/progress.json` (or set `ALGO_STUDIO_DATA_DIR=/path/to/dir`).
- Export progress: visit `http://127.0.0.1:8788/api/export-progress` to download a JSON backup of your progress at any time.
- Optional online Gemini mentor: export `GEMINI_API_KEY="your-key"` before running `./start.sh` if you want live Gemini replies in the AI Co-Pilot while online. Without it (or whenever offline), the built-in offline AST mentor handles coaching automatically.
- Run tests:

```bash
python3 test_server.py -v
```
