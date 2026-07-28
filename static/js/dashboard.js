/**
 * dashboard.js — auto-refreshes usage stats for the current session.
 * The dashboard already renders server-side; this script auto-refreshes
 * the stat cards every 30 seconds so the user sees live updates without
 * a manual page reload.
 */

(function () {
  'use strict';

  // sessionId is injected by the template as a global var
  if (typeof sessionId === 'undefined') return;

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const elRequests     = document.getElementById('total-requests');
  const elInputTokens  = document.getElementById('total-input-tokens');
  const elOutputTokens = document.getElementById('total-output-tokens');
  const elCost         = document.getElementById('total-cost');
  const tableBody      = document.getElementById('usage-table-body');

  // ── Helpers ───────────────────────────────────────────────────────────────
  function fmt(n) {
    return Number(n).toLocaleString();
  }

  function fmtCost(n) {
    return '$' + Number(n).toFixed(6);
  }

  function fmtCostFull(n) {
    return '$' + Number(n).toFixed(8);
  }

  function fmtTime(isoString) {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return isoString;
    }
  }

  // ── Refresh stats from /api/usage ────────────────────────────────────────
  async function refreshStats() {
    try {
      const res  = await fetch(`/api/usage?session_id=${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();

      const agg = data.aggregates || {};

      // Update summary cards
      if (elRequests)     elRequests.textContent     = fmt(agg.total_requests || 0);
      if (elInputTokens)  elInputTokens.textContent  = fmt(agg.total_input_tokens || 0);
      if (elOutputTokens) elOutputTokens.textContent = fmt(agg.total_output_tokens || 0);
      if (elCost)         elCost.textContent         = fmtCost(agg.total_cost_usd || 0);

      // Rebuild table rows
      if (tableBody && Array.isArray(data.calls)) {
        tableBody.innerHTML = data.calls.map(function (call, i) {
          return `<tr>
            <td class="td-index">${i + 1}</td>
            <td class="td-time">${fmtTime(call.created_at)}</td>
            <td class="td-num">${fmt(call.prompt_tokens)}</td>
            <td class="td-num">${fmt(call.completion_tokens)}</td>
            <td class="td-num td-total">${fmt(call.total_tokens)}</td>
            <td class="td-cost">${fmtCostFull(call.estimated_cost_usd)}</td>
          </tr>`;
        }).join('');

        // If table was hidden because empty, show it now
        const tableEmpty = document.getElementById('table-empty');
        if (tableEmpty && data.calls.length > 0) tableEmpty.style.display = 'none';
      }

    } catch (err) {
      // Silent fail — don't disrupt the user
      console.warn('Dashboard refresh failed:', err.message);
    }
  }

  // ── Auto-refresh every 30 seconds ────────────────────────────────────────
  refreshStats(); // immediate on load
  setInterval(refreshStats, 30000);

})();
