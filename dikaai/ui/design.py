"""DikaAI Design System - Neobrutalism + Liquid + Mobile-First"""

# SVG Icons (no emojis)
ICONS = {
    'brain': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"/><path d="M9 21h6"/><path d="M12 6v4"/></svg>',
    'chart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m7 16 4-4 4 4 5-5"/></svg>',
    'chat': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    'code': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    'settings': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    'zap': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    'send': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
    'x': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    'clock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    'database': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    'layers': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    'terminal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
    'folder': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    'cpu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
    'activity': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    'users': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'shield': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    'key': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
    'copy': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    'external': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
    'arrow_right': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    'message': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    'trash': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    'refresh': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    'lock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    'unlock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
}

# CSS Variables for Neobrutalism + Liquid Design
CSS_VARS = """
:root {
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --surface-2: #252525;
    --surface-3: #303030;
    --border: #3a3a3a;
    --text: #f0f0f0;
    --text-2: #999;
    --text-3: #666;
    --primary: #7c3aed;
    --primary-light: #a78bfa;
    --primary-dark: #5b21b6;
    --primary-bg: #7c3aed15;
    --accent: #06b6d4;
    --accent-bg: #06b6d415;
    --success: #10b981;
    --success-bg: #10b98115;
    --warning: #f59e0b;
    --warning-bg: #f59e0b15;
    --danger: #ef4444;
    --danger-bg: #ef444415;
    --radius: 16px;
    --radius-sm: 10px;
    --radius-xs: 6px;
    --shadow: 0 4px 20px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 40px rgba(0,0,0,0.4);
    --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    --font: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    --mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
}
"""

# Base styles
BASE_CSS = CSS_VARS + """
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
}
a { color: var(--primary-light); text-decoration: none; }
a:hover { color: var(--primary); }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-3); }

/* Utility */
.container { max-width: 1200px; margin: 0 auto; padding: 0 16px; }
@media(min-width:768px) { .container { padding: 0 24px; } }
"""

# Button styles
BUTTON_CSS = """
.btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px; border-radius: var(--radius-sm);
    font-family: var(--font); font-size: 14px; font-weight: 600;
    border: 2px solid transparent; cursor: pointer;
    transition: var(--transition); white-space: nowrap;
}
.btn:active { transform: scale(0.97); }
.btn-primary { background: var(--primary); color: white; border-color: var(--primary); }
.btn-primary:hover { background: var(--primary-dark); }
.btn-ghost { background: transparent; color: var(--text-2); border-color: var(--border); }
.btn-ghost:hover { background: var(--surface-2); color: var(--text); border-color: var(--text-3); }
.btn-icon {
    width: 40px; height: 40px; padding: 0; justify-content: center;
    border-radius: var(--radius-sm);
}
.btn svg { width: 18px; height: 18px; flex-shrink: 0; }
"""

# Card styles
CARD_CSS = """
.card {
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    transition: var(--transition);
}
.card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: var(--shadow); }
.card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    font-size: 14px; font-weight: 600;
}
.card-body { padding: 20px; }
.card-body.no-pad { padding: 0; }
"""

# Input styles
INPUT_CSS = """
.input {
    width: 100%; padding: 12px 16px;
    background: var(--surface-2); border: 2px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text); font-family: var(--font); font-size: 14px;
    transition: var(--transition); outline: none;
}
.input:focus { border-color: var(--primary); background: var(--surface); }
.input::placeholder { color: var(--text-3); }
textarea.input { resize: none; min-height: 44px; max-height: 200px; line-height: 1.5; }
"""

# Toggle switch
TOGGLE_CSS = """
.toggle { position: relative; width: 48px; height: 26px; cursor: pointer; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; position: absolute; }
.toggle-track {
    position: absolute; inset: 0;
    background: var(--surface-3); border: 2px solid var(--border);
    border-radius: 13px; transition: var(--transition);
}
.toggle input:checked + .toggle-track { background: var(--primary); border-color: var(--primary); }
.toggle-thumb {
    position: absolute; top: 3px; left: 3px;
    width: 18px; height: 18px;
    background: white; border-radius: 50%;
    transition: var(--transition);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.toggle input:checked ~ .toggle-thumb { transform: translateX(22px); }
"""

# Stat card
STAT_CSS = """
.stat {
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    text-align: center;
    transition: var(--transition);
}
.stat:hover { border-color: var(--primary); transform: translateY(-2px); }
.stat-icon {
    width: 40px; height: 40px; margin: 0 auto 12px;
    display: flex; align-items: center; justify-content: center;
    background: var(--primary-bg); border-radius: var(--radius-sm);
    color: var(--primary-light);
}
.stat-icon svg { width: 20px; height: 20px; }
.stat-label { font-size: 11px; font-weight: 600; color: var(--text-3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.stat-value { font-size: 28px; font-weight: 700; color: var(--text); }
.stat-sub { font-size: 12px; color: var(--text-3); margin-top: 4px; }
"""

# Message bubble
BUBBLE_CSS = """
.bubble {
    padding: 14px 18px;
    border-radius: var(--radius);
    line-height: 1.6;
    font-size: 14px;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-width: 85%;
    animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.bubble-user {
    background: var(--primary);
    color: white;
    border-bottom-right-radius: 4px;
    margin-left: auto;
}
.bubble-ai {
    background: var(--surface-2);
    color: var(--text);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
}
.bubble pre {
    background: var(--bg);
    padding: 12px;
    border-radius: var(--radius-xs);
    overflow-x: auto;
    margin: 8px 0;
    border: 1px solid var(--border);
}
.bubble pre code { font-family: var(--mono); font-size: 13px; }
.bubble code {
    background: var(--bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 13px;
}
"""

# Route tag
ROUTE_CSS = """
.route-tag {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px;
}
.route-code { background: var(--primary-bg); color: var(--primary-light); }
.route-tool { background: var(--success-bg); color: var(--success); }
.route-reason { background: var(--warning-bg); color: var(--warning); }
.route-search { background: var(--accent-bg); color: var(--accent); }
.route-chat { background: var(--surface-3); color: var(--text-2); }
"""

# Progress bar
PROGRESS_CSS = """
.progress { width: 100%; height: 6px; background: var(--surface-3); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--primary-light)); border-radius: 3px; transition: width 0.5s ease; }
"""

# Responsive grid
GRID_CSS = """
.grid { display: grid; gap: 16px; }
.grid-2 { grid-template-columns: 1fr; }
.grid-3 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
@media(min-width:768px) {
    .grid-2 { grid-template-columns: 1fr 1fr; }
}
"""

# Mobile nav
NAV_CSS = """
.nav-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: var(--surface);
    border-top: 2px solid var(--border);
    display: flex; justify-content: space-around;
    padding: 8px 0 calc(8px + env(safe-area-inset-bottom));
    z-index: 100;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}
.nav-item {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    padding: 6px 16px; border-radius: var(--radius-sm);
    color: var(--text-3); font-size: 10px; font-weight: 600;
    transition: var(--transition); text-decoration: none;
    -webkit-tap-highlight-color: transparent;
}
.nav-item.active { color: var(--primary-light); }
.nav-item svg { width: 22px; height: 22px; }
@media(min-width:768px) { .nav-bar { display: none; } }
"""

# Header
HEADER_CSS = """
.header {
    position: sticky; top: 0; z-index: 50;
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    padding: 12px 16px;
    display: flex; align-items: center; gap: 12px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}
.header-logo {
    display: flex; align-items: center; gap: 8px;
    font-size: 18px; font-weight: 700;
    color: var(--primary-light);
}
.header-logo svg { width: 24px; height: 24px; }
.header-nav { display: none; gap: 4px; margin-left: 16px; }
.header-nav a {
    padding: 6px 14px; border-radius: var(--radius-sm);
    font-size: 13px; font-weight: 500; color: var(--text-2);
    transition: var(--transition);
}
.header-nav a:hover { background: var(--surface-2); color: var(--text); }
.header-nav a.active { background: var(--primary-bg); color: var(--primary-light); }
.header-status {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; color: var(--success); font-weight: 500;
}
.header-status::before {
    content: ''; width: 8px; height: 8px;
    background: var(--success); border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.header-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }
@media(min-width:768px) {
    .header-nav { display: flex; }
    .header { padding: 12px 24px; }
}
"""

# Toast
TOAST_CSS = """
.toast {
    position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
    background: var(--surface-2); border: 2px solid var(--border);
    color: var(--text); padding: 12px 20px;
    border-radius: var(--radius-sm);
    font-size: 13px; font-weight: 500;
    box-shadow: var(--shadow-lg);
    opacity: 0; transition: opacity 0.3s ease;
    pointer-events: none; z-index: 200;
    max-width: 90vw; text-align: center;
}
.toast.show { opacity: 1; }
@media(min-width:768px) { .toast { bottom: 24px; } }
"""
