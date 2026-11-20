#!/usr/bin/env python3
"""Build a single self-contained AlgoStudio.html for zero-Terminal ChromeOS / desktop use.

Double-clicking AlgoStudio.html in ChromeOS Files (or Chrome/Edge/Safari on any OS)
opens the complete Algo Studio workbench directly via file:// with:
- Instant offline boot for all 406 problems across 6 courses (120-Day SWE/FDE Plan,
  LeetCode Top 150, Grind 75, Grind 70 Core, NeetCode 150 + DAG, SQL 50 + DAG).
- Persistent progress saved in browser localStorage with 1-click Export / Import JSON.
- Instant offline native TypeScript execution directly in Chrome.
- Lazy-loaded in-browser Python 3 + SQLite 3 (Pyodide WebAssembly v0.27.2) for
  Python tests, Python Tutor stack/heap tracing, live SQL 50 queries, 20-check AST
  rubric scoring, approach checks, FDE stress tests, and offline AST Co-Pilot.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import curriculum_data as cd
import curated_lists as cl

PYODIDE_VERSION = "0.27.2"
PYODIDE_BASE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

CURRICULUM_STUB_PY = '''"""Lightweight Pyodide loader for curriculum_data backed by curriculum_boot.json."""

from __future__ import annotations

import json
from pathlib import Path

_BOOT_PATH = Path(__file__).resolve().parent / "curriculum_boot.json"
_DATA = json.loads(_BOOT_PATH.read_text(encoding="utf-8"))

PHASES = _DATA["phases"]
ALL_TAGS = _DATA["allTags"]
EDGE_CASE_PLAYBOOK = _DATA["edgeCasePlaybook"]
EDGE_CASE_RESOURCES = _DATA["edgeCaseResources"]
PROBLEMS = _DATA["problems"]
PROBLEMS_BY_DAY = {int(p["day"]): p for p in PROBLEMS}
'''

BROWSER_RUNTIME_JS = r'''
    /* ======================================================================
     * Single-File Browser Runtime (Zero-Terminal ChromeOS / file:// Edition)
     * - Serves /api/state, /api/curated, /api/progress instantaneously from
     *   embedded gzipped data + localStorage.
     * - Runs TypeScript tests natively in Chrome V8 (100% offline).
     * - Lazily boots Pyodide WebAssembly (Python 3 + SQLite 3) for Python
     *   execution, Python Tutor tracing, SQL 50, 20-check rubric & Co-Pilot.
     * ====================================================================== */
    const __ALGO_STORAGE_KEY = 'algoStudioProgress_v1';
    const __ALGO_PYODIDE_BASE = '__PYODIDE_BASE_URL__';
    const __ALGO_ALLOWED_COURSES = new Set([
      'schedule-120',
      'leetcode-150',
      'grind-75',
      'grind-70',
      'neetcode-150',
      'sql-50',
    ]);
    const __ALGO_ALLOWED_LANGS = new Set(['python', 'typescript', 'go', 'sql']);

    let __bootDataPromise = null;
    let __bootData = null;
    let __pyFilesPromise = null;
    let __pyodideReadyPromise = null;
    let __pyodideInstance = null;
    let __pyodideQueue = Promise.resolve();
    let __memProgressFallback = null;
    let __dayToLcNum = {};
    let __lcNumToDays = {};
    let __problemsByDay = {};

    async function __decompressGzB64Json(scriptElId) {
      const el = document.getElementById(scriptElId);
      if (!el) throw new Error(`Missing embedded bundle: ${scriptElId}`);
      const b64 = (el.textContent || '').replace(/\s+/g, '');
      const binary = atob(b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      if (typeof DecompressionStream === 'undefined') {
        throw new Error('This browser does not support DecompressionStream. Open AlgoStudio.html in Chrome 80+ or ChromeOS Chrome.');
      }
      const stream = new Response(bytes.buffer).body.pipeThrough(new DecompressionStream('gzip'));
      const text = await new Response(stream).text();
      return JSON.parse(text);
    }

    async function __ensureBootData() {
      if (__bootData) return __bootData;
      if (!__bootDataPromise) {
        __bootDataPromise = __decompressGzB64Json('algo-studio-boot-gz').then((data) => {
          __bootData = data;
          __dayToLcNum = {};
          __lcNumToDays = {};
          __problemsByDay = {};
          const probs = data?.curriculum?.problems || [];
          for (const p of probs) {
            const dNum = Number(p.day);
            __problemsByDay[dNum] = p;
            const lcid = String(p.leetcodeId || '');
            if (lcid.toUpperCase().startsWith('LC')) {
              const m = lcid.match(/(\d+)/);
              if (m) {
                const lcN = Number(m[1]);
                __dayToLcNum[dNum] = lcN;
                if (!__lcNumToDays[lcN]) __lcNumToDays[lcN] = [];
                __lcNumToDays[lcN].push(dNum);
              }
            }
          }
          return data;
        });
      }
      return __bootDataPromise;
    }

    function __utcDateStr(d = new Date()) {
      return d.toISOString().slice(0, 10);
    }

    function __utcStampStr(d = new Date()) {
      return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
    }

    function __defaultProgress() {
      return {
        currentDay: 1,
        activeCourse: 'schedule-120',
        coursePositions: {},
        solvedDays: {},
        solvedLcIds: {},
        bookmarks: [],
        pressureScores: {},
        interviewHistory: [],
        oaHistory: [],
        drafts: {},
        submissions: {},
        notes: {},
        chatHistory: {},
        layoutSizes: {},
        revealedHiddenDays: {},
        failedAttemptsByDay: {},
        lastActiveDate: __utcDateStr(),
        streak: 1,
      };
    }

    function __saveProgressLocal(prog) {
      __memProgressFallback = prog;
      try {
        localStorage.setItem(__ALGO_STORAGE_KEY, JSON.stringify(prog));
        if (prog.drafts) localStorage.setItem('algoStudioDrafts_v1', JSON.stringify(prog.drafts));
        if (prog.layoutSizes) localStorage.setItem('algoStudioLayoutSizes_v1', JSON.stringify(prog.layoutSizes));
      } catch (_) {}
    }

    function __nextUnsolvedDay(solvedDays, afterDay = 0) {
      const solvedSet = new Set(
        Object.keys(solvedDays || {})
          .filter((k) => /^\d+$/.test(String(k)))
          .map((k) => Number(k))
      );
      const totalDays = (__bootData?.curriculum?.problems?.length) || 120;
      for (let offset = 1; offset <= totalDays; offset++) {
        const cand = ((afterDay + offset - 1) % totalDays) + 1;
        if (!solvedSet.has(cand)) return cand;
      }
      return Math.min(totalDays, Math.max(1, afterDay));
    }

    function __orderedCourseProblemIds(courseId) {
      const sheetId = courseId === 'grind-70' ? 'grind-75' : courseId;
      const sheets = __bootData?.curated?.sheets || [];
      const byId = __bootData?.curated?.problemsById || {};
      const sheet = sheets.find((s) => s.id === sheetId);
      if (!sheet) return [];
      const ordered = [];
      const seen = new Set();
      for (const grp of sheet.groups || []) {
        for (const pid of grp.problemIds || []) {
          if (seen.has(pid)) continue;
          const prob = byId[pid];
          if (!prob) continue;
          if (courseId === 'grind-70') {
            const meta = (prob.sheetMeta || {})['grind-75'] || {};
            if (meta.isCore70 === false) continue;
          }
          seen.add(pid);
          ordered.push(pid);
        }
      }
      return ordered;
    }

    function __nextUnsolvedCuratedId(courseId, solvedLcIds, afterPid) {
      const ordered = __orderedCourseProblemIds(courseId);
      if (!ordered.length) return afterPid || null;
      const byId = __bootData?.curated?.problemsById || {};
      let startIdx = 0;
      if (afterPid && ordered.includes(afterPid)) startIdx = ordered.indexOf(afterPid);
      const n = ordered.length;
      for (let offset = 1; offset <= n; offset++) {
        const cand = ordered[(startIdx + offset) % n];
        const prob = byId[cand];
        const lcN = prob?.lcNum;
        if (lcN == null || !solvedLcIds[String(lcN)]) return cand;
      }
      return ordered[(startIdx + 1) % n];
    }

    function __loadProgressLocal(autoAdvance = true) {
      let raw = null;
      try {
        const text = localStorage.getItem(__ALGO_STORAGE_KEY);
        if (text) raw = JSON.parse(text);
      } catch (_) {}
      if (!raw && __memProgressFallback) raw = __memProgressFallback;
      const base = __defaultProgress();
      if (raw && typeof raw === 'object') Object.assign(base, raw);
      if (!__ALGO_ALLOWED_COURSES.has(base.activeCourse)) base.activeCourse = 'schedule-120';
      if (!base.coursePositions || typeof base.coursePositions !== 'object') base.coursePositions = {};
      if (!base.solvedDays || typeof base.solvedDays !== 'object') base.solvedDays = {};
      if (!base.solvedLcIds || typeof base.solvedLcIds !== 'object') base.solvedLcIds = {};
      if (!base.drafts || typeof base.drafts !== 'object') base.drafts = {};
      if (!base.submissions || typeof base.submissions !== 'object') base.submissions = {};
      if (!base.notes || typeof base.notes !== 'object') base.notes = {};
      if (!base.chatHistory || typeof base.chatHistory !== 'object') base.chatHistory = {};
      if (!base.layoutSizes || typeof base.layoutSizes !== 'object') base.layoutSizes = {};
      if (!base.revealedHiddenDays || typeof base.revealedHiddenDays !== 'object') base.revealedHiddenDays = {};
      if (!base.failedAttemptsByDay || typeof base.failedAttemptsByDay !== 'object') base.failedAttemptsByDay = {};
      if (!base.pressureScores || typeof base.pressureScores !== 'object') base.pressureScores = {};
      if (!Array.isArray(base.bookmarks)) base.bookmarks = [];
      if (!Array.isArray(base.interviewHistory)) base.interviewHistory = [];
      if (!Array.isArray(base.oaHistory)) base.oaHistory = [];

      let mirrored = false;
      for (const [dStr, info] of Object.entries(base.solvedDays)) {
        if (/^\d+$/.test(dStr)) {
          const lcN = __dayToLcNum[Number(dStr)];
          if (lcN != null && !base.solvedLcIds[String(lcN)]) {
            base.solvedLcIds[String(lcN)] = info;
            mirrored = true;
          }
        }
      }
      const totalProbs = (__bootData?.curriculum?.problems?.length) || 120;
      const cur = Number(base.currentDay || 1);
      if (autoAdvance && base.solvedDays[String(cur)] && Object.keys(base.solvedDays).length < totalProbs) {
        base.currentDay = __nextUnsolvedDay(base.solvedDays, cur);
        mirrored = true;
      }
      if (mirrored || !raw) __saveProgressLocal(base);
      return base;
    }

    function __computeTagStats(solvedDays) {
      const solvedSet = new Set(
        Object.keys(solvedDays || {})
          .filter((k) => /^\d+$/.test(String(k)))
          .map((k) => Number(k))
      );
      const counts = {};
      const allTags = __bootData?.curriculum?.allTags || [];
      for (const t of allTags) counts[t.name] = { total: 0, solved: 0 };
      for (const p of (__bootData?.curriculum?.problems || [])) {
        const d = Number(p.day);
        for (const tagName of (p.tags || [])) {
          if (!counts[tagName]) counts[tagName] = { total: 0, solved: 0 };
          counts[tagName].total += 1;
          if (solvedSet.has(d)) counts[tagName].solved += 1;
        }
      }
      return allTags.map((t) => {
        const c = counts[t.name] || { total: 0, solved: 0 };
        return {
          ...t,
          curriculumTotal: c.total,
          curriculumSolved: c.solved,
        };
      });
    }

    function __computeSpacedRepetition(prog) {
      const todayStr = __utcDateStr();
      const solvedDays = prog.solvedDays || {};
      const failedByDay = prog.failedAttemptsByDay || {};
      const dueReviewDays = [];
      const weakTagScores = {};

      function bumpWeakTags(dayInt, weight, reason) {
        const prob = __problemsByDay[dayInt];
        if (!prob) return;
        for (const t of (prob.tags || []).slice(0, 3)) {
          if (!weakTagScores[t]) weakTagScores[t] = { name: t, score: 0, days: [], reasons: [] };
          weakTagScores[t].score += weight;
          if (!weakTagScores[t].days.includes(dayInt)) weakTagScores[t].days.push(dayInt);
          if (!weakTagScores[t].reasons.includes(reason)) weakTagScores[t].reasons.push(reason);
        }
      }

      for (const [dStr, info] of Object.entries(solvedDays)) {
        if (!/^\d+$/.test(dStr)) continue;
        const dInt = Number(dStr);
        const prob = __problemsByDay[dInt];
        if (!prob) continue;
        const rating = String(info?.rating || 'Good');
        const nextRev = String(info?.nextReviewDate || '9999-12-31');
        const isDue = nextRev <= todayStr;
        const isStruggled = rating === 'Again' || rating === 'Hard';
        if (isDue || isStruggled) {
          dueReviewDays.push({
            day: dInt,
            title: prob.title,
            leetcodeId: prob.leetcodeId,
            difficulty: prob.difficulty,
            rating,
            nextReviewDate: nextRev,
            reason: isStruggled ? `Rated ${rating}` : 'Review date reached',
          });
        }
        if (rating === 'Again') bumpWeakTags(dInt, 3, `Day ${dInt} rated Again`);
        else if (rating === 'Hard') bumpWeakTags(dInt, 2, `Day ${dInt} rated Hard`);
      }

      for (const [dStr, failCntRaw] of Object.entries(failedByDay)) {
        const failCnt = Number(failCntRaw || 0);
        if (/^\d+$/.test(dStr) && failCnt > 0) {
          const dInt = Number(dStr);
          bumpWeakTags(dInt, Math.min(3, failCnt), `Day ${dStr} (${failCnt} failed test runs)`);
          if (failCnt >= 2 && !solvedDays[dStr]) {
            const prob = __problemsByDay[dInt];
            if (prob) {
              dueReviewDays.push({
                day: dInt,
                title: prob.title,
                leetcodeId: prob.leetcodeId,
                difficulty: prob.difficulty,
                rating: 'Retry',
                nextReviewDate: todayStr,
                reason: `${failCnt} failed test runs`,
              });
            }
          }
        }
      }

      const rank = (r) => (r === 'Again' || r === 'Retry' ? 0 : r === 'Hard' ? 1 : 2);
      dueReviewDays.sort((a, b) => rank(a.rating) - rank(b.rating) || a.nextReviewDate.localeCompare(b.nextReviewDate) || a.day - b.day);
      const weakTopics = Object.values(weakTagScores)
        .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
        .slice(0, 8)
        .map((w) => ({ tag: w.name, name: w.name, weakScore: w.score, score: w.score, days: w.days, reasons: w.reasons }));

      return {
        dueCount: dueReviewDays.length,
        dueReviewDays,
        weakTopics,
      };
    }

    function __handleLocalProgressPost(body) {
      const prog = __loadProgressLocal(false);
      const byId = __bootData?.curated?.problemsById || {};
      const totalDays = (__bootData?.curriculum?.problems?.length) || 120;

      if ('activeCourse' in body) {
        const cv = String(body.activeCourse || '').slice(0, 40);
        if (__ALGO_ALLOWED_COURSES.has(cv)) prog.activeCourse = cv;
      }
      if ('courseProblemId' in body) {
        const cpid = String(body.courseProblemId || '').slice(0, 100);
        const ck = String(body.course || prog.activeCourse || '').slice(0, 40);
        if (__ALGO_ALLOWED_COURSES.has(ck) && ck !== 'schedule-120' && byId[cpid]) {
          prog.coursePositions[ck] = cpid;
        }
      }
      if ('currentDay' in body) {
        const dVal = Number(body.currentDay || 1);
        if (Number.isFinite(dVal)) prog.currentDay = Math.max(1, Math.min(totalDays, Math.trunc(dVal)));
      }
      if ('note' in body && 'problemId' in body) {
        const pid = String(body.problemId || '').slice(0, 100);
        if (byId[pid]) prog.notes[pid] = String(body.note || '').slice(0, 200000);
      } else if ('note' in body && 'day' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        prog.notes[String(dInt)] = String(body.note || '').slice(0, 200000);
      }
      if ('draft' in body && 'problemId' in body && 'language' in body) {
        const pid = String(body.problemId || '').slice(0, 100);
        const lang = String(body.language || '').toLowerCase().slice(0, 32);
        if (byId[pid] && __ALGO_ALLOWED_LANGS.has(lang)) {
          prog.drafts[`${pid}:${lang}`] = String(body.draft || '').slice(0, 200000);
        }
      } else if ('draft' in body && 'day' in body && 'language' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        const lang = String(body.language || '').toLowerCase().slice(0, 32);
        if (__ALGO_ALLOWED_LANGS.has(lang)) {
          prog.drafts[`${dInt}:${lang}`] = String(body.draft || '').slice(0, 200000);
        }
      }
      if (body.draftsBatch && typeof body.draftsBatch === 'object') {
        for (const [dk, dv] of Object.entries(body.draftsBatch).slice(0, 400)) {
          if (typeof dk === 'string' && dk.length <= 100 && typeof dv === 'string' && dv.trim()) {
            if (!prog.drafts[dk] || !String(prog.drafts[dk]).trim()) {
              prog.drafts[dk] = dv.slice(0, 200000);
            }
          }
        }
      }
      if (body.layoutSizes && typeof body.layoutSizes === 'object') {
        for (const [lk, lv] of Object.entries(body.layoutSizes).slice(0, 20)) {
          if (typeof lk === 'string' && lk.length <= 64 && typeof lv === 'number' && Number.isFinite(lv)) {
            prog.layoutSizes[lk] = Math.max(0, Math.min(5000, Math.trunc(lv)));
          }
        }
      }
      if (body.resetLayout) prog.layoutSizes = {};
      if ('revealHiddenDay' in body && 'day' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        prog.revealedHiddenDays[String(dInt)] = Boolean(body.revealHiddenDay);
      }
      if (body.clearChat && 'problemId' in body) {
        prog.chatHistory[String(body.problemId || '').slice(0, 100)] = [];
      } else if (body.clearChat && 'day' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        prog.chatHistory[String(dInt)] = [];
      }
      if (body.toggleBookmark && body.key) {
        const k = String(body.key).slice(0, 100);
        const idx = prog.bookmarks.indexOf(k);
        if (idx >= 0) prog.bookmarks.splice(idx, 1);
        else if (prog.bookmarks.length < 500) prog.bookmarks.push(k);
      }
      if (body.savePressureScore && body.key) {
        const k = String(body.key).slice(0, 100);
        const sc = Math.max(0, Math.min(1000000, Math.trunc(Number(body.score || 0))));
        const tr = Math.max(1, Math.min(10, Math.trunc(Number(body.tier || 1))));
        const st = Math.max(0, Math.min(100000, Math.trunc(Number(body.maxStreak || 0))));
        const prev = prog.pressureScores[k] || {};
        prog.pressureScores[k] = {
          bestScore: Math.max(sc, Number(prev.bestScore || 0)),
          bestTier: sc >= Number(prev.bestScore || 0) ? Math.max(tr, Number(prev.bestTier || 0)) : Number(prev.bestTier || tr),
          bestStreak: Math.max(st, Number(prev.bestStreak || 0)),
          updatedAt: __utcStampStr(),
        };
      }
      if (body.saveInterviewRecord && typeof body.saveInterviewRecord === 'object') {
        const r = body.saveInterviewRecord;
        prog.interviewHistory.unshift({
          date: String(r.date || '').slice(0, 32),
          problemId: String(r.problemId || '').slice(0, 80),
          title: String(r.title || '').slice(0, 160),
          difficulty: String(r.difficulty || '').slice(0, 32),
          score: Math.max(0, Math.min(100, Math.trunc(Number(r.score || 0)))),
          signal: String(r.signal || '').slice(0, 120),
          elapsedMin: Math.max(0, Math.min(600, Math.trunc(Number(r.elapsedMin || 0)))),
        });
        prog.interviewHistory = prog.interviewHistory.slice(0, 30);
      }
      if (body.saveOaRecord && typeof body.saveOaRecord === 'object') {
        const r = body.saveOaRecord;
        prog.oaHistory.unshift({
          date: String(r.date || '').slice(0, 32),
          totalPoints: Math.max(0, Math.min(10000, Math.trunc(Number(r.totalPoints || 0)))),
          maxPoints: Math.max(1, Math.min(10000, Math.trunc(Number(r.maxPoints || 300)))),
          passedQuestions: Math.max(0, Math.min(50, Math.trunc(Number(r.passedQuestions || 0)))),
          totalQuestions: Math.max(0, Math.min(50, Math.trunc(Number(r.totalQuestions || 3)))),
          elapsedMin: Math.max(0, Math.min(600, Math.trunc(Number(r.elapsedMin || 0)))),
        });
        prog.oaHistory = prog.oaHistory.slice(0, 30);
      }

      if (body.saveAcceptedSubmission && typeof body.saveAcceptedSubmission === 'object') {
        const rawSub = body.saveAcceptedSubmission;
        const subPassed = Math.trunc(Number(rawSub.passed || 0));
        const subTotal = Math.trunc(Number(rawSub.total || 0));
        const subLang = String(rawSub.language || '').toLowerCase().slice(0, 32);
        const subCode = String(rawSub.code || '').slice(0, 200000);
        if (
          rawSub.allPassed === true &&
          subTotal > 0 &&
          subPassed === subTotal &&
          __ALGO_ALLOWED_LANGS.has(subLang) &&
          subCode.trim().length > 0
        ) {
          let subKey = null;
          if (rawSub.problemId && byId[String(rawSub.problemId)]) {
            const cprob = byId[String(rawSub.problemId)];
            subKey = cprob.lcNum != null ? `lc:${Math.trunc(Number(cprob.lcNum))}` : `id:${String(rawSub.problemId)}`;
          } else if (rawSub.day != null && Number.isFinite(Number(rawSub.day))) {
            const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(rawSub.day))));
            const lcN = __dayToLcNum[dInt];
            subKey = lcN != null ? `lc:${lcN}` : `day:${dInt}`;
          } else if (/^(lc:\d+|day:\d+|id:[A-Za-z0-9_-]{1,80})$/.test(String(rawSub.key || ''))) {
            subKey = String(rawSub.key);
          }
          if (subKey) {
            const rtRaw = Number(rawSub.runtimeMs || 0);
            const rtMs = Number.isFinite(rtRaw) ? Math.round(Math.max(0, Math.min(600000, rtRaw)) * 100) / 100 : 0;
            const subCourse = __ALGO_ALLOWED_COURSES.has(String(rawSub.course || '')) ? String(rawSub.course) : 'schedule-120';
            const subRec = {
              id: `sub_${Date.now()}_${subCode.length % 997}`,
              submittedAt: __utcStampStr(),
              language: subLang,
              code: subCode,
              passed: subPassed,
              total: subTotal,
              runtimeMs: rtMs,
              course: subCourse,
              problemLabel: String(rawSub.problemLabel || '').slice(0, 160),
            };
            if (!prog.submissions || typeof prog.submissions !== 'object') prog.submissions = {};
            const existing = Array.isArray(prog.submissions[subKey]) ? prog.submissions[subKey].slice() : [];
            if (
              existing.length > 0 &&
              existing[0].language === subRec.language &&
              String(existing[0].code || '').trim() === subRec.code.trim()
            ) {
              existing[0] = subRec;
            } else {
              existing.unshift(subRec);
            }
            prog.submissions[subKey] = existing.slice(0, 25);
          }
        }
      }

      let nextDay = null;
      let nextProblemId = null;

      if (body.toggleSolvedCurated && body.problemId) {
        const pid = String(body.problemId).slice(0, 100);
        const cprob = byId[pid];
        const lcN = cprob?.lcNum;
        const wantSolved = body.solved !== false;
        let rating = String(body.rating || 'Good').slice(0, 16);
        if (!['Again', 'Hard', 'Good', 'Easy'].includes(rating)) rating = 'Good';
        const daysOffset = { Again: 1, Hard: 3, Good: 7, Easy: 14 }[rating] || 7;
        const now = new Date();
        const nextRev = __utcDateStr(new Date(now.getTime() + daysOffset * 86400000));
        let entryLang = String(body.language || (cprob?.isSql ? 'sql' : 'python')).toLowerCase();
        if (!__ALGO_ALLOWED_LANGS.has(entryLang)) entryLang = 'python';
        const entry = {
          solvedAt: __utcStampStr(now),
          rating,
          nextReviewDate: nextRev,
          language: entryLang,
          attempts: 1,
        };
        if (lcN != null) {
          if (wantSolved) prog.solvedLcIds[String(lcN)] = entry;
          else delete prog.solvedLcIds[String(lcN)];
          for (const dMatch of (__lcNumToDays[Number(lcN)] || [])) {
            if (wantSolved) prog.solvedDays[String(dMatch)] = entry;
            else delete prog.solvedDays[String(dMatch)];
          }
        }
        if (wantSolved && body.advanceToNext) {
          const ck = String(body.course || prog.activeCourse || '').slice(0, 40);
          if (__ALGO_ALLOWED_COURSES.has(ck) && ck !== 'schedule-120') {
            nextProblemId = __nextUnsolvedCuratedId(ck, prog.solvedLcIds, pid);
            if (nextProblemId) prog.coursePositions[ck] = nextProblemId;
          }
        }
      }

      if (body.markSolved && 'day' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        const dStr = String(dInt);
        let rating = String(body.rating || 'Good').slice(0, 16);
        if (!['Again', 'Hard', 'Good', 'Easy'].includes(rating)) rating = 'Good';
        const daysOffset = { Again: 1, Hard: 3, Good: 7, Easy: 14 }[rating] || 7;
        const now = new Date();
        const nextRev = __utcDateStr(new Date(now.getTime() + daysOffset * 86400000));
        const prev = prog.solvedDays[dStr] || {};
        let entryLang = String(body.language || 'python').toLowerCase();
        if (!__ALGO_ALLOWED_LANGS.has(entryLang)) entryLang = 'python';
        const entry = {
          solvedAt: __utcStampStr(now),
          rating,
          nextReviewDate: nextRev,
          language: entryLang,
          attempts: Number(prev.attempts || 0) + 1,
        };
        prog.solvedDays[dStr] = entry;
        const lcN = __dayToLcNum[dInt];
        if (lcN != null) prog.solvedLcIds[String(lcN)] = entry;
        if (body.advanceToNext !== false) {
          nextDay = __nextUnsolvedDay(prog.solvedDays, dInt);
          prog.currentDay = nextDay;
        }
      }

      if (body.unmarkSolved && 'day' in body) {
        const dInt = Math.max(1, Math.min(totalDays, Math.trunc(Number(body.day || 1))));
        delete prog.solvedDays[String(dInt)];
        const lcN = __dayToLcNum[dInt];
        if (lcN != null) delete prog.solvedLcIds[String(lcN)];
      }

      __saveProgressLocal(prog);
      return {
        ok: true,
        progress: prog,
        tags: __computeTagStats(prog.solvedDays),
        spacedRepetition: __computeSpacedRepetition(prog),
        nextDay: nextDay || prog.currentDay,
        nextProblemId,
      };
    }

    function __stripTypeScriptTypes(tsCode) {
      return String(tsCode || '').split('\n').map((line) => {
        if (/^\s*type\s+\w+\s*=[^;]+;\s*$/.test(line)) return '// ' + line;
        let s = line;
        s = s.replace(/\b(Map|Set|Array)\s*<[^>;()]+>\s*\(/g, '$1(');
        s = s.replace(/(\)|\w|\])\s*!(?=[.;,\)\]\s])/g, '$1');
        s = s.replace(/\b(const|let|var)\s+(\w+)\s*:\s*[^=;]+\s*=/g, '$1 $2 =');
        s = s.replace(/\)\s*:\s*[A-Za-z0-9_<>\[\]\|\s]+(?=\s*(\{|=>))/g, ')');
        s = s.replace(/\(([^()?]*:\s*[A-Za-z0-9_<>\[\]\|]+[^()?]*)\)/g, (full, inner) => {
          if (inner.includes('?')) return full;
          const cleaned = inner.split(',').map((p) => p.replace(/:\s*[A-Za-z0-9_<>\[\]\|\s]+/g, ''));
          return '(' + cleaned.join(', ') + ')';
        });
        return s;
      }).join('\n');
    }

    function __runTypeScriptTestCases(funcName, code, testCases) {
      const jsCode = __stripTypeScriptTypes(code);
      const userLines = String(code || '').split('\n');
      const returnLines = [];
      userLines.forEach((ln, idx) => {
        if (/\breturn\b/.test(ln)) returnLines.push(idx + 1);
      });
      const defaultRetLine = returnLines.length ? returnLines[returnLines.length - 1] : userLines.length;
      let logs = [];
      const customConsole = {
        log: (...args) => logs.push(args.map((a) => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ')),
        error: (...args) => logs.push(args.map((a) => String(a)).join(' ')),
        warn: (...args) => logs.push(args.map((a) => String(a)).join(' ')),
      };

      let fn = null;
      try {
        const factory = new Function(
          'console',
          `${jsCode}\nreturn (typeof ${funcName} === 'function') ? ${funcName} : null;`
        );
        fn = factory(customConsole);
      } catch (err) {
        return {
          ok: false,
          error: `${err?.name || 'SyntaxError'}: ${err?.message || err}`,
          errorLine: 1,
          errorSourceLine: (userLines[0] || '').trim(),
          tracedCode: code,
          tracedLanguage: 'typescript',
        };
      }
      if (typeof fn !== 'function') {
        return {
          ok: false,
          error: `Function ${funcName} not found`,
          tracedCode: code,
          tracedLanguage: 'typescript',
        };
      }

      const results = [];
      let passed = 0;
      let visPassed = 0;
      let visTotal = 0;
      let hidPassed = 0;
      let hidTotal = 0;
      let firstErrorLine = null;

      for (let i = 0; i < testCases.length; i++) {
        const tc = testCases[i];
        const isHidden = Boolean(tc.hidden);
        if (isHidden) hidTotal += 1;
        else visTotal += 1;
        logs = [];
        const t0 = performance.now();
        try {
          const argsCopy = JSON.parse(JSON.stringify(tc.args || []));
          const actual = fn(...argsCopy);
          const dtMs = Math.round((performance.now() - t0) * 100) / 100;
          const ok = JSON.stringify(actual) === JSON.stringify(tc.expected);
          if (ok) {
            passed += 1;
            if (isHidden) hidPassed += 1;
            else visPassed += 1;
          } else if (firstErrorLine === null) {
            firstErrorLine = defaultRetLine;
          }
          const src = !ok && userLines[defaultRetLine - 1] ? userLines[defaultRetLine - 1].trim() : '';
          results.push({
            index: i + 1,
            label: tc.label || '',
            input: tc.args,
            expected: tc.expected,
            actual: actual ?? null,
            passed: ok,
            hidden: isHidden,
            category: String(tc.category || ''),
            edgeReason: String(tc.edgeReason || ''),
            runtimeMs: dtMs,
            stdout: logs.join('\n'),
            suspectLine: !ok ? defaultRetLine : null,
            suspectSource: src,
          });
        } catch (err) {
          const dtMs = Math.round((performance.now() - t0) * 100) / 100;
          if (firstErrorLine === null) firstErrorLine = defaultRetLine;
          const src = userLines[defaultRetLine - 1] ? userLines[defaultRetLine - 1].trim() : '';
          results.push({
            index: i + 1,
            label: tc.label || '',
            input: tc.args,
            expected: tc.expected,
            actual: null,
            error: `${err?.name || 'Error'}: ${err?.message || err}`,
            errorLine: defaultRetLine,
            suspectLine: defaultRetLine,
            suspectSource: src,
            stdout: logs.join('\n'),
            passed: false,
            hidden: isHidden,
            category: String(tc.category || ''),
            edgeReason: String(tc.edgeReason || ''),
            runtimeMs: dtMs,
          });
        }
      }

      return {
        ok: true,
        passed,
        total: testCases.length,
        visiblePassed: visPassed,
        visibleTotal: visTotal,
        hiddenPassed: hidPassed,
        hiddenTotal: hidTotal,
        allPassed: passed === testCases.length,
        highlightLine: firstErrorLine,
        results,
        tracedCode: code,
        tracedLanguage: 'typescript',
      };
    }

    window.__algoRunTsTestCases = (funcName, code, testCasesJson) => {
      const cases = JSON.parse(String(testCasesJson || '[]'));
      return JSON.stringify(__runTypeScriptTestCases(funcName, code, cases));
    };

    function __setPyodideStatusBanner(msg) {
      const runSummary = document.getElementById('run-status-summary');
      if (runSummary && msg) runSummary.textContent = msg;
    }

    function __loadScriptOnce(url) {
      return new Promise((resolve, reject) => {
        if (typeof window.loadPyodide === 'function') {
          resolve();
          return;
        }
        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        script.crossOrigin = 'anonymous';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(
          'Could not load in-browser Python 3 / SQLite 3 runtime (no internet connection on first run). ' +
          'Connect to Wi-Fi once so Chrome caches Pyodide WebAssembly, or use TypeScript / Study / Browse modes which work completely offline.'
        ));
        document.head.appendChild(script);
      });
    }

    async function __ensurePyodide() {
      if (__pyodideInstance) return __pyodideInstance;
      if (!__pyodideReadyPromise) {
        __pyodideReadyPromise = (async () => {
          __setPyodideStatusBanner('Loading in-browser Python 3 & SQLite 3 runtime (first run only)...');
          const boot = await __ensureBootData();
          if (!__pyFilesPromise) {
            __pyFilesPromise = __decompressGzB64Json('algo-studio-pyfiles-gz');
          }
          const [pyFiles] = await Promise.all([
            __pyFilesPromise,
            __loadScriptOnce(__ALGO_PYODIDE_BASE + 'pyodide.js'),
          ]);
          const pyodide = await window.loadPyodide({ indexURL: __ALGO_PYODIDE_BASE });
          __setPyodideStatusBanner('Initialising SQLite 3 & Algo Studio Python engine...');
          await pyodide.loadPackage('sqlite3');
          try { pyodide.FS.mkdir('/app'); } catch (_) {}
          try { pyodide.FS.mkdir('/app/data'); } catch (_) {}
          pyodide.FS.writeFile('/app/curriculum_boot.json', JSON.stringify(boot.curriculum));
          pyodide.FS.writeFile('/app/curated_catalog.json', JSON.stringify(boot.curated));
          for (const [fname, content] of Object.entries(pyFiles)) {
            pyodide.FS.writeFile('/app/' + fname, String(content));
          }
          pyodide.runPython(`
import sys
if '/app' not in sys.path:
    sys.path.insert(0, '/app')
import pyodide_shim
pyodide_shim.install_browser_patches()
`);
          __pyodideInstance = pyodide;
          return pyodide;
        })().catch((err) => {
          __pyodideReadyPromise = null;
          throw err;
        });
      }
      return __pyodideReadyPromise;
    }

    async function __dispatchPyodidePost(route, body) {
      const task = async () => {
        const pyodide = await __ensurePyodide();
        const prog = __loadProgressLocal(false);
        const dispatchFn = pyodide.globals.get('pyodide_shim').dispatch_api;
        const rawOut = dispatchFn(route, JSON.stringify(body || {}), JSON.stringify(prog));
        const parsed = JSON.parse(String(rawOut));
        if (parsed && parsed._syncedProgress && typeof parsed._syncedProgress === 'object') {
          __saveProgressLocal(parsed._syncedProgress);
          delete parsed._syncedProgress;
        }
        return parsed;
      };
      const next = __pyodideQueue.then(task, task);
      __pyodideQueue = next.catch(() => {});
      return next;
    }

    async function apiGet(path) {
      try {
        const boot = await __ensureBootData();
        const cleanPath = String(path || '').split('?')[0];
        if (cleanPath === '/api/health') return { ok: true, app: 'algo-studio', mode: 'single-file' };
        if (cleanPath === '/api/curated') {
          return {
            ok: true,
            sheets: boot.curated.sheets || [],
            dagNodes: boot.curated.dagNodes || [],
            problemsById: boot.curated.problemsById || {},
          };
        }
        if (cleanPath === '/api/state') {
          const isSync = String(path || '').includes('sync=1');
          const prog = __loadProgressLocal(!isSync);
          return {
            ok: true,
            progress: prog,
            phases: boot.curriculum.phases || [],
            tags: __computeTagStats(prog.solvedDays),
            spacedRepetition: __computeSpacedRepetition(prog),
            edgeCasePlaybook: boot.curriculum.edgeCasePlaybook || [],
            edgeCaseResources: boot.curriculum.edgeCaseResources || [],
            problems: boot.curriculum.problems || [],
          };
        }
        return { ok: false, error: `Unknown local route: ${path}` };
      } catch (err) {
        return { ok: false, error: String(err?.message || err) };
      }
    }

    async function apiPost(path, body, _extraFetchOpts = {}) {
      try {
        await __ensureBootData();
        const cleanPath = String(path || '').split('?')[0];
        if (cleanPath === '/api/progress') {
          return __handleLocalProgressPost(body || {});
        }
        // Native offline TypeScript execution without loading Pyodide when running standard test cases
        if (
          cleanPath === '/api/run' &&
          !body?.problemId &&
          String(body?.language || '').toLowerCase() === 'typescript' &&
          !Array.isArray(body?.customTestArgs)
        ) {
          const dayNum = Math.max(1, Math.min((__bootData?.curriculum?.problems?.length) || 120, Math.trunc(Number(body?.day || 1))));
          const prob = __problemsByDay[dayNum];
          if (!prob) return { ok: false, error: `Unknown problem day ${dayNum}` };
          const res = __runTypeScriptTestCases(prob.funcName, String(body?.code || ''), prob.testCases || []);
          const prog = __loadProgressLocal(false);
          prog.drafts[`${dayNum}:typescript`] = String(body?.code || '');
          prog.currentDay = dayNum;
          if (!res.ok || Number(res.passed || 0) < Number(res.total || 1)) {
            prog.failedAttemptsByDay[String(dayNum)] = Number(prog.failedAttemptsByDay[String(dayNum)] || 0) + 1;
          }
          __saveProgressLocal(prog);
          res.progress = prog;
          res.tags = __computeTagStats(prog.solvedDays);
          res.spacedRepetition = __computeSpacedRepetition(prog);
          return res;
        }
        return await __dispatchPyodidePost(cleanPath, body || {});
      } catch (err) {
        return { ok: false, error: String(err?.message || err) };
      }
    }

    function __wireBackupRestoreButtons() {
      const expBtn = document.getElementById('export-progress-btn');
      const impBtn = document.getElementById('import-progress-btn');
      const impInput = document.getElementById('import-progress-file');
      if (expBtn && !expBtn.dataset.bound) {
        expBtn.dataset.bound = '1';
        expBtn.addEventListener('click', () => {
          try { flushDraftSaveNow(); } catch (_) {}
          const prog = __loadProgressLocal(false);
          const blob = new Blob([JSON.stringify(prog, null, 2) + '\n'], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `algo-studio-progress-${__utcDateStr()}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          setTimeout(() => URL.revokeObjectURL(url), 1000);
          __setPyodideStatusBanner('Progress backup downloaded as JSON.');
        });
      }
      if (impBtn && impInput && !impBtn.dataset.bound) {
        impBtn.dataset.bound = '1';
        impBtn.addEventListener('click', () => impInput.click());
        impInput.addEventListener('change', async () => {
          const file = impInput.files && impInput.files[0];
          impInput.value = '';
          if (!file) return;
          try {
            const text = await file.text();
            const parsed = JSON.parse(text);
            if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
              throw new Error('JSON root must be an object.');
            }
            const merged = Object.assign(__defaultProgress(), parsed);
            __saveProgressLocal(merged);
            const fresh = await apiGet('/api/state?sync=1');
            if (fresh.ok) {
              state.progress = fresh.progress;
              state.tags = fresh.tags || [];
              state.spacedRepetition = fresh.spacedRepetition || state.spacedRepetition;
              applyLayoutSizes(state.progress.layoutSizes || {});
              const targetCourse = state.progress.activeCourse || 'schedule-120';
              if (targetCourse !== 'schedule-120') {
                const targetPid = state.progress.coursePositions?.[targetCourse] || null;
                switchCourse(targetCourse, { problemId: targetPid, skipFlush: true, skipPersist: true });
              } else {
                state.activeCourse = 'schedule-120';
                state.activeDay = Number(state.progress.currentDay || 1);
                state.activeCuratedProblemId = null;
                renderHeaderStats();
                populateSelectors();
                renderActiveProblem();
              }
              renderRoadmapAndTags();
              if (window.StudioV2?.onProgressUpdated) window.StudioV2.onProgressUpdated();
              __setPyodideStatusBanner(`Imported progress (${Object.keys(state.progress.solvedLcIds || {}).length} solved LC IDs).`);
            }
          } catch (err) {
            __setPyodideStatusBanner(`Import failed: ${err?.message || err}`);
          }
        });
      }
    }
'''


def _gzip_b64_json(obj: object) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=9)
    return base64.b64encode(compressed).decode("ascii")


def build_single_html(output_path: Path | None = None) -> Path:
    out_file = output_path or (ROOT_DIR / "AlgoStudio.html")
    index_html = (ROOT_DIR / "public" / "index.html").read_text(encoding="utf-8")
    studio_v2_js = (ROOT_DIR / "public" / "studio_v2.js").read_text(encoding="utf-8")
    favicon_bytes = (ROOT_DIR / "public" / "favicon.svg").read_bytes()
    favicon_data_uri = "data:image/svg+xml;base64," + base64.b64encode(favicon_bytes).decode("ascii")

    # 1. Build embedded gzipped boot payload (all 120 daily problems + 286 curated problems)
    boot_payload = {
        "curriculum": {
            "phases": cd.PHASES,
            "allTags": cd.ALL_TAGS,
            "edgeCasePlaybook": cd.EDGE_CASE_PLAYBOOK,
            "edgeCaseResources": cd.EDGE_CASE_RESOURCES,
            "problems": cd.PROBLEMS,
        },
        "curated": {
            "sheets": cl.SHEETS,
            "dagNodes": cl.DAG_NODES,
            "problemsById": cl.PROBLEMS_BY_ID,
        },
    }
    boot_b64 = _gzip_b64_json(boot_payload)

    # 2. Build embedded gzipped Pyodide Python backend modules
    py_files = {
        "curriculum_data.py": CURRICULUM_STUB_PY,
        "curated_lists.py": (ROOT_DIR / "curated_lists.py").read_text(encoding="utf-8"),
        "server.py": (ROOT_DIR / "server.py").read_text(encoding="utf-8"),
        "pyodide_shim.py": (ROOT_DIR / "pyodide_shim.py").read_text(encoding="utf-8"),
    }
    pyfiles_b64 = _gzip_b64_json(py_files)

    html = index_html

    # 3. Inline favicon as data URI and strip HTTP-only manifest/icon/preload references
    for target, repl in (
        ('content="/favicon.svg"', f'content="{favicon_data_uri}"'),
        ('href="/favicon.svg"', f'href="{favicon_data_uri}"'),
        ('src="/favicon.svg"', f'src="{favicon_data_uri}"'),
        ('  <link rel="apple-touch-icon" href="/icon-192.png">\n', ""),
        ('  <link rel="manifest" href="/manifest.json">\n', ""),
        ('  <script src="/preload.js"></script>\n', ""),
        ('id="popout-btn" href="/"', 'id="popout-btn" href="#"'),
    ):
        if target not in html:
            raise RuntimeError(f"Expected anchor not found in public/index.html: {target!r}")
        html = html.replace(target, repl, 1)

    # 4. Add Export JSON / Import JSON backup controls into the top toolbar
    toolbar_anchor = '          <button type="button" class="icon-btn" id="reset-layout-btn" title="Reset all resized column widths and box heights to default">Reset Layout</button>'
    toolbar_repl = (
        toolbar_anchor
        + '\n          <button type="button" class="icon-btn" id="export-progress-btn" title="Download all solved progress, drafts, bookmarks, and notes as a JSON backup">Export</button>'
        + '\n          <button type="button" class="icon-btn" id="import-progress-btn" title="Restore progress from a previously exported JSON backup">Import</button>'
        + '\n          <input type="file" id="import-progress-file" accept=".json,application/json" style="display:none">'
    )
    if toolbar_anchor not in html:
        raise RuntimeError("Toolbar anchor not found in public/index.html")
    html = html.replace(toolbar_anchor, toolbar_repl, 1)

    # 5. Replace HTTP apiGet / apiPost block with the single-file browser runtime
    api_start_anchor = "    function getAuthHeaders(extra = {}) {"
    api_end_anchor = "    function escapeHtml(str) {"
    s_idx = html.find(api_start_anchor)
    e_idx = html.find(api_end_anchor)
    if s_idx < 0 or e_idx < 0 or e_idx <= s_idx:
        raise RuntimeError("Could not locate apiGet/apiPost block in public/index.html")
    runtime_js = BROWSER_RUNTIME_JS.replace("__PYODIDE_BASE_URL__", PYODIDE_BASE_URL)
    html = html[:s_idx] + runtime_js + "\n\n" + html[e_idx:]

    # 6. Inject embedded gzipped bundles right before the main <script>
    main_script_anchor = "  <script>\n    const state = {"
    if main_script_anchor not in html:
        raise RuntimeError("Could not locate main <script> block in public/index.html")
    bundles_html = (
        f'  <script type="text/plain" id="algo-studio-boot-gz">{boot_b64}</script>\n'
        f'  <script type="text/plain" id="algo-studio-pyfiles-gz">{pyfiles_b64}</script>\n'
    )
    html = html.replace(main_script_anchor, bundles_html + main_script_anchor, 1)

    # 7. Inline studio_v2.js BEFORE booting init() so StudioV2 is guaranteed ready
    tail_anchor = (
        "    init();\n"
        "    if ('serviceWorker' in navigator && (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')) {\n"
        "      navigator.serviceWorker.register('/sw.js').catch(() => {});\n"
        "    }\n"
        "  </script>\n"
        '  <script src="/studio_v2.js"></script>\n'
        "</body>"
    )
    if tail_anchor not in html:
        raise RuntimeError("Could not locate tail script block in public/index.html")

    safe_studio_v2_js = studio_v2_js.replace("</script", "<\\/script")
    tail_repl = (
        "    __wireBackupRestoreButtons();\n"
        "    window.AlgoStudioBridge.bootSingleFile = () => init();\n"
        "  </script>\n"
        "  <script>\n"
        + safe_studio_v2_js
        + "\n  </script>\n"
        "  <script>\n"
        "    window.AlgoStudioBridge.bootSingleFile();\n"
        "  </script>\n"
        "</body>"
    )
    html = html.replace(tail_anchor, tail_repl, 1)

    out_file.write_text(html, encoding="utf-8")
    return out_file


if __name__ == "__main__":
    built = build_single_html()
    size_kb = built.stat().st_size / 1024.0
    print(f"Built {built} ({size_kb:.1f} KB / {size_kb / 1024.0:.2f} MB)")
