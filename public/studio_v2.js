/* Algo Studio v2.0.0 Frontend Module
 * Implements:
 * - Tab 5 Special Curated Problem Lists (Grind 75 / Core 70, LeetCode Top 150, NeetCode 150 + DAG, SQL 50 + DAG)
 * - Live SQLite 3 Schema & Side-by-Side Result Table Renderers
 * - Editor Find/Replace (Ctrl+F / Ctrl+H), Go to Line (Ctrl+G), Word Wrap, Font Size, Bookmarks
 * - 5-Mode Structured AI Prompt Builder (Copy for AI)
 * - Tab 2 Timed Pressure Recall Drills (Line Recall, Token Blitz, Blind Master)
 * - Tab 2 4-Stage 45-Min Mock Interview & 75-Min 3-Question OA Simulator
 * - Tab 3 Multi-Approach Trade-Off Matrix & Beginner Guide
 */
(function () {
  'use strict';

  const B = () => window.AlgoStudioBridge;

  const v2State = {
    activeSheetId: 'grind-75',
    grindCore70Only: false,
    sheetViewMode: 'list', /* 'list' | 'dag' */
    selectedDagNodeId: null,
    searchQuery: '',
    diffFilter: 'all',
    statusFilter: 'all',
    coachMode: 'guided', /* 'guided' | 'pressure' | 'exam' */
    editorFontSize: 13,
    editorWrap: false,
    findMatchIndex: -1,
    copyAiTimerId: null,
    /* Pressure Recall Drill State */
    pressure: {
      tier: 1,
      active: false,
      finished: false,
      problemKey: '',
      lines: [],
      stepIdx: 0,
      lives: 3,
      score: 0,
      streak: 0,
      maxStreak: 0,
      timeLeft: 12,
      maxTime: 12,
      timerId: null,
      currentQuestion: null,
      feedback: null,
      peeked: false,
    },
    /* Exam Simulator State */
    exam: {
      subMode: 'mock', /* 'mock' | 'oa' */
      mockPool: 'grind-75',
      mockDiff: 'all',
      mockActive: false,
      mockStage: 1,
      mockProblem: null,
      mockSeconds: 45 * 60,
      mockTimerId: null,
      mockClarifyText: '',
      mockApproachText: '',
      mockApproachFeedback: null,
      mockCode: '',
      mockRunResult: null,
      mockComplexityText: '',
      mockFinalGrade: null,
      mockGrading: false,
      /* OA 3-Question */
      oaIncludeSql: true,
      oaActive: false,
      oaFinished: false,
      oaSeconds: 75 * 60,
      oaTimerId: null,
      oaActiveIdx: 0,
      oaQuestions: [],
      oaSummary: null,
      oaRunning: false,
      oaSubmitting: false,
    },
    selectedApproachIdx: -1,
  };

  /* ==========================================================================
     HELPERS
     ========================================================================== */
  function esc(str) {
    return B().escapeHtml(str);
  }

  function rich(str) {
    return B().formatRichText(str);
  }

  function isCuratedSolved(prob) {
    if (!prob) return false;
    const solvedLc = B().state.progress?.solvedLcIds || {};
    return Boolean(solvedLc[String(prob.lcNum)]);
  }

  function bookmarkKeyForProblem(p) {
    if (!p) return '';
    return p.isCurated ? String(p.id) : `day-${p.day}`;
  }

  function isBookmarked(key, bookmarkSet = null) {
    if (bookmarkSet) return bookmarkSet.has(String(key));
    const list = B().state.progress?.bookmarks || [];
    return list.includes(String(key));
  }

  function shuffleArray(arr) {
    const out = [...arr];
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  function formatClock(totalSeconds) {
    const s = Math.max(0, Math.floor(totalSeconds));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  function getSheetById(sheetId) {
    const sheets = B().state.curatedCatalog?.sheets || [];
    return sheets.find((s) => s.id === sheetId) || sheets[0] || null;
  }

  function getProblemById(pid) {
    return B().state.curatedCatalog?.problemsById?.[pid] || null;
  }

  function computeSheetStats(sheet, core70Only = false) {
    if (!sheet) return { solved: 0, total: 0 };
    const seen = new Set();
    let solved = 0;
    for (const grp of sheet.groups || []) {
      for (const pid of grp.problemIds || []) {
        if (seen.has(pid)) continue;
        const prob = getProblemById(pid);
        if (!prob) continue;
        if (core70Only && sheet.id === 'grind-75') {
          const meta = prob.sheetMeta?.['grind-75'];
          if (meta && meta.isCore70 === false) continue;
        }
        seen.add(pid);
        if (isCuratedSolved(prob)) solved++;
      }
    }
    return { solved, total: seen.size };
  }

  function inferCourseForProblem(prob, preferredCourse = null) {
    if (preferredCourse) return preferredCourse;
    if (v2State.activeSheetId === 'grind-75') {
      return v2State.grindCore70Only ? 'grind-70' : 'grind-75';
    }
    const sm = prob?.sheetMeta || {};
    if (v2State.activeSheetId && sm[v2State.activeSheetId]) return v2State.activeSheetId;
    if (sm['grind-75']) return 'grind-75';
    if (sm['leetcode-150']) return 'leetcode-150';
    if (sm['neetcode-150']) return 'neetcode-150';
    if (sm['sql-50']) return 'sql-50';
    return 'grind-75';
  }

  function openCuratedProblem(problemId, opts = {}) {
    const bridge = B();
    const prob = getProblemById(problemId);
    if (!prob) return;
    const courseId = inferCourseForProblem(prob, opts.courseId || null);
    bridge.switchCourse(courseId, { problemId });
    if (opts.switchToPressure) {
      bridge.switchTab('coach');
      switchCoachMode('pressure');
      initPressureDrillForProblem(bridge.currentProblem(), v2State.pressure.tier);
    } else if (opts.switchToWorkbench !== false) {
      bridge.switchTab('workbench');
    }
  }

  function syncSheetFromCourse(courseId) {
    if (courseId === 'grind-70') {
      v2State.activeSheetId = 'grind-75';
      v2State.grindCore70Only = true;
      v2State.selectedDagNodeId = null;
      v2State.sheetViewMode = 'list';
      renderCuratedListsTab();
    } else if (courseId === 'grind-75') {
      v2State.activeSheetId = 'grind-75';
      v2State.grindCore70Only = false;
      v2State.selectedDagNodeId = null;
      v2State.sheetViewMode = 'list';
      renderCuratedListsTab();
    } else if (['leetcode-150', 'neetcode-150', 'sql-50'].includes(courseId)) {
      v2State.activeSheetId = courseId;
      v2State.selectedDagNodeId = null;
      const nextSheet = getSheetById(courseId);
      v2State.sheetViewMode = nextSheet?.hasDag ? 'dag' : 'list';
      renderCuratedListsTab();
    }
  }

  function returnToScheduleDay() {
    B().switchCourse('schedule-120');
  }

  /* ==========================================================================
     CURATED CONTEXT BANNER & BOOKMARK BUTTON
     ========================================================================== */
  function updateCuratedContextBanner(p) {
    const banner = document.getElementById('curated-context-banner');
    if (!banner) return;
    // The native Course Selection Menu inside .day-strip now handles active course context cleanly.
    banner.classList.remove('visible');
  }

  function updateBookmarkButtonUI(p) {
    const btn = document.getElementById('toggle-bookmark-btn');
    if (!btn || !p) return;
    const key = bookmarkKeyForProblem(p);
    const saved = isBookmarked(key);
    btn.classList.toggle('bookmarked', saved);
    btn.setAttribute('aria-pressed', saved ? 'true' : 'false');
    btn.textContent = saved ? '★ Saved' : '☆ Save';
  }

  async function toggleBookmarkKey(key) {
    const bridge = B();
    const res = await bridge.apiPost('/api/progress', { toggleBookmark: true, key });
    if (res && res.ok) {
      bridge.state.progress = res.progress;
      updateBookmarkButtonUI(bridge.currentProblem());
      renderCuratedListsTab();
    }
  }

  /* ==========================================================================
     SQL 50 SCHEMA & EXPECTED VS ACTUAL TABLE RENDERERS
     ========================================================================== */
  function renderSqlTableHtml(columns, rows, emptyLabel = '0 rows returned') {
    const cols = Array.isArray(columns) ? columns : [];
    const dataRows = Array.isArray(rows) ? rows : [];
    if (!cols.length && !dataRows.length) {
      return `<div class="muted" style="padding:8px 10px; font-size:11.5px;">${esc(emptyLabel)}</div>`;
    }
    const headerCols = cols.length
      ? cols
      : (dataRows[0] && typeof dataRows[0] === 'object' && !Array.isArray(dataRows[0]) ? Object.keys(dataRows[0]) : []);
    let thead = '<tr>' + headerCols.map((c) => `<th>${esc(c)}</th>`).join('') + '</tr>';
    let tbody = '';
    if (!dataRows.length) {
      tbody = `<tr><td colspan="${Math.max(1, headerCols.length)}" class="muted">${esc(emptyLabel)}</td></tr>`;
    } else {
      tbody = dataRows.slice(0, 30).map((row) => {
        if (Array.isArray(row)) {
          return '<tr>' + row.map((cell) => `<td>${esc(cell === null || cell === undefined ? 'NULL' : String(cell))}</td>`).join('') + '</tr>';
        }
        return '<tr>' + headerCols.map((c) => {
          const val = row[c];
          return `<td>${esc(val === null || val === undefined ? 'NULL' : String(val))}</td>`;
        }).join('') + '</tr>';
      }).join('');
    }
    return `<div class="sql-table-wrap"><table class="sql-data-table"><thead>${thead}</thead><tbody>${tbody}</tbody></table></div>`;
  }

  function renderSqlSchemaBox(p, boxEl) {
    if (!boxEl) return;
    if (!p || !p.isSql) {
      boxEl.style.display = 'none';
      return;
    }
    const tables = p.schemaTables || [];
    let html = `<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">` +
      `<span style="font-size:12px; font-weight:650; color:var(--fg);">Database Schema &amp; Seed Tables (${tables.length})</span>` +
      `<span class="stat-pill" style="font-size:10.5px;">SQLite 3 Engine</span>` +
      `</div>`;
    if (tables.length) {
      html += `<div style="display:flex; flex-direction:column; gap:8px;">`;
      for (const tbl of tables) {
        html += `<div class="sql-schema-table-card">` +
          `<div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">` +
          `<span style="font-family:var(--font-mono); font-size:12px; font-weight:650; color:var(--accent);">${esc(tbl.name)}</span>` +
          `<span class="muted tabular" style="font-size:11px;">${(tbl.rows || []).length} rows</span>` +
          `</div>` +
          renderSqlTableHtml(tbl.columns || [], tbl.rows || [], 'Empty table') +
          `</div>`;
      }
      html += `</div>`;
    }
    if (p.sqlSchema) {
      html += `<details style="margin-top:4px;"><summary class="muted" style="cursor:pointer; font-size:11.5px;">Inspect raw SQL DDL &amp; seed inserts</summary>` +
        `<pre class="stdout-pre" style="margin-top:6px; max-height:160px; overflow:auto;">${esc(p.sqlSchema)}</pre></details>`;
    }
    boxEl.innerHTML = html;
    boxEl.style.display = 'flex';
  }

  function renderSqlTestResults(res, container, summary, submitBtn) {
    const bridge = B();
    const p = bridge.currentProblem();
    container.innerHTML = '';
    const tc = (res.results && res.results[0]) || null;

    if (res.allPassed) {
      bridge.setErrorHighlight(null, '');
      if (submitBtn) submitBtn.classList.add('ready');
      summary.textContent = `SQL query matched expected output (${tc?.runtimeMs ?? 0} ms). Click Submit & Mark Solved to sync progress.`;
      const acc = document.createElement('div');
      acc.className = 'accepted-banner';
      acc.innerHTML =
        `<span>SQL Query Accepted (${esc(tc?.stdout || 'Matched expected result set')})</span>` +
        `<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">` +
        `<button type="button" class="btn-submit ready" id="accepted-sql-save-stay-btn" style="padding:4px 11px; font-size:12px;">Submit &amp; Save</button>` +
        `<button type="button" class="btn-subtle-accent" id="accepted-sql-submit-btn" style="padding:4px 10px; font-size:12px;">Submit &amp; Next →</button>` +
        `</div>`;
      container.appendChild(acc);
      document.getElementById('accepted-sql-save-stay-btn')?.addEventListener('click', () => bridge.submitCurrentSolution('Good', { advance: false }));
      document.getElementById('accepted-sql-submit-btn')?.addEventListener('click', () => bridge.submitCurrentSolution('Good', { advance: true }));
    } else {
      if (submitBtn) submitBtn.classList.remove('ready');
      const errLn = res.errorLine || tc?.errorLine || null;
      const errMsg = res.error || tc?.error || 'Result set did not match expected rows.';
      if (errLn) {
        bridge.setErrorHighlight(errLn, `Line ${errLn}: ${errMsg}`);
      } else {
        bridge.setErrorHighlight(null, '');
      }
      summary.textContent = res.error || tc?.error
        ? `SQL Execution Error: ${errMsg}`
        : `Query ran (${tc?.runtimeMs ?? 0} ms) but output rows differed from expected.`;
    }

    if (tc) {
      const rowBox = document.createElement('div');
      rowBox.className = 'test-case-row ' + (tc.passed ? 'test-pass' : 'test-fail');
      let inner =
        `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
        `<span style="font-weight:650; color:${tc.passed ? 'var(--success)' : 'var(--danger)'};">${esc(tc.label || 'SQLite Dataset')} [${tc.passed ? 'PASS' : 'FAIL'}]</span>` +
        `<div style="display:flex; align-items:center; gap:6px;">` +
        (!tc.passed ? `<button type="button" class="btn-subtle-accent" id="sql-diagnose-btn" style="padding:2px 8px; font-size:11px;">Diagnose in AI Co-Pilot ◫</button>` : '') +
        `<span class="muted tabular">${Number(tc.runtimeMs ?? 0) || 0} ms</span>` +
        `</div>` +
        `</div>`;

      if (tc.error) {
        inner += `<pre class="stdout-pre">${esc(tc.error)}</pre>`;
      }

      inner += `<div class="sql-result-grid">` +
        `<div>` +
        `<div style="font-size:11.5px; font-weight:650; color:var(--success); margin-bottom:4px;">Expected Output (${(tc.expected || []).length} rows)</div>` +
        renderSqlTableHtml(tc.expectedColumns || [], tc.expected || [], '0 expected rows') +
        `</div>` +
        `<div>` +
        `<div style="font-size:11.5px; font-weight:650; color:${tc.passed ? 'var(--success)' : 'var(--danger)'}; margin-bottom:4px;">Your Query Output (${Array.isArray(tc.actual) ? tc.actual.length : 0} rows)</div>` +
        (tc.error
          ? `<div class="muted" style="padding:8px 10px; border:1px solid var(--border-col); border-radius:var(--radius-sm); font-size:11.5px;">Fix the SQL error above to inspect returned rows.</div>`
          : renderSqlTableHtml(tc.actualColumns || [], tc.actual || [], '0 rows returned')) +
        `</div>` +
        `</div>`;
      rowBox.innerHTML = inner;
      container.appendChild(rowBox);

      document.getElementById('sql-diagnose-btn')?.addEventListener('click', () => {
        bridge.sendInlineChatMessage(
          tc.error
            ? `Debug this SQLite error on ${p?.title || 'this query'}: ${tc.error}`
            : `My SQL query returned different rows than expected. Explain what clause or join condition I am missing without giving away the full answer first.`
        );
      });
    }
  }

  /* ==========================================================================
     EDITOR QUALITY-OF-LIFE: FIND & REPLACE, GO TO LINE, WRAP, FONT SIZE, COPY FOR AI
     ========================================================================== */
  function openFindBar(focusReplace = false) {
    const bar = document.getElementById('editor-find-bar');
    if (!bar) return;
    bar.classList.add('open');
    const ta = document.getElementById('code-editor');
    const findInput = document.getElementById('editor-find-input');
    const repInput = document.getElementById('editor-replace-input');
    if (ta && findInput && ta.selectionStart !== ta.selectionEnd) {
      const sel = ta.value.slice(ta.selectionStart, ta.selectionEnd);
      if (sel && !sel.includes('\n') && sel.length <= 60) {
        findInput.value = sel;
      }
    }
    if (focusReplace && repInput) {
      repInput.focus();
      repInput.select();
    } else if (findInput) {
      findInput.focus();
      findInput.select();
    }
    updateFindStatus();
  }

  function closeFindBar() {
    const bar = document.getElementById('editor-find-bar');
    if (bar) bar.classList.remove('open');
    document.getElementById('code-editor')?.focus();
  }

  function openGoToLinePrompt() {
    const bar = document.getElementById('editor-find-bar');
    const lnInput = document.getElementById('editor-goto-line-input');
    if (bar) bar.classList.add('open');
    if (lnInput) {
      lnInput.focus();
      lnInput.select();
    }
  }

  function getFindMatches(needle) {
    const ta = document.getElementById('code-editor');
    if (!ta || !needle) return [];
    const text = ta.value.toLowerCase();
    const q = needle.toLowerCase();
    const out = [];
    let pos = 0;
    while (pos <= text.length) {
      const idx = text.indexOf(q, pos);
      if (idx === -1) break;
      out.push(idx);
      pos = idx + Math.max(1, q.length);
    }
    return out;
  }

  function updateFindStatus() {
    const findInput = document.getElementById('editor-find-input');
    const statusEl = document.getElementById('editor-find-status');
    if (!findInput || !statusEl) return;
    const q = findInput.value;
    if (!q) {
      statusEl.textContent = '';
      return;
    }
    const matches = getFindMatches(q);
    if (!matches.length) {
      statusEl.textContent = '0 matches';
      return;
    }
    const idx = v2State.findMatchIndex >= 0 && v2State.findMatchIndex < matches.length ? v2State.findMatchIndex + 1 : 0;
    statusEl.textContent = idx ? `${idx} of ${matches.length}` : `${matches.length} found`;
  }

  function findNextInEditor() {
    const ta = document.getElementById('code-editor');
    const findInput = document.getElementById('editor-find-input');
    if (!ta || !findInput) return;
    const q = findInput.value;
    const matches = getFindMatches(q);
    if (!matches.length) {
      v2State.findMatchIndex = -1;
      updateFindStatus();
      return;
    }
    const curEnd = ta.selectionEnd || 0;
    let nextIdx = matches.findIndex((pos) => pos >= curEnd);
    if (nextIdx === -1) nextIdx = 0;
    v2State.findMatchIndex = nextIdx;
    const start = matches[nextIdx];
    ta.focus();
    ta.setSelectionRange(start, start + q.length);
    const lineNum = ta.value.slice(0, start).split('\n').length;
    const frame = document.getElementById('editor-frame');
    if (frame) {
      frame.scrollTop = Math.max(0, (lineNum - 4) * 20);
    }
    updateFindStatus();
  }

  function replaceCurrentMatch() {
    const ta = document.getElementById('code-editor');
    const findInput = document.getElementById('editor-find-input');
    const repInput = document.getElementById('editor-replace-input');
    if (!ta || !findInput || !repInput) return;
    const q = findInput.value;
    if (!q) return;
    const sel = ta.value.slice(ta.selectionStart, ta.selectionEnd);
    if (sel.toLowerCase() !== q.toLowerCase()) {
      findNextInEditor();
      return;
    }
    const rep = repInput.value;
    const start = ta.selectionStart;
    ta.value = ta.value.slice(0, start) + rep + ta.value.slice(ta.selectionEnd);
    ta.setSelectionRange(start, start + rep.length);
    B().updateEditorRender();
    B().scheduleDraftSave();
    findNextInEditor();
  }

  function replaceAllMatches() {
    const ta = document.getElementById('code-editor');
    const findInput = document.getElementById('editor-find-input');
    const repInput = document.getElementById('editor-replace-input');
    const statusEl = document.getElementById('editor-find-status');
    if (!ta || !findInput || !repInput) return;
    const q = findInput.value;
    if (!q) return;
    const rep = repInput.value;
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(escaped, 'gi');
    const matches = ta.value.match(re);
    if (!matches || !matches.length) {
      if (statusEl) statusEl.textContent = '0 replaced';
      return;
    }
    ta.value = ta.value.replace(re, () => rep);
    B().updateEditorRender();
    B().scheduleDraftSave();
    if (statusEl) statusEl.textContent = `Replaced ${matches.length}`;
  }

  function goToLineInEditor(lineNum) {
    const ta = document.getElementById('code-editor');
    const frame = document.getElementById('editor-frame');
    if (!ta) return;
    const lines = ta.value.split('\n');
    const target = Math.max(1, Math.min(lines.length, Number(lineNum) || 1));
    let offset = 0;
    for (let i = 0; i < target - 1; i++) {
      offset += lines[i].length + 1;
    }
    ta.focus();
    ta.setSelectionRange(offset, offset + lines[target - 1].length);
    if (frame) {
      frame.scrollTop = Math.max(0, (target - 4) * 20);
    }
    const statusEl = document.getElementById('editor-find-status');
    if (statusEl) statusEl.textContent = `Line ${target}`;
  }

  function applyEditorFontSize(nextSize) {
    const clamped = Math.max(11, Math.min(18, Number(nextSize) || 13));
    v2State.editorFontSize = clamped;
    const ta = document.getElementById('code-editor');
    const hi = document.getElementById('code-highlight-layer');
    const gutter = document.getElementById('line-gutter');
    if (ta) ta.style.fontSize = `${clamped}px`;
    if (hi) hi.style.fontSize = `${clamped}px`;
    if (gutter) gutter.style.fontSize = `${Math.max(10, clamped - 1)}px`;
    try {
      localStorage.setItem('algoStudioEditorFont_v2', String(clamped));
    } catch (_) {}
  }

  function toggleEditorWordWrap() {
    v2State.editorWrap = !v2State.editorWrap;
    const frame = document.getElementById('editor-frame');
    const btn = document.getElementById('editor-wrap-btn');
    if (frame) frame.classList.toggle('word-wrap', v2State.editorWrap);
    if (btn) btn.classList.toggle('btn-subtle-accent', v2State.editorWrap);
    try {
      localStorage.setItem('algoStudioEditorWrap_v2', v2State.editorWrap ? '1' : '0');
    } catch (_) {}
  }

  function buildCopyForAiPrompt(modeOverride = '') {
    const bridge = B();
    const p = bridge.currentProblem();
    const code = document.getElementById('code-editor')?.value || '';
    const mode = modeOverride || document.getElementById('copilot-prompt-mode-select')?.value || 'visual_explainer';
    const modeInstructions = {
      visual_explainer: [
        'Explain this problem visually for a visual learner using clean monospace diagrams and step-by-step state pictures.',
        'Format your answer in four short parts:',
        '1. Visual mental model: draw a crisp ASCII diagram of the input structure (array boxes with indices, pointer arrows ^, linked-list -> chains, tree branches, or hash-map buckets) showing the core invariant before any long prose.',
        '2. Step-by-step visual storyboard on Example 1: walk through each key iteration showing the updated diagram, pointer positions, and auxiliary memory side by side, with one plain-English line explaining why each move happens.',
        '3. Naive vs optimal visual contrast: show why the brute-force path repeats work and how the optimal structure cuts Time and Space Big-O.',
        '4. Code check: inspect my numbered code below, highlight any bug or suboptimal loop by exact line number, and show a visual before/after fix if needed.',
      ].join('\n'),
      full_tutor: 'Act as a senior SWE / FDE interview coach. Review my code, identify correctness or edge-case bugs, explain the optimal mental pivot, analyse Big-O time and space complexity, and suggest one follow-up question.',
      hints_only: 'Act as a Socratic interview coach. Do NOT write or reveal the full solution code. Give me 2 progressive nudges about the missing invariant or bug so I can fix it myself.',
      debug_bug: 'Focus strictly on debugging why my current code fails the test cases below. Pinpoint the offending line, walk through the failing input step by step with a visual variable snapshot, and show the minimal patch.',
      explain_complexity: 'Analyse the exact worst-case and amortised time and space complexity of my code below, and compare it visually against the optimal bound.',
      visualize_trace: 'Produce a clean step-by-step visual state trace table (variables, pointer positions, and data structures at each iteration) on Example 1 using my current code.',
    };

    const numberedCode = code
      .trimEnd()
      .split('\n')
      .map((ln, idx) => `${idx + 1}: ${ln}`)
      .join('\n');

    const parts = [
      `## Prompt Mode: ${mode.replace(/_/g, ' ').toUpperCase()}`,
      modeInstructions[mode] || modeInstructions.visual_explainer,
      '',
      `## Problem: ${p.leetcodeId} - ${p.title} (${p.difficulty})`,
      p.statement || '',
    ];

    const ex0 = Array.isArray(p.examples) && p.examples.length ? p.examples[0] : null;
    if (ex0) {
      parts.push('', '## Example 1');
      if (ex0.input) parts.push(`- Input: ${ex0.input}`);
      if (ex0.output) parts.push(`- Output: ${ex0.output}`);
      if (ex0.explanation) parts.push(`- Explanation: ${ex0.explanation}`);
    }

    if (p.isSql && p.sqlSchema) {
      parts.push('', '## SQL Schema', '```sql', p.sqlSchema.trim(), '```');
    }
    if ((p.constraints || []).length) {
      parts.push('', '## Constraints', ...p.constraints.map((c) => `- ${c}`));
    }
    parts.push('', `## My Current Code (${bridge.state.activeLang}, line-numbered)`, '```' + bridge.state.activeLang, numberedCode, '```');

    const lastRes = bridge.state.lastRunResult;
    if (lastRes) {
      parts.push('', `## Latest Execution Result (${lastRes.passed ?? 0} / ${lastRes.total ?? 0} passed)`);
      if (lastRes.error) {
        parts.push(`Error: ${lastRes.error}`);
      }
      const fails = (lastRes.results || []).filter((r) => !r.passed).slice(0, 3);
      for (const f of fails) {
        parts.push(
          `- Test ${f.index} (${f.label || 'Case'}): Input=${JSON.stringify(f.input)} | Expected=${JSON.stringify(f.expected)} | Actual=${JSON.stringify(f.error || f.actual)}`
        );
      }
    }
    return parts.join('\n');
  }

  /* ==========================================================================
     TAB 5: SPECIAL CURATED PROBLEM LISTS (GRIND 75, LC 150, NEETCODE 150, SQL 50)
     ========================================================================== */
  function buildDagSvgHtml(sheet) {
    const allNodes = B().state.curatedCatalog?.dagNodes || [];
    const nodes = allNodes.filter((n) => n.sheetId === sheet.id);
    if (!nodes.length) {
      return `<div class="muted">No skill-tree graph defined for this sheet.</div>`;
    }
    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const nodeStatsById = new Map(nodes.map((n) => {
      const pids = n.problemIds || [];
      const solved = pids.filter((pid) => isCuratedSolved(getProblemById(pid))).length;
      return [n.id, { solved, total: pids.length }];
    }));
    const W = 1040;
    const maxY = Math.max(...nodes.map((n) => Number(n.y || 0))) + 115;
    const H = Math.max(360, maxY);
    const boxW = 164;
    const boxH = 62;

    let edgesSvg = '';
    for (const n of nodes) {
      const x2 = Number(n.x || 0) + boxW / 2;
      const y2 = Number(n.y || 0);
      for (const preId of n.prereqs || []) {
        const pre = nodeById.get(preId);
        if (!pre) continue;
        const x1 = Number(pre.x || 0) + boxW / 2;
        const y1 = Number(pre.y || 0) + boxH;
        const midY = (y1 + y2) / 2;
        const preStats = nodeStatsById.get(preId) || { solved: 0, total: 0 };
        const preComplete = preStats.solved > 0 && preStats.solved === preStats.total;
        const strokeCol = preComplete ? 'var(--success)' : 'var(--border-col)';
        edgesSvg += `<path d="M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2 - 3}" fill="none" stroke="${strokeCol}" stroke-width="${preComplete ? 2.2 : 1.5}" marker-end="url(#dag-arrow)"></path>`;
      }
    }

    let nodesSvg = '';
    for (const n of nodes) {
      const { solved, total } = nodeStatsById.get(n.id) || { solved: 0, total: 0 };
      const pct = total ? Math.round((solved / total) * 100) : 0;
      const isSelected = v2State.selectedDagNodeId === n.id;
      const stroke = isSelected
        ? 'var(--accent)'
        : (solved === total && total > 0 ? 'var(--success)' : 'var(--border-col)');
      const fill = isSelected
        ? 'color-mix(in srgb, var(--accent) 12%, var(--surface))'
        : 'var(--surface)';
      const titleShort = (n.title || '').length > 20 ? n.title.slice(0, 19) + '...' : (n.title || '');
      nodesSvg +=
        `<g class="dag-node-box" data-dag-node="${esc(n.id)}" transform="translate(${Number(n.x) || 0}, ${Number(n.y) || 0})">` +
        `<rect x="0" y="0" width="${boxW}" height="${boxH}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="${isSelected ? 2 : 1.2}"></rect>` +
        `<text x="10" y="18" font-size="10" font-weight="650" fill="var(--accent)" font-family="var(--font-mono)">${esc(n.code || '')}</text>` +
        `<text x="${boxW - 10}" y="18" text-anchor="end" font-size="10.5" font-weight="600" fill="${solved === total && total > 0 ? 'var(--success)' : 'var(--fg-secondary)'}" font-family="var(--font-mono)">${solved}/${total}</text>` +
        `<text x="10" y="36" font-size="12" font-weight="650" fill="var(--fg)" font-family="var(--font-sans)">${esc(titleShort)}</text>` +
        `<rect x="10" y="46" width="${boxW - 20}" height="6" rx="3" fill="var(--surface-3)"></rect>` +
        `<rect x="10" y="46" width="${Math.round(((boxW - 20) * pct) / 100)}" height="6" rx="3" fill="${pct === 100 ? 'var(--success)' : 'var(--accent)'}"></rect>` +
        `</g>`;
    }

    return (
      `<div class="dag-stage-wrap">` +
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap;">` +
      `<span class="muted" style="font-size:11.5px;">Click any module node to filter its problem list below. Green edges indicate completed prerequisite tracks.</span>` +
      (v2State.selectedDagNodeId ? `<button type="button" id="dag-clear-node-btn" style="padding:2px 8px; font-size:11px;">Show All Modules</button>` : '') +
      `</div>` +
      `<svg viewBox="0 0 ${W} ${H}" width="100%" style="min-width:740px; height:auto; display:block;" role="img" aria-label="${esc(sheet.title)} prerequisite skill tree">` +
      `<defs><marker id="dag-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 1 L 10 5 L 0 9 z" fill="var(--fg-muted)"></path></marker></defs>` +
      edgesSvg +
      nodesSvg +
      `</svg>` +
      `</div>`
    );
  }

  function buildCuratedGroupsHtml(activeSheet, activeStats) {
    const bookmarkSet = new Set((B().state.progress?.bookmarks || []).map(String));
    const searchLower = v2State.searchQuery.trim().toLowerCase();
    let visibleProblemCount = 0;
    let groupsHtml = '';

    for (const grp of activeSheet.groups || []) {
      if (v2State.selectedDagNodeId && grp.id && grp.id !== v2State.selectedDagNodeId) {
        continue;
      }
      const rows = [];
      let grpSolved = 0;
      let grpTotal = 0;

      for (const pid of grp.problemIds || []) {
        const prob = getProblemById(pid);
        if (!prob) continue;
        if (activeSheet.id === 'grind-75' && v2State.grindCore70Only) {
          const meta = prob.sheetMeta?.['grind-75'];
          if (meta && meta.isCore70 === false) continue;
        }
        grpTotal++;
        const solved = isCuratedSolved(prob);
        if (solved) grpSolved++;
        const bookmarked = isBookmarked(prob.id, bookmarkSet);

        if (v2State.diffFilter !== 'all' && prob.difficulty !== v2State.diffFilter) continue;
        if (v2State.statusFilter === 'solved' && !solved) continue;
        if (v2State.statusFilter === 'todo' && solved) continue;
        if (v2State.statusFilter === 'bookmarked' && !bookmarked) continue;
        if (searchLower) {
          const hay = [
            prob.title,
            prob.leetcodeId,
            String(prob.lcNum),
            grp.title,
            ...(prob.tags || []),
            ...(prob.companies || []),
          ].join(' ').toLowerCase();
          if (!hay.includes(searchLower)) continue;
        }

        visibleProblemCount++;
        const diffCls = prob.difficulty.includes('Easy') ? 'diff-Easy' : prob.difficulty.includes('Medium') ? 'diff-Medium' : 'diff-Hard';
        const topTags = (prob.tags || []).slice(0, 2);
        const topCo = (prob.companies || []).slice(0, 1);

        rows.push(
          `<div class="curated-row" style="${solved ? 'background:color-mix(in srgb, var(--success) 5%, var(--surface));' : ''}">` +
          `<div class="curated-row-left">` +
          `<span class="muted tabular" style="font-family:var(--font-mono); font-size:11.5px; min-width:52px;">${esc(prob.leetcodeId)}</span>` +
          `<button type="button" data-open-curated="${esc(prob.id)}" style="border:none; background:transparent; padding:0; text-align:left; font-weight:600; font-size:13px; color:var(--fg); cursor:pointer;">${esc(prob.title)}</button>` +
          (prob.isSql ? `<span class="stat-pill" style="font-size:10px; padding:1px 5px;">SQL</span>` : '') +
          `</div>` +
          `<div class="curated-row-meta">` +
          topTags.map((t) => `<span class="tag-chip" style="font-size:10.5px;">${esc(t)}</span>`).join('') +
          topCo.map((c) => `<span class="stat-pill" style="font-size:10px; padding:1px 6px;">${esc(c)}</span>`).join('') +
          `<span class="diff-badge ${diffCls}">${esc(prob.difficulty)}</span>` +
          `<button type="button" data-bm-curated="${esc(prob.id)}" class="bookmark-toggle-btn${bookmarked ? ' bookmarked' : ''}" style="padding:2px 7px; font-size:11px;" title="Bookmark problem">${bookmarked ? '★' : '☆'}</button>` +
          `<button type="button" data-solve-toggle-curated="${esc(prob.id)}" class="roadmap-solved-btn${solved ? ' is-solved' : ''}" style="padding:2px 8px; font-size:11px;">${solved ? 'Remove Solved' : 'Mark Solved'}</button>` +
          `<button type="button" data-drill-curated="${esc(prob.id)}" style="padding:3px 8px; font-size:11px;">Drill</button>` +
          `<button type="button" class="btn-subtle-accent" data-open-curated="${esc(prob.id)}" style="padding:3px 9px; font-size:11px;">Solve →</button>` +
          `</div>` +
          `</div>`
        );
      }

      if (!rows.length) continue;
      groupsHtml +=
        `<div class="curated-group-card">` +
        `<div class="curated-group-head">` +
        `<span>${esc(grp.title)}</span>` +
        `<span class="muted tabular">${grpSolved} / ${grpTotal} solved</span>` +
        `</div>` +
        rows.join('') +
        `</div>`;
    }

    if (!groupsHtml) {
      groupsHtml = `<div class="inner-box muted">No curated problems match your current search or filter settings. Clear the filters to browse all ${activeStats.total} problems in ${esc(activeSheet.title)}.</div>`;
    }
    return { groupsHtml, visibleProblemCount };
  }

  function wireCuratedGroupRowListeners(container) {
    if (!container) return;
    container.querySelectorAll('[data-open-curated]').forEach((btn) => {
      btn.addEventListener('click', () => openCuratedProblem(btn.getAttribute('data-open-curated')));
    });
    container.querySelectorAll('[data-drill-curated]').forEach((btn) => {
      btn.addEventListener('click', () => openCuratedProblem(btn.getAttribute('data-drill-curated'), { switchToPressure: true }));
    });
    container.querySelectorAll('[data-bm-curated]').forEach((btn) => {
      btn.addEventListener('click', () => toggleBookmarkKey(btn.getAttribute('data-bm-curated')));
    });
    container.querySelectorAll('[data-solve-toggle-curated]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const pid = btn.getAttribute('data-solve-toggle-curated');
        const prob = getProblemById(pid);
        if (!prob) return;
        const nextSolved = !isCuratedSolved(prob);
        btn.disabled = true;
        try {
          const bridge = B();
          const res = await bridge.apiPost('/api/progress', {
            toggleSolvedCurated: true,
            problemId: pid,
            solved: nextSolved,
            rating: 'Good',
            language: prob.isSql ? 'sql' : 'python',
          });
          if (res && res.ok) {
            bridge.state.progress = res.progress;
            if (res.tags) bridge.state.tags = res.tags;
            if (res.spacedRepetition) bridge.state.spacedRepetition = res.spacedRepetition;
            bridge.renderHeaderStats();
            bridge.populateSelectors();
            bridge.updateSolvedIndicatorsForActiveDay();
            bridge.renderRoadmapAndTags();
            renderCuratedListsTab();
          }
        } finally {
          btn.disabled = false;
        }
      });
    });
  }

  function renderCuratedListsTab() {
    const pane = document.getElementById('pane-lists');
    if (!pane) return;
    const catalog = B().state.curatedCatalog;
    if (!catalog || !(catalog.sheets || []).length) {
      pane.innerHTML = `<div class="card"><div class="muted">Loading curated problem lists (Grind 75, LeetCode Top 150, NeetCode 150, SQL 50)...</div></div>`;
      return;
    }

    const sheets = catalog.sheets;
    const activeSheet = getSheetById(v2State.activeSheetId);
    if (!activeSheet) return;
    if (!activeSheet.hasDag && v2State.sheetViewMode === 'dag') {
      v2State.sheetViewMode = 'list';
      v2State.selectedDagNodeId = null;
    }

    const totalUniqueSolved = Object.keys(B().state.progress?.solvedLcIds || {}).length;
    const totalUniqueCatalog = Object.keys(catalog.problemsById || {}).length;

    const sheetCardsHtml = sheets.map((s) => {
      const st = computeSheetStats(s, s.id === 'grind-75' && v2State.grindCore70Only);
      const pct = st.total ? Math.round((st.solved / st.total) * 100) : 0;
      const isAct = s.id === activeSheet.id;
      return (
        `<button type="button" class="sheet-tab-card${isAct ? ' active' : ''}" data-select-sheet="${esc(s.id)}">` +
        `<span class="sheet-tab-title">${esc(s.shortTitle || s.title)}</span>` +
        `<span class="sheet-tab-stat">${st.solved} / ${st.total} solved (${pct}%)</span>` +
        `<div style="width:100%; height:4px; border-radius:2px; background:var(--surface-3); overflow:hidden; margin-top:2px;">` +
        `<div style="width:${pct}%; height:100%; background:${pct === 100 ? 'var(--success)' : 'var(--accent)'};"></div>` +
        `</div>` +
        `</button>`
      );
    }).join('');

    const activeStats = computeSheetStats(activeSheet, activeSheet.id === 'grind-75' && v2State.grindCore70Only);
    const { groupsHtml, visibleProblemCount } = buildCuratedGroupsHtml(activeSheet, activeStats);

    const grindToggleHtml = activeSheet.id === 'grind-75'
      ? `<button type="button" id="grind-core70-toggle-btn" class="${v2State.grindCore70Only ? 'btn-subtle-accent' : ''}" style="font-size:11.5px; padding:4px 9px;">${v2State.grindCore70Only ? 'Showing Core 70 (Switch to All 75)' : 'Showing All 75 (Filter Core 70)'}</button>`
      : '';

    const dagToggleHtml = activeSheet.hasDag
      ? `<button type="button" id="curated-dag-toggle-btn" class="${v2State.sheetViewMode === 'dag' ? 'btn-subtle-accent' : ''}" style="font-size:11.5px; padding:4px 9px;">${v2State.sheetViewMode === 'dag' ? 'Hide Skill-Tree DAG' : 'Show Skill-Tree DAG'}</button>`
      : '';

    pane.innerHTML =
      `<div class="card">` +
      `<div class="card-header">` +
      `<div>` +
      `<h2 class="card-title">Curated Interview Problem Lists</h2>` +
      `<span class="muted">Grind 75 (Core 70 + 5), LeetCode Top Interview 150, NeetCode 150 Skill-Tree, and SQL 50 Relational Mastery. Solved state syncs automatically across every sheet and your 120-day schedule.</span>` +
      `</div>` +
      `<span class="stat-pill tabular">${totalUniqueSolved} / ${totalUniqueCatalog} unique solved</span>` +
      `</div>` +
      `<div class="sheets-nav-grid">${sheetCardsHtml}</div>` +
      `</div>` +

      `<div class="card">` +
      `<div class="card-header">` +
      `<div>` +
      `<h3 class="card-title">${esc(activeSheet.title)}</h3>` +
      `<span class="muted">${esc(activeSheet.subtitle || '')}</span>` +
      `</div>` +
      `<div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">` +
      grindToggleHtml +
      dagToggleHtml +
      `<span class="stat-pill tabular">${activeStats.solved} / ${activeStats.total} solved</span>` +
      `</div>` +
      `</div>` +

      (activeSheet.hasDag && v2State.sheetViewMode === 'dag' ? buildDagSvgHtml(activeSheet) : '') +

      `<div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">` +
      `<input type="text" id="curated-search-input" class="compact-text-input" placeholder="Search title, LC #, tag, or company (e.g. Google, 206, Tree)..." value="${esc(v2State.searchQuery)}" style="flex:1 1 220px;" aria-label="Search curated problems">` +
      `<select id="curated-diff-select" class="day-select" style="width:auto; min-width:115px; flex:initial;" aria-label="Filter by difficulty">` +
      `<option value="all"${v2State.diffFilter === 'all' ? ' selected' : ''}>All Difficulties</option>` +
      `<option value="Easy"${v2State.diffFilter === 'Easy' ? ' selected' : ''}>Easy</option>` +
      `<option value="Medium"${v2State.diffFilter === 'Medium' ? ' selected' : ''}>Medium</option>` +
      `<option value="Hard"${v2State.diffFilter === 'Hard' ? ' selected' : ''}>Hard</option>` +
      `</select>` +
      `<select id="curated-status-select" class="day-select" style="width:auto; min-width:120px; flex:initial;" aria-label="Filter by status">` +
      `<option value="all"${v2State.statusFilter === 'all' ? ' selected' : ''}>All Statuses</option>` +
      `<option value="todo"${v2State.statusFilter === 'todo' ? ' selected' : ''}>Unsolved</option>` +
      `<option value="solved"${v2State.statusFilter === 'solved' ? ' selected' : ''}>Solved</option>` +
      `<option value="bookmarked"${v2State.statusFilter === 'bookmarked' ? ' selected' : ''}>Bookmarked</option>` +
      `</select>` +
      `<span id="curated-visible-count" class="muted tabular" style="font-size:11.5px;">Showing ${visibleProblemCount}</span>` +
      `</div>` +

      `<div id="curated-groups-container" style="display:flex; flex-direction:column; gap:10px;">${groupsHtml}</div>` +
      `</div>`;

    const groupsContainer = document.getElementById('curated-groups-container');
    const refreshFilteredGroups = () => {
      const next = buildCuratedGroupsHtml(activeSheet, activeStats);
      if (groupsContainer) {
        groupsContainer.innerHTML = next.groupsHtml;
        wireCuratedGroupRowListeners(groupsContainer);
      }
      const cntEl = document.getElementById('curated-visible-count');
      if (cntEl) cntEl.textContent = `Showing ${next.visibleProblemCount}`;
    };

    // Wire Tab 5 listeners
    pane.querySelectorAll('[data-select-sheet]').forEach((btn) => {
      btn.addEventListener('click', () => {
        v2State.activeSheetId = btn.getAttribute('data-select-sheet');
        v2State.selectedDagNodeId = null;
        const nextSheet = getSheetById(v2State.activeSheetId);
        v2State.sheetViewMode = nextSheet?.hasDag ? 'dag' : 'list';
        renderCuratedListsTab();
      });
    });

    document.getElementById('grind-core70-toggle-btn')?.addEventListener('click', () => {
      v2State.grindCore70Only = !v2State.grindCore70Only;
      renderCuratedListsTab();
    });

    document.getElementById('curated-dag-toggle-btn')?.addEventListener('click', () => {
      v2State.sheetViewMode = v2State.sheetViewMode === 'dag' ? 'list' : 'dag';
      if (v2State.sheetViewMode !== 'dag') v2State.selectedDagNodeId = null;
      renderCuratedListsTab();
    });

    document.getElementById('dag-clear-node-btn')?.addEventListener('click', () => {
      v2State.selectedDagNodeId = null;
      renderCuratedListsTab();
    });

    pane.querySelectorAll('[data-dag-node]').forEach((g) => {
      g.addEventListener('click', () => {
        const nid = g.getAttribute('data-dag-node');
        v2State.selectedDagNodeId = v2State.selectedDagNodeId === nid ? null : nid;
        renderCuratedListsTab();
      });
    });

    const searchInput = document.getElementById('curated-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        v2State.searchQuery = e.target.value;
        refreshFilteredGroups();
      });
    }

    document.getElementById('curated-diff-select')?.addEventListener('change', (e) => {
      v2State.diffFilter = e.target.value;
      refreshFilteredGroups();
    });

    document.getElementById('curated-status-select')?.addEventListener('change', (e) => {
      v2State.statusFilter = e.target.value;
      refreshFilteredGroups();
    });

    wireCuratedGroupRowListeners(groupsContainer);
  }

  /* ==========================================================================
     TAB 3: MULTI-APPROACH TRADE-OFF MATRIX & BEGINNER GUIDE
     ========================================================================== */
  function renderApproachesMatrix(p) {
    const card = document.getElementById('solution-approaches-card');
    if (!card || !p) return;

    let approaches = Array.isArray(p.approaches) && p.approaches.length ? p.approaches : [];
    if (!approaches.length) {
      approaches = [
        {
          name: 'Instinctive Baseline',
          badge: 'BRUTE FORCE',
          timeComplexity: p.complexity?.bruteTime || 'O(N^2)',
          spaceComplexity: p.complexity?.bruteSpace || 'O(1)',
          intuition: p.mentalModel?.instinctiveTrap || 'Direct brute-force exploration without auxiliary state caching.',
          code: '',
        },
        {
          name: 'Optimal SWE Approach',
          badge: 'OPTIMAL',
          timeComplexity: p.complexity?.optimalTime || 'O(N)',
          spaceComplexity: p.complexity?.optimalSpace || 'O(N)',
          intuition: p.mentalModel?.optimalPivot || p.walkthrough || '',
          code: p.solutionCode?.[B().state.activeLang] || p.solutionCode?.python || p.solutionCode?.sql || '',
        },
      ];
    }

    if (v2State.selectedApproachIdx < 0 || v2State.selectedApproachIdx >= approaches.length) {
      v2State.selectedApproachIdx = approaches.length - 1;
    }
    const sel = approaches[v2State.selectedApproachIdx];

    const rowsHtml = approaches.map((ap, idx) => {
      const isSel = idx === v2State.selectedApproachIdx;
      const badgeText = String(ap.badge || (idx === approaches.length - 1 ? 'OPTIMAL' : 'APPROACH')).toUpperCase();
      const badgeCol = badgeText.includes('OPTIMAL') ? 'var(--success)' : badgeText.includes('BRUTE') ? 'var(--danger)' : 'var(--accent)';
      return (
        `<tr data-approach-idx="${idx}" class="${isSel ? 'selected' : ''}">` +
        `<td style="font-weight:600; color:var(--fg);">${esc(ap.name || `Approach ${idx + 1}`)}</td>` +
        `<td><span class="stat-pill" style="font-size:10px; padding:1px 6px; color:${badgeCol};">${esc(badgeText)}</span></td>` +
        `<td style="font-family:var(--font-mono);">${esc(ap.timeComplexity || '')}</td>` +
        `<td style="font-family:var(--font-mono);">${esc(ap.spaceComplexity || '')}</td>` +
        `<td class="muted">${rich(ap.intuition || '')}</td>` +
        `</tr>`
      );
    }).join('');

    const guideHtml = p.beginnerGuide
      ? `<details class="inner-box" style="margin-top:4px;"><summary style="cursor:pointer; font-weight:650; font-size:12px; color:var(--fg);">Beginner Guide &amp; Mental Intuition</summary>` +
        `<div style="margin-top:6px; font-size:12.5px; color:var(--fg-secondary); line-height:1.55;">${rich(p.beginnerGuide)}</div></details>`
      : '';

    card.style.display = 'flex';
    card.innerHTML =
      `<div class="card-header">` +
      `<div>` +
      `<h2 class="card-title">Approach Trade-Off Matrix (${approaches.length} ${approaches.length === 1 ? 'Approach' : 'Approaches'})</h2>` +
      `<span class="muted">Compare Brute Force, Better, and Optimal trade-offs. Click any row to preview or load its implementation.</span>` +
      `</div>` +
      (sel?.code ? `<button type="button" id="load-selected-approach-btn" class="btn-subtle-accent">Load Selected into Editor</button>` : '') +
      `</div>` +
      `<div class="sql-table-wrap">` +
      `<table class="approach-matrix-table">` +
      `<thead><tr><th>Approach</th><th>Tier</th><th>Time</th><th>Space</th><th>Core Intuition</th></tr></thead>` +
      `<tbody>${rowsHtml}</tbody>` +
      `</table>` +
      `</div>` +
      (sel?.code ? `<pre class="solution-code-pre" style="max-height:240px;">${B().highlightCodeHtml(sel.code)}</pre>` : '') +
      guideHtml;

    card.querySelectorAll('[data-approach-idx]').forEach((tr) => {
      tr.addEventListener('click', () => {
        v2State.selectedApproachIdx = Number(tr.getAttribute('data-approach-idx'));
        renderApproachesMatrix(p);
      });
    });

    document.getElementById('load-selected-approach-btn')?.addEventListener('click', () => {
      if (!sel?.code) return;
      const ta = document.getElementById('code-editor');
      if (ta) {
        ta.value = sel.code;
        B().setErrorHighlight(null, '');
        B().updateEditorRender();
        B().scheduleDraftSave();
        B().switchTab('workbench');
      }
    });
  }

  /* ==========================================================================
     TAB 2 SUB-MODE SWITCHER (GUIDED | PRESSURE RECALL | MOCK & OA)
     ========================================================================== */
  function switchCoachMode(mode) {
    v2State.coachMode = mode;
    document.querySelectorAll('#coach-mode-bar .coach-mode-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-coach-mode') === mode);
    });
    const pGuided = document.getElementById('coach-panel-guided');
    const pPress = document.getElementById('coach-panel-pressure');
    const pExam = document.getElementById('coach-panel-exam');
    if (pGuided) pGuided.style.display = mode === 'guided' ? 'flex' : 'none';
    if (pPress) pPress.style.display = mode === 'pressure' ? 'flex' : 'none';
    if (pExam) pExam.style.display = mode === 'exam' ? 'flex' : 'none';

    if (mode !== 'pressure') stopPressureTimer();
    if (mode === 'pressure') {
      renderPressurePanel();
    } else if (mode === 'exam') {
      renderExamPanel();
    }
    window.StudioV3?.onCoachModeChanged?.(mode);
  }

  /* ==========================================================================
     TAB 2 SUB-MODE B: TIMED PRESSURE RECALL DRILLS
     ========================================================================== */
  function stopPressureTimer() {
    if (v2State.pressure.timerId) {
      clearInterval(v2State.pressure.timerId);
      v2State.pressure.timerId = null;
    }
  }

  function extractDrillLines(p) {
    const raw = (p?.isSql ? p?.solutionCode?.sql : (p?.solutionCode?.python || p?.solutionCode?.typescript || p?.solutionCode?.go)) || '';
    const prefixLines = [];
    const drillLines = [];
    for (const line of raw.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (trimmed.startsWith('#') || trimmed.startsWith('--') || trimmed.startsWith('//')) continue;
      if (!p?.isSql && drillLines.length === 0 && (trimmed.startsWith('class Solution') || trimmed.startsWith('def '))) {
        prefixLines.push(line);
        continue;
      }
      drillLines.push(line);
    }
    return { prefixLines, drillLines: drillLines.slice(0, 12) };
  }

  function mutateLineDistractors(line, allLines, isSql) {
    const candidates = new Set();
    const t = line.trim();
    const swaps = isSql
      ? [
          ['LEFT JOIN', 'INNER JOIN'],
          ['INNER JOIN', 'LEFT JOIN'],
          ['>=', '>'],
          ['<=', '<'],
          ['=', '!='],
          ['DESC', 'ASC'],
          ['ASC', 'DESC'],
          ['GROUP BY', 'ORDER BY'],
          ['COUNT(', 'SUM('],
          ['AND', 'OR'],
          ['IS NULL', 'IS NOT NULL'],
          ['DISTINCT ', ''],
        ]
      : [
          [' <= ', ' < '],
          [' < ', ' <= '],
          [' >= ', ' > '],
          [' > ', ' >= '],
          ['+ 1', '- 1'],
          ['- 1', '+ 1'],
          [' == ', ' != '],
          [' != ', ' == '],
          ['+= 1', '-= 1'],
          ['-= 1', '+= 1'],
          [' and ', ' or '],
          [' or ', ' and '],
          ['min(', 'max('],
          ['max(', 'min('],
          ['pop()', 'popleft()'],
          ['True', 'False'],
          ['False', 'True'],
        ];

    for (const [a, b] of swaps) {
      if (t.includes(a)) {
        const m = line.replace(a, b);
        if (m.trim() !== t) candidates.add(m);
      }
      if (candidates.size >= 3) break;
    }
    for (const other of allLines) {
      if (other.trim() !== t && candidates.size < 3) {
        candidates.add(other);
      }
    }
    const fallbacks = isSql
      ? ['WHERE 1 = 0', 'ORDER BY 1 DESC', 'GROUP BY id HAVING COUNT(*) > 1']
      : ['return None', 'continue', 'break'];
    for (const fb of fallbacks) {
      if (candidates.size >= 3) break;
      if (fb !== t) candidates.add(fb);
    }
    return Array.from(candidates).slice(0, 3);
  }

  function buildPressureQuestion(lines, idx, tier, isSql) {
    const target = lines[idx] || '';
    if (tier === 2) {
      const tokens = target.match(/[A-Za-z_][A-Za-z0-9_]*|==|!=|<=|>=|\+=|-=/g) || [];
      const interesting = tokens.filter((tk) => tk.length >= 2 && !['def', 'self', 'the'].includes(tk));
      const chosen = interesting.length ? interesting[Math.min(interesting.length - 1, Math.floor(interesting.length / 2))] : (tokens[0] || target.trim());
      const masked = target.replace(chosen, '_____');
      const pool = isSql
        ? ['LEFT', 'INNER', 'COUNT', 'SUM', 'AVG', 'HAVING', 'WHERE', 'DISTINCT', 'DESC', 'ASC', 'COALESCE', 'NULL']
        : ['left', 'right', 'mid', 'curr', 'prev', 'seen', 'nums', 'len', 'max', 'min', 'append', 'pop', '<=', '<', '==', '!=', 'None'];
      const opts = new Set([chosen]);
      for (const pTok of pool) {
        if (opts.size >= 4) break;
        if (pTok !== chosen) opts.add(pTok);
      }
      const shuffled = shuffleArray(Array.from(opts));
      return { kind: 'token', maskedLine: masked, answer: chosen, options: shuffled };
    }
    if (tier === 3) {
      return { kind: 'blind', answer: target.trim(), fullLine: target };
    }
    const distractors = mutateLineDistractors(target, lines, isSql);
    const options = shuffleArray([target, ...distractors]);
    return { kind: 'line', answer: target, options };
  }

  function initPressureDrillForProblem(p, tier = 1) {
    stopPressureTimer();
    const extracted = extractDrillLines(p);
    const lines = extracted.drillLines;
    const pr = v2State.pressure;
    pr.tier = Number(tier) || 1;
    pr.problemKey = B().activeProblemKey(p);
    pr.prefixLines = extracted.prefixLines;
    pr.lines = lines;
    pr.stepIdx = 0;
    pr.lives = 3;
    pr.score = 0;
    pr.streak = 0;
    pr.maxStreak = 0;
    pr.maxTime = pr.tier === 3 ? 22 : pr.tier === 2 ? 10 : 12;
    pr.timeLeft = pr.maxTime;
    pr.active = lines.length > 0;
    pr.finished = false;
    pr.feedback = null;
    pr.peeked = false;
    pr.currentQuestion = lines.length ? buildPressureQuestion(lines, 0, pr.tier, Boolean(p?.isSql)) : null;

    if (pr.active) {
      pr.timerId = setInterval(() => {
        if (!v2State.pressure.active || v2State.pressure.finished) {
          stopPressureTimer();
          return;
        }
        v2State.pressure.timeLeft = Math.max(0, v2State.pressure.timeLeft - 1);
        const clockEl = document.getElementById('pressure-timer-pill');
        if (clockEl) clockEl.textContent = `${v2State.pressure.timeLeft}s`;
        if (v2State.pressure.timeLeft <= 0) {
          submitPressureAnswer(null, true);
        }
      }, 1000);
    }
    renderPressurePanel();
  }

  async function finishPressureDrill() {
    stopPressureTimer();
    const pr = v2State.pressure;
    pr.active = false;
    pr.finished = true;
    const bridge = B();
    const res = await bridge.apiPost('/api/progress', {
      savePressureScore: true,
      key: pr.problemKey,
      score: pr.score,
      tier: pr.tier,
      maxStreak: pr.maxStreak,
    });
    if (res && res.ok) {
      bridge.state.progress = res.progress;
    }
    renderPressurePanel();
  }

  function submitPressureAnswer(choice, timedOut = false) {
    const pr = v2State.pressure;
    if (!pr.active || pr.finished || !pr.currentQuestion) return;
    const p = B().currentProblem();
    const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isCorrect = !timedOut && norm(choice) === norm(pr.currentQuestion.answer);

    if (isCorrect) {
      pr.streak++;
      pr.maxStreak = Math.max(pr.maxStreak, pr.streak);
      const mult = Math.min(8, 1 + Math.floor(pr.streak / 2));
      const gain = (pr.peeked ? 50 : 100) * mult + pr.timeLeft * 5;
      pr.score += gain;
      pr.feedback = { ok: true, text: `Correct (+${gain} pts, ${mult}x multiplier)` };
      pr.stepIdx++;
      if (pr.stepIdx >= pr.lines.length) {
        finishPressureDrill();
        return;
      }
      pr.timeLeft = pr.maxTime;
      pr.peeked = false;
      pr.currentQuestion = buildPressureQuestion(pr.lines, pr.stepIdx, pr.tier, Boolean(p?.isSql));
    } else {
      pr.streak = 0;
      pr.lives--;
      pr.feedback = {
        ok: false,
        text: timedOut
          ? `Time expired. Expected: ${pr.currentQuestion.answer.trim()}`
          : `Mismatch. Expected: ${pr.currentQuestion.answer.trim()}`,
      };
      if (pr.lives <= 0) {
        finishPressureDrill();
        return;
      }
      pr.stepIdx++;
      if (pr.stepIdx >= pr.lines.length) {
        finishPressureDrill();
        return;
      }
      pr.timeLeft = pr.maxTime;
      pr.peeked = false;
      pr.currentQuestion = buildPressureQuestion(pr.lines, pr.stepIdx, pr.tier, Boolean(p?.isSql));
    }
    renderPressurePanel();
  }

  function renderPressurePanel() {
    const panel = document.getElementById('coach-panel-pressure');
    if (!panel) return;
    const bridge = B();
    const p = bridge.currentProblem();
    if (!p) return;
    const pr = v2State.pressure;
    const pKey = bridge.activeProblemKey(p);
    const best = bridge.state.progress?.pressureScores?.[pKey] || null;

    const tierMeta = [
      { id: 1, name: 'Tier 1: Line Recall', desc: 'Pick the exact next optimal line against subtle off-by-one distractors (12s).' },
      { id: 2, name: 'Tier 2: Token Blitz', desc: 'Restore the critical missing operator, pointer, or SQL clause (10s).' },
      { id: 3, name: 'Tier 3: Blind Master', desc: 'Type the next logical line from cold memory with Peek assist (22s).' },
    ];

    let bodyHtml = '';
    if (!pr.active && !pr.finished) {
      bodyHtml =
        `<div class="pivot-grid">` +
        tierMeta.map((t) =>
          `<div class="inner-box" style="display:flex; flex-direction:column; gap:6px; justify-content:space-between;">` +
          `<div><div style="font-weight:650; font-size:13px; color:var(--fg);">${esc(t.name)}</div><div class="muted" style="margin-top:3px;">${esc(t.desc)}</div></div>` +
          `<button type="button" class="${t.id === pr.tier ? 'btn-primary' : ''}" data-start-pressure-tier="${t.id}">Start ${esc(t.name.split(':')[1].trim())}</button>` +
          `</div>`
        ).join('') +
        `</div>`;
    } else if (pr.finished) {
      const survived = pr.lives > 0 && pr.stepIdx >= pr.lines.length;
      bodyHtml =
        `<div class="inner-box" style="border-left:3px solid ${survived ? 'var(--success)' : 'var(--warn)'}; display:flex; flex-direction:column; gap:8px;">` +
        `<div style="font-size:14px; font-weight:650; color:var(--fg);">${survived ? 'Recall Drill Complete' : 'Out of Lives'} (${pr.stepIdx} / ${pr.lines.length} lines)</div>` +
        `<div class="muted">Final Score: <span class="tabular" style="color:var(--fg); font-weight:650;">${pr.score}</span> | Max Streak: <span class="tabular">${pr.maxStreak}</span> | Saved Best: <span class="tabular">${best?.bestScore ?? pr.score}</span></div>` +
        `<div style="display:flex; gap:8px; flex-wrap:wrap;">` +
        `<button type="button" class="btn-primary" id="pressure-retry-btn">Run Again</button>` +
        `<button type="button" id="pressure-next-tier-btn">Try Tier ${Math.min(3, pr.tier + 1)}</button>` +
        `<button type="button" id="pressure-open-workbench-btn">Code from Scratch in Workbench →</button>` +
        `</div>` +
        `</div>`;
    } else {
      const revealedLines = [...(pr.prefixLines || []), ...pr.lines.slice(0, pr.stepIdx)];
      const q = pr.currentQuestion;
      const mult = Math.min(8, 1 + Math.floor(pr.streak / 2));

      let questionHtml = '';
      if (q.kind === 'line') {
        questionHtml =
          `<div class="muted" style="font-size:12px;">Select Line ${pr.stepIdx + 1} of ${pr.lines.length}:</div>` +
          `<div style="display:flex; flex-direction:column; gap:6px;">` +
          q.options.map((opt, idx) =>
            `<button type="button" class="pressure-option-btn" data-pressure-opt="${idx}">${esc(opt)}</button>`
          ).join('') +
          `</div>`;
      } else if (q.kind === 'token') {
        questionHtml =
          `<div class="muted" style="font-size:12px;">Fill the missing token in Line ${pr.stepIdx + 1}:</div>` +
          `<pre class="solution-code-pre" style="padding:8px 10px; margin:0;">${esc(q.maskedLine)}</pre>` +
          `<div style="display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:6px;">` +
          q.options.map((opt, idx) =>
            `<button type="button" class="pressure-option-btn" data-pressure-opt="${idx}">${esc(opt)}</button>`
          ).join('') +
          `</div>`;
      } else {
        const hintPreview = pr.peeked ? q.answer.slice(0, Math.max(4, Math.ceil(q.answer.length * 0.45))) + '...' : '';
        questionHtml =
          `<div class="muted" style="font-size:12px;">Type Line ${pr.stepIdx + 1} from memory (press Enter to submit):</div>` +
          (pr.peeked ? `<div class="inner-box" style="font-family:var(--font-mono); font-size:12px; color:var(--accent);">Peek Hint: ${esc(hintPreview)}</div>` : '') +
          `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
          `<input type="text" id="pressure-blind-input" class="compact-mono-input" style="flex:1 1 240px;" placeholder="Type next line of code..." aria-label="Next line from memory">` +
          `<button type="button" id="pressure-peek-btn">Peek (-50%)</button>` +
          `<button type="button" class="btn-primary" id="pressure-blind-submit-btn">Check Line</button>` +
          `</div>`;
      }

      bodyHtml =
        `<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">` +
        `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
        `<span class="stat-pill tabular">Step ${pr.stepIdx + 1} / ${pr.lines.length}</span>` +
        `<span class="stat-pill tabular" style="color:${pr.lives === 1 ? 'var(--danger)' : 'var(--fg)'};">Lives: ${pr.lives} / 3</span>` +
        `<span class="stat-pill tabular" style="color:var(--accent);">Score: ${pr.score} (${mult}x)</span>` +
        `<span class="stat-pill tabular" id="pressure-timer-pill" style="color:${pr.timeLeft <= 4 ? 'var(--danger)' : 'var(--warn)'};">${pr.timeLeft}s</span>` +
        `</div>` +
        `<button type="button" id="pressure-abort-btn" style="font-size:11.5px; padding:3px 9px;">Stop Drill</button>` +
        `</div>` +
        (pr.feedback
          ? `<div class="inner-box" style="border-left:3px solid ${pr.feedback.ok ? 'var(--success)' : 'var(--danger)'}; font-size:12px;">${esc(pr.feedback.text)}</div>`
          : '') +
        `<pre class="solution-code-pre" style="max-height:170px; margin:0;">${revealedLines.length ? bridge.highlightCodeHtml(revealedLines.join('\n')) : '<span class="muted">// Beginning of optimal implementation...</span>'}</pre>` +
        questionHtml;
    }

    panel.innerHTML =
      `<div class="card">` +
      `<div class="card-header">` +
      `<div>` +
      `<h2 class="card-title">Timed Pressure Recall Drill: ${esc(p.leetcodeId)} ${esc(p.title)}</h2>` +
      `<span class="muted">Active-recall muscle memory built directly from the optimal ${p.isSql ? 'SQL' : 'Python'} solution.</span>` +
      `</div>` +
      `<span class="stat-pill tabular">${best ? `Best: ${Number(best.bestScore) || 0} (Tier ${Number(best.bestTier) || 1})` : 'No best score yet'}</span>` +
      `</div>` +
      bodyHtml +
      `</div>`;

    panel.querySelectorAll('[data-start-pressure-tier]').forEach((btn) => {
      btn.addEventListener('click', () => initPressureDrillForProblem(p, Number(btn.getAttribute('data-start-pressure-tier'))));
    });
    panel.querySelectorAll('[data-pressure-opt]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.getAttribute('data-pressure-opt'));
        const choice = v2State.pressure.currentQuestion?.options?.[idx];
        submitPressureAnswer(choice, false);
      });
    });
    document.getElementById('pressure-peek-btn')?.addEventListener('click', () => {
      v2State.pressure.peeked = true;
      renderPressurePanel();
    });
    const blindSubmit = () => {
      const inp = document.getElementById('pressure-blind-input');
      if (inp) submitPressureAnswer(inp.value, false);
    };
    document.getElementById('pressure-blind-submit-btn')?.addEventListener('click', blindSubmit);
    const blindInput = document.getElementById('pressure-blind-input');
    if (blindInput) {
      blindInput.focus();
      blindInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          blindSubmit();
        }
      });
    }
    document.getElementById('pressure-abort-btn')?.addEventListener('click', () => {
      stopPressureTimer();
      v2State.pressure.active = false;
      v2State.pressure.finished = false;
      renderPressurePanel();
    });
    document.getElementById('pressure-retry-btn')?.addEventListener('click', () => initPressureDrillForProblem(p, pr.tier));
    document.getElementById('pressure-next-tier-btn')?.addEventListener('click', () => initPressureDrillForProblem(p, Math.min(3, pr.tier + 1)));
    document.getElementById('pressure-open-workbench-btn')?.addEventListener('click', () => bridge.switchTab('workbench'));
  }

  /* ==========================================================================
     TAB 2 SUB-MODE C: 4-STAGE 45-MIN MOCK INTERVIEW & 75-MIN 3-QUESTION OA
     ========================================================================== */
  function stopExamTimers() {
    if (v2State.exam.mockTimerId) {
      clearInterval(v2State.exam.mockTimerId);
      v2State.exam.mockTimerId = null;
    }
    if (v2State.exam.oaTimerId) {
      clearInterval(v2State.exam.oaTimerId);
      v2State.exam.oaTimerId = null;
    }
  }

  function pickPoolProblems(poolId, diffFilter = 'all') {
    const bridge = B();
    let list = [];
    if (poolId === 'schedule-120') {
      list = (bridge.state.problems || []).map((p) => ({ ...p, isCurated: false }));
    } else {
      const sheet = getSheetById(poolId);
      const seen = new Set();
      for (const g of sheet?.groups || []) {
        for (const pid of g.problemIds || []) {
          if (seen.has(pid)) continue;
          seen.add(pid);
          const cp = getProblemById(pid);
          if (cp) list.push({ ...cp, isCurated: true });
        }
      }
    }
    if (diffFilter !== 'all') {
      list = list.filter((p) => (p.difficulty || '').includes(diffFilter));
    }
    return list;
  }

  function startMockInterview() {
    stopExamTimers();
    const candidates = pickPoolProblems(v2State.exam.mockPool, v2State.exam.mockDiff);
    if (!candidates.length) return;
    const chosen = candidates[Math.floor(Math.random() * candidates.length)];
    const ex = v2State.exam;
    ex.mockActive = true;
    ex.mockStage = 1;
    ex.mockProblem = chosen;
    ex.mockSeconds = 45 * 60;
    ex.mockClarifyText = '';
    ex.mockApproachText = '';
    ex.mockApproachFeedback = null;
    ex.mockCode = chosen.isSql ? (chosen.starterCode?.sql || '') : (chosen.starterCode?.python || '');
    ex.mockRunResult = null;
    ex.mockComplexityText = '';
    ex.mockFinalGrade = null;

    ex.mockTimerId = setInterval(() => {
      if (!v2State.exam.mockActive) return;
      v2State.exam.mockSeconds = Math.max(0, v2State.exam.mockSeconds - 1);
      const el = document.getElementById('mock-clock-pill');
      if (el) el.textContent = formatClock(v2State.exam.mockSeconds);
    }, 1000);
    renderExamPanel();
  }

  async function gradeMockInterview() {
    const ex = v2State.exam;
    const p = ex.mockProblem;
    if (!p || ex.mockGrading) return;
    ex.mockGrading = true;
    const btn = document.getElementById('mock-grade-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Grading...';
    }
    try {
      const bridge = B();
      const lang = p.isSql ? 'sql' : 'python';
      const idPayload = p.isCurated ? { problemId: p.id } : { day: p.day };
      const grade = await bridge.apiPost('/api/analyse', { ...idPayload, language: lang, code: ex.mockCode });
      if (!grade || !grade.ok) return;
      ex.mockFinalGrade = grade;
      if (ex.mockTimerId) {
        clearInterval(ex.mockTimerId);
        ex.mockTimerId = null;
      }
      const elapsedMin = Math.max(1, Math.round((45 * 60 - ex.mockSeconds) / 60));
      const rec = {
        date: new Date().toISOString().slice(0, 10),
        problemId: p.isCurated ? p.id : `day-${p.day}`,
        title: `${p.leetcodeId}: ${p.title}`,
        difficulty: p.difficulty,
        score: grade.totalScore ?? 0,
        signal: grade.hiringSignal || grade.signal || 'Evaluated',
        elapsedMin,
      };
      const saveRes = await bridge.apiPost('/api/progress', { saveInterviewRecord: rec });
      if (saveRes && saveRes.ok) {
        bridge.state.progress = saveRes.progress;
      }
    } finally {
      ex.mockGrading = false;
      renderExamPanel();
    }
  }

  function startOaSimulation() {
    stopExamTimers();
    const dsaPool = pickPoolProblems('grind-75', 'all');
    const easyDsa = dsaPool.filter((p) => p.difficulty === 'Easy');
    const medDsa = dsaPool.filter((p) => p.difficulty === 'Medium');
    const hardOrMed = pickPoolProblems('leetcode-150', 'Medium');
    const sqlPool = pickPoolProblems('sql-50', 'all');

    const pickOne = (arr, excludeIds) => {
      const avail = arr.filter((x) => !excludeIds.has(x.id));
      return avail.length ? avail[Math.floor(Math.random() * avail.length)] : arr[0];
    };

    const used = new Set();
    const q1 = pickOne(easyDsa.length ? easyDsa : dsaPool, used);
    if (q1) used.add(q1.id);
    const q2 = pickOne(medDsa.length ? medDsa : dsaPool, used);
    if (q2) used.add(q2.id);
    const q3 = v2State.exam.oaIncludeSql && sqlPool.length
      ? pickOne(sqlPool, used)
      : pickOne(hardOrMed.length ? hardOrMed : dsaPool, used);

    const picked = [q1, q2, q3].filter(Boolean);
    const ex = v2State.exam;
    ex.oaActive = true;
    ex.oaFinished = false;
    ex.oaSeconds = 75 * 60;
    ex.oaActiveIdx = 0;
    ex.oaSummary = null;
    ex.oaQuestions = picked.map((p, idx) => ({
      slot: `Q${idx + 1}`,
      problem: p,
      lang: p.isSql ? 'sql' : 'python',
      code: p.isSql ? (p.starterCode?.sql || '') : (p.starterCode?.python || ''),
      runResult: null,
      passed: false,
    }));

    ex.oaTimerId = setInterval(() => {
      if (!v2State.exam.oaActive || v2State.exam.oaFinished) return;
      v2State.exam.oaSeconds = Math.max(0, v2State.exam.oaSeconds - 1);
      const el = document.getElementById('oa-clock-pill');
      if (el) el.textContent = formatClock(v2State.exam.oaSeconds);
      if (v2State.exam.oaSeconds <= 0) {
        submitFullOa();
      }
    }, 1000);
    renderExamPanel();
  }

  async function runActiveOaQuestion() {
    const ex = v2State.exam;
    const item = ex.oaQuestions[ex.oaActiveIdx];
    if (!item || ex.oaRunning) return;
    ex.oaRunning = true;
    const btn = document.getElementById('oa-run-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = `Running ${item.slot}...`;
    }
    try {
      const bridge = B();
      const p = item.problem;
      const idPayload = p.isCurated ? { problemId: p.id } : { day: p.day };
      const res = await bridge.apiPost('/api/run', { ...idPayload, language: item.lang, code: item.code });
      item.runResult = res;
      item.passed = Boolean(res && res.allPassed);
    } finally {
      ex.oaRunning = false;
      renderExamPanel();
    }
  }

  async function submitFullOa() {
    const ex = v2State.exam;
    if (ex.oaSubmitting || ex.oaFinished) return;
    ex.oaSubmitting = true;
    if (ex.oaTimerId) {
      clearInterval(ex.oaTimerId);
      ex.oaTimerId = null;
    }
    const btn = document.getElementById('oa-submit-all-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Submitting...';
    }
    try {
      const bridge = B();
      let totalPoints = 0;
      const breakdown = [];
      for (const item of ex.oaQuestions) {
        if (!item.runResult) {
          const p = item.problem;
          const idPayload = p.isCurated ? { problemId: p.id } : { day: p.day };
          item.runResult = await bridge.apiPost('/api/run', { ...idPayload, language: item.lang, code: item.code });
          item.passed = Boolean(item.runResult && item.runResult.allPassed);
        }
        const passed = item.runResult?.passed || 0;
        const total = Math.max(1, item.runResult?.total || 1);
        const pts = Math.round((passed / total) * 100);
        totalPoints += pts;
        breakdown.push({
          slot: item.slot,
          title: `${item.problem.leetcodeId}: ${item.problem.title}`,
          passed,
          total,
          points: pts,
        });
      }
      const elapsedMin = Math.max(1, Math.round((75 * 60 - ex.oaSeconds) / 60));
      ex.oaFinished = true;
      ex.oaSummary = { totalPoints, maxPoints: ex.oaQuestions.length * 100, elapsedMin, breakdown };
      const rec = {
        date: new Date().toISOString().slice(0, 10),
        totalPoints,
        maxPoints: ex.oaQuestions.length * 100,
        passedQuestions: ex.oaQuestions.filter((q) => q.passed).length,
        totalQuestions: ex.oaQuestions.length,
        elapsedMin,
      };
      const saveRes = await bridge.apiPost('/api/progress', { saveOaRecord: rec });
      if (saveRes && saveRes.ok) {
        bridge.state.progress = saveRes.progress;
      }
    } finally {
      ex.oaSubmitting = false;
      renderExamPanel();
    }
  }

  function renderExamPanel() {
    const panel = document.getElementById('coach-panel-exam');
    if (!panel) return;
    const bridge = B();
    const ex = v2State.exam;
    const interviewHist = bridge.state.progress?.interviewHistory || [];
    const oaHist = bridge.state.progress?.oaHistory || [];

    const switcherHtml =
      `<div class="card">` +
      `<div class="card-header">` +
      `<div>` +
      `<h2 class="card-title">Timed Interview &amp; OA Simulation</h2>` +
      `<span class="muted">Practise under realistic 45-minute technical interview stages or a 75-minute 3-question Online Assessment graded by Algo Studio's live runner and 20-check rubric.</span>` +
      `</div>` +
      `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
      `<button type="button" id="exam-mode-mock-btn" class="${ex.subMode === 'mock' ? 'btn-primary' : ''}">45-Min Mock Interview</button>` +
      `<button type="button" id="exam-mode-oa-btn" class="${ex.subMode === 'oa' ? 'btn-primary' : ''}">75-Min 3-Question OA</button>` +
      `</div>` +
      `</div>` +
      `</div>`;

    let mainHtml = '';
    if (ex.subMode === 'mock') {
      if (!ex.mockActive) {
        const histRows = interviewHist.slice(0, 6).map((h) =>
          `<tr><td>${esc(h.date || '')}</td><td>${esc(h.title || '')}</td><td>${esc(h.difficulty || '')}</td><td class="tabular" style="font-weight:650;">${Number(h.score ?? 0) || 0} / 100</td><td>${esc(h.signal || '')}</td><td class="tabular">${Number(h.elapsedMin ?? 0) || 0}m</td></tr>`
        ).join('');
        mainHtml =
          `<div class="card">` +
          `<div class="card-header"><h3 class="card-title">Configure 45-Minute 4-Stage Mock Interview</h3></div>` +
          `<div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">` +
          `<label class="muted" style="font-weight:600;">Question Pool:</label>` +
          `<select id="mock-pool-select" class="day-select" style="width:auto; min-width:170px; flex:initial;">` +
          `<option value="grind-75"${ex.mockPool === 'grind-75' ? ' selected' : ''}>Grind 75 (75)</option>` +
          `<option value="leetcode-150"${ex.mockPool === 'leetcode-150' ? ' selected' : ''}>LeetCode Top 150 (150)</option>` +
          `<option value="neetcode-150"${ex.mockPool === 'neetcode-150' ? ' selected' : ''}>NeetCode 150 (150)</option>` +
          `<option value="sql-50"${ex.mockPool === 'sql-50' ? ' selected' : ''}>SQL 50 (50)</option>` +
          `<option value="schedule-120"${ex.mockPool === 'schedule-120' ? ' selected' : ''}>120-Day Schedule (120)</option>` +
          `</select>` +
          `<select id="mock-diff-select" class="day-select" style="width:auto; min-width:120px; flex:initial;">` +
          `<option value="all"${ex.mockDiff === 'all' ? ' selected' : ''}>Any Difficulty</option>` +
          `<option value="Easy"${ex.mockDiff === 'Easy' ? ' selected' : ''}>Easy</option>` +
          `<option value="Medium"${ex.mockDiff === 'Medium' ? ' selected' : ''}>Medium</option>` +
          `<option value="Hard"${ex.mockDiff === 'Hard' ? ' selected' : ''}>Hard</option>` +
          `</select>` +
          `<button type="button" class="btn-primary" id="start-mock-btn">Draw Problem &amp; Start 45:00 Clock</button>` +
          `</div>` +
          (interviewHist.length
            ? `<div style="margin-top:8px;"><div style="font-size:12px; font-weight:650; margin-bottom:6px;">Recent Mock Interview History</div>` +
              `<div class="sql-table-wrap"><table class="sql-data-table"><thead><tr><th>Date</th><th>Problem</th><th>Difficulty</th><th>Score</th><th>Signal</th><th>Time</th></tr></thead><tbody>${histRows}</tbody></table></div></div>`
            : `<div class="muted">No mock interviews logged yet. Draw a random unseen problem above to practise clarifying, stating your invariant, coding, and grading against the 20-check rubric.</div>`) +
          `</div>`;
      } else {
        const p = ex.mockProblem;
        const stageNames = ['1. Clarify (0 to 5m)', '2. Approach (5 to 15m)', '3. Implement (15 to 35m)', '4. Complexity & Grade'];
        const pills = stageNames.map((nm, idx) =>
          `<button type="button" class="step-pill${ex.mockStage === idx + 1 ? ' current unlocked' : (idx + 1 < ex.mockStage ? ' unlocked' : '')}" data-mock-stage="${idx + 1}">${esc(nm)}</button>`
        ).join('');

        let stageContent = '';
        if (ex.mockStage === 1) {
          stageContent =
            `<div class="inner-box"><div style="font-weight:650; font-size:12px; margin-bottom:4px;">Clarifying Questions to Ask Before Coding</div>` +
            `<ul style="margin:0; padding-left:18px; font-size:12.5px; color:var(--fg-secondary);">${(p.clarifyingQuestions || []).map((q) => `<li>${rich(q)}</li>`).join('')}</ul></div>` +
            `<textarea id="mock-clarify-input" class="exam-textarea" style="min-height:90px; font-family:var(--font-sans);" placeholder="Jot down input bounds, null/empty edge cases, and assumptions you verified...">${esc(ex.mockClarifyText)}</textarea>` +
            `<div style="display:flex; justify-content:flex-end;"><button type="button" class="btn-primary" data-mock-stage="2">Proceed to Stage 2: Approach →</button></div>`;
        } else if (ex.mockStage === 2) {
          stageContent =
            `<div class="muted">State your data structure, core invariant, and target time/space complexity in 2 to 3 sentences:</div>` +
            `<textarea id="mock-approach-input" class="exam-textarea" style="min-height:100px; font-family:var(--font-sans);" placeholder="e.g. Use a hash map storing seen values to indices for O(N) time and O(N) space...">${esc(ex.mockApproachText)}</textarea>` +
            (ex.mockApproachFeedback
              ? `<div class="inner-box"><span class="stat-pill" style="margin-right:6px;">${esc(ex.mockApproachFeedback.badge || 'Reviewed')}</span>${rich(ex.mockApproachFeedback.summary || '')}</div>`
              : '') +
            `<div style="display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap;">` +
            `<button type="button" id="mock-check-approach-btn" class="btn-subtle-accent">Verify Approach with Coach</button>` +
            `<button type="button" class="btn-primary" data-mock-stage="3">Proceed to Stage 3: Implement →</button>` +
            `</div>`;
        } else if (ex.mockStage === 3) {
          const rr = ex.mockRunResult;
          stageContent =
            `<textarea id="mock-code-input" class="exam-textarea" spellcheck="false" aria-label="Mock interview code editor">${esc(ex.mockCode)}</textarea>` +
            `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
            `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
            `<button type="button" class="btn-primary" id="mock-run-btn">Run Live Tests</button>` +
            `<button type="button" id="mock-open-workbench-btn">Open in Full Workbench</button>` +
            `</div>` +
            `<button type="button" class="btn-subtle-accent" data-mock-stage="4">Proceed to Stage 4: Grade →</button>` +
            `</div>` +
            (rr
              ? `<div class="inner-box" style="border-left:3px solid ${rr.allPassed ? 'var(--success)' : 'var(--danger)'};">` +
                `<div style="font-weight:650; font-size:12.5px;">${Number(rr.passed ?? 0) || 0} / ${Number(rr.total ?? 0) || 0} test cases passed${rr.error ? ' | ' + esc(rr.error) : ''}</div>` +
                `</div>`
              : '');
        } else {
          const g = ex.mockFinalGrade;
          stageContent =
            `<textarea id="mock-complexity-input" class="exam-textarea" style="min-height:80px; font-family:var(--font-sans);" placeholder="Summarise your final Time & Space complexity and trade-offs...">${esc(ex.mockComplexityText)}</textarea>` +
            `<div style="display:flex; gap:8px; flex-wrap:wrap;">` +
            `<button type="button" class="btn-primary" id="mock-grade-btn">Submit &amp; Grade Interview (20-Check Rubric)</button>` +
            `<button type="button" id="mock-end-btn">End Mock Session</button>` +
            `</div>` +
            (g
              ? `<div class="inner-box" style="border-left:3px solid ${(Number(g.totalScore ?? 0) || 0) >= 80 ? 'var(--success)' : 'var(--warn)'}; display:flex; flex-direction:column; gap:6px;">` +
                `<div style="display:flex; justify-content:space-between; align-items:center;">` +
                `<span style="font-weight:650; font-size:13.5px;">${esc(g.hiringSignal || g.signal || 'Graded')}</span>` +
                `<span class="stat-pill tabular">Score: ${Number(g.totalScore ?? 0) || 0} / 100</span>` +
                `</div>` +
                `<div style="font-size:12.5px; color:var(--fg-secondary);">${rich(g.diagnosis || '')}</div>` +
                `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
                (g.rubric || []).map((r) => `<span class="stat-pill tabular">${esc(r.axis.split('(')[0].trim())}: ${Number(r.score ?? 0) || 0}/${Number(r.max ?? 0) || 0}</span>`).join('') +
                `</div>` +
                `</div>`
              : '');
        }

        mainHtml =
          `<div class="card">` +
          `<div class="card-header">` +
          `<div>` +
          `<h3 class="card-title">Mock Interview: ${esc(p.leetcodeId)} ${esc(p.title)}</h3>` +
          `<span class="diff-badge ${p.difficulty.includes('Easy') ? 'diff-Easy' : p.difficulty.includes('Medium') ? 'diff-Medium' : 'diff-Hard'}">${esc(p.difficulty)}</span>` +
          `</div>` +
          `<div style="display:flex; align-items:center; gap:6px;">` +
          `<span class="stat-pill tabular" id="mock-clock-pill">${formatClock(ex.mockSeconds)}</span>` +
          `<button type="button" id="mock-end-top-btn" style="font-size:11.5px; padding:3px 9px;">Exit Mock</button>` +
          `</div>` +
          `</div>` +
          `<div class="exam-stage-pills">${pills}</div>` +
          `<div class="inner-box" style="max-height:170px; overflow-y:auto;">` +
          `<div class="statement-text">${rich(p.statement || '')}</div>` +
          (p.isSql && p.schemaTables?.length
            ? `<div style="margin-top:6px;">${p.schemaTables.map((t) => `<div style="font-size:11.5px; font-weight:650; margin-top:4px;">Table ${esc(t.name)}</div>` + renderSqlTableHtml(t.columns, t.rows)).join('')}</div>`
            : '') +
          `</div>` +
          stageContent +
          `</div>`;
      }
    } else {
      // 75-Min 3-Question OA Simulator
      if (!ex.oaActive) {
        const oaRows = oaHist.slice(0, 6).map((h) =>
          `<tr><td>${esc(h.date || '')}</td><td class="tabular">${Number(h.passedQuestions ?? 0) || 0} / ${Number(h.totalQuestions ?? 3) || 3} passed</td><td class="tabular" style="font-weight:650;">${Number(h.totalPoints ?? 0) || 0} / ${Number(h.maxPoints ?? 300) || 300}</td><td class="tabular">${Number(h.elapsedMin ?? 0) || 0}m</td></tr>`
        ).join('');
        mainHtml =
          `<div class="card">` +
          `<div class="card-header"><h3 class="card-title">75-Minute 3-Question Online Assessment (OA)</h3></div>` +
          `<p class="muted" style="margin:0;">Draws Q1 (Easy DSA), Q2 (Medium DSA), and Q3 (SQL 50 or Medium DSA) into a single timed assessment with live execution.</p>` +
          `<div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">` +
          `<label style="display:inline-flex; align-items:center; gap:6px; font-size:12.5px; cursor:pointer;">` +
          `<input type="checkbox" id="oa-include-sql-chk"${ex.oaIncludeSql ? ' checked' : ''}> Include SQL 50 relational query as Q3` +
          `</label>` +
          `<button type="button" class="btn-primary" id="start-oa-btn">Start 75-Min OA Assessment</button>` +
          `</div>` +
          (oaHist.length
            ? `<div style="margin-top:8px;"><div style="font-size:12px; font-weight:650; margin-bottom:6px;">Recent OA Results</div>` +
              `<div class="sql-table-wrap"><table class="sql-data-table"><thead><tr><th>Date</th><th>Solved</th><th>Composite Score</th><th>Time</th></tr></thead><tbody>${oaRows}</tbody></table></div></div>`
            : `<div class="muted">No OA sessions completed yet.</div>`) +
          `</div>`;
      } else {
        const cur = ex.oaQuestions[ex.oaActiveIdx];
        const qTabs = ex.oaQuestions.map((item, idx) =>
          `<button type="button" class="step-pill${idx === ex.oaActiveIdx ? ' current unlocked' : ''}" data-oa-q="${idx}">` +
          `${esc(item.slot)}: ${esc(item.problem.leetcodeId)} (${item.passed ? 'PASS' : (item.runResult ? 'TRIED' : esc(item.problem.difficulty))})` +
          `</button>`
        ).join('');

        mainHtml =
          `<div class="card">` +
          `<div class="card-header">` +
          `<div>` +
          `<h3 class="card-title">Online Assessment in Progress</h3>` +
          `<span class="muted">Switch freely between Q1, Q2, and Q3 before submitting.</span>` +
          `</div>` +
          `<div style="display:flex; align-items:center; gap:6px;">` +
          `<span class="stat-pill tabular" id="oa-clock-pill">${formatClock(ex.oaSeconds)}</span>` +
          (!ex.oaFinished ? `<button type="button" class="btn-submit ready" id="oa-submit-all-btn" style="padding:4px 10px; font-size:12px;">Submit Full OA</button>` : '') +
          `<button type="button" id="oa-exit-btn" style="font-size:11.5px; padding:3px 9px;">Exit OA</button>` +
          `</div>` +
          `</div>` +
          `<div class="exam-stage-pills">${qTabs}</div>` +
          (ex.oaSummary
            ? `<div class="inner-box" style="border-left:3px solid var(--success);">` +
              `<div style="font-weight:650; font-size:13.5px;">OA Submitted: ${Number(ex.oaSummary.totalPoints ?? 0) || 0} / ${Number(ex.oaSummary.maxPoints ?? 300) || 300} points (${Number(ex.oaSummary.elapsedMin ?? 0) || 0}m)</div>` +
              `<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:6px;">` +
              ex.oaSummary.breakdown.map((b) => `<span class="stat-pill tabular">${esc(b.slot)} ${esc(b.title)}: ${Number(b.points ?? 0) || 0}/100 (${Number(b.passed ?? 0) || 0}/${Number(b.total ?? 0) || 0})</span>`).join('') +
              `</div></div>`
            : '') +
          (cur
            ? `<div class="inner-box" style="max-height:175px; overflow-y:auto;">` +
              `<div style="font-weight:650; font-size:13px; margin-bottom:4px;">${esc(cur.slot)}: ${esc(cur.problem.leetcodeId)} ${esc(cur.problem.title)} (${esc(cur.problem.difficulty)}${cur.problem.isSql ? ' | SQLite 3' : ' | Python 3'})</div>` +
              `<div class="statement-text">${rich(cur.problem.statement || '')}</div>` +
              (cur.problem.isSql && cur.problem.schemaTables?.length
                ? cur.problem.schemaTables.map((t) => `<div style="font-size:11.5px; font-weight:650; margin-top:4px;">Table ${esc(t.name)}</div>` + renderSqlTableHtml(t.columns, t.rows)).join('')
                : '') +
              `</div>` +
              `<textarea id="oa-code-input" class="exam-textarea" spellcheck="false" aria-label="OA code editor">${esc(cur.code)}</textarea>` +
              `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
              `<button type="button" class="btn-primary" id="oa-run-btn">Run ${esc(cur.slot)} Tests</button>` +
              `<span class="muted tabular">${cur.runResult ? `${Number(cur.runResult.passed ?? 0) || 0} / ${Number(cur.runResult.total ?? 0) || 0} passed${cur.runResult.error ? ' | ' + esc(cur.runResult.error) : ''}` : 'Not run yet'}</span>` +
              `</div>`
            : '') +
          `</div>`;
      }
    }

    panel.innerHTML = switcherHtml + mainHtml;

    // Wire Exam Panel Listeners
    document.getElementById('exam-mode-mock-btn')?.addEventListener('click', () => {
      v2State.exam.subMode = 'mock';
      renderExamPanel();
    });
    document.getElementById('exam-mode-oa-btn')?.addEventListener('click', () => {
      v2State.exam.subMode = 'oa';
      renderExamPanel();
    });
    document.getElementById('mock-pool-select')?.addEventListener('change', (e) => {
      v2State.exam.mockPool = e.target.value;
    });
    document.getElementById('mock-diff-select')?.addEventListener('change', (e) => {
      v2State.exam.mockDiff = e.target.value;
    });
    document.getElementById('start-mock-btn')?.addEventListener('click', startMockInterview);

    panel.querySelectorAll('[data-mock-stage]').forEach((btn) => {
      btn.addEventListener('click', () => {
        v2State.exam.mockStage = Number(btn.getAttribute('data-mock-stage'));
        renderExamPanel();
      });
    });
    document.getElementById('mock-clarify-input')?.addEventListener('input', (e) => { v2State.exam.mockClarifyText = e.target.value; });
    document.getElementById('mock-approach-input')?.addEventListener('input', (e) => { v2State.exam.mockApproachText = e.target.value; });
    document.getElementById('mock-code-input')?.addEventListener('input', (e) => { v2State.exam.mockCode = e.target.value; });
    document.getElementById('mock-complexity-input')?.addEventListener('input', (e) => { v2State.exam.mockComplexityText = e.target.value; });

    document.getElementById('mock-check-approach-btn')?.addEventListener('click', async () => {
      const p = v2State.exam.mockProblem;
      if (!p) return;
      const btn = document.getElementById('mock-check-approach-btn');
      if (btn) btn.disabled = true;
      try {
        const idPayload = p.isCurated ? { problemId: p.id } : { day: p.day };
        const res = await bridge.apiPost('/api/approach-check', { ...idPayload, approach: v2State.exam.mockApproachText });
        v2State.exam.mockApproachFeedback = res;
      } finally {
        if (btn) btn.disabled = false;
        renderExamPanel();
      }
    });

    document.getElementById('mock-run-btn')?.addEventListener('click', async () => {
      const p = v2State.exam.mockProblem;
      if (!p) return;
      const btn = document.getElementById('mock-run-btn');
      if (btn) btn.disabled = true;
      try {
        const idPayload = p.isCurated ? { problemId: p.id } : { day: p.day };
        const lang = p.isSql ? 'sql' : 'python';
        v2State.exam.mockRunResult = await bridge.apiPost('/api/run', { ...idPayload, language: lang, code: v2State.exam.mockCode });
      } finally {
        if (btn) btn.disabled = false;
        renderExamPanel();
      }
    });

    document.getElementById('mock-open-workbench-btn')?.addEventListener('click', () => {
      const p = v2State.exam.mockProblem;
      if (!p) return;
      if (p.isCurated) {
        openCuratedProblem(p.id);
      } else {
        bridge.switchCourse('schedule-120', { day: p.day });
        bridge.switchTab('workbench');
      }
      const ta = document.getElementById('code-editor');
      if (ta && v2State.exam.mockCode) {
        ta.value = v2State.exam.mockCode;
        bridge.updateEditorRender();
      }
    });

    document.getElementById('mock-grade-btn')?.addEventListener('click', gradeMockInterview);
    const exitMock = () => {
      stopExamTimers();
      v2State.exam.mockActive = false;
      renderExamPanel();
    };
    document.getElementById('mock-end-btn')?.addEventListener('click', exitMock);
    document.getElementById('mock-end-top-btn')?.addEventListener('click', exitMock);

    document.getElementById('oa-include-sql-chk')?.addEventListener('change', (e) => {
      v2State.exam.oaIncludeSql = Boolean(e.target.checked);
    });
    document.getElementById('start-oa-btn')?.addEventListener('click', startOaSimulation);
    panel.querySelectorAll('[data-oa-q]').forEach((btn) => {
      btn.addEventListener('click', () => {
        v2State.exam.oaActiveIdx = Number(btn.getAttribute('data-oa-q'));
        renderExamPanel();
      });
    });
    document.getElementById('oa-code-input')?.addEventListener('input', (e) => {
      const item = v2State.exam.oaQuestions[v2State.exam.oaActiveIdx];
      if (item) item.code = e.target.value;
    });
    document.getElementById('oa-run-btn')?.addEventListener('click', runActiveOaQuestion);
    document.getElementById('oa-submit-all-btn')?.addEventListener('click', submitFullOa);
    document.getElementById('oa-exit-btn')?.addEventListener('click', () => {
      stopExamTimers();
      v2State.exam.oaActive = false;
      renderExamPanel();
    });
    window.StudioV3?.onExamRendered?.(v2State.exam, panel);
  }

  /* ==========================================================================
     INITIALISATION & EVENT WIRING
     ========================================================================== */
  function wireGlobalListeners() {
    const bridge = B();

    document.getElementById('toggle-bookmark-btn')?.addEventListener('click', () => {
      const p = bridge.currentProblem();
      if (p) toggleBookmarkKey(bookmarkKeyForProblem(p));
    });

    document.getElementById('back-to-curated-list-btn')?.addEventListener('click', () => {
      bridge.switchTab('lists');
    });

    document.getElementById('return-to-120day-btn')?.addEventListener('click', () => {
      returnToScheduleDay();
    });

    // Editor QOL buttons
    document.getElementById('editor-find-toggle-btn')?.addEventListener('click', () => {
      const bar = document.getElementById('editor-find-bar');
      if (bar?.classList.contains('open')) closeFindBar();
      else openFindBar(false);
    });
    document.getElementById('editor-find-close-btn')?.addEventListener('click', closeFindBar);
    document.getElementById('editor-find-next-btn')?.addEventListener('click', findNextInEditor);
    document.getElementById('editor-replace-one-btn')?.addEventListener('click', replaceCurrentMatch);
    document.getElementById('editor-replace-all-btn')?.addEventListener('click', replaceAllMatches);
    document.getElementById('editor-find-input')?.addEventListener('input', () => {
      v2State.findMatchIndex = -1;
      updateFindStatus();
    });
    document.getElementById('editor-find-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        findNextInEditor();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closeFindBar();
      }
    });
    document.getElementById('editor-goto-line-btn')?.addEventListener('click', () => {
      const val = document.getElementById('editor-goto-line-input')?.value;
      goToLineInEditor(val);
    });
    document.getElementById('editor-goto-line-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        goToLineInEditor(e.target.value);
      }
    });
    document.getElementById('editor-wrap-btn')?.addEventListener('click', toggleEditorWordWrap);
    document.getElementById('editor-font-dec-btn')?.addEventListener('click', () => applyEditorFontSize(v2State.editorFontSize - 1));
    document.getElementById('editor-font-inc-btn')?.addEventListener('click', () => applyEditorFontSize(v2State.editorFontSize + 1));

    // Copy for AI button
    document.getElementById('copy-for-ai-btn')?.addEventListener('click', () => {
      const text = buildCopyForAiPrompt();
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(text).catch(() => bridge.copyTextFallback(text));
      } else {
        bridge.copyTextFallback(text);
      }
      const btn = document.getElementById('copy-for-ai-btn');
      if (btn) {
        btn.textContent = 'Copied ✓';
        if (v2State.copyAiTimerId) clearTimeout(v2State.copyAiTimerId);
        v2State.copyAiTimerId = setTimeout(() => {
          btn.textContent = 'Copy for AI';
          v2State.copyAiTimerId = null;
        }, 1600);
      }
    });

    // Tab 2 Mode Bar
    document.querySelectorAll('#coach-mode-bar .coach-mode-btn').forEach((btn) => {
      btn.addEventListener('click', () => switchCoachMode(btn.getAttribute('data-coach-mode')));
    });

    // Keyboard shortcuts: Ctrl+F (Find), Ctrl+H (Replace), Ctrl+G (Go to Line) when Workbench is active
    document.addEventListener('keydown', (e) => {
      const wbActive = document.getElementById('pane-workbench')?.classList.contains('active');
      if (!wbActive) return;
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
        const k = e.key.toLowerCase();
        if (k === 'f') {
          e.preventDefault();
          openFindBar(false);
        } else if (k === 'h') {
          e.preventDefault();
          openFindBar(true);
        } else if (k === 'g') {
          e.preventDefault();
          openGoToLinePrompt();
        }
      }
    });

    // Restore editor preferences
    try {
      const savedFont = Number(localStorage.getItem('algoStudioEditorFont_v2'));
      if (savedFont >= 11 && savedFont <= 18) applyEditorFontSize(savedFont);
      if (localStorage.getItem('algoStudioEditorWrap_v2') === '1') toggleEditorWordWrap();
    } catch (_) {}
  }

  let _v2Initialized = false;

  async function loadCuratedCatalog() {
    const bridge = B();
    try {
      const res = await bridge.apiGet('/api/curated');
      if (res && res.ok) {
        bridge.state.curatedCatalog = {
          sheets: res.sheets || [],
          dagNodes: res.dagNodes || [],
          problemsById: res.problemsById || {},
        };
        renderCuratedListsTab();
        return;
      }
      throw new Error(res?.error || 'Failed to load curated catalog');
    } catch (err) {
      const pane = document.getElementById('pane-lists');
      if (pane) {
        pane.innerHTML =
          `<div class="card"><div class="inner-box" style="display:flex; align-items:center; justify-content:space-between; gap:8px;">` +
          `<span class="muted">Could not load curated problem lists (${esc(err?.message || err)}).</span>` +
          `<button type="button" id="retry-curated-catalog-btn" class="btn-subtle-accent">Retry</button>` +
          `</div></div>`;
        document.getElementById('retry-curated-catalog-btn')?.addEventListener('click', loadCuratedCatalog);
      }
    }
  }

  async function init() {
    if (_v2Initialized) return;
    _v2Initialized = true;
    wireGlobalListeners();
    await loadCuratedCatalog();
    const bridge = B();
    const lv = bridge.state.progress?.lastVisited;
    const savedCourse = lv?.course || bridge.state.progress?.activeCourse || 'schedule-120';
    if (savedCourse !== 'schedule-120') {
      const savedPid =
        (lv?.course === savedCourse && lv?.problemId) ||
        bridge.state.progress?.coursePositions?.[savedCourse] ||
        null;
      bridge.switchCourse(savedCourse, { problemId: savedPid, skipFlush: true, skipPersist: true });
    } else {
      bridge.renderHeaderStats();
      bridge.populateSelectors();
      onActiveProblemRendered(bridge.currentProblem());
    }
    window.StudioV3?.init?.();
  }

  function onActiveProblemRendered(p) {
    v2State.selectedApproachIdx = -1;
    updateCuratedContextBanner(p);
    updateBookmarkButtonUI(p);
    renderApproachesMatrix(p);
    if (v2State.coachMode === 'pressure') {
      stopPressureTimer();
      v2State.pressure.active = false;
      v2State.pressure.finished = false;
      renderPressurePanel();
    }
    window.StudioV3?.onActiveProblemRendered?.(p);
  }

  function onProgressUpdated() {
    updateBookmarkButtonUI(B().currentProblem());
    renderCuratedListsTab();
  }

  function openPressureForActive() {
    const bridge = B();
    bridge.switchTab('coach');
    switchCoachMode('pressure');
    initPressureDrillForProblem(bridge.currentProblem(), v2State.pressure.tier);
  }

  window.StudioV2 = {
    init,
    onActiveProblemRendered,
    onProgressUpdated,
    syncSheetFromCourse,
    renderSqlSchemaBox,
    renderSqlTestResults,
    renderCuratedListsTab,
    openCuratedProblem,
    switchCoachMode,
    openPressureForActive,
    openFindBar,
    openGoToLinePrompt,
    buildCopyForAiPrompt,
  };

  if (window.AlgoStudioBridge?.state?.initialized) {
    init();
  }
})();
