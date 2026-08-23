'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Icon from './components/Icon';
import { useToast } from './components/Toast';

type Stats = {
  db?: { total?: number; processed?: number; unique_chats?: number };
  model?: { step?: number; params?: number; vocab_size?: number };
  vocab_tokens?: number;
  status?: string;
  uptime?: number;
  toggles?: { auto_reply?: boolean; training?: boolean; scraping?: boolean };
  loss_chart?: { losses?: number[] };
  recent_messages?: string[];
  total_loss?: number;
  total_steps?: number;
  engine?: Record<string, unknown>;
};

function formatNum(n: number | undefined): string {
  n = n || 0;
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toString();
}
function formatTime(s: number | undefined): string {
  s = s || 0;
  if (s >= 3600) return Math.floor(s / 3600) + 'h ' + Math.floor((s % 3600) / 60) + 'm';
  return Math.floor(s / 60) + 'm';
}
function esc(t: string): string {
  return (t || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

const TOGGLES = [
  { key: 'auto_reply', label: 'Auto-Reply', icon: 'zap', desc: 'Balas otomatis di Telegram' },
  { key: 'training', label: 'Training', icon: 'cpu', desc: 'Model belajar dari data' },
  { key: 'scraping', label: 'Scraping', icon: 'refresh', desc: 'Ambil chat dari Telegram' },
] as const;

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [quick, setQuick] = useState('');
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; text: string }[]>([]);
  const [statusId, setStatusId] = useState('status-badge');
  const { toast, node } = useToast();
  const chartRef = useRef<HTMLCanvasElement>(null);

  async function fetchStats() {
    try {
      const r = await fetch('/api/stats');
      const d: Stats = await r.json();
      setStats(d);
      const badge = document.getElementById(statusId);
      if (badge) badge.textContent = (d.status || 'idle').toUpperCase();
      drawChart(d.loss_chart?.losses || []);
    } catch {
      /* ignore network errors */
    }
  }

  useEffect(() => {
    fetchStats();
    const id = setInterval(fetchStats, 10000);
    return () => clearInterval(id);
  }, []);

  function drawChart(losses: number[]) {
    const c = chartRef.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const w = c.offsetWidth || 600;
    const h = 200;
    c.width = w * dpr;
    c.height = h * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    if (!losses || losses.length < 2) {
      ctx.fillStyle = '#606078';
      ctx.font = '14px Inter';
      ctx.textAlign = 'center';
      ctx.fillText('Waiting for training data...', w / 2, h / 2);
      return;
    }
    const maxL = Math.max(...losses) * 1.1 || 1;
    ctx.strokeStyle = '#282838';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = (i / 4) * h;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
      ctx.fillStyle = '#606078';
      ctx.font = '10px Inter';
      ctx.textAlign = 'left';
      ctx.fillText((maxL - (i / 4) * maxL).toFixed(3), 4, y + 12);
    }
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, '#7c5cfc');
    grad.addColorStop(1, '#00d4aa');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = '#7c5cfc';
    ctx.shadowBlur = 6;
    ctx.beginPath();
    for (let i = 0; i < losses.length; i++) {
      const x = (i / (losses.length - 1)) * w;
      const y = h - (losses[i] / maxL) * h;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, 'rgba(124,92,252,0.15)');
    g.addColorStop(1, 'rgba(124,92,252,0)');
    ctx.fillStyle = g;
    ctx.fill();
  }

  async function quickChat() {
    const t = quick.trim();
    if (!t) return;
    setQuick('');
    setMessages((m) => [...m, { role: 'user', text: t }]);
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: t }),
      });
      const d = await r.json();
      setMessages((m) => [...m, { role: 'ai', text: d.reply || d.response || '(no reply)' }]);
    } catch {
      setMessages((m) => [...m, { role: 'ai', text: 'Error' }]);
    }
  }

  function exportCSV() {
    fetch('/api/export')
      .then((r) => r.blob())
      .then((b) => {
        const u = URL.createObjectURL(b);
        const a = document.createElement('a');
        a.href = u;
        a.download = 'dikaai_' + new Date().toISOString().slice(0, 10) + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(u);
        toast('CSV exported!');
      })
      .catch(() => toast('Export failed'));
  }

  const db = stats?.db || {};
  const m = stats?.model || {};
  const losses = stats?.loss_chart?.losses || [];
  const processed = db.processed || 0;
  const total = db.total || 0;
  const processPct = total ? Math.round((processed / total) * 100) : 0;
  const currentLoss = losses.length ? losses[losses.length - 1].toFixed(4) : '-';
  const avgLoss =
    stats && stats.total_loss !== undefined && stats.total_steps
      ? (stats.total_loss / stats.total_steps).toFixed(4)
      : '-';
  const recent = (stats?.recent_messages || []).slice().reverse();
  const t = stats?.toggles || {};

  return (
    <div className="container">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><Icon name="chat" /></div>
          <div className="stat-label">Messages</div>
          <div className="stat-value">{formatNum(db.total)}</div>
          <div className="stat-sub">{(db.unique_chats || 0)} chats</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Icon name="check" /></div>
          <div className="stat-label">Processed</div>
          <div className="stat-value">{formatNum(db.processed)}</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${processPct}%` }} />
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Icon name="activity" /></div>
          <div className="stat-label">Steps</div>
          <div className="stat-value">{formatNum(m.step)}</div>
          <div className="stat-sub">{formatNum(m.params)} params</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Icon name="layers" /></div>
          <div className="stat-label">Loss</div>
          <div className="stat-value">{currentLoss}</div>
          <div className="stat-sub">avg: {avgLoss}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Icon name="database" /></div>
          <div className="stat-label">Vocab</div>
          <div className="stat-value">{stats?.vocab_tokens || m.vocab_size || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Icon name="clock" /></div>
          <div className="stat-label">Uptime</div>
          <div className="stat-value">{formatTime(stats?.uptime)}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head"><Icon name="zap" />Status</div>
          <div className="panel-body">
            <div className="toggle-group">
              {TOGGLES.map((tg) => (
                <div className="toggle-row" key={tg.key}>
                  <div className="toggle-info">
                    <div className="toggle-label"><Icon name={tg.icon} />{tg.label}</div>
                    <div className="toggle-desc">{tg.desc}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 8px var(--success)' }} />
                    <span style={{ fontSize: 11, color: 'var(--success)', fontWeight: 600 }}>ON</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span style={{ display: 'flex', alignItems: 'center' }}><Icon name="chat" />Quick Chat</span>
            <Link className="open-full" href="/chat">Open Full <Icon name="external" /></Link>
          </div>
          <div className="panel-body np">
            <div className="quick-chat-box">
              <div className="quick-chat-msgs">
                {messages.map((mm, i) => (
                  <div key={i} className={`q-msg ${mm.role}`}>{mm.text}</div>
                ))}
              </div>
              <div className="quick-chat-input">
                <input
                  type="text"
                  value={quick}
                  placeholder="Quick ask..."
                  onChange={(e) => setQuick(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') quickChat(); }}
                />
                <button onClick={quickChat}><Icon name="send" /></button>
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span style={{ display: 'flex', alignItems: 'center' }}><Icon name="message" />Recent Messages</span>
            <span style={{ color: 'var(--primary-light)', fontSize: 12 }}>{recent.length}</span>
          </div>
          <div className="panel-body">
            <div className="msg-list">
              {recent.length === 0 && <div style={{ color: 'var(--text-3)', fontSize: 12 }}>No messages yet</div>}
              {recent.map((msg, i) => (
                <div className="msg-item" key={i}>
                  <Icon name="message" size={12} />
                  <span dangerouslySetInnerHTML={{ __html: esc(msg) }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <span style={{ display: 'flex', alignItems: 'center' }}><Icon name="chart" />Training Loss</span>
          <span style={{ color: 'var(--primary-light)', fontSize: 12 }}>{losses.length} points</span>
          <button className="export-btn" onClick={exportCSV}>
            <Icon name="download" /><span>Export</span>
          </button>
        </div>
        <div className="panel-body">
          <canvas ref={chartRef} id="lossChart" />
        </div>
      </div>

      {node}
    </div>
  );
}
