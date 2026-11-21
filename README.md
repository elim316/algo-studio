# Algo Studio

Offline coding interview workbench built for Chromebooks (zero Terminal required) as well as Windows, macOS, and Linux. Practise all 406 problems across 6 structured courses with no account sign-in and no package installs.

## Quick start on Chromebook (auto-updating offline app)

The easiest way to run Algo Studio on ChromeOS is the installable Progressive Web App hosted via GitHub Pages at https://elim316.github.io/algo-studio/ :

1. Open https://elim316.github.io/algo-studio/ in Chrome on your Chromebook.
2. Click the Install icon on the right side of the Chrome address bar to add Algo Studio as a standalone app on your Chromebook Shelf.
3. Run one Python or SQL 50 problem while online once so the Service Worker caches the Pyodide WebAssembly runtime on your Chromebook.

How auto-updates and offline mode work:
- Automatic updates on every push: whenever changes are pushed to `main`, GitHub Actions automatically rebuilds and publishes the PWA. The next time you open Algo Studio while online, the Service Worker updates the app silently in the background (or shows a 1-click `Update Now` banner if a tab is already open).
- Full offline support: the Service Worker caches both the complete 406-problem workbench and the Pyodide Python 3 / SQLite 3 runtime in separate browser caches, so updating the app never forces re-downloading Pyodide and everything continues working offline without Wi-Fi.
- Your progress stays strictly on your device: GitHub Pages serves only the static app and problem catalog. All solved checkmarks, passed submissions, code drafts, notes, bookmarks, last visited question, drill high scores, and mock/OA history live exclusively in your Chromebook's local `localStorage` and are never uploaded. Click `Export` in the top toolbar anytime for a JSON backup or `Import` to restore on another device.

## Courses included

Switch courses anytime from the Course dropdown next to the problem selector. Solved progress and passed submissions stay synchronised across every course by LeetCode problem number.

- Our 120-Day List: 120 progressive SWE and FDE interview problems across 16 phases covering 86 algorithmic and systems topics, paired with 601 hidden edge-case tests and a 9-domain edge-case playbook.
- LeetCode Top 150: all 150 official interview problems organised across 23 categories.
- Grind 75 and Grind 70 (Core): Tech Interview Handbook's 8-week schedule with a direct Grind 70 Core course option.
- NeetCode 150 Skill-Tree: all 150 problems across 18 modules with an interactive SVG prerequisite graph.
- SQL 50 Relational Mastery: all 50 relational SQL problems executed against seeded SQLite 3 schemas with side-by-side Expected vs Your Query Output tables.

## Built-in practice tools

- Live code execution: Python 3 (including `ListNode`, `TreeNode`, Graph `Node`, `QuadTree`, and class-design harnesses), TypeScript, and SQLite 3 run directly in Chrome, or locally via the Python 3 server (plus optional Go when installed).
- Passed submissions history and Practise Again: only solutions that pass all tests and are submitted are saved under `Submissions (N)` (synchronised across courses by LeetCode problem number). Clicking `Submit` stays on the current question by default (with an optional `Submit & Next` button in the passing banner), and Algo Studio remembers your exact last visited question across reloads even if it is already solved. Click `Practise Again` to reset to starter code without losing saved answers, and `Revert to Latest Passed` or `Revert to Editor` to restore any past pass anytime.
- Resizable Python Tutor memory visualiser: side-by-side traced code pane, call stack frames, heap object tables, pointer arrows, clickable gutter breakpoints, `Fit Code`, font/wrap controls, drag handles, and full-window `Expand` mode.
- Guided Coaching and 20-check rubric scorer: 3-tier progressive hints, mental-model pivots, and a transparent 100-point rubric explaining how to earn full marks.
- Timed Pressure Recall Drills: Line Recall, Token Blitz, and Blind Master drills with countdown timers, lives, streak multipliers, and saved high scores.
- Mock Interview and 75-minute OA Simulator: 4-stage 45-minute technical interview simulator and 3-question 75-minute online assessment simulator (Easy DSA, Medium DSA, and SQL 50).
- AI Co-Pilot (Offline AST + optional live Gemini 2.5): works offline out of the box with the built-in AST mentor and 5 prompt modes (`Full Tutor`, `Hints Only`, `Debug Bug`, `Big-O Only`, `Trace Table`) plus `Copy for AI`. Click `Gemini Key` in the Co-Pilot header to paste a free personal Google AI Studio API key (stored strictly in your browser's `localStorage`, never uploaded or included in JSON exports) for live conversational Gemini 2.5 Flash and Gemini 2.5 Pro coaching directly in Chrome.

## Alternative: single-file download (`AlgoStudio.html`)

If you prefer a standalone file with no web hosting, download `AlgoStudio.html` from this repository into your Chromebook `Downloads` folder and double-click it in ChromeOS Files.

## Alternative: local server mode (air-gapped offline + Go support)

If you have Terminal access on Windows, macOS, Linux, or ChromeOS Linux and want local file-based `data/progress.json` storage plus Go compilation:

- macOS, Linux, or ChromeOS Linux: clone the repository and run `./start.sh` (or double-click `Algo Studio.command` on macOS).
- Windows: install Python 3, clone the repository, and double-click `Algo Studio.bat`.

## Rebuilding bundles and running tests

```bash
python3 build_single_html.py
python3 build_single_html.py --pwa-dir dist
python3 test_server.py -v
```
