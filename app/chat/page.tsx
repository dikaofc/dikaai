'use client';
import { useEffect, useRef, useState } from 'react';
import Icon from '../components/Icon';
import { ENGINE_SIDEBAR_EVENT } from '../components/Navbar';

type Msg = {
  role: 'user' | 'assistant';
  content: string;
  route?: string;
  time?: string;
  topic?: string;
};

const CHIPS = [
  { label: 'Fibonacci', icon: 'code', text: 'Write a fibonacci function' },
  { label: 'Binary Search', icon: 'search', text: 'Write a binary search in Python' },
  { label: 'Fix Error', icon: 'terminal', text: 'Fix this error: TypeError on line 5' },
  { label: 'Git Status', icon: 'folder', text: 'git status' },
  { label: 'Explain', icon: 'brain', text: 'Explain quicksort algorithm' },
  { label: 'Rust', icon: 'code', text: 'Write a Rust struct with methods' },
  { label: 'JS Debounce', icon: 'zap', text: 'Write a JavaScript debounce function' },
  { label: 'C++ Sort', icon: 'code', text: 'Write a C++ vector sort with lambda' },
];

const MEM = [
  { key: 'tasks', label: 'Total Tasks', icon: 'zap' },
  { key: 'rate', label: 'Success Rate', icon: 'check' },
  { key: 'episodes', label: 'Episodes', icon: 'clock' },
  { key: 'facts', label: 'Facts', icon: 'database' },
  { key: 'topics', label: 'Topics', icon: 'search' },
  { key: 'tokens', label: 'Tokens', icon: 'cpu' },
  { key: 'step', label: 'Model Step', icon: 'activity' },
  { key: 'vocab', label: 'Vocab', icon: 'layers' },
];

function escapeHtml(t: string): string {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}
function formatContent(raw: string): string {
  let html = escapeHtml(raw);
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  return html;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<Record<string, string | number>>({});
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function autoGrow() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  }
  useEffect(autoGrow, [input]);

  function scrollToBottom() {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }

  async function send(text: string) {
    if (isLoading) return;
    setIsLoading(true);
    setMessages((m) => [...m, { role: 'user', content: text }]);
    const typing: Msg = { role: 'assistant', content: '' };
    setMessages((m) => [...m, typing]);
    scrollToBottom();
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const d = await r.json();
      const reply: Msg = {
        role: 'assistant',
        content: d.response || d.reply || '',
        route: d.route,
        time: d.time,
        topic: d.topic,
      };
      setMessages((m) => [...m.slice(0, -1), reply]);
      loadStats();
    } catch (err) {
      const e = err as Error;
      setMessages((m) => [...m.slice(0, -1), { role: 'assistant', content: 'Error: ' + e.message }]);
    }
    setIsLoading(false);
    textareaRef.current?.focus();
  }

  function sendFromInput() {
    const t = input.trim();
    if (!t || isLoading) return;
    send(t);
    setInput('');
  }

  async function loadStats() {
    try {
      const r = await fetch('/api/stats');
      const d = await r.json();
      const header = document.getElementById('header-stats');
      if (header) header.textContent = `${d.db?.total || 0} tasks | ${d.status || 'idle'}`;
      const out: Record<string, string | number> = {};
      if (d.model) {
        out.step = d.model.step || 0;
        out.vocab = d.model.vocab_size || 0;
      }
      const e = d.engine || {};
      out.tasks = e.total || 0;
      out.rate = e.rate || '0%';
      out.episodes = e.episodes || 0;
      out.facts = e.facts || 0;
      out.topics = e.topics || 0;
      out.tokens = e.tokens || 0;
      setStats(out);
    } catch {
      /* ignore */
    }
  }
  useEffect(() => {
    loadStats();
    const id = setInterval(loadStats, 30000);
    return () => clearInterval(id);
  }, []);

  useEffect(scrollToBottom, [messages]);

  function toggleSidebar() {
    setSidebarOpen((s) => {
      const open = !s;
      document.body.classList.toggle('no-scroll', open);
      return open;
    });
  }
  useEffect(() => {
    function onToggle() {
      toggleSidebar();
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setSidebarOpen(false);
        document.body.classList.remove('no-scroll');
      }
    }
    window.addEventListener(ENGINE_SIDEBAR_EVENT, onToggle);
    document.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener(ENGINE_SIDEBAR_EVENT, onToggle);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  return (
    <div className="chat-wrap">
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'show' : ''}`}
        onClick={toggleSidebar}
      />

      <aside className={`chat-sidebar ${sidebarOpen ? 'open' : ''}`} id="sidebar">
        <div className="sidebar-title"><Icon name="layers" />Engine</div>
        <div className="mem-list">
          {MEM.map((mem) => (
            <div className="mem-item" key={mem.key}>
              <div className="mem-label"><Icon name={mem.icon} />{mem.label}</div>
              <div className="mem-val" id={`mem-${mem.key}`}>{stats[mem.key] ?? '-'}</div>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-main">
        <div className="chat-messages" id="messages" ref={messagesRef}>
          {messages.length === 0 && (
            <div className="welcome-box">
              <h2>DikaAI v3.2</h2>
              <p>AI Coding Agent with memory, context, multi-language code generation, and tools.</p>
              <div className="welcome-chips">
                {CHIPS.map((c) => (
                  <div className="welcome-chip" key={c.label} onClick={() => send(c.text)}>
                    <Icon name={c.icon} />{c.label}
                  </div>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div className={`msg-row ${msg.role === 'user' ? 'user' : 'ai'}`} key={i}>
              <div className={`msg-bubble ${msg.role === 'user' ? 'msg-user' : 'msg-ai'}`}
                dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }} />
              {(msg.route || msg.time || msg.topic) && (
                <div className="msg-meta">
                  {msg.route && <span className={`route-badge ${msg.route}`}>{msg.route}</span>}
                  {msg.time && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                      <Icon name="clock" size={11} />{msg.time}
                    </span>
                  )}
                  {msg.topic && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                      <Icon name="folder" size={11} />{msg.topic}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="typing-ind"><span /><span /><span /></div>
          )}
        </div>
        <div className="chat-input-area">
          <div className="chat-input-wrap">
            <textarea
              id="input"
              ref={textareaRef}
              value={input}
              placeholder="Ask DikaAI anything..."
              rows={1}
              autoFocus
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendFromInput(); } }}
            />
            <button className="send-btn" onClick={sendFromInput} disabled={isLoading} aria-label="Send">
              <Icon name="send" />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
