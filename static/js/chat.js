/**
 * chat.js — fetch-based chat interface for Interview Prep Coach
 * No page reloads. Sends full message to POST /chat, appends reply to DOM.
 */

(function () {
  'use strict';

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const chatArea     = document.getElementById('chat-area');
  const messageList  = document.getElementById('message-list');
  const messageInput = document.getElementById('message-input');
  const sendBtn      = document.getElementById('send-btn');
  const loadingEl    = document.getElementById('loading-indicator');
  const errorBanner  = document.getElementById('chat-error-banner');
  const errorText    = document.getElementById('chat-error-text');
  const errorDismiss = document.getElementById('error-dismiss-btn');
  const tokenBar     = document.getElementById('token-bar');
  const tokenText    = document.getElementById('token-bar-text');
  const emptyState   = document.getElementById('chat-empty-state');

  const SESSION_ID = parseInt(chatArea.dataset.sessionId, 10);

  // ── Helpers ───────────────────────────────────────────────────────────────

  function scrollToBottom(smooth = true) {
    messageList.scrollTo({
      top: messageList.scrollHeight,
      behavior: smooth ? 'smooth' : 'instant',
    });
  }

  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function showError(msg) {
    errorText.textContent = msg;
    errorBanner.style.display = 'flex';
  }

  function hideError() {
    errorBanner.style.display = 'none';
    errorText.textContent = '';
  }

  function setLoading(isLoading) {
    sendBtn.disabled = isLoading || !messageInput.value.trim();
    messageInput.disabled = isLoading;
    loadingEl.style.display = isLoading ? 'flex' : 'none';
    loadingEl.setAttribute('aria-hidden', String(!isLoading));
  }

  function updateTokenBar(tokens, costUsd) {
    tokenBar.style.display = 'block';
    tokenText.textContent =
      `Last call — ${tokens.prompt.toLocaleString()} in · ` +
      `${tokens.completion.toLocaleString()} out · ` +
      `${tokens.total.toLocaleString()} total · ` +
      `$${costUsd.toFixed(8)}`;
  }

  // ── Render a message bubble into the DOM ─────────────────────────────────

  function appendMessage(role, content, timestamp) {
    const isUser = role === 'user';
    const time   = timestamp ? new Date(timestamp) : new Date();

    // Remove empty state on first message
    if (emptyState) emptyState.remove();

    const msgEl = document.createElement('div');
    msgEl.className = `message ${isUser ? 'message--user' : 'message--ai'}`;
    msgEl.dataset.role = role;

    if (isUser) {
      msgEl.innerHTML = `
        <div class="message-body">
          <div class="message-bubble">${escapeHtml(content)}</div>
          <div class="message-meta">
            <span class="meta-sender">You</span>
            <span class="meta-time">${formatTime(time)}</span>
          </div>
        </div>
        <div class="message-avatar message-avatar--user" aria-hidden="true">
          <span class="avatar-initials">You</span>
        </div>`;
    } else {
      // AI messages: render line breaks and basic markdown-like formatting
      msgEl.innerHTML = `
        <div class="message-avatar" aria-hidden="true">
          <span class="avatar-initials">AI</span>
        </div>
        <div class="message-body">
          <div class="message-bubble">${formatAiContent(content)}</div>
          <div class="message-meta">
            <span class="meta-sender">Coach</span>
            <span class="meta-time">${formatTime(time)}</span>
          </div>
        </div>`;
    }

    // Insert before the loading indicator
    messageList.insertBefore(msgEl, loadingEl);
    scrollToBottom();
  }

  // ── Simple XSS guard ─────────────────────────────────────────────────────
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ── Format AI content: preserve line breaks, bold **text**, escape rest ──
  function formatAiContent(str) {
    // Escape HTML first
    let safe = escapeHtml(str);
    // Convert **bold** to <strong>
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to <br>
    safe = safe.replace(/\n/g, '<br>');
    return safe;
  }

  // ── Auto-resize textarea ─────────────────────────────────────────────────
  function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
  }

  // ── Send message ─────────────────────────────────────────────────────────
  async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content || sendBtn.disabled) return;

    hideError();

    // Optimistically append user message
    appendMessage('user', content);

    // Reset input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Show loading
    setLoading(true);
    scrollToBottom();

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, message: content }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server error (${response.status})`);
      }

      // Append AI reply
      appendMessage('model', data.reply);

      // Update token bar
      if (data.tokens && data.cost_usd !== undefined) {
        updateTokenBar(data.tokens, data.cost_usd);
      }

    } catch (err) {
      showError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
      messageInput.focus();
    }
  }

  // ── Event listeners ───────────────────────────────────────────────────────

  // Enable send button only when there is content
  messageInput.addEventListener('input', function () {
    sendBtn.disabled = !this.value.trim();
    autoResize();
  });

  // Enter sends, Shift+Enter inserts newline
  messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  errorDismiss.addEventListener('click', hideError);

  // ── Init: scroll to bottom if there are existing messages ────────────────
  if (messageList.querySelectorAll('.message').length > 0) {
    scrollToBottom(false);
  }

  messageInput.focus();

})();
