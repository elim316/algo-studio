/* Algo Studio v2.4 Frontend Module (StudioV3)
 * Implements:
 * 1. Richer Python Tutor Visualisations (2D Matrix / DP Grid, Binary Tree SVG, Graph Adjacency SVG)
 * 2. Per-Problem Collapsible Visual Whiteboard Scratchpad (Pen, Arrow, Node Box, Eraser, Undo, Synced Vectors)
 * 3. Empirical Big-O Scaling Visualiser (4-point step-counted SVG curve vs O(N), O(N log N), O(N^2))
 * 4. 30-Second Pattern Recognition Flash Drills (Tab 2 4th mode, 120-day pool, hidden titles/tags)
 * 5. Think-Aloud Interview Mode (Web Speech API mic + live 4-pillar checklist + Communication Score)
 * 6. Cross-Device Private GitHub Gist Sync Modal (3-way non-destructive merge across devices)
 */
(function () {
  'use strict';

  const B = () => window.AlgoStudioBridge;

  const v3State = {
    initialized: false,
    autoVisualOn: true,
    lastFrame: null,
    lastPrevFrame: null,
    /* Whiteboard state */
    wbOpen: false,
    wbTool: 'pen', /* 'pen' | 'arrow' | 'box' | 'eraser' */
    wbColor: 'ink', /* 'ink' | 'accent' | 'green' */
    wbDrawing: false,
    wbStrokes: [],
    wbActiveStroke: null,
    wbSaveTimer: null,
    wbProbKey: '',
    /* Big-O benchmark state */
    bigOLoading: false,
    bigOResult: null,
    /* 30-Second Pattern Flash Drill state */
    flash: {
      scope: 'all', /* 'all' | 'weak' | 'due' | 'phase1' | 'phase2' */
      active: false,
      revealed: false,
      currentProb: null,
      correctTag: '',
      choices: [],
      chosenTag: '',
      timeLeft: 30,
      timerId: null,
      streak: 0,
      sessionAttempted: 0,
      sessionCorrect: 0,
      recentDays: [],
    },
    /* Think-Aloud Interview state */
    thinkAloud: {
      problemId: '',
      recording: false,
      recognition: null,
      transcript: '',
      interimText: '',
      grade: null,
      grading: false,
    },
    /* Gist sync state */
    gist: {
      configured: false,
      gistId: '',
      masked: '',
      lastSyncedAt: '',
      busy: false,
      message: '',
      isError: false,
    },
  };

  function esc(str) {
    return B() ? B().escapeHtml(str) : String(str ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function rich(str) {
    return B()?.formatRichText ? B().formatRichText(str) : esc(str);
  }

  /* ==========================================================================
     SCOPED STYLES (100% theme-adaptive using :root CSS tokens)
     ========================================================================== */
  function injectStyles() {
    if (document.getElementById('studio-v3-styles')) return;
    const style = document.createElement('style');
    style.id = 'studio-v3-styles';
    style.textContent = `
      /* 1. Richer Python Tutor Visual Overlay Strip */
      .pt-rich-visual-strip {
        display: none;
        flex-direction: column;
        gap: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
        border: 1px solid var(--border-col);
        border-radius: var(--radius-sm);
        background: var(--surface-2);
        min-width: 0;
        max-width: 100%;
        box-sizing: border-box;
        overflow: hidden;
      }
      .pt-rich-visual-strip.visible { display: flex; }
      .pt-rich-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 6px 10px;
        flex-wrap: wrap;
        min-width: 0;
        max-width: 100%;
      }
      .pt-rich-meta-pills {
        display: flex;
        align-items: center;
        gap: 4px;
        flex-wrap: wrap;
        min-width: 0;
        max-width: 100%;
      }
      .pt-rich-title {
        font-size: 11.5px;
        font-weight: 650;
        color: var(--fg);
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .pt-rich-canvas-scroll {
        overflow-x: auto;
        padding: 4px 2px;
      }
      .pt-grid-table {
        border-collapse: separate;
        border-spacing: 3px;
        font-family: var(--font-mono);
        font-size: 11.5px;
        font-variant-numeric: tabular-nums;
      }
      .pt-grid-idx {
        color: var(--fg-muted);
        font-size: 10px;
        text-align: center;
        padding: 2px 5px;
        user-select: none;
      }
      .pt-grid-cell {
        min-width: 34px;
        height: 30px;
        padding: 2px 6px;
        text-align: center;
        border-radius: 5px;
        border: 1px solid var(--border-col);
        background: var(--surface);
        color: var(--fg);
        position: relative;
        transition: background-color 180ms var(--ease-out), border-color 180ms var(--ease-out);
      }
      .pt-grid-cell.is-mutated {
        border-color: var(--success);
        background: color-mix(in srgb, var(--success) 18%, var(--surface));
        font-weight: 700;
      }
      .pt-grid-cell.is-cursor {
        border-color: var(--accent);
        box-shadow: inset 0 0 0 1.5px var(--accent);
        font-weight: 700;
      }
      .pt-grid-cell.is-bound {
        border-style: dashed;
        border-color: var(--warn);
      }
      .pt-grid-cell-ptr {
        display: block;
        font-size: 9px;
        line-height: 1;
        color: var(--accent);
        font-weight: 700;
        margin-top: 1px;
      }
      .pt-svg-stage {
        display: block;
        width: 100%;
        min-width: 320px;
        max-height: 220px;
        height: auto;
      }

      /* 2. Per-Problem Collapsible Visual Whiteboard Scratchpad */
      .whiteboard-card {
        display: none;
        flex-direction: column;
        gap: 6px;
        padding: 8px 10px;
        border: 1px solid var(--border-col);
        border-radius: var(--radius-sm);
        background: var(--surface-2);
      }
      .whiteboard-card.open { display: flex; }
      .whiteboard-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 6px;
        flex-wrap: wrap;
      }
      .whiteboard-tool-group {
        display: flex;
        align-items: center;
        gap: 4px;
        flex-wrap: wrap;
      }
      .wb-tool-btn {
        padding: 3px 8px;
        font-size: 11px;
        border-radius: 5px;
      }
      .wb-tool-btn.active {
        background: color-mix(in srgb, var(--accent) 14%, var(--surface));
        border-color: var(--accent);
        color: var(--accent);
        font-weight: 650;
      }
      .wb-swatch {
        width: 18px;
        height: 18px;
        border-radius: 999px;
        padding: 0;
        border: 2px solid var(--border-col);
        cursor: pointer;
        transition: transform 150ms var(--ease-out), border-color 150ms var(--ease-out);
      }
      .wb-swatch.active {
        border-color: var(--fg);
        transform: scale(1.12);
      }
      .whiteboard-canvas-wrap {
        position: relative;
        width: 100%;
        height: 210px;
        border-radius: 6px;
        border: 1px solid var(--border-col);
        background-color: var(--surface);
        background-image: radial-gradient(color-mix(in srgb, var(--fg-muted) 28%, transparent) 1px, transparent 1px);
        background-size: 16px 16px;
        overflow: hidden;
      }
      #whiteboard-canvas {
        width: 100%;
        height: 100%;
        display: block;
        touch-action: none;
        cursor: crosshair;
      }

      /* 3. Empirical Big-O Scaling Visualiser Card */
      .bigo-card {
        display: none;
        flex-direction: column;
        gap: 8px;
        padding: 10px 12px;
        border: 1px solid var(--border-col);
        border-radius: var(--radius-sm);
        background: var(--surface);
      }
      .bigo-card.open { display: flex; }
      .bigo-grid {
        display: grid;
        grid-template-columns: minmax(260px, 1.35fr) minmax(190px, 1fr);
        gap: 10px;
        align-items: center;
      }
      @media (max-width: 780px) {
        .bigo-grid { grid-template-columns: 1fr; }
      }
      .bigo-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11.5px;
        font-variant-numeric: tabular-nums;
      }
      .bigo-table th, .bigo-table td {
        padding: 4px 6px;
        text-align: right;
        border-bottom: 1px solid var(--border-col);
      }
      .bigo-table th:first-child, .bigo-table td:first-child { text-align: left; }
      .bigo-table th {
        font-size: 10.5px;
        color: var(--fg-muted);
        font-weight: 600;
      }

      /* 4. 30-Second Pattern Flash Drill */
      .flash-shell {
        display: grid;
        grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.9fr);
        gap: 12px;
        align-items: start;
      }
      @media (max-width: 860px) {
        .flash-shell { grid-template-columns: 1fr; }
      }
      .flash-choice-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
      }
      @media (max-width: 600px) {
        .flash-choice-grid { grid-template-columns: 1fr; }
      }
      .flash-choice-btn {
        text-align: left;
        padding: 11px 12px;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-col);
        background: var(--surface);
        color: var(--fg);
        font-size: 12.5px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: border-color 150ms var(--ease-out), background-color 150ms var(--ease-out), transform 120ms var(--ease-out);
      }
      .flash-choice-btn:hover:not(:disabled) {
        border-color: var(--accent);
        background: color-mix(in srgb, var(--accent) 8%, var(--surface));
      }
      .flash-choice-btn:active:not(:disabled) { transform: scale(0.985); }
      .flash-choice-btn.is-correct {
        border-color: var(--success);
        background: var(--success-bg);
        color: var(--success);
      }
      .flash-choice-btn.is-wrong {
        border-color: var(--danger);
        background: var(--danger-bg);
        color: var(--danger);
      }
      .flash-key-badge {
        font-family: var(--font-mono);
        font-size: 10.5px;
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid var(--border-col);
        background: var(--surface-2);
        color: var(--fg-secondary);
        flex-shrink: 0;
      }

      /* 5. Think-Aloud Interview Bar */
      .think-aloud-box {
        display: flex;
        flex-direction: column;
        gap: 7px;
        padding: 10px 11px;
        border: 1px solid var(--border-col);
        border-radius: var(--radius-sm);
        background: var(--surface-2);
      }
      .think-aloud-mic-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--fg-muted);
        margin-right: 5px;
      }
      .think-aloud-mic-dot.live {
        background: var(--danger);
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 28%, transparent);
      }
      .pillar-pill {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid var(--border-col);
        background: var(--surface);
        color: var(--fg-secondary);
        font-weight: 550;
      }
      .pillar-pill.met {
        border-color: color-mix(in srgb, var(--success) 50%, var(--border-col));
        background: var(--success-bg);
        color: var(--success);
      }

      /* 6. GitHub Gist Sync Modal */
      .gist-sync-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.48);
        backdrop-filter: blur(2px);
        z-index: 96;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      .gist-sync-backdrop.open { display: flex; }
      .gist-sync-dialog {
        width: 100%;
        max-width: 520px;
        background: var(--surface);
        border: 1px solid var(--border-col);
        border-radius: var(--radius);
        padding: 16px 18px;
        box-shadow: 0 22px 54px rgba(15, 23, 42, 0.28);
        display: flex;
        flex-direction: column;
        gap: 12px;
        transform: scale(0.95);
        opacity: 0;
        transition: transform 180ms var(--ease-out), opacity 180ms var(--ease-out);
      }
      .gist-sync-backdrop.open .gist-sync-dialog {
        transform: scale(1);
        opacity: 1;
      }
      .gist-sync-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: var(--fg-muted);
        margin-right: 5px;
      }
      .gist-sync-dot.connected { background: var(--success); }
    `;
    document.head.appendChild(style);
  }

  /* ==========================================================================
     1. RICHER PYTHON TUTOR VISUALISATIONS (2D GRID, BINARY TREE SVG, GRAPH SVG)
     ========================================================================== */
  function extractPrimitivesMap(frame) {
    const map = {};
    for (const v of frame?.frameVars || []) {
      if (v && v.kind === 'primitive') {
        map[v.name] = v.value;
      }
    }
    return map;
  }

  function buildRefLabelsMap(frame) {
    const map = new Map();
    for (const v of frame?.frameVars || []) {
      if (v && v.kind === 'ref' && v.refId) {
        if (!map.has(v.refId)) map.set(v.refId, []);
        map.get(v.refId).push(v.name);
      }
    }
    return map;
  }

  function detectBinaryTree(frame) {
    const objs = frame?.heapObjects || [];
    const byId = new Map(objs.map((o) => [o.id, o]));
    const treeObjs = objs.filter((o) => {
      if (o.type !== 'instance') return false;
      if (o.className === 'TreeNode') return true;
      const names = new Set((o.fields || []).map((f) => f.name));
      return names.has('val') && (names.has('left') || names.has('right'));
    });
    if (!treeObjs.length) return null;

    const childIds = new Set();
    for (const t of treeObjs) {
      for (const f of t.fields || []) {
        if ((f.name === 'left' || f.name === 'right') && f.kind === 'ref' && f.refId) {
          childIds.add(f.refId);
        }
      }
    }
    const refLabels = buildRefLabelsMap(frame);
    let rootId = null;
    for (const v of frame?.frameVars || []) {
      if (v.kind === 'ref' && byId.get(v.refId) && treeObjs.some((t) => t.id === v.refId)) {
        if (['root', 'tree'].includes(v.name)) {
          rootId = v.refId;
          break;
        }
      }
    }
    if (!rootId) {
      const top = treeObjs.find((t) => !childIds.has(t.id));
      rootId = top ? top.id : treeObjs[0].id;
    }

    // BFS layout up to 5 levels (max 31 nodes)
    const nodes = [];
    const edges = [];
    const visited = new Set();
    const queue = [{ id: rootId, depth: 0, slot: 0 }];
    let maxDepth = 0;

    while (queue.length && nodes.length < 31) {
      const cur = queue.shift();
      if (!cur.id || visited.has(cur.id) || cur.depth > 5) continue;
      const obj = byId.get(cur.id);
      if (!obj || obj.type !== 'instance') continue;
      visited.add(cur.id);
      maxDepth = Math.max(maxDepth, cur.depth);
      const valField = (obj.fields || []).find((f) => f.name === 'val');
      const leftField = (obj.fields || []).find((f) => f.name === 'left');
      const rightField = (obj.fields || []).find((f) => f.name === 'right');
      const valStr = valField ? String(valField.value ?? '') : '?';
      nodes.push({
        id: cur.id,
        val: valStr,
        depth: cur.depth,
        slot: cur.slot,
        labels: refLabels.get(cur.id) || [],
      });
      if (leftField && leftField.kind === 'ref' && leftField.refId && byId.has(leftField.refId) && cur.depth < 5) {
        edges.push({ from: cur.id, to: leftField.refId });
        queue.push({ id: leftField.refId, depth: cur.depth + 1, slot: cur.slot * 2 });
      }
      if (rightField && rightField.kind === 'ref' && rightField.refId && byId.has(rightField.refId) && cur.depth < 5) {
        edges.push({ from: cur.id, to: rightField.refId });
        queue.push({ id: rightField.refId, depth: cur.depth + 1, slot: cur.slot * 2 + 1 });
      }
    }
    return nodes.length ? { kind: 'tree', nodes, edges, maxDepth } : null;
  }

  function detectMatrix2D(frame) {
    const objs = frame?.heapObjects || [];
    const byId = new Map(objs.map((o) => [o.id, o]));
    const refLabels = buildRefLabelsMap(frame);
    const preferredOrder = ['dp', 'grid', 'matrix', 'board', 'memo', 'mat', 'heights', 'res'];
    const candidates = [];

    for (const o of objs) {
      if (o.type !== 'list' || !Array.isArray(o.elements)) continue;
      const rows = o.elements;
      if (rows.length < 2 || rows.length > 14) continue;
      if (!rows.every((r) => Array.isArray(r) && r.length >= 2 && r.length <= 14)) continue;
      const firstLen = rows[0].length;
      if (!rows.every((r) => r.length === firstLen)) continue;
      if (!rows.every((r) => r.every((c) => c === null || typeof c === 'number' || typeof c === 'string' || typeof c === 'boolean'))) continue;
      const labels = refLabels.get(o.id) || [];
      // Avoid mistaking 2-col edge/interval lists (e.g. [[1,2],[2,3],[3,4]]) unless named grid/matrix/dp
      const namedMatrix = labels.some((nm) => preferredOrder.includes(nm.toLowerCase()));
      if (firstLen === 2 && rows.length >= 3 && !namedMatrix) continue;
      const prio = namedMatrix ? 10 : 1;
      candidates.push({ obj: o, name: labels[0] || 'matrix', rows, prio });
    }
    if (!candidates.length) return null;
    candidates.sort((a, b) => b.prio - a.prio);
    return { kind: 'matrix', ...candidates[0] };
  }

  function detectGraphAdjacency(frame) {
    const objs = frame?.heapObjects || [];
    const refLabels = buildRefLabelsMap(frame);
    const graphNames = new Set(['graph', 'adj', 'adj_list', 'adjlist', 'g', 'edges', 'neighbors', 'neighbours']);

    for (const o of objs) {
      const labels = refLabels.get(o.id) || [];
      const isNamedGraph = labels.some((nm) => graphNames.has(nm.toLowerCase()));
      if (o.type === 'dict' && Array.isArray(o.entries) && o.entries.length >= 2 && o.entries.length <= 14) {
        const listVals = o.entries.filter((e) => Array.isArray(e[1]));
        if (listVals.length < 2) continue;
        if (!isNamedGraph) {
          // Require companion traversal variable to avoid rendering arbitrary dict-of-lists as a graph
          const varNames = new Set((frame?.frameVars || []).map((v) => String(v.name || '').toLowerCase()));
          const hasGraphVar = ['visited', 'seen', 'queue', 'q', 'dist', 'indegree', 'color', 'colour'].some((k) => varNames.has(k));
          if (!hasGraphVar) continue;
        }
        const nodeSet = new Set();
        const edgeList = [];
        for (const [k, nbrs] of o.entries) {
          const u = String(k);
          nodeSet.add(u);
          if (!Array.isArray(nbrs)) continue;
          for (const item of nbrs.slice(0, 10)) {
            if (Array.isArray(item) && item.length >= 2) {
              const v = String(item[0]);
              nodeSet.add(v);
              edgeList.push({ u, v, w: String(item[1]) });
            } else if (typeof item === 'string' || typeof item === 'number') {
              const v = String(item);
              nodeSet.add(v);
              edgeList.push({ u, v, w: '' });
            }
          }
        }
        const nodes = Array.from(nodeSet).slice(0, 14);
        if (nodes.length >= 2) {
          return { kind: 'graph', name: labels[0] || 'graph', nodes, edges: edgeList };
        }
      }
    }
    return null;
  }

  function renderTreeVisualHtml(tree) {
    const W = 520;
    const levelH = 44;
    const H = Math.max(104, (tree.maxDepth + 1) * levelH + 34);
    const pos = new Map();
    for (const n of tree.nodes) {
      const slots = Math.pow(2, n.depth);
      const x = ((n.slot + 0.5) / slots) * (W - 44) + 22;
      const y = 26 + n.depth * levelH;
      pos.set(n.id, { x, y });
    }

    const edgesSvg = tree.edges
      .map((e) => {
        const a = pos.get(e.from);
        const b = pos.get(e.to);
        if (!a || !b) return '';
        return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="var(--border-col)" stroke-width="1.6"></line>`;
      })
      .join('');

    const nodesSvg = tree.nodes
      .map((n) => {
        const pt = pos.get(n.id);
        const isActive = n.labels.length > 0;
        const fill = isActive ? 'color-mix(in srgb, var(--accent) 16%, var(--surface))' : 'var(--surface)';
        const stroke = isActive ? 'var(--accent)' : 'var(--border-col)';
        const lbl = n.labels.length
          ? `<text x="${pt.x.toFixed(1)}" y="${(pt.y - 18).toFixed(1)}" text-anchor="middle" font-size="9.5" font-weight="700" fill="var(--accent)" font-family="var(--font-mono)">${esc(n.labels.join(','))}</text>`
          : '';
        return (
          `<g>` +
          `<circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="14" fill="${fill}" stroke="${stroke}" stroke-width="${isActive ? 2 : 1.4}"></circle>` +
          `<text x="${pt.x.toFixed(1)}" y="${(pt.y + 4).toFixed(1)}" text-anchor="middle" font-size="11" font-weight="650" fill="var(--fg)" font-family="var(--font-mono)">${esc(n.val)}</text>` +
          lbl +
          `</g>`
        );
      })
      .join('');

    return (
      `<div class="pt-rich-header">` +
      `<span class="pt-rich-title">Binary Tree Visualiser <span class="stat-pill tabular">${tree.nodes.length} nodes</span></span>` +
      `<span class="muted" style="font-size:10.5px;">Highlighted nodes show active pointer variables in the current stack frame</span>` +
      `</div>` +
      `<div class="pt-rich-canvas-scroll">` +
      `<svg class="pt-svg-stage" viewBox="0 0 ${W} ${H}" role="img" aria-label="Live binary tree state">${edgesSvg}${nodesSvg}</svg>` +
      `</div>`
    );
  }

  function renderMatrixVisualHtml(mat, frame, prevFrame) {
    const prims = extractPrimitivesMap(frame);
    const rows = mat.rows;
    const R = rows.length;
    const C = rows[0].length;

    // Locate previous matrix for mutation diff
    let prevRows = null;
    if (prevFrame) {
      const prevObj = (prevFrame.heapObjects || []).find((o) => o.id === mat.obj.id && Array.isArray(o.elements));
      if (prevObj) prevRows = prevObj.elements;
    }

    // Detect numeric range for subtle DP heatmap shading
    const nums = [];
    for (const row of rows) {
      for (const v of row) {
        if (typeof v === 'number' && Number.isFinite(v)) nums.push(v);
      }
    }
    const minVal = nums.length ? Math.min(...nums) : 0;
    const maxVal = nums.length ? Math.max(...nums) : 0;
    const hasHeatmap = nums.length === R * C && maxVal > minVal;

    // Active cursor pairs
    const cursors = [];
    const pairs = [['r', 'c'], ['row', 'col'], ['i', 'j'], ['nr', 'nc'], ['x', 'y']];
    for (const [rk, ck] of pairs) {
      if (Number.isInteger(prims[rk]) && Number.isInteger(prims[ck])) {
        cursors.push({ r: prims[rk], c: prims[ck], label: `${rk},${ck}` });
      }
    }
    const topB = Number.isInteger(prims.top) ? prims.top : null;
    const botB = Number.isInteger(prims.bottom) ? prims.bottom : null;
    const leftB = Number.isInteger(prims.left) ? prims.left : null;
    const rightB = Number.isInteger(prims.right) ? prims.right : null;

    let thead = '<tr><th class="pt-grid-idx"></th>';
    for (let c = 0; c < C; c++) thead += `<th class="pt-grid-idx">c${c}</th>`;
    thead += '</tr>';

    let tbody = '';
    for (let r = 0; r < R; r++) {
      tbody += `<tr><td class="pt-grid-idx">r${r}</td>`;
      for (let c = 0; c < C; c++) {
        const val = rows[r][c];
        const prevVal = prevRows && prevRows[r] ? prevRows[r][c] : val;
        const mutated = prevRows !== null && JSON.stringify(val) !== JSON.stringify(prevVal);
        const hitCursors = cursors.filter((k) => k.r === r && k.c === c);
        const onBound = (topB !== null && r === topB) || (botB !== null && r === botB) || (leftB !== null && c === leftB) || (rightB !== null && c === rightB);
        let bgStyle = '';
        if (!mutated && hasHeatmap && typeof val === 'number') {
          const pct = Math.round(((val - minVal) / (maxVal - minVal)) * 22);
          if (pct > 0) bgStyle = `background:color-mix(in srgb, var(--accent) ${pct}%, var(--surface));`;
        } else if (!mutated && (val === '1' || val === '#')) {
          bgStyle = `background:color-mix(in srgb, var(--success) 16%, var(--surface));`;
        }
        const cls = ['pt-grid-cell', mutated ? 'is-mutated' : '', hitCursors.length ? 'is-cursor' : '', onBound ? 'is-bound' : ''].filter(Boolean).join(' ');
        const valDisp = val === null ? 'None' : String(val);
        const ptrHtml = hitCursors.length ? `<span class="pt-grid-cell-ptr">${esc(hitCursors.map((k) => k.label).join(' '))}</span>` : '';
        tbody += `<td class="${cls}" style="${bgStyle}">${esc(valDisp)}${ptrHtml}</td>`;
      }
      tbody += '</tr>';
    }

    const boundParts = [
      topB !== null ? `top=${topB}` : '',
      botB !== null ? `bottom=${botB}` : '',
      leftB !== null ? `left=${leftB}` : '',
      rightB !== null ? `right=${rightB}` : '',
    ].filter(Boolean);
    const metaHtml = boundParts.length
      ? `<div class="pt-rich-meta-pills">${boundParts.map((b) => `<span class="stat-pill tabular" style="font-size:10px; padding:1px 6px;">${esc(b)}</span>`).join('')}</div>`
      : `<span class="muted tabular" style="font-size:10.5px;">Green cells mutated on this step; outlined cells match active (r, c) or (i, j) cursors</span>`;

    return (
      `<div class="pt-rich-header">` +
      `<span class="pt-rich-title">2D Grid / DP Matrix: <code>${esc(mat.name)}</code> <span class="stat-pill tabular">${R} x ${C}</span></span>` +
      metaHtml +
      `</div>` +
      `<div class="pt-rich-canvas-scroll"><table class="pt-grid-table"><thead>${thead}</thead><tbody>${tbody}</tbody></table></div>`
    );
  }

  function renderGraphVisualHtml(graph, frame) {
    const objs = frame?.heapObjects || [];
    const byId = new Map(objs.map((o) => [o.id, o]));
    const visitedSet = new Set();
    const frontierSet = new Set();
    const activeNodes = new Set();

    for (const v of frame?.frameVars || []) {
      const nm = String(v.name || '').toLowerCase();
      if (v.kind === 'ref' && v.refId) {
        const obj = byId.get(v.refId);
        if (!obj) continue;
        const elems = Array.isArray(obj.elements)
          ? obj.elements
          : (Array.isArray(obj.entries) ? obj.entries.map((e) => e[0]) : []);
        if (['visited', 'seen', 'done', 'dist'].includes(nm)) {
          elems.forEach((x) => visitedSet.add(String(Array.isArray(x) ? x[0] : x)));
        } else if (['queue', 'q', 'stack', 'heap', 'pq', 'frontier'].includes(nm)) {
          elems.forEach((x) => frontierSet.add(String(Array.isArray(x) ? x[x.length - 1] : x)));
        }
      } else if (v.kind === 'primitive' && ['u', 'v', 'node', 'curr', 'cur', 'src', 'nei'].includes(nm)) {
        activeNodes.add(String(v.value));
      }
    }

    const W = 500;
    const H = 196;
    const cx = W / 2;
    const cy = H / 2;
    const rad = Math.min(W, H) * 0.36;
    const pos = new Map();
    graph.nodes.forEach((id, idx) => {
      const angle = (2 * Math.PI * idx) / graph.nodes.length - Math.PI / 2;
      pos.set(id, { x: cx + rad * Math.cos(angle), y: cy + rad * Math.sin(angle) });
    });

    const edgesSvg = graph.edges.slice(0, 48).map((e) => {
      const a = pos.get(e.u);
      const b = pos.get(e.v);
      if (!a || !b || e.u === e.v) return '';
      const mx = (a.x + b.x) / 2;
      const my = (a.y + b.y) / 2;
      const wTxt = e.w
        ? `<text x="${mx.toFixed(1)}" y="${(my - 4).toFixed(1)}" text-anchor="middle" font-size="9.5" fill="var(--fg-secondary)" font-family="var(--font-mono)">${esc(e.w)}</text>`
        : '';
      return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="var(--border-col)" stroke-width="1.4" marker-end="url(#pt-graph-arr)"></line>${wTxt}`;
    }).join('');

    const nodesSvg = graph.nodes.map((id) => {
      const pt = pos.get(id);
      let fill = 'var(--surface)';
      let stroke = 'var(--border-col)';
      let sw = 1.4;
      if (activeNodes.has(id)) {
        fill = 'color-mix(in srgb, var(--accent) 20%, var(--surface))';
        stroke = 'var(--accent)';
        sw = 2.2;
      } else if (frontierSet.has(id)) {
        fill = 'color-mix(in srgb, var(--warn) 18%, var(--surface))';
        stroke = 'var(--warn)';
        sw = 1.9;
      } else if (visitedSet.has(id)) {
        fill = 'color-mix(in srgb, var(--success) 18%, var(--surface))';
        stroke = 'var(--success)';
        sw = 1.8;
      }
      const shortLbl = id.length > 5 ? id.slice(0, 4) + '..' : id;
      return (
        `<g>` +
        `<circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="15" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"></circle>` +
        `<text x="${pt.x.toFixed(1)}" y="${(pt.y + 4).toFixed(1)}" text-anchor="middle" font-size="10.5" font-weight="650" fill="var(--fg)" font-family="var(--font-mono)">${esc(shortLbl)}</text>` +
        `</g>`
      );
    }).join('');

    return (
      `<div class="pt-rich-header">` +
      `<span class="pt-rich-title">Graph State Visualiser: <code>${esc(graph.name)}</code> <span class="stat-pill tabular">${graph.nodes.length} nodes</span></span>` +
      `<span class="muted" style="font-size:10.5px;">Accent = active, Amber = queue/frontier, Green = visited</span>` +
      `</div>` +
      `<div class="pt-rich-canvas-scroll">` +
      `<svg class="pt-svg-stage" viewBox="0 0 ${W} ${H}" role="img" aria-label="Live graph traversal state">` +
      `<defs><marker id="pt-graph-arr" viewBox="0 0 10 10" refX="19" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 1 L 10 5 L 0 9 z" fill="var(--fg-muted)"></path></marker></defs>` +
      `${edgesSvg}${nodesSvg}</svg>` +
      `</div>`
    );
  }

  function onVisualiserFrame(frame, prevFrame) {
    v3State.lastFrame = frame || null;
    v3State.lastPrevFrame = prevFrame || null;
    const strip = document.getElementById('pt-rich-visual-strip');
    if (!strip) return;
    if (!v3State.autoVisualOn || !frame) {
      strip.classList.remove('visible');
      return;
    }
    const tree = detectBinaryTree(frame);
    if (tree) {
      strip.innerHTML = renderTreeVisualHtml(tree);
      strip.classList.add('visible');
      return;
    }
    const mat = detectMatrix2D(frame);
    if (mat) {
      strip.innerHTML = renderMatrixVisualHtml(mat, frame, prevFrame);
      strip.classList.add('visible');
      return;
    }
    const graph = detectGraphAdjacency(frame);
    if (graph) {
      strip.innerHTML = renderGraphVisualHtml(graph, frame);
      strip.classList.add('visible');
      return;
    }
    strip.classList.remove('visible');
  }

  function mountVisualOverlayControls() {
    const visCard = document.getElementById('live-visualiser-card');
    if (!visCard || document.getElementById('pt-rich-visual-strip')) return;

    const split = document.getElementById('pt-workspace-split');
    const strip = document.createElement('div');
    strip.id = 'pt-rich-visual-strip';
    strip.className = 'pt-rich-visual-strip';
    strip.setAttribute('aria-label', 'Automatic Grid, Tree, and Graph visualiser');
    if (split && split.parentNode) {
      split.parentNode.insertBefore(strip, split);
    }

    const toggleCodeBtn = document.getElementById('pt-toggle-code-btn');
    if (toggleCodeBtn && toggleCodeBtn.parentNode && !document.getElementById('pt-visual-overlay-toggle')) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.id = 'pt-visual-overlay-toggle';
      btn.className = 'btn-subtle-accent';
      btn.style.cssText = 'padding:3px 8px; font-size:11.5px;';
      btn.title = 'Automatically render 2D matrices, binary trees, and graphs above the Python Tutor heap';
      btn.textContent = 'Auto Visual: On';
      btn.addEventListener('click', () => {
        v3State.autoVisualOn = !v3State.autoVisualOn;
        btn.textContent = v3State.autoVisualOn ? 'Auto Visual: On' : 'Auto Visual: Off';
        btn.className = v3State.autoVisualOn ? 'btn-subtle-accent' : '';
        onVisualiserFrame(v3State.lastFrame, v3State.lastPrevFrame);
      });
      toggleCodeBtn.parentNode.insertBefore(btn, toggleCodeBtn);
    }
  }

  /* ==========================================================================
     2. PER-PROBLEM COLLAPSIBLE VISUAL WHITEBOARD SCRATCHPAD
     ========================================================================== */
  function resolveInkColor(token) {
    const cs = getComputedStyle(document.documentElement);
    if (token === 'accent') return cs.getPropertyValue('--accent').trim() || '#2563eb';
    if (token === 'green') return cs.getPropertyValue('--success').trim() || '#16a34a';
    return cs.getPropertyValue('--fg').trim() || '#111827';
  }

  function resizeAndDrawWhiteboard() {
    const canvas = document.getElementById('whiteboard-canvas');
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const dpr = window.devicePixelRatio || 1;
    const targetW = Math.round(rect.width * dpr);
    const targetH = Math.round(rect.height * dpr);
    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const drawList = v3State.wbActiveStroke ? [...v3State.wbStrokes, v3State.wbActiveStroke] : v3State.wbStrokes;
    let boxCounter = 0;

    for (const s of drawList) {
      if (!s || !Array.isArray(s.pts) || !s.pts.length) continue;
      const color = resolveInkColor(s.c || 'ink');
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = s.t === 'pen' ? 2.1 : 1.8;

      if (s.t === 'pen') {
        ctx.beginPath();
        const p0 = s.pts[0];
        ctx.moveTo(p0[0] * rect.width, p0[1] * rect.height);
        for (let i = 1; i < s.pts.length; i++) {
          ctx.lineTo(s.pts[i][0] * rect.width, s.pts[i][1] * rect.height);
        }
        ctx.stroke();
      } else if (s.t === 'arrow' && s.pts.length >= 2) {
        const a = s.pts[0];
        const b = s.pts[s.pts.length - 1];
        const x1 = a[0] * rect.width;
        const y1 = a[1] * rect.height;
        const x2 = b[0] * rect.width;
        const y2 = b[1] * rect.height;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        const ang = Math.atan2(y2 - y1, x2 - x1);
        const head = 9;
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - head * Math.cos(ang - 0.48), y2 - head * Math.sin(ang - 0.48));
        ctx.lineTo(x2 - head * Math.cos(ang + 0.48), y2 - head * Math.sin(ang + 0.48));
        ctx.closePath();
        ctx.fill();
      } else if (s.t === 'box' && s.pts.length >= 2) {
        boxCounter++;
        const a = s.pts[0];
        const b = s.pts[s.pts.length - 1];
        const x = Math.min(a[0], b[0]) * rect.width;
        const y = Math.min(a[1], b[1]) * rect.height;
        const w = Math.max(24, Math.abs(b[0] - a[0]) * rect.width);
        const h = Math.max(22, Math.abs(b[1] - a[1]) * rect.height);
        const r = Math.min(7, w / 4, h / 4);
        ctx.beginPath();
        ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h);
        ctx.stroke();
        ctx.font = '600 11px ui-monospace, SFMono-Regular, Menlo, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(s.lbl || boxCounter), x + w / 2, y + h / 2);
      }
    }

    const cntEl = document.getElementById('wb-stroke-count');
    if (cntEl) cntEl.textContent = `${v3State.wbStrokes.length} ${v3State.wbStrokes.length === 1 ? 'stroke' : 'strokes'}`;
  }

  function scheduleWhiteboardSave() {
    const bridge = B();
    const key = v3State.wbProbKey || bridge?.activeProblemKey?.() || '';
    if (!key) return;
    if (bridge?.state?.progress) {
      bridge.state.progress.whiteboards = bridge.state.progress.whiteboards || {};
      bridge.state.progress.whiteboards[key] = v3State.wbStrokes.slice(0, 120);
    }
    if (v3State.wbSaveTimer) clearTimeout(v3State.wbSaveTimer);
    v3State.wbSaveTimer = setTimeout(() => {
      v3State.wbSaveTimer = null;
      bridge?.apiPost?.('/api/progress', {
        whiteboardKey: key,
        whiteboardStrokes: v3State.wbStrokes.slice(0, 120),
      }).catch(() => {});
    }, 350);
  }

  function loadWhiteboardForProblem(p) {
    const bridge = B();
    const key = bridge?.activeProblemKey?.(p) || (p ? (p.isCurated ? String(p.id) : `day-${p.day}`) : '');
    v3State.wbProbKey = key;
    const saved = bridge?.state?.progress?.whiteboards?.[key];
    v3State.wbStrokes = Array.isArray(saved) ? JSON.parse(JSON.stringify(saved)) : [];
    v3State.wbActiveStroke = null;
    if (v3State.wbOpen) {
      requestAnimationFrame(resizeAndDrawWhiteboard);
    }
    const btn = document.getElementById('scratchpad-toggle-btn');
    if (btn) {
      btn.textContent = v3State.wbStrokes.length ? `Scratchpad (${v3State.wbStrokes.length})` : 'Scratchpad';
    }
  }

  function mountWhiteboard() {
    const stressBtn = document.getElementById('stress-test-btn');
    if (stressBtn && stressBtn.parentNode && !document.getElementById('scratchpad-toggle-btn')) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.id = 'scratchpad-toggle-btn';
      btn.title = 'Open per-problem visual whiteboard scratchpad to sketch trees, pointers, and DP grids';
      btn.textContent = 'Scratchpad';
      btn.addEventListener('click', () => {
        v3State.wbOpen = !v3State.wbOpen;
        const card = document.getElementById('whiteboard-card');
        if (card) card.classList.toggle('open', v3State.wbOpen);
        btn.classList.toggle('btn-subtle-accent', v3State.wbOpen);
        if (v3State.wbOpen) requestAnimationFrame(resizeAndDrawWhiteboard);
      });
      stressBtn.parentNode.insertBefore(btn, stressBtn);
    }

    const editorFrame = document.getElementById('editor-frame');
    if (!editorFrame || !editorFrame.parentNode || document.getElementById('whiteboard-card')) return;

    const card = document.createElement('div');
    card.id = 'whiteboard-card';
    card.className = 'whiteboard-card';
    card.setAttribute('aria-label', 'Visual algorithm whiteboard scratchpad');
    card.innerHTML =
      `<div class="whiteboard-toolbar">` +
      `<div class="whiteboard-tool-group">` +
      `<span style="font-size:11.5px; font-weight:650; color:var(--fg); margin-right:4px;">Scratchpad</span>` +
      `<button type="button" class="wb-tool-btn active" data-wb-tool="pen">Pen</button>` +
      `<button type="button" class="wb-tool-btn" data-wb-tool="arrow">Arrow</button>` +
      `<button type="button" class="wb-tool-btn" data-wb-tool="box">Node Box</button>` +
      `<button type="button" class="wb-tool-btn" data-wb-tool="eraser">Eraser</button>` +
      `<span style="width:1px; height:14px; background:var(--border-col); margin:0 3px;"></span>` +
      `<button type="button" class="wb-swatch active" data-wb-color="ink" style="background:var(--fg);" title="Ink colour" aria-label="Ink colour"></button>` +
      `<button type="button" class="wb-swatch" data-wb-color="accent" style="background:var(--accent);" title="Accent colour" aria-label="Accent colour"></button>` +
      `<button type="button" class="wb-swatch" data-wb-color="green" style="background:var(--success);" title="Green colour" aria-label="Green colour"></button>` +
      `</div>` +
      `<div class="whiteboard-tool-group">` +
      `<span id="wb-stroke-count" class="muted tabular" style="font-size:10.5px; margin-right:4px;">0 strokes</span>` +
      `<button type="button" id="wb-undo-btn" class="wb-tool-btn">Undo</button>` +
      `<button type="button" id="wb-clear-btn" class="wb-tool-btn">Clear</button>` +
      `<button type="button" id="wb-close-btn" class="wb-tool-btn">Close</button>` +
      `</div>` +
      `</div>` +
      `<div class="whiteboard-canvas-wrap"><canvas id="whiteboard-canvas"></canvas></div>`;
    editorFrame.parentNode.insertBefore(card, editorFrame);

    card.querySelectorAll('[data-wb-tool]').forEach((b) => {
      b.addEventListener('click', () => {
        v3State.wbTool = b.getAttribute('data-wb-tool');
        card.querySelectorAll('[data-wb-tool]').forEach((x) => x.classList.toggle('active', x === b));
      });
    });
    card.querySelectorAll('[data-wb-color]').forEach((b) => {
      b.addEventListener('click', () => {
        v3State.wbColor = b.getAttribute('data-wb-color');
        card.querySelectorAll('[data-wb-color]').forEach((x) => x.classList.toggle('active', x === b));
      });
    });
    document.getElementById('wb-undo-btn')?.addEventListener('click', () => {
      v3State.wbStrokes.pop();
      resizeAndDrawWhiteboard();
      scheduleWhiteboardSave();
    });
    document.getElementById('wb-clear-btn')?.addEventListener('click', () => {
      v3State.wbStrokes = [];
      resizeAndDrawWhiteboard();
      scheduleWhiteboardSave();
    });
    document.getElementById('wb-close-btn')?.addEventListener('click', () => {
      v3State.wbOpen = false;
      card.classList.remove('open');
      document.getElementById('scratchpad-toggle-btn')?.classList.remove('btn-subtle-accent');
    });

    const canvas = document.getElementById('whiteboard-canvas');
    const normPoint = (ev) => {
      const r = canvas.getBoundingClientRect();
      return [
        Math.max(0, Math.min(1, Number(((ev.clientX - r.left) / Math.max(1, r.width)).toFixed(4)))),
        Math.max(0, Math.min(1, Number(((ev.clientY - r.top) / Math.max(1, r.height)).toFixed(4)))),
      ];
    };

    const eraseNear = (pt) => {
      const before = v3State.wbStrokes.length;
      v3State.wbStrokes = v3State.wbStrokes.filter((s) => {
        return !(s.pts || []).some((p) => Math.hypot(p[0] - pt[0], p[1] - pt[1]) < 0.035);
      });
      if (v3State.wbStrokes.length !== before) {
        resizeAndDrawWhiteboard();
        scheduleWhiteboardSave();
      }
    };

    canvas.addEventListener('pointerdown', (ev) => {
      canvas.setPointerCapture?.(ev.pointerId);
      const pt = normPoint(ev);
      if (v3State.wbTool === 'eraser') {
        v3State.wbDrawing = true;
        eraseNear(pt);
        return;
      }
      v3State.wbDrawing = true;
      const boxCount = v3State.wbStrokes.filter((s) => s.t === 'box').length + 1;
      v3State.wbActiveStroke = {
        t: v3State.wbTool,
        c: v3State.wbColor,
        pts: [pt],
        ...(v3State.wbTool === 'box' ? { lbl: String(boxCount) } : {}),
      };
      resizeAndDrawWhiteboard();
    });

    canvas.addEventListener('pointermove', (ev) => {
      if (!v3State.wbDrawing) return;
      const pt = normPoint(ev);
      if (v3State.wbTool === 'eraser') {
        eraseNear(pt);
        return;
      }
      if (!v3State.wbActiveStroke) return;
      if (v3State.wbTool === 'pen') {
        const last = v3State.wbActiveStroke.pts[v3State.wbActiveStroke.pts.length - 1];
        if (Math.hypot(pt[0] - last[0], pt[1] - last[1]) > 0.004 && v3State.wbActiveStroke.pts.length < 180) {
          v3State.wbActiveStroke.pts.push(pt);
        }
      } else {
        v3State.wbActiveStroke.pts = [v3State.wbActiveStroke.pts[0], pt];
      }
      resizeAndDrawWhiteboard();
    });

    const finishStroke = () => {
      if (!v3State.wbDrawing) return;
      v3State.wbDrawing = false;
      if (v3State.wbActiveStroke) {
        if (v3State.wbActiveStroke.pts.length === 1 && v3State.wbActiveStroke.t === 'box') {
          const p0 = v3State.wbActiveStroke.pts[0];
          v3State.wbActiveStroke.pts.push([Math.min(0.98, p0[0] + 0.08), Math.min(0.96, p0[1] + 0.16)]);
        }
        v3State.wbStrokes.push(v3State.wbActiveStroke);
        if (v3State.wbStrokes.length > 120) v3State.wbStrokes = v3State.wbStrokes.slice(-120);
        v3State.wbActiveStroke = null;
        resizeAndDrawWhiteboard();
        scheduleWhiteboardSave();
        const btn = document.getElementById('scratchpad-toggle-btn');
        if (btn) btn.textContent = `Scratchpad (${v3State.wbStrokes.length})`;
      }
    };
    canvas.addEventListener('pointerup', finishStroke);
    canvas.addEventListener('pointercancel', finishStroke);

    // Redraw cleanly on Light/Dark theme switch
    document.getElementById('theme-btn')?.addEventListener('click', () => {
      setTimeout(() => {
        if (v3State.wbOpen) resizeAndDrawWhiteboard();
      }, 40);
    });
  }

  /* ==========================================================================
     3. EMPIRICAL BIG-O SCALING VISUALISER
     ========================================================================== */
  function buildBigOSvgChart(res) {
    const pts = res.points || [];
    const ref = res.referenceCurves || {};
    const W = 460;
    const H = 180;
    const pad = { l: 48, r: 16, t: 18, b: 30 };
    const plotW = W - pad.l - pad.r;
    const plotH = H - pad.t - pad.b;

    const maxN = Math.max(...pts.map((p) => Number(p.n) || 1));
    const minN = Math.min(...pts.map((p) => Number(p.n) || 1));
    const measuredMax = Math.max(...pts.map((p) => Number(p.ops) || 1));
    // Clamp vertical ceiling so O(N^2) reference does not crush an O(N) user curve flat
    const yCeiling = Math.max(measuredMax * 1.25, 10);

    const xOf = (n) => pad.l + ((n - minN) / Math.max(1, maxN - minN)) * plotW;
    const yOf = (ops) => pad.t + plotH - Math.min(1.06, Math.max(0, ops / yCeiling)) * plotH;

    let gridSvg = '';
    for (let i = 0; i <= 3; i++) {
      const val = Math.round((yCeiling * i) / 3);
      const y = pad.t + plotH - (plotH * i) / 3;
      gridSvg += `<line x1="${pad.l}" y1="${y.toFixed(1)}" x2="${W - pad.r}" y2="${y.toFixed(1)}" stroke="var(--border-col)" stroke-dasharray="2 3" stroke-width="1"></line>`;
      gridSvg += `<text x="${pad.l - 6}" y="${(y + 3).toFixed(1)}" text-anchor="end" font-size="9.5" fill="var(--fg-muted)" font-family="var(--font-mono)">${val}</text>`;
    }

    const refMeta = [
      { key: 'O(N)', color: 'var(--success)', dash: '4 3' },
      { key: 'O(N log N)', color: 'var(--warn)', dash: '5 3' },
      { key: 'O(N^2)', color: 'var(--danger)', dash: '2 3' },
    ];
    let refSvg = '';
    for (const rm of refMeta) {
      const vals = ref[rm.key];
      if (!Array.isArray(vals) || vals.length !== pts.length) continue;
      const d = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${xOf(p.n).toFixed(1)} ${yOf(vals[idx]).toFixed(1)}`).join(' ');
      refSvg += `<path d="${d}" fill="none" stroke="${rm.color}" stroke-width="1.4" stroke-dasharray="${rm.dash}" opacity="0.72"></path>`;
    }

    const userD = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${xOf(p.n).toFixed(1)} ${yOf(p.ops).toFixed(1)}`).join(' ');
    const dotsSvg = pts.map((p) => {
      const cx = xOf(p.n);
      const cy = yOf(p.ops);
      return (
        `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4" fill="var(--accent)" stroke="var(--surface)" stroke-width="1.5"></circle>` +
        `<text x="${cx.toFixed(1)}" y="${H - 10}" text-anchor="middle" font-size="9.5" fill="var(--fg-secondary)" font-family="var(--font-mono)">N=${p.n}</text>`
      );
    }).join('');

    return (
      `<svg viewBox="0 0 ${W} ${H}" width="100%" style="height:auto; display:block;" role="img" aria-label="Empirical Big-O step count scaling chart">` +
      gridSvg +
      `<line x1="${pad.l}" y1="${pad.t}" x2="${pad.l}" y2="${pad.t + plotH}" stroke="var(--border-col)" stroke-width="1.2"></line>` +
      `<line x1="${pad.l}" y1="${pad.t + plotH}" x2="${W - pad.r}" y2="${pad.t + plotH}" stroke="var(--border-col)" stroke-width="1.2"></line>` +
      refSvg +
      `<path d="${userD}" fill="none" stroke="var(--accent)" stroke-width="2.4"></path>` +
      dotsSvg +
      `</svg>`
    );
  }

  function renderBigOCard(res, errMsg = '') {
    const card = document.getElementById('bigo-bench-card');
    if (!card) return;
    card.classList.add('open');
    if (errMsg || !res?.ok) {
      card.innerHTML =
        `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">` +
        `<span style="font-size:12px; font-weight:650; color:var(--danger);">Empirical Big-O Scaling Plotter</span>` +
        `<button type="button" id="bigo-close-btn" style="padding:2px 8px; font-size:11px;">Close</button>` +
        `</div>` +
        `<div class="muted" style="font-size:12px;">${esc(errMsg || res?.error || 'Could not run complexity benchmark.')}</div>`;
      document.getElementById('bigo-close-btn')?.addEventListener('click', () => card.classList.remove('open'));
      return;
    }

    const pts = res.points || [];
    const okTone = res.status === 'optimal' ? 'var(--success)' : 'var(--warn)';
    const rowsHtml = pts.map((pt, idx) => {
      const ratio = idx > 0 && pts[idx - 1].ops > 0 ? `${(pt.ops / pts[idx - 1].ops).toFixed(2)}x` : 'base';
      return `<tr><td>N = ${Number(pt.n)}</td><td>${Number(pt.ops).toLocaleString()}</td><td>${Number(pt.ms).toFixed(2)} ms</td><td>${ratio}</td></tr>`;
    }).join('');

    card.innerHTML =
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">` +
      `<span style="font-size:12px; font-weight:650; color:var(--fg);">Empirical Big-O Scaling Plot</span>` +
      `<span class="stat-pill tabular" style="color:${okTone}; border-color:${okTone};">Detected: ${esc(res.detectedClass)}</span>` +
      `<span class="stat-pill tabular">Target: ${esc(res.targetOptimal)}</span>` +
      `</div>` +
      `<button type="button" id="bigo-close-btn" style="padding:2px 8px; font-size:11px;">Close</button>` +
      `</div>` +
      `<div style="font-size:12px; color:var(--fg-secondary);">${esc(res.verdict || '')}</div>` +
      `<div class="bigo-grid">` +
      `<div>${buildBigOSvgChart(res)}` +
      `<div style="display:flex; gap:10px; flex-wrap:wrap; font-size:10.5px; color:var(--fg-muted); padding-left:8px;">` +
      `<span><span style="color:var(--accent); font-weight:700;">Solid</span> Your Code Ops</span>` +
      `<span><span style="color:var(--success);">Dashed</span> O(N)</span>` +
      `<span><span style="color:var(--warn);">Dashed</span> O(N log N)</span>` +
      `<span><span style="color:var(--danger);">Dashed</span> O(N^2)</span>` +
      `</div></div>` +
      `<div><table class="bigo-table"><thead><tr><th>Size</th><th>Step Ops</th><th>Time</th><th>Growth</th></tr></thead><tbody>${rowsHtml}</tbody></table></div>` +
      `</div>`;
    document.getElementById('bigo-close-btn')?.addEventListener('click', () => card.classList.remove('open'));
  }

  async function runBigOBenchmark() {
    if (v3State.bigOLoading) return;
    const bridge = B();
    const btn = document.getElementById('bigo-bench-btn');
    const code = document.getElementById('code-editor')?.value || '';
    v3State.bigOLoading = true;
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Plotting...';
    }
    try {
      const payload = {
        ...bridge.activeProblemIdPayload(),
        language: bridge.state.activeLang || 'python',
        code,
      };
      const res = await bridge.apiPost('/api/complexity-bench', payload);
      v3State.bigOResult = res;
      renderBigOCard(res);
      document.getElementById('bigo-bench-card')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      renderBigOCard(null, err?.message || String(err));
    } finally {
      v3State.bigOLoading = false;
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Big-O Plot';
      }
    }
  }

  function mountBigOPlotter() {
    const stressBtn = document.getElementById('stress-test-btn');
    if (stressBtn && stressBtn.parentNode && !document.getElementById('bigo-bench-btn')) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.id = 'bigo-bench-btn';
      btn.title = 'Run your Python code across 4 scaled input sizes and plot measured operations against O(N), O(N log N), and O(N^2)';
      btn.textContent = 'Big-O Plot';
      btn.addEventListener('click', runBigOBenchmark);
      stressBtn.insertAdjacentElement('afterend', btn);
    }

    const consoleBox = document.getElementById('test-console-box');
    const resultsEl = document.getElementById('test-results-container');
    if (consoleBox && resultsEl && !document.getElementById('bigo-bench-card')) {
      const card = document.createElement('div');
      card.id = 'bigo-bench-card';
      card.className = 'bigo-card';
      consoleBox.insertBefore(card, resultsEl);
    }
  }

  /* ==========================================================================
     4. 30-SECOND PATTERN RECOGNITION FLASH DRILLS (TAB 2 4TH MODE)
     ========================================================================== */
  function stopFlashTimer() {
    if (v3State.flash.timerId) {
      clearInterval(v3State.flash.timerId);
      v3State.flash.timerId = null;
    }
  }

  function sanitiseFlashStatement(prob) {
    let text = String(prob?.statement || '').trim();
    const title = String(prob?.title || '').trim();
    if (title.length >= 4) {
      const escTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      text = text.replace(new RegExp(escTitle, 'gi'), '[problem target]');
    }
    text = text.replace(/LC\s*\d+/gi, '[masked]');
    return text.length > 360 ? text.slice(0, 357) + '...' : text;
  }

  function pickFlashPool() {
    const bridge = B();
    const all = (bridge?.state?.problems || []).filter((p) => !p.isSql && Array.isArray(p.tags) && p.tags.length > 0);
    const scope = v3State.flash.scope;
    if (scope === 'weak') {
      const weakNames = new Set((bridge?.state?.spacedRepetition?.weakTopics || []).map((w) => w.name));
      const matched = all.filter((p) => p.tags.some((t) => weakNames.has(t)));
      return matched.length >= 4 ? matched : all;
    }
    if (scope === 'due') {
      const dueDays = new Set((bridge?.state?.spacedRepetition?.dueReview || []).map((d) => Number(d.day)));
      const matched = all.filter((p) => dueDays.has(Number(p.day)));
      return matched.length >= 4 ? matched : all;
    }
    if (scope === 'phase1') return all.filter((p) => Number(p.phase) <= 6);
    if (scope === 'phase2') return all.filter((p) => Number(p.phase) >= 7);
    return all;
  }

  function startNextFlashCard() {
    stopFlashTimer();
    const pool = pickFlashPool();
    if (!pool.length) return;
    const fresh = pool.filter((p) => !v3State.flash.recentDays.includes(p.day));
    const bucket = fresh.length ? fresh : pool;
    const chosen = bucket[Math.floor(Math.random() * bucket.length)];
    v3State.flash.recentDays.push(chosen.day);
    if (v3State.flash.recentDays.length > 25) v3State.flash.recentDays.shift();

    const correctTag = chosen.tags[0];
    const allTags = Array.from(new Set((B()?.state?.problems || []).map((p) => p.tags?.[0]).filter(Boolean)));
    const distractors = allTags
      .filter((t) => t !== correctTag && !chosen.tags.includes(t))
      .sort(() => Math.random() - 0.5)
      .slice(0, 3);
    const choices = [correctTag, ...distractors].sort(() => Math.random() - 0.5);

    v3State.flash.active = true;
    v3State.flash.revealed = false;
    v3State.flash.currentProb = chosen;
    v3State.flash.correctTag = correctTag;
    v3State.flash.choices = choices;
    v3State.flash.chosenTag = '';
    v3State.flash.timeLeft = 30;

    v3State.flash.timerId = setInterval(() => {
      if (!v3State.flash.active || v3State.flash.revealed) return;
      v3State.flash.timeLeft = Math.max(0, v3State.flash.timeLeft - 1);
      updateFlashRing();
      if (v3State.flash.timeLeft <= 0) {
        submitFlashAnswer('__timeout__');
      }
    }, 1000);

    renderFlashPanel();
  }

  function updateFlashRing() {
    const txt = document.getElementById('flash-timer-text');
    const arc = document.getElementById('flash-timer-arc');
    if (txt) txt.textContent = `${v3State.flash.timeLeft}s`;
    if (arc) {
      const circ = 2 * Math.PI * 22;
      const offset = circ * (1 - v3State.flash.timeLeft / 30);
      arc.setAttribute('stroke-dashoffset', offset.toFixed(1));
      arc.setAttribute('stroke', v3State.flash.timeLeft <= 8 ? 'var(--danger)' : 'var(--accent)');
    }
  }

  function submitFlashAnswer(tag) {
    if (!v3State.flash.active || v3State.flash.revealed) return;
    stopFlashTimer();
    v3State.flash.revealed = true;
    v3State.flash.chosenTag = tag;
    const correct = tag === v3State.flash.correctTag;
    v3State.flash.sessionAttempted++;
    if (correct) {
      v3State.flash.sessionCorrect++;
      v3State.flash.streak++;
    } else {
      v3State.flash.streak = 0;
    }

    const bridge = B();
    const prev = bridge?.state?.progress?.flashDrillStats || { attempted: 0, correct: 0, bestStreak: 0 };
    const nextStats = {
      attempted: Number(prev.attempted || 0) + 1,
      correct: Number(prev.correct || 0) + (correct ? 1 : 0),
      bestStreak: Math.max(Number(prev.bestStreak || 0), v3State.flash.streak),
    };
    if (bridge?.state?.progress) {
      bridge.state.progress.flashDrillStats = nextStats;
    }
    bridge?.apiPost?.('/api/progress', { saveFlashDrillStats: nextStats }).catch(() => {});
    renderFlashPanel();
  }

  function renderFlashPanel() {
    const panel = document.getElementById('coach-panel-flash');
    if (!panel) return;
    const bridge = B();
    const fl = v3State.flash;
    const stats = bridge?.state?.progress?.flashDrillStats || { attempted: 0, correct: 0, bestStreak: 0 };
    const accPct = stats.attempted ? Math.round((stats.correct / stats.attempted) * 100) : 0;

    const scopes = [
      ['all', 'All 120 Days'],
      ['weak', 'Weak Topics'],
      ['due', 'Due Review'],
      ['phase1', 'Foundations (Days 1 to 50)'],
      ['phase2', 'Graphs, DP & Systems (Days 51 to 120)'],
    ];
    const scopeBtns = scopes.map(([id, lbl]) =>
      `<button type="button" data-flash-scope="${id}" class="${fl.scope === id ? 'btn-subtle-accent' : ''}" style="padding:3px 9px; font-size:11.5px;">${esc(lbl)}</button>`
    ).join('');

    const headerCard =
      `<div class="card">` +
      `<div class="card-header">` +
      `<div>` +
      `<h2 class="card-title">30-Second Pattern Recognition Flash Drills</h2>` +
      `<span class="muted">Titles and tags are hidden. Read the constraints and problem essence, then name the optimal pattern before the 30-second clock expires.</span>` +
      `</div>` +
      `<div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">` +
      `<span class="stat-pill tabular">Accuracy: ${accPct}% (${stats.correct}/${stats.attempted})</span>` +
      `<span class="stat-pill tabular">Best Streak: ${stats.bestStreak}</span>` +
      `</div>` +
      `</div>` +
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<div style="display:flex; gap:5px; flex-wrap:wrap;">${scopeBtns}</div>` +
      `<button type="button" id="flash-start-btn" class="btn-primary">${fl.active ? 'Draw New Card' : 'Start 30s Flash Drill'}</button>` +
      `</div>` +
      `</div>`;

    let bodyHtml = '';
    if (!fl.active || !fl.currentProb) {
      bodyHtml =
        `<div class="card"><div class="inner-box muted" style="font-size:12.5px; line-height:1.55;">` +
        `Click Start 30s Flash Drill above. You can answer with keyboard keys 1 to 4 and press Enter for the next problem.` +
        `</div></div>`;
    } else {
      const p = fl.currentProb;
      const circ = (2 * Math.PI * 22).toFixed(1);
      const offset = (2 * Math.PI * 22 * (1 - fl.timeLeft / 30)).toFixed(1);
      const isRight = fl.revealed && fl.chosenTag === fl.correctTag;
      const constraintsHtml = (p.constraints || []).slice(0, 4).map((c) => `<li>${rich(c)}</li>`).join('');
      const triggerCue = p.mentalModel?.triggerSignal || 'Spot the constraint bottleneck and recurring state transition.';

      const choicesHtml = fl.choices.map((tag, idx) => {
        let cls = 'flash-choice-btn';
        if (fl.revealed) {
          if (tag === fl.correctTag) cls += ' is-correct';
          else if (tag === fl.chosenTag) cls += ' is-wrong';
        }
        return (
          `<button type="button" class="${cls}" data-flash-choice="${esc(tag)}"${fl.revealed ? ' disabled' : ''}>` +
          `<span class="flash-key-badge">${idx + 1}</span>` +
          `<span>${esc(tag)}</span>` +
          `</button>`
        );
      }).join('');

      const revealHtml = fl.revealed
        ? `<div class="inner-box" style="border-left:3px solid ${isRight ? 'var(--success)' : 'var(--danger)'}; display:flex; flex-direction:column; gap:8px;">` +
          `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
          `<span style="font-weight:650; font-size:13px; color:${isRight ? 'var(--success)' : 'var(--danger)'};">` +
          `${isRight ? 'Correct Pattern Recognised' : (fl.chosenTag === '__timeout__' ? 'Time Expired' : 'Missed Pattern')}: Day ${p.day} (${esc(p.leetcodeId)}: ${esc(p.title)})` +
          `</span>` +
          `<div style="display:flex; gap:6px;">` +
          `<button type="button" id="flash-open-prob-btn" style="padding:3px 9px; font-size:11.5px;">Open in Workbench</button>` +
          `<button type="button" id="flash-next-btn" class="btn-primary" style="padding:3px 10px; font-size:11.5px;">Next Card →</button>` +
          `</div>` +
          `</div>` +
          `<div class="vs-contrast-grid">` +
          `<div class="vs-contrast-box trap"><span class="vs-contrast-tag">Instinctive Trap:</span>${rich(p.mentalModel?.instinctiveTrap || 'Brute-force rescanning.')}</div>` +
          `<div class="vs-contrast-box pivot"><span class="vs-contrast-tag">Optimal Pivot:</span>${rich(p.mentalModel?.optimalPivot || '')}</div>` +
          `</div>` +
          `</div>`
        : '';

      bodyHtml =
        `<div class="card">` +
        `<div class="flash-shell">` +
        `<div style="display:flex; flex-direction:column; gap:10px;">` +
        `<div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">` +
        `<span class="diff-badge ${p.difficulty.includes('Easy') ? 'diff-Easy' : p.difficulty.includes('Medium') ? 'diff-Medium' : 'diff-Hard'}">${esc(p.difficulty)}</span>` +
        `<span class="stat-pill">Title &amp; Tags Hidden</span>` +
        `<span class="stat-pill tabular">Session Streak: ${fl.streak}</span>` +
        `</div>` +
        `<div class="inner-box" style="font-size:13px; line-height:1.55;">${rich(sanitiseFlashStatement(p))}</div>` +
        (constraintsHtml ? `<div class="inner-box"><div style="font-size:11.5px; font-weight:650; margin-bottom:4px;">Constraints</div><ul style="margin:0; padding-left:18px; font-size:12px; color:var(--fg-secondary);">${constraintsHtml}</ul></div>` : '') +
        `<div class="inner-box" style="font-size:12px; color:var(--fg-secondary);"><span style="font-weight:650; color:var(--fg);">Trigger Cue: </span>${rich(triggerCue)}</div>` +
        `</div>` +
        `<div style="display:flex; flex-direction:column; align-items:center; gap:10px; padding:12px; border:1px solid var(--border-col); border-radius:var(--radius-sm); background:var(--surface-2);">` +
        `<svg width="62" height="62" viewBox="0 0 54 54" aria-label="30 second countdown timer">` +
        `<circle cx="27" cy="27" r="22" fill="none" stroke="var(--border-col)" stroke-width="4"></circle>` +
        `<circle id="flash-timer-arc" cx="27" cy="27" r="22" fill="none" stroke="${fl.timeLeft <= 8 ? 'var(--danger)' : 'var(--accent)'}" stroke-width="4" stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${offset}" transform="rotate(-90 27 27)"></circle>` +
        `<text id="flash-timer-text" x="27" y="31" text-anchor="middle" font-size="13" font-weight="700" fill="var(--fg)" font-family="var(--font-mono)">${fl.timeLeft}s</text>` +
        `</svg>` +
        `<div style="font-size:12px; font-weight:650; text-align:center;">Which primary pattern solves this optimally?</div>` +
        `<div class="flash-choice-grid" style="width:100%;">${choicesHtml}</div>` +
        `</div>` +
        `</div>` +
        revealHtml +
        `</div>`;
    }

    panel.innerHTML = headerCard + bodyHtml;

    panel.querySelectorAll('[data-flash-scope]').forEach((b) => {
      b.addEventListener('click', () => {
        v3State.flash.scope = b.getAttribute('data-flash-scope');
        if (v3State.flash.active) startNextFlashCard();
        else renderFlashPanel();
      });
    });
    document.getElementById('flash-start-btn')?.addEventListener('click', startNextFlashCard);
    panel.querySelectorAll('[data-flash-choice]').forEach((b) => {
      b.addEventListener('click', () => submitFlashAnswer(b.getAttribute('data-flash-choice')));
    });
    document.getElementById('flash-next-btn')?.addEventListener('click', startNextFlashCard);
    document.getElementById('flash-open-prob-btn')?.addEventListener('click', () => {
      const p = v3State.flash.currentProb;
      if (!p) return;
      stopFlashTimer();
      bridge.switchCourse('schedule-120', { day: p.day });
      bridge.switchTab('workbench');
    });
  }

  function mountFlashDrillMode() {
    const modeBar = document.getElementById('coach-mode-bar');
    const examPanel = document.getElementById('coach-panel-exam');
    if (!modeBar || !examPanel || document.getElementById('coach-mode-flash-btn')) return;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'coach-mode-flash-btn';
    btn.className = 'coach-mode-btn';
    btn.setAttribute('data-coach-mode', 'flash');
    btn.textContent = 'Pattern Flash (30s)';
    btn.addEventListener('click', () => window.StudioV2?.switchCoachMode?.('flash'));
    modeBar.appendChild(btn);

    const flashPanel = document.createElement('div');
    flashPanel.id = 'coach-panel-flash';
    flashPanel.style.cssText = 'display:none; flex-direction:column; gap:12px;';
    examPanel.insertAdjacentElement('afterend', flashPanel);

    // Keyboard shortcuts 1-4 and Enter when Flash Drill panel is visible
    document.addEventListener('keydown', (e) => {
      const coachOpen = document.getElementById('pane-coach')?.classList.contains('active');
      const flashOpen = flashPanel.style.display !== 'none';
      if (!coachOpen || !flashOpen || !v3State.flash.active) return;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;
      if (!v3State.flash.revealed && ['1', '2', '3', '4'].includes(e.key)) {
        const idx = Number(e.key) - 1;
        if (v3State.flash.choices[idx]) {
          e.preventDefault();
          submitFlashAnswer(v3State.flash.choices[idx]);
        }
      } else if (v3State.flash.revealed && e.key === 'Enter') {
        e.preventDefault();
        startNextFlashCard();
      }
    });
  }

  function onCoachModeChanged(mode) {
    const flashPanel = document.getElementById('coach-panel-flash');
    if (flashPanel) {
      flashPanel.style.display = mode === 'flash' ? 'flex' : 'none';
    }
    if (mode === 'flash') {
      renderFlashPanel();
    } else {
      stopFlashTimer();
    }
  }

  /* ==========================================================================
     5. THINK-ALOUD INTERVIEW MODE (WEB SPEECH API + LIVE 4-PILLAR CHECKLIST)
     ========================================================================== */
  function evalLivePillars(text) {
    const low = String(text || '').toLowerCase();
    return {
      constraints: /(empty|null|none|duplicate|negative|bound|constraint|size|length|sorted|assume|clarify)/.test(low),
      bigO: /(\bo\s*\([^)]{1,18}\)|time complexity|space complexity|linear|constant|logarithmic|quadratic|big o)/.test(low),
      tradeoff: /(brute|naive|instead|trade|optimis|optimiz|invariant|hash|map|heap|stack|queue|pointer|window|dp|binary search|bfs|dfs|trie)/.test(low),
      dryrun: /(example|trace|walk through|dry run|step|edge case|base case|index|return)/.test(low),
    };
  }

  function stopThinkAloudMic() {
    if (v3State.thinkAloud.recognition) {
      try { v3State.thinkAloud.recognition.stop(); } catch (_) {}
      v3State.thinkAloud.recognition = null;
    }
    v3State.thinkAloud.recording = false;
    v3State.thinkAloud.interimText = '';
  }

  function toggleThinkAloudMic(stageLabel) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    if (v3State.thinkAloud.recording) {
      stopThinkAloudMic();
      updateThinkAloudUi(stageLabel);
      return;
    }
    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';
    v3State.thinkAloud.recognition = rec;
    v3State.thinkAloud.recording = true;

    rec.onresult = (ev) => {
      let interim = '';
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const seg = ev.results[i][0]?.transcript || '';
        if (ev.results[i].isFinal) {
          const clean = seg.trim();
          if (clean) {
            const prefix = `[${stageLabel}] `;
            v3State.thinkAloud.transcript = (v3State.thinkAloud.transcript ? v3State.thinkAloud.transcript + '\n' : '') + prefix + clean;
          }
        } else {
          interim += seg;
        }
      }
      v3State.thinkAloud.interimText = interim;
      const ta = document.getElementById('mock-think-aloud-input');
      if (ta) ta.value = v3State.thinkAloud.transcript;
      updateThinkAloudUi(stageLabel);
    };
    rec.onerror = () => {
      stopThinkAloudMic();
      updateThinkAloudUi(stageLabel);
    };
    rec.onend = () => {
      v3State.thinkAloud.recording = false;
      v3State.thinkAloud.interimText = '';
      updateThinkAloudUi(stageLabel);
    };
    try {
      rec.start();
    } catch (_) {
      stopThinkAloudMic();
    }
    updateThinkAloudUi(stageLabel);
  }

  function updateThinkAloudUi(stageLabel) {
    const flags = evalLivePillars(v3State.thinkAloud.transcript);
    const map = [
      ['ta-pill-constraints', flags.constraints],
      ['ta-pill-bigo', flags.bigO],
      ['ta-pill-tradeoff', flags.tradeoff],
      ['ta-pill-dryrun', flags.dryrun],
    ];
    for (const [id, ok] of map) {
      document.getElementById(id)?.classList.toggle('met', Boolean(ok));
    }
    const dot = document.getElementById('ta-mic-dot');
    const lbl = document.getElementById('ta-mic-label');
    if (dot) dot.classList.toggle('live', v3State.thinkAloud.recording);
    if (lbl) lbl.textContent = v3State.thinkAloud.recording ? `Listening (${stageLabel})... Stop` : 'Start Think-Aloud Mic';
    const interimEl = document.getElementById('ta-interim-caption');
    if (interimEl) interimEl.textContent = v3State.thinkAloud.interimText ? `Hearing: "${v3State.thinkAloud.interimText}"` : '';
  }

  async function gradeThinkAloud(prob) {
    if (!prob || v3State.thinkAloud.grading) return;
    v3State.thinkAloud.grading = true;
    const btn = document.getElementById('ta-grade-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Scoring...';
    }
    try {
      const bridge = B();
      const idPayload = prob.isCurated ? { problemId: prob.id } : { day: prob.day };
      const res = await bridge.apiPost('/api/grade-think-aloud', {
        ...idPayload,
        transcript: v3State.thinkAloud.transcript,
      });
      if (res && res.ok) {
        v3State.thinkAloud.grade = res;
        renderThinkAloudGradeCard();
      }
    } finally {
      v3State.thinkAloud.grading = false;
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Score Narration';
      }
    }
  }

  function renderThinkAloudGradeCard() {
    const out = document.getElementById('ta-grade-output');
    const g = v3State.thinkAloud.grade;
    if (!out || !g) return;
    const score = Number(g.communicationScore ?? 0);
    const pills = (g.pillars || []).map((pl) =>
      `<span class="pillar-pill${pl.met ? ' met' : ''} tabular">${esc(pl.name)}: ${Number(pl.score)}/${Number(pl.max)}</span>`
    ).join('');
    const tips = (g.missingPrompts || []).length
      ? `<ul style="margin:4px 0 0; padding-left:18px; font-size:11.5px; color:var(--fg-secondary);">${g.missingPrompts.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>`
      : '';
    out.style.display = 'flex';
    out.innerHTML =
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<span style="font-weight:650; font-size:12px;">Think-Aloud Communication Debrief</span>` +
      `<span class="stat-pill tabular" style="color:${score >= 75 ? 'var(--success)' : 'var(--warn)'};">Communication: ${score} / 100</span>` +
      `</div>` +
      `<div style="font-size:12px; color:var(--fg-secondary);">${esc(g.summary || '')}</div>` +
      `<div style="display:flex; gap:5px; flex-wrap:wrap;">${pills}</div>` +
      tips;
  }

  function onExamRendered(examState, panelEl) {
    if (!examState || !panelEl) return;
    if (!examState.mockActive || examState.subMode !== 'mock' || !examState.mockProblem) {
      stopThinkAloudMic();
      return;
    }
    const prob = examState.mockProblem;
    const pid = prob.isCurated ? String(prob.id) : `day-${prob.day}`;
    if (v3State.thinkAloud.problemId !== pid) {
      stopThinkAloudMic();
      v3State.thinkAloud.problemId = pid;
      v3State.thinkAloud.transcript = '';
      v3State.thinkAloud.grade = null;
    }

    const stageLabels = { 1: 'Clarify', 2: 'Plan & Big-O', 3: 'Code', 4: 'Edge Cases' };
    const curStage = stageLabels[examState.mockStage] || 'Interview';
    const hasSpeech = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
    const flags = evalLivePillars(v3State.thinkAloud.transcript);

    const cards = panelEl.querySelectorAll('.card');
    const mockCard = cards[cards.length - 1];
    if (!mockCard || mockCard.querySelector('#exam-think-aloud-bar')) return;

    const bar = document.createElement('div');
    bar.id = 'exam-think-aloud-bar';
    bar.className = 'think-aloud-box';
    bar.innerHTML =
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">` +
      `<span style="font-size:12px; font-weight:650; color:var(--fg);">Think-Aloud Interview Narration</span>` +
      `<span class="stat-pill">Stage: ${esc(curStage)}</span>` +
      `</div>` +
      `<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">` +
      (hasSpeech
        ? `<button type="button" id="ta-mic-btn" class="btn-subtle-accent" style="padding:3px 9px; font-size:11.5px;"><span id="ta-mic-dot" class="think-aloud-mic-dot${v3State.thinkAloud.recording ? ' live' : ''}"></span><span id="ta-mic-label">${v3State.thinkAloud.recording ? `Listening (${esc(curStage)})... Stop` : 'Start Think-Aloud Mic'}</span></button>`
        : `<span class="muted" style="font-size:11px;">Voice capture unsupported in this browser; type your narration below</span>`) +
      `<button type="button" id="ta-grade-btn" style="padding:3px 9px; font-size:11.5px;">Score Narration</button>` +
      `</div>` +
      `</div>` +
      `<div style="display:flex; gap:5px; flex-wrap:wrap;">` +
      `<span id="ta-pill-constraints" class="pillar-pill${flags.constraints ? ' met' : ''}">Constraints</span>` +
      `<span id="ta-pill-bigo" class="pillar-pill${flags.bigO ? ' met' : ''}">Big-O</span>` +
      `<span id="ta-pill-tradeoff" class="pillar-pill${flags.tradeoff ? ' met' : ''}">Trade-off</span>` +
      `<span id="ta-pill-dryrun" class="pillar-pill${flags.dryrun ? ' met' : ''}">Dry-Run</span>` +
      `</div>` +
      `<textarea id="mock-think-aloud-input" class="exam-textarea" style="min-height:66px; font-family:var(--font-sans); font-size:12px;" placeholder="Speak aloud with the mic or jot your verbal cues (constraints, brute-vs-optimal trade-off, Big-O, example trace)...">${esc(v3State.thinkAloud.transcript)}</textarea>` +
      `<div id="ta-interim-caption" class="muted" style="font-size:11px;"></div>` +
      `<div id="ta-grade-output" class="inner-box" style="display:none; flex-direction:column; gap:6px;"></div>`;
    mockCard.appendChild(bar);

    document.getElementById('ta-mic-btn')?.addEventListener('click', () => toggleThinkAloudMic(curStage));
    document.getElementById('ta-grade-btn')?.addEventListener('click', () => gradeThinkAloud(prob));
    document.getElementById('mock-think-aloud-input')?.addEventListener('input', (e) => {
      v3State.thinkAloud.transcript = e.target.value;
      updateThinkAloudUi(curStage);
    });
    if (v3State.thinkAloud.grade) {
      renderThinkAloudGradeCard();
    } else if (examState.mockFinalGrade && v3State.thinkAloud.transcript.trim()) {
      gradeThinkAloud(prob);
    }
  }

  /* ==========================================================================
     6. CROSS-DEVICE PRIVATE GITHUB GIST SYNC
     ========================================================================== */
  async function refreshGistStatus() {
    try {
      const res = await B()?.apiGet?.('/api/gist-sync/status');
      if (res && res.ok) {
        v3State.gist.configured = Boolean(res.configured);
        v3State.gist.gistId = String(res.gistId || '');
        v3State.gist.masked = String(res.masked || '');
        v3State.gist.lastSyncedAt = String(res.lastSyncedAt || '');
        updateGistToolbarDot();
      }
    } catch (_) {}
  }

  function updateGistToolbarDot() {
    const dot = document.getElementById('gist-sync-dot');
    if (dot) dot.classList.toggle('connected', v3State.gist.configured);
  }

  function renderGistModalContent() {
    const body = document.getElementById('gist-sync-modal-body');
    if (!body) return;
    const g = v3State.gist;
    const statusText = g.configured
      ? `Connected (${g.masked || 'token saved'})${g.lastSyncedAt ? ' | Last synced ' + g.lastSyncedAt : ''}`
      : 'Not connected yet';

    body.innerHTML =
      `<div class="inner-box" style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<span style="font-size:12px; font-weight:600; color:${g.configured ? 'var(--success)' : 'var(--fg-secondary)'};">${esc(statusText)}</span>` +
      (g.gistId
        ? `<a href="https://gist.github.com/${encodeURIComponent(g.gistId)}" target="_blank" rel="noopener noreferrer" class="ext-link" style="font-size:11.5px;">Open Private Gist ↗</a>`
        : '') +
      `</div>` +
      `<div style="font-size:12px; color:var(--fg-secondary); line-height:1.5;">` +
      `Keep solved problems, accepted submissions, notes, whiteboards, and flash drill streaks synchronised across desktop, Chromebook, and mobile using your own private GitHub Gist. ` +
      `<a href="https://github.com/settings/tokens/new?scopes=gist&description=AlgoStudioSync" target="_blank" rel="noopener noreferrer" class="ext-link">Create a gist-only token ↗</a>` +
      `</div>` +
      `<div style="display:flex; flex-direction:column; gap:8px;">` +
      `<label style="font-size:11.5px; font-weight:600;">GitHub Personal Access Token (gist scope only)` +
      `<input type="password" id="gist-token-input" class="compact-text-input" style="width:100%; margin-top:4px;" placeholder="${g.configured ? 'Saved locally (leave blank to reuse existing token)' : 'ghp_... or github_pat_...'}" autocomplete="off">` +
      `</label>` +
      `<label style="font-size:11.5px; font-weight:600;">Private Gist ID` +
      `<div style="display:flex; gap:6px; margin-top:4px;">` +
      `<input type="text" id="gist-id-input" class="compact-mono-input" style="flex:1;" value="${esc(g.gistId)}" placeholder="Leave blank on first device to create a new private Gist">` +
      (g.gistId ? `<button type="button" id="gist-copy-id-btn" style="padding:4px 9px; font-size:11.5px;">Copy ID</button>` : '') +
      `</div>` +
      `</label>` +
      `</div>` +
      (g.message
        ? `<div class="inner-box" style="border-left:3px solid ${g.isError ? 'var(--danger)' : 'var(--success)'}; font-size:12px; color:${g.isError ? 'var(--danger)' : 'var(--fg)'};">${esc(g.message)}</div>`
        : '') +
      `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap;">` +
      `<div style="display:flex; gap:6px; flex-wrap:wrap;">` +
      `<button type="button" id="gist-push-btn" class="btn-primary"${g.busy ? ' disabled' : ''}>${g.busy ? 'Syncing...' : 'Push & Merge'}</button>` +
      `<button type="button" id="gist-pull-btn" class="btn-subtle-accent"${g.busy ? ' disabled' : ''}>Pull & Merge</button>` +
      `</div>` +
      (g.configured ? `<button type="button" id="gist-disconnect-btn" style="color:var(--danger);"${g.busy ? ' disabled' : ''}>Disconnect</button>` : '') +
      `</div>`;

    document.getElementById('gist-push-btn')?.addEventListener('click', () => runGistAction('push'));
    document.getElementById('gist-pull-btn')?.addEventListener('click', () => runGistAction('pull'));
    document.getElementById('gist-disconnect-btn')?.addEventListener('click', () => runGistAction('disconnect'));
    document.getElementById('gist-copy-id-btn')?.addEventListener('click', () => {
      const idVal = document.getElementById('gist-id-input')?.value || v3State.gist.gistId;
      if (!idVal) return;
      if (navigator.clipboard?.writeText) navigator.clipboard.writeText(idVal).catch(() => B()?.copyTextFallback?.(idVal));
      else B()?.copyTextFallback?.(idVal);
      const b = document.getElementById('gist-copy-id-btn');
      if (b) { b.textContent = 'Copied'; setTimeout(() => { b.textContent = 'Copy ID'; }, 1400); }
    });
  }

  async function runGistAction(action) {
    if (v3State.gist.busy) return;
    const token = document.getElementById('gist-token-input')?.value?.trim() || '';
    const gistId = document.getElementById('gist-id-input')?.value?.trim() || '';
    v3State.gist.busy = true;
    v3State.gist.message = '';
    v3State.gist.isError = false;
    renderGistModalContent();

    try {
      const bridge = B();
      const res = await bridge.apiPost('/api/gist-sync', { action, token, gistId });
      if (!res || !res.ok) {
        v3State.gist.isError = true;
        v3State.gist.message = res?.error || 'GitHub Gist sync failed.';
      } else {
        v3State.gist.configured = Boolean(res.configured);
        v3State.gist.gistId = String(res.gistId || '');
        v3State.gist.masked = String(res.masked || '');
        v3State.gist.lastSyncedAt = String(res.lastSyncedAt || '');
        v3State.gist.isError = false;
        v3State.gist.message = res.summary || (action === 'disconnect' ? 'Disconnected GitHub Gist sync.' : 'Progress synchronised.');
        if (res.progress) {
          bridge.state.progress = res.progress;
          if (res.tags) bridge.state.tags = res.tags;
          if (res.spacedRepetition) bridge.state.spacedRepetition = res.spacedRepetition;
          bridge.renderHeaderStats();
          bridge.populateSelectors();
          bridge.renderRoadmapAndTags();
          bridge.updateSolvedIndicatorsForActiveDay();
          window.StudioV2?.onProgressUpdated?.();
          loadWhiteboardForProblem(bridge.currentProblem());
        }
        updateGistToolbarDot();
      }
    } catch (err) {
      v3State.gist.isError = true;
      v3State.gist.message = err?.message || String(err);
    } finally {
      v3State.gist.busy = false;
      renderGistModalContent();
    }
  }

  function openGistSyncModal() {
    const modal = document.getElementById('gist-sync-modal');
    if (!modal) return;
    modal.classList.add('open');
    renderGistModalContent();
    refreshGistStatus().then(renderGistModalContent);
  }

  function closeGistSyncModal() {
    document.getElementById('gist-sync-modal')?.classList.remove('open');
  }

  function mountGistSync() {
    const shortcutsBtn = document.getElementById('shortcuts-palette-btn');
    if (shortcutsBtn && shortcutsBtn.parentNode && !document.getElementById('gist-sync-btn')) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'icon-btn';
      btn.id = 'gist-sync-btn';
      btn.title = 'Synchronise progress across devices via your own private GitHub Gist';
      btn.innerHTML = `<span id="gist-sync-dot" class="gist-sync-dot"></span>Sync`;
      btn.addEventListener('click', openGistSyncModal);
      shortcutsBtn.parentNode.insertBefore(btn, shortcutsBtn);
    }

    if (!document.getElementById('gist-sync-modal')) {
      const backdrop = document.createElement('div');
      backdrop.id = 'gist-sync-modal';
      backdrop.className = 'gist-sync-backdrop';
      backdrop.setAttribute('role', 'dialog');
      backdrop.setAttribute('aria-modal', 'true');
      backdrop.setAttribute('aria-labelledby', 'gist-sync-modal-title');
      backdrop.innerHTML =
        `<div class="gist-sync-dialog">` +
        `<div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">` +
        `<h2 id="gist-sync-modal-title" style="margin:0; font-size:15px; font-weight:650;">Cross-Device Private GitHub Gist Sync</h2>` +
        `<button type="button" id="gist-sync-close-btn" style="padding:3px 9px; font-size:11.5px;">Close</button>` +
        `</div>` +
        `<div id="gist-sync-modal-body" style="display:flex; flex-direction:column; gap:10px;"></div>` +
        `</div>`;
      document.body.appendChild(backdrop);

      document.getElementById('gist-sync-close-btn')?.addEventListener('click', closeGistSyncModal);
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) closeGistSyncModal();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && backdrop.classList.contains('open')) {
          closeGistSyncModal();
        }
      });
    }
  }

  /* ==========================================================================
     LIFECYCLE & PUBLIC HOOKS
     ========================================================================== */
  function onActiveProblemRendered(p) {
    loadWhiteboardForProblem(p);
    const bigoCard = document.getElementById('bigo-bench-card');
    if (bigoCard) bigoCard.classList.remove('open');
  }

  function init() {
    if (v3State.initialized) return;
    v3State.initialized = true;
    injectStyles();
    mountVisualOverlayControls();
    mountWhiteboard();
    mountBigOPlotter();
    mountFlashDrillMode();
    mountGistSync();
    refreshGistStatus();
    if (B()?.currentProblem) {
      loadWhiteboardForProblem(B().currentProblem());
    }
  }

  window.StudioV3 = {
    init,
    onVisualiserFrame,
    onActiveProblemRendered,
    onCoachModeChanged,
    onExamRendered,
    openGistSyncModal,
    runBigOBenchmark,
    startNextFlashCard,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (window.AlgoStudioBridge) init();
    });
  } else if (window.AlgoStudioBridge) {
    init();
  }
})();
