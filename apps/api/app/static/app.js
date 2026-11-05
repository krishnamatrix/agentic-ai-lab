// ==========================================================================
// AGENTIC CRM ASSISTANT - CLIENT APPLICATION
// ==========================================================================

(function () {
  'use strict';

  // State
  let currentConversationId = 'demo-001';
  let currentUserId = 'default-user';
  let isThinking = false;
  let sampleQueriesData = [];

  // DOM Elements
  const sessionSelect = document.getElementById('session-select');
  const btnNewSession = document.getElementById('btn-new-session');
  const btnResetSession = document.getElementById('btn-reset-session');
  const btnToggleInspector = document.getElementById('btn-toggle-inspector');
  const btnCloseInspector = document.getElementById('btn-close-inspector');
  const inspectorPane = document.getElementById('inspector-pane');
  const chipsScroll = document.getElementById('chips-scroll');
  const starterGrid = document.getElementById('starter-grid');
  const messagesContainer = document.getElementById('messages-container');
  const messagesStream = document.getElementById('messages-stream');
  const welcomeCard = document.getElementById('welcome-card');
  const typingIndicator = document.getElementById('typing-indicator');
  const typingActivity = document.getElementById('typing-activity');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const btnSend = document.getElementById('btn-send');
  const inputSessionTag = document.getElementById('input-session-tag');
  const headerMemCount = document.getElementById('header-mem-count');
  const userMemoriesCountBadge = document.getElementById('user-memories-count-badge');
  const userMemoryItemsList = document.getElementById('user-memory-items-list');
  const convMemoriesCountBadge = document.getElementById('conv-memories-count-badge');
  const convMemoryItemsList = document.getElementById('conv-memory-items-list');
  const summaryStatusChip = document.getElementById('summary-status-chip');
  const summaryBox = document.getElementById('summary-box');
  const historyCountBadge = document.getElementById('history-count-badge');
  const memoryHistoryList = document.getElementById('memory-history-list');
  const toastContainer = document.getElementById('toast-container');

  // ------------------------------------------------------------------------
  // Initialize
  // ------------------------------------------------------------------------
  async function init() {
    setupEventListeners();
    await loadSampleQueries();
    await switchSession(currentConversationId);
  }

  // ------------------------------------------------------------------------
  // Event Listeners
  // ------------------------------------------------------------------------
  function setupEventListeners() {
    // Session change
    sessionSelect.addEventListener('change', (e) => {
      switchSession(e.target.value);
    });

    // New Session
    btnNewSession.addEventListener('click', () => {
      const name = prompt('Enter a new session ID:', `session-${Date.now().toString().slice(-4)}`);
      if (name && name.trim()) {
        const cleanId = name.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
        addSessionOption(cleanId);
        switchSession(cleanId);
        showToast(`Created session: ${cleanId}`, 'success');
      }
    });

    // Reset Session
    btnResetSession.addEventListener('click', async () => {
      if (confirm(`Are you sure you want to clear all messages and memories for session '${currentConversationId}'?`)) {
        await resetSession(currentConversationId);
      }
    });

    // Toggle Inspector
    btnToggleInspector.addEventListener('click', () => {
      inspectorPane.classList.toggle('collapsed');
    });

    btnCloseInspector.addEventListener('click', () => {
      inspectorPane.classList.add('collapsed');
    });

    // Auto-expanding textarea & key submission
    messageInput.addEventListener('input', () => {
      messageInput.style.height = 'auto';
      messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + 'px';
    });

    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    // Chat Form Submit
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = messageInput.value.trim();
      if (!text || isThinking) return;

      messageInput.value = '';
      messageInput.style.height = 'auto';
      await sendMessage(text);
    });
  }

  // ------------------------------------------------------------------------
  // Session Management
  // ------------------------------------------------------------------------
  function addSessionOption(sessionId) {
    const exists = Array.from(sessionSelect.options).some(opt => opt.value === sessionId);
    if (!exists) {
      const option = document.createElement('option');
      option.value = sessionId;
      option.textContent = sessionId;
      sessionSelect.appendChild(option);
    }
  }

  async function switchSession(sessionId) {
    currentConversationId = sessionId;
    sessionSelect.value = sessionId;
    if (inputSessionTag) inputSessionTag.textContent = sessionId;

    // Fetch conversation state
    try {
      const res = await fetch(`/api/conversations/${sessionId}?user_id=${encodeURIComponent(currentUserId)}`);
      if (res.ok) {
        const data = await res.json();
        renderConversationHistory(data.history || []);
        updateInspectorState(data.user_memories || [], data.conversation_memories || [], data.summary, data.memory_histories || []);
      } else {
        renderConversationHistory([]);
        updateInspectorState([], [], null, []);
      }
    } catch (err) {
      console.warn('Failed to fetch conversation history:', err);
      renderConversationHistory([]);
      updateInspectorState([], [], null, []);
    }
  }

  async function resetSession(sessionId) {
    try {
      const res = await fetch(`/api/conversations/${sessionId}/reset`, { method: 'POST' });
      if (res.ok) {
        renderConversationHistory([]);
        updateInspectorState([], [], null, []);
        showToast(`Session '${sessionId}' reset successfully`, 'info');
      }
    } catch (err) {
      showToast('Failed to reset session', 'error');
    }
  }

  // ------------------------------------------------------------------------
  // Sample Queries Loading
  // ------------------------------------------------------------------------
  async function loadSampleQueries() {
    try {
      const res = await fetch('/api/sample-queries');
      if (res.ok) {
        sampleQueriesData = await res.json();
        renderPromptChips(sampleQueriesData);
        renderStarterPrompts(sampleQueriesData);
      }
    } catch (err) {
      console.warn('Could not load sample queries', err);
    }
  }

  function renderPromptChips(categories) {
    chipsScroll.innerHTML = '';
    categories.forEach(cat => {
      cat.queries.forEach(query => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'prompt-chip';
        chip.innerHTML = `<span class="chip-icon">✦</span><span>${escapeHtml(query)}</span>`;
        chip.addEventListener('click', () => {
          messageInput.value = query;
          messageInput.focus();
        });
        chipsScroll.appendChild(chip);
      });
    });
  }

  function renderStarterPrompts(categories) {
    starterGrid.innerHTML = '';
    categories.forEach(cat => {
      const card = document.createElement('div');
      card.className = 'starter-btn';
      card.innerHTML = `
        <div class="starter-title">${escapeHtml(cat.category)}</div>
        <div class="starter-prompt">"${escapeHtml(cat.queries[0])}"</div>
      `;
      card.addEventListener('click', () => {
        messageInput.value = cat.queries[0];
        messageInput.focus();
      });
      starterGrid.appendChild(card);
    });
  }

  // ------------------------------------------------------------------------
  // Sending Message & Agent Chat
  // ------------------------------------------------------------------------
  async function sendMessage(text) {
    welcomeCard.style.display = 'none';

    // Append User Message to UI
    appendMessage('user', text);

    // Show Thinking Indicator
    setThinking(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          conversation_id: currentConversationId,
          user_id: currentUserId,
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();

      // Append Assistant Message
      appendMessage('assistant', data.reply);

      // Update Inspector State (Memories, Summary & History)
      updateInspectorState(data.user_memories || [], data.conversation_memories || [], data.summary, data.memory_histories || []);

    } catch (error) {
      appendMessage('assistant', `⚠️ **Error communicating with agent:**\n${error.message}`);
      showToast(error.message, 'error');
    } finally {
      setThinking(false);
    }
  }

  function setThinking(active) {
    isThinking = active;
    btnSend.disabled = active;
    typingIndicator.style.display = active ? 'flex' : 'none';

    if (active) {
      const activities = [
        'Analyzing query & extracting durable memory...',
        'Checking CRM database (companies, people, interactions)...',
        'Performing semantic vector embedding search...',
        'Synthesizing final response...'
      ];
      let actIdx = 0;
      if (typingActivity) typingActivity.textContent = activities[0];
      const interval = setInterval(() => {
        if (!isThinking) {
          clearInterval(interval);
          return;
        }
        actIdx = (actIdx + 1) % activities.length;
        if (typingActivity) typingActivity.textContent = activities[actIdx];
      }, 2400);

      scrollToBottom();
    }
  }

  // ------------------------------------------------------------------------
  // Message Rendering
  // ------------------------------------------------------------------------
  function renderConversationHistory(messages) {
    messagesStream.innerHTML = '';
    if (!messages || messages.length === 0) {
      welcomeCard.style.display = 'block';
    } else {
      welcomeCard.style.display = 'none';
      messages.forEach(msg => {
        appendMessage(msg.role, msg.content, false);
      });
    }
    scrollToBottom();
  }

  function appendMessage(role, content, animate = true) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user' 
      ? '<span>You</span>' 
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMarkdown(content);

    const meta = document.createElement('div');
    meta.className = 'message-meta';
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    meta.innerHTML = `
      <span>${timeStr}</span>
      <button class="copy-btn" title="Copy text">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span>Copy</span>
      </button>
    `;

    meta.querySelector('.copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(content);
      showToast('Copied to clipboard', 'info');
    });

    bubble.appendChild(meta);

    if (role === 'user') {
      row.appendChild(bubble);
      row.appendChild(avatar);
    } else {
      row.appendChild(avatar);
      row.appendChild(bubble);
    }

    messagesStream.appendChild(row);
    scrollToBottom();
  }

  function scrollToBottom() {
    setTimeout(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 50);
  }

  // ------------------------------------------------------------------------
  // Inspector Panel Updates
  // ------------------------------------------------------------------------
  function updateInspectorState(userMemories = [], convMemories = [], summary = null, memoryHistories = []) {
    // 1a. User Memories
    const userCount = userMemories.length;
    if (headerMemCount) headerMemCount.textContent = userCount + convMemories.length;
    if (userMemoriesCountBadge) userMemoriesCountBadge.textContent = `${userCount} ${userCount === 1 ? 'item' : 'items'}`;

    if (userMemoryItemsList) {
      if (userCount === 0) {
        userMemoryItemsList.innerHTML = `<div class="empty-state-hint">No user memories yet. Share a lasting preference to populate this.</div>`;
      } else {
        userMemoryItemsList.innerHTML = '';
        userMemories.forEach(mem => renderMemoryItem(mem, userMemoryItemsList));
      }
    }

    // 1b. Conversation Memories
    const convCount = convMemories.length;
    if (convMemoriesCountBadge) convMemoriesCountBadge.textContent = `${convCount} ${convCount === 1 ? 'item' : 'items'}`;

    if (convMemoryItemsList) {
      if (convCount === 0) {
        convMemoryItemsList.innerHTML = `<div class="empty-state-hint">No conversation memories yet. Try "For this discussion, call this Project Phoenix."</div>`;
      } else {
        convMemoryItemsList.innerHTML = '';
        convMemories.forEach(mem => renderMemoryItem(mem, convMemoryItemsList));
      }
    }

    // 2. Memory History
    const histCount = memoryHistories.length;
    if (historyCountBadge) historyCountBadge.textContent = `${histCount} ${histCount === 1 ? 'event' : 'events'}`;

    if (memoryHistoryList) {
      if (histCount === 0) {
        memoryHistoryList.innerHTML = `<div class="empty-state-hint">No memory operations yet. Interact with the agent to see history here.</div>`;
      } else {
        memoryHistoryList.innerHTML = '';
        // Show newest first
        [...memoryHistories].reverse().forEach(entry => {
          const opClass = `hist-op-${entry.operation}`;
          const opLabel = entry.operation.toUpperCase();
          const ts = entry.timestamp
            ? new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            : '';
          const hasDiff = entry.operation === 'update' && entry.previous_value !== null;
          const diffHtml = hasDiff
            ? `<div class="hist-diff">
                 <span class="hist-prev">${escapeHtml(String(entry.previous_value))}</span>
                 <span class="hist-arrow">\u2192</span>
                 <span class="hist-next">${escapeHtml(String(entry.new_value))}</span>
               </div>`
            : entry.new_value !== null
              ? `<div class="hist-value">${escapeHtml(String(entry.new_value))}</div>`
              : '';

          const item = document.createElement('div');
          item.className = 'history-item';
          item.innerHTML = `
            <div class="history-item-top">
              <span class="hist-op-badge ${opClass}">${opLabel}</span>
              <span class="hist-key">${escapeHtml(entry.key)}</span>
              <span class="hist-ts">${ts}</span>
            </div>
            ${diffHtml}
          `;
          memoryHistoryList.appendChild(item);
        });
      }
    }

    // 3. Summary
    if (summary && summary.trim()) {
      if (summaryStatusChip) { summaryStatusChip.textContent = 'Active'; summaryStatusChip.className = 'status-chip active'; }
      if (summaryBox) { summaryBox.className = 'summary-box active'; summaryBox.textContent = summary; }
    } else {
      if (summaryStatusChip) { summaryStatusChip.textContent = 'Empty'; summaryStatusChip.className = 'status-chip'; }
      if (summaryBox) { summaryBox.className = 'summary-box'; summaryBox.innerHTML = `<span class="empty-state-hint">No compaction needed yet. Appears after multiple conversation turns.</span>`; }
    }
  }

  function renderMemoryItem(mem, container) {
    const item = document.createElement('div');
    item.className = 'memory-item';
    const typeClass = `type-${(mem.type || 'preference').toLowerCase()}`;
    item.innerHTML = `
      <div class="memory-item-top">
        <span class="memory-type-badge ${typeClass}">${escapeHtml(mem.type || 'memory')}</span>
        <span class="memory-conf">${Math.round((mem.confidence || 1.0) * 100)}% conf</span>
      </div>
      <div class="memory-key">${escapeHtml(mem.key)}</div>
      <div class="memory-val">${escapeHtml(mem.value)}</div>
    `;
    container.appendChild(item);
  }

  // ------------------------------------------------------------------------
  // Helper: Markdown Formatter
  // ------------------------------------------------------------------------
  function formatMarkdown(text) {
    if (!text) return '';
    let out = escapeHtml(text);

    // Bold: **text**
    out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    out = out.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Inline Code: `code`
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bullet lists: - item or * item
    out = out.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    out = out.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

    // Line breaks to paragraphs
    const paragraphs = out.split(/\n\n+/);
    return paragraphs.map(p => {
      if (p.startsWith('<ul>')) return p;
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');
  }

  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(40px)';
      toast.style.transition = 'all 200ms ease';
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  // Run on page load
  window.addEventListener('DOMContentLoaded', init);
})();
