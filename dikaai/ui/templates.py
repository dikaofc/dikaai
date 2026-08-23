"""DikaAI UI Templates - Neobrutalism + Liquid Design System
All pages: Dashboard, Chat, API Docs
Mobile-first, Android-optimized, SVG icons (no emojis)
"""

# SVG icon helper
def icon(name, size=20):
    icons = {
        'brain': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a5 5 0 0 1 5 5c0 1.8-1 3.4-2.4 4.3A5 5 0 0 1 14 14v1h-4v-1a5 5 0 0 1-2.6-2.7C6 10.4 5 8.8 5 7a5 5 0 0 1 5-5z"/><path d="M9 19h6"/><path d="M12 2v3"/></svg>',
        'chart': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m7 16 4-4 4 4 5-5"/></svg>',
        'chat': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
        'message': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
        'arrow_right': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
        'code': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
        'download': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        'settings': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
        'zap': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        'send': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
        'menu': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
        'x': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        'check': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
        'clock': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        'database': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
        'layers': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
        'terminal': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
        'folder': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
        'search': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        'cpu': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/></svg>',
        'activity': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
        'users': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        'external': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
        'refresh': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
        'trash': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
        'lock': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        'key': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
        'copy': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    }
    return icons.get(name, '')

# ============================================================
# DESIGN SYSTEM CSS
# ============================================================

DESIGN_CSS = """
:root{
  --bg:#0c0c14;
  --surface:#16161f;
  --surface-2:#1e1e2a;
  --surface-3:#282838;
  --border:#2d2d40;
  --border-strong:#3a3a55;
  --text:#ededf0;
  --text-2:#9494a8;
  --text-3:#606078;
  --primary:#7c5cfc;
  --primary-light:#a78bfa;
  --primary-dark:#5b3cc4;
  --primary-bg:rgba(124,92,252,0.08);
  --primary-border:rgba(124,92,252,0.3);
  --accent:#00d4aa;
  --accent-bg:rgba(0,212,170,0.08);
  --success:#00d4aa;
  --success-bg:rgba(0,212,170,0.08);
  --warning:#fbbf24;
  --warning-bg:rgba(251,191,36,0.08);
  --danger:#f87171;
  --danger-bg:rgba(248,113,113,0.08);
  --radius:18px;
  --radius-sm:12px;
  --radius-xs:8px;
  --shadow-sm:0 2px 8px rgba(0,0,0,0.2);
  --shadow:0 4px 20px rgba(0,0,0,0.3);
  --shadow-lg:0 8px 40px rgba(0,0,0,0.4);
  --ease:cubic-bezier(.16,1,.3,1);
  --ease-std:cubic-bezier(.4,0,.2,1);
  --t-fast:.15s var(--ease-std);
  --t:.22s var(--ease-std);
  --t-slow:.35s var(--ease);
  --font:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  --mono:'JetBrains Mono','SF Mono','Fira Code',monospace;
  --nav-h:60px;
  --safe-t:env(safe-area-inset-top);
  --safe-b:env(safe-area-inset-bottom);
  --gap:14px;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent}
body{
  font-family:var(--font);background:var(--bg);color:var(--text);
  min-height:100vh;min-height:100dvh;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  overflow-x:hidden;display:flex;flex-direction:column;
}
body.no-scroll{overflow:hidden}
a{color:var(--primary-light);text-decoration:none;transition:color var(--t-fast)}
a:hover{color:var(--primary)}
:focus-visible{outline:2px solid var(--primary);outline-offset:2px;border-radius:6px}
img,svg{max-width:100%}
.app-main{flex:1;display:flex;flex-direction:column;min-height:0;min-width:0}
.container{max-width:1100px;width:100%;margin:0 auto;padding:16px;flex:1}
@media(min-width:768px){.container{padding:24px}}

/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--text-3)}
@media (prefers-reduced-motion:reduce){
  *{transition-duration:.01ms!important;animation-duration:.01ms!important;scroll-behavior:auto!important}
}
"""

NAVBAR_CSS = """
.nav-bottom{
  position:sticky;bottom:0;z-index:100;flex-shrink:0;
  display:flex;justify-content:center;gap:0;
  background:rgba(22,22,31,0.92);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-top:1px solid var(--border);
  padding:6px 8px calc(6px + var(--safe-b));
  margin-top:auto;
}
.nav-inner{display:flex;width:100%;max-width:420px;justify-content:space-around;gap:8px}
.nav-item{
  flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;
  padding:8px 6px;border-radius:var(--radius-sm);
  color:var(--text-3);font-size:11px;font-weight:600;
  transition:var(--t);text-decoration:none;
  -webkit-tap-highlight-color:transparent;cursor:pointer;
  background:transparent;border:none;
}
.nav-item:active{transform:scale(.94)}
.nav-item.active{color:var(--primary-light);background:var(--primary-bg)}
.nav-item.active svg{color:var(--primary-light)}
.nav-item svg{width:22px;height:22px;color:var(--text-3);transition:color var(--t)}
.nav-item:hover svg{color:var(--text-2)}
@media(min-width:861px){.nav-bottom{display:none}}
"""

HEADER_CSS = """
.topbar{
  position:sticky;top:0;z-index:50;flex-shrink:0;
  display:flex;align-items:center;gap:10px;
  padding:10px 16px;padding-top:calc(10px + var(--safe-t));
  background:rgba(22,22,31,0.85);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
}
.topbar-logo{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:800;letter-spacing:-.3px;color:var(--primary-light);white-space:nowrap}
.topbar-logo svg{width:26px;height:26px;flex-shrink:0}
.topbar-nav{display:none;gap:4px;margin-left:12px}
.topbar-nav a{
  display:flex;align-items:center;gap:6px;
  padding:7px 14px;border-radius:var(--radius-sm);
  font-size:13px;font-weight:600;color:var(--text-2);
  transition:var(--t);border:1px solid transparent;
}
.topbar-nav a svg{width:15px;height:15px}
.topbar-nav a:hover{color:var(--text);background:var(--surface-2)}
.topbar-nav a.active{color:var(--primary-light);background:var(--primary-bg);border-color:var(--primary-border)}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:8px;min-width:0}
.status-dot{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--success);font-weight:600;white-space:nowrap}
.status-dot::before{content:'';width:8px;height:8px;background:var(--success);border-radius:50%;animation:pulse 2s infinite;box-shadow:0 0 8px var(--success)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes spin{to{transform:rotate(360deg)}}
.icon-btn{
  display:flex;align-items:center;gap:6px;
  padding:8px 12px;border-radius:var(--radius-sm);
  background:var(--surface-2);border:1px solid var(--border);
  color:var(--text-2);font-size:12px;font-weight:600;cursor:pointer;
  transition:var(--t);-webkit-tap-highlight-color:transparent;white-space:nowrap;
}
.icon-btn:hover{border-color:var(--primary-border);color:var(--primary-light)}
.icon-btn:active{transform:scale(.96)}
.icon-btn svg{width:15px;height:15px}
.topbar-menu{display:none}
@media(max-width:860px){.topbar-menu{display:flex}}
@media(min-width:861px){.topbar-nav{display:flex}.topbar{padding:10px 24px;padding-top:calc(10px + var(--safe-t))}}
"""

STAT_CARD_CSS = """
.stat-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px 14px;text-align:center;
  transition:var(--t);position:relative;overflow:hidden;
}
.stat-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--primary),var(--accent));
  border-radius:var(--radius) var(--radius) 0 0;opacity:0;
  transition:var(--t);
}
.stat-card:hover{border-color:var(--primary-border);transform:translateY(-3px);box-shadow:var(--shadow)}
.stat-card:hover::before{opacity:1}
.stat-icon{
  width:42px;height:42px;margin:0 auto 10px;
  display:flex;align-items:center;justify-content:center;
  background:var(--primary-bg);border:1px solid var(--primary-border);
  border-radius:var(--radius-sm);color:var(--primary-light);
}
.stat-icon svg{width:20px;height:20px}
.stat-label{font-size:11px;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px}
.stat-value{font-size:26px;font-weight:800;color:var(--text);line-height:1.15;word-break:break-word}
.stat-sub{font-size:11px;color:var(--text-3);margin-top:4px;word-break:break-word}
"""

PANEL_CSS = """
.panel{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden;
  display:flex;flex-direction:column;min-width:0;
  transition:var(--t);
}
.panel:hover{border-color:var(--primary-border)}
.panel-head{
  padding:14px 18px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  font-size:13px;font-weight:700;color:var(--text-2);
}
.panel-head svg{width:16px;height:16px;margin-right:6px;opacity:0.7;flex-shrink:0}
.panel-body{padding:18px;flex:1;overflow:auto;min-height:0}
.panel-body.np{padding:0}
"""

TOGGLE_CSS = """
.toggle-group{display:flex;flex-direction:column;gap:10px}
.toggle-row{
  display:flex;justify-content:space-between;align-items:center;gap:12px;
  padding:12px 14px;background:var(--surface-2);
  border:1px solid var(--border);border-radius:var(--radius-sm);
  transition:var(--t);
}
.toggle-row:hover{border-color:var(--primary-border)}
.toggle-info{flex:1;min-width:0}
.toggle-label{font-size:13px;font-weight:600;color:var(--text);display:flex;align-items:center;gap:6px}
.toggle-label svg{width:16px;height:16px;color:var(--primary-light);flex-shrink:0}
.toggle-desc{font-size:11px;color:var(--text-3);margin-top:2px}
.switch{position:relative;width:48px;height:26px;cursor:pointer;flex-shrink:0}
.switch input{opacity:0;width:0;height:0;position:absolute}
.switch-track{
  position:absolute;inset:0;
  background:var(--surface-3);border:1px solid var(--border);
  border-radius:13px;transition:var(--t);
}
.switch input:checked+.switch-track{background:var(--primary);border-color:var(--primary)}
.switch-thumb{
  position:absolute;top:4px;left:4px;
  width:16px;height:16px;background:#fff;border-radius:50%;
  transition:var(--t);box-shadow:0 2px 6px rgba(0,0,0,0.3);
}
.switch input:checked~.switch-thumb{transform:translateX(22px)}
"""

CHAT_PAGE_CSS = """
.chat-wrap{flex:1;display:flex;min-height:0;overflow:hidden;position:relative}
.chat-sidebar{
  width:268px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);
  display:flex;flex-direction:column;overflow:hidden;
  transition:transform var(--t-slow);
}
.sidebar-title{padding:16px;font-size:12px;color:var(--text-3);text-transform:uppercase;letter-spacing:1px;font-weight:700;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.sidebar-title svg{width:14px;height:14px;flex-shrink:0}
.mem-list{flex:1;overflow-y:auto;padding:10px;display:grid;grid-template-columns:1fr 1fr;gap:8px;align-content:start}
.mem-item{
  padding:12px;border-radius:var(--radius-sm);
  background:var(--surface-2);border:1px solid var(--border);
  transition:var(--t);
}
.mem-item:hover{border-color:var(--primary-border)}
.mem-item .mem-label{color:var(--primary-light);font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;display:flex;align-items:center;gap:4px}
.mem-item .mem-label svg{width:12px;height:12px;flex-shrink:0}
.mem-item .mem-val{color:var(--text);font-size:15px;font-weight:700;word-break:break-word}
.chat-main{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.chat-messages{flex:1;overflow-y:auto;padding:20px;padding-bottom:calc(20px + var(--safe-b));display:flex;flex-direction:column;gap:14px;min-height:0;scroll-behavior:smooth}
.msg-bubble{
  max-width:82%;padding:14px 18px;border-radius:var(--radius);
  line-height:1.65;font-size:14px;white-space:pre-wrap;word-wrap:break-word;overflow-wrap:anywhere;
  animation:msgIn .3s var(--ease);
}
@keyframes msgIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg-user{
  background:var(--primary);color:#fff;
  border:1px solid var(--primary-dark);
  border-bottom-right-radius:4px;margin-left:auto;
  box-shadow:0 2px 12px rgba(124,92,252,0.25);
}
.msg-ai{
  background:var(--surface-2);color:var(--text);
  border:1px solid var(--border);border-bottom-left-radius:4px;
}
.msg-ai:hover{border-color:var(--primary-border)}
.msg-meta{font-size:11px;color:var(--text-3);margin-top:6px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.msg-meta svg{width:12px;height:12px}
.msg-user .msg-meta{justify-content:flex-end}
.route-badge{
  display:inline-flex;align-items:center;gap:3px;
  padding:2px 10px;border-radius:20px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;
}
.route-badge.code{background:var(--primary-bg);color:var(--primary-light);border:1px solid var(--primary-border)}
.route-badge.tool{background:var(--success-bg);color:var(--success);border:1px solid rgba(0,212,170,0.3)}
.route-badge.reason{background:var(--warning-bg);color:var(--warning);border:1px solid rgba(251,191,36,0.3)}
.route-badge.search{background:rgba(56,189,248,0.08);color:#38bdf8;border:1px solid rgba(56,189,248,0.3)}
.route-badge.chat{background:var(--surface-3);color:var(--text-2);border:1px solid var(--border)}
.msg-bubble pre{background:var(--bg);padding:12px;border-radius:var(--radius-xs);overflow-x:auto;margin:8px 0;border:1px solid var(--border);max-width:100%}
.msg-bubble pre code{font-family:var(--mono);font-size:13px;color:var(--accent);white-space:pre}
.msg-bubble code{background:var(--bg);padding:2px 6px;border-radius:4px;font-family:var(--mono);font-size:13px;word-break:break-word}
.msg-bubble a{color:var(--primary-light);text-decoration:underline}
.typing-ind{display:flex;gap:5px;padding:14px 18px;background:var(--surface-2);border:1px solid var(--border);border-radius:var(--radius);border-bottom-left-radius:4px;width:fit-content}
.typing-ind span{width:8px;height:8px;background:var(--primary);border-radius:50%;animation:bounce 1.4s infinite ease-in-out}
.typing-ind span:nth-child(2){animation-delay:0.2s}
.typing-ind span:nth-child(3){animation-delay:0.4s}
@keyframes bounce{0%,80%,100%{transform:scale(0.3);opacity:0.4}40%{transform:scale(1);opacity:1}}
.chat-input-area{padding:12px 16px;padding-bottom:calc(12px + var(--safe-b));background:var(--surface);border-top:1px solid var(--border);flex-shrink:0}
.chat-input-wrap{display:flex;gap:8px;max-width:860px;margin:0 auto;align-items:flex-end}
.chat-input-wrap textarea{
  flex:1;background:var(--surface-2);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:13px 16px;
  color:var(--text);font-size:14px;font-family:var(--font);
  resize:none;min-height:48px;max-height:180px;line-height:1.5;
  transition:border-color var(--t-fast),box-shadow var(--t-fast);outline:none;
}
.chat-input-wrap textarea:focus{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-bg)}
.chat-input-wrap textarea::placeholder{color:var(--text-3)}
.send-btn{
  background:var(--primary);color:#fff;border:1px solid var(--primary-dark);
  border-radius:var(--radius-sm);padding:0 20px;height:48px;cursor:pointer;
  font-weight:700;font-size:14px;transition:var(--t);
  display:flex;align-items:center;gap:6px;min-width:60px;justify-content:center;flex-shrink:0;
}
.send-btn:hover{background:var(--primary-dark);transform:translateY(-1px)}
.send-btn:active{transform:scale(0.97)}
.send-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.send-btn svg{width:18px;height:18px}
.welcome-box{text-align:center;padding:clamp(28px,6vw,60px) 20px}
.welcome-box h2{font-size:clamp(24px,5vw,28px);font-weight:800;margin-bottom:6px;background:linear-gradient(135deg,var(--primary),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.welcome-box p{font-size:14px;color:var(--text-2);max-width:460px;margin:0 auto;line-height:1.6}
.welcome-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:24px}
.welcome-chip{
  background:var(--surface-2);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:9px 16px;
  font-size:13px;font-weight:600;color:var(--text);
  cursor:pointer;transition:var(--t);
  display:flex;align-items:center;gap:6px;
}
.welcome-chip:hover{border-color:var(--primary);color:var(--primary-light);transform:translateY(-2px)}
.welcome-chip:active{transform:scale(.97)}
.welcome-chip svg{width:16px;height:16px;flex-shrink:0}
.sidebar-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:40;opacity:0;transition:opacity var(--t)}
.sidebar-overlay.show{display:block;opacity:1}
@media(max-width:860px){
  .chat-sidebar{position:fixed;top:0;left:0;bottom:0;height:100%;height:100dvh;z-index:50;width:min(82vw,300px);transform:translateX(-100%);box-shadow:var(--shadow-lg)}
  .chat-sidebar.open{transform:translateX(0)}
  .mem-list{grid-template-columns:1fr 1fr}
  .msg-bubble{max-width:90%}
  .chat-messages{padding:14px}
}
@media(max-width:420px){
  .mem-list{grid-template-columns:1fr}
  .msg-bubble{max-width:94%}
  .send-btn{padding:0 16px;min-width:54px}
}
@media(min-width:861px){.chat-sidebar{transform:none!important}.mem-list{grid-template-columns:1fr 1fr}}
"""

API_DOCS_CSS = """
.docs-body{padding:32px 16px;max-width:900px;margin:0 auto;width:100%}
@media(min-width:768px){.docs-body{padding:40px 24px}}
.docs-body h1{font-size:clamp(26px,6vw,32px);font-weight:800;margin-bottom:6px;background:linear-gradient(135deg,var(--primary),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.docs-body .sub{color:var(--text-2);margin-bottom:28px;font-size:14px}
.docs-body h2{font-size:20px;font-weight:700;margin:32px 0 14px;color:var(--primary-light);border-bottom:1px solid var(--border);padding-bottom:8px;display:flex;align-items:center;gap:8px}
.docs-body h2 svg{width:18px;height:18px;flex-shrink:0}
.docs-section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:14px}
.docs-section .method{display:inline-block;padding:3px 10px;border-radius:var(--radius-xs);font-size:12px;font-weight:800;margin-right:8px;font-family:var(--mono)}
.method.get{background:var(--success-bg);color:var(--success);border:1px solid rgba(0,212,170,0.3)}
.method.post{background:var(--primary-bg);color:var(--primary-light);border:1px solid var(--primary-border)}
.docs-section .path{font-family:var(--mono);font-size:14px;color:var(--text);word-break:break-all}
.docs-section .desc{color:var(--text-2);font-size:13px;margin-top:10px}
.docs-section .auth{color:var(--warning);font-size:11px;margin-top:6px;display:flex;align-items:center;gap:4px}
.docs-section .auth svg{width:12px;height:12px}
pre{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;overflow-x:auto;font-size:13px;margin:12px 0;-webkit-overflow-scrolling:touch}
code{font-family:var(--mono);color:var(--accent)}
.cli-block{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:18px;margin:14px 0;font-size:13px;line-height:1.7;overflow-x:auto;
}
.cli-block .comment{color:var(--text-3)}
.cli-block .cmd{color:var(--accent);font-family:var(--mono);white-space:pre-wrap;word-break:break-all}
.docs-nav{display:flex;gap:6px;margin-bottom:24px;flex-wrap:wrap}
.docs-nav a{
  color:var(--text-2);font-size:13px;font-weight:600;
  padding:7px 14px;border-radius:var(--radius-sm);
  border:1px solid var(--border);transition:var(--t);
  display:flex;align-items:center;gap:5px;
}
.docs-nav a svg{width:13px;height:13px}
.docs-nav a:hover{color:var(--primary-light);border-color:var(--primary-border)}
.docs-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin-top:12px;border:1px solid var(--border);border-radius:var(--radius-sm)}
.docs-table{width:100%;border-collapse:collapse;min-width:560px}
.docs-table th{text-align:left;padding:12px;color:var(--primary-light);font-size:12px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid var(--border);background:var(--surface)}
.docs-table td{padding:12px;border-bottom:1px solid var(--surface-3);font-size:13px}
.docs-table td:first-child{font-family:var(--mono);font-weight:700}
.docs-table tr:last-child td{border-bottom:none}
.docs-table tr:hover td{background:var(--surface-2)}
"""

# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():
    i = icon
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#0c0c14">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>DikaAI Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{DESIGN_CSS}{NAVBAR_CSS}{HEADER_CSS}{STAT_CARD_CSS}{PANEL_CSS}{TOGGLE_CSS}

.stats-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:14px}}
@media(min-width:560px){{.stats-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(min-width:860px){{.stats-grid{{grid-template-columns:repeat(6,1fr)}}}}
.grid-3{{display:grid;gap:14px;margin-bottom:14px}}
@media(min-width:820px){{.grid-3{{grid-template-columns:1fr 1fr 1fr}}}}

canvas{{width:100%;height:200px;border-radius:var(--radius-xs);display:block}}
.msg-list{{max-height:240px;overflow-y:auto;font-size:12px}}
.msg-item{{padding:8px 0;border-bottom:1px solid var(--surface-3);color:var(--text-2);word-break:break-word;display:flex;align-items:flex-start;gap:8px}}
.msg-item svg{{flex-shrink:0;margin-top:2px;color:var(--text-3)}}
.msg-item span{{flex:1;min-width:0}}
.progress-bar{{width:100%;height:6px;background:var(--surface-3);border-radius:3px;overflow:hidden;margin-top:8px}}
.progress-fill{{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent));border-radius:3px;transition:width 0.5s ease}}
.quick-chat-box{{display:flex;flex-direction:column;height:240px}}
.quick-chat-msgs{{flex:1;overflow-y:auto;padding:12px;font-size:13px;display:flex;flex-direction:column;gap:4px}}
.q-msg{{padding:8px 12px;border-radius:var(--radius-sm);max-width:90%;word-break:break-word}}
.q-msg.user{{align-self:flex-end;background:var(--primary);color:#fff}}
.q-msg.ai{{align-self:flex-start;background:var(--surface-2);border:1px solid var(--border);color:var(--accent)}}
.quick-chat-input{{display:flex;gap:8px;padding:12px;border-top:1px solid var(--border)}}
.quick-chat-input input{{flex:1;min-width:0;background:var(--surface-2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:var(--radius-sm);font-family:var(--font);font-size:13px;outline:none;transition:border-color var(--t-fast),box-shadow var(--t-fast)}}
.quick-chat-input input:focus{{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-bg)}}
.quick-chat-input button{{background:var(--primary);color:#fff;border:1px solid var(--primary-dark);border-radius:var(--radius-sm);padding:10px 16px;cursor:pointer;font-weight:700;font-size:13px;transition:var(--t);display:flex;align-items:center;gap:4px;flex-shrink:0}}
.quick-chat-input button:hover{{background:var(--primary-dark)}}
.quick-chat-input button:active{{transform:scale(.97)}}
.quick-chat-input button svg{{width:16px;height:16px}}

.toast{{position:fixed;bottom:calc(76px + var(--safe-b));left:50%;transform:translateX(-50%) translateY(12px);background:var(--surface-2);border:1px solid var(--border);color:var(--text);padding:12px 20px;border-radius:var(--radius-sm);font-size:13px;font-weight:600;box-shadow:var(--shadow-lg);opacity:0;transition:opacity .3s var(--ease-std),transform .3s var(--ease-std);pointer-events:none;z-index:200;max-width:90vw;text-align:center}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}
@media(min-width:861px){{.toast{{bottom:24px}}}}
.export-btn{{display:flex;align-items:center;gap:4px;padding:7px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-2);color:var(--text-2);font-size:12px;font-weight:600;cursor:pointer;transition:var(--t)}}
.export-btn:hover{{border-color:var(--primary-border);color:var(--primary-light)}}
.export-btn:active{{transform:scale(.96)}}
.export-btn svg{{width:14px;height:14px}}
.export-btn span{{display:none}}
@media(min-width:420px){{.export-btn span{{display:inline}}}}
.open-full{{color:var(--primary-light);font-size:11px;font-weight:600;display:flex;align-items:center;gap:2px;white-space:nowrap}}
.open-full svg{{width:12px;height:12px}}
.footer-line{{text-align:center;padding:20px 16px calc(20px + var(--safe-b));color:var(--text-3);font-size:11px}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo">{i('brain',26)} DikaAI</div>
  <nav class="topbar-nav">
    <a href="/" class="active">{i('chart',14)} Dashboard</a>
    <a href="/chat">{i('chat',14)} Chat</a>
    <a href="/docs">{i('code',14)} API</a>
  </nav>
  <div class="topbar-right">
    <div class="status-dot" id="status-badge">IDLE</div>
    <button class="export-btn" onclick="exportCSV()">{i('download',14)}<span>Export</span></button>
  </div>
</div>

<div class="container">

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon">{i('chat',20)}</div>
      <div class="stat-label">Messages</div>
      <div class="stat-value" id="total-msgs">0</div>
      <div class="stat-sub" id="unique-chats">0 chats</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">{i('check',20)}</div>
      <div class="stat-label">Processed</div>
      <div class="stat-value" id="processed">0</div>
      <div class="progress-bar"><div class="progress-fill" id="process-bar" style="width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">{i('activity',20)}</div>
      <div class="stat-label">Steps</div>
      <div class="stat-value" id="train-steps">0</div>
      <div class="stat-sub" id="model-params">0 params</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">{i('layers',20)}</div>
      <div class="stat-label">Loss</div>
      <div class="stat-value" id="current-loss">-</div>
      <div class="stat-sub" id="avg-loss">avg: -</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">{i('database',20)}</div>
      <div class="stat-label">Vocab</div>
      <div class="stat-value" id="vocab-size">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">{i('clock',20)}</div>
      <div class="stat-label">Uptime</div>
      <div class="stat-value" id="uptime">0m</div>
    </div>
  </div>

  <div class="grid-3">

    <div class="panel">
      <div class="panel-head">{i('settings',16)} Controls</div>
      <div class="panel-body">
        <div class="toggle-group">
          <div class="toggle-row">
            <div class="toggle-info">
              <div class="toggle-label">{i('zap',16)} Auto-Reply</div>
              <div class="toggle-desc">Balas otomatis di Telegram</div>
            </div>
            <label class="switch"><input type="checkbox" id="toggle-reply" checked onchange="toggleFeature('auto_reply',this.checked)"><span class="switch-track"></span><span class="switch-thumb"></span></label>
          </div>
          <div class="toggle-row">
            <div class="toggle-info">
              <div class="toggle-label">{i('cpu',16)} Training</div>
              <div class="toggle-desc">Model belajar dari data</div>
            </div>
            <label class="switch"><input type="checkbox" id="toggle-training" checked onchange="toggleFeature('training',this.checked)"><span class="switch-track"></span><span class="switch-thumb"></span></label>
          </div>
          <div class="toggle-row">
            <div class="toggle-info">
              <div class="toggle-label">{i('refresh',16)} Scraping</div>
              <div class="toggle-desc">Ambil chat dari Telegram</div>
            </div>
            <label class="switch"><input type="checkbox" id="toggle-scraping" checked onchange="toggleFeature('scraping',this.checked)"><span class="switch-track"></span><span class="switch-thumb"></span></label>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">{i('chat',16)} Quick Chat <a class="open-full" href="/chat">Open Full {i('external',12)}</a></div>
      <div class="panel-body np">
        <div class="quick-chat-box">
          <div class="quick-chat-msgs" id="quick-chat"></div>
          <div class="quick-chat-input">
            <input type="text" id="quick-input" placeholder="Quick ask..." onkeydown="if(event.key==='Enter')quickChat()">
            <button onclick="quickChat()">{i('send',16)}</button>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">{i('message',16)} Recent Messages <span id="msg-count" style="color:var(--primary-light);font-size:12px">0</span></div>
      <div class="panel-body"><div class="msg-list" id="msg-list"></div></div>
    </div>

  </div>

  <div class="panel">
    <div class="panel-head">{i('chart',16)} Training Loss <span id="chart-info" style="color:var(--primary-light);font-size:12px">0 points</span></div>
    <div class="panel-body"><canvas id="lossChart"></canvas></div>
  </div>

</div>

<div class="footer-line">DikaAI v3.2 &middot; Auto-refresh 10s &middot; Vercel + Upstash Redis</div>

<nav class="nav-bottom">
  <div class="nav-inner">
    <a class="nav-item active" href="/">{i('chart',22)}<span>Dashboard</span></a>
    <a class="nav-item" href="/chat">{i('chat',22)}<span>Chat</span></a>
    <a class="nav-item" href="/docs">{i('code',22)}<span>API</span></a>
  </div>
</nav>

<div class="toast" id="toast"></div>

<script>
const $=id=>document.getElementById(id);
function formatNum(n){{if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return (n||0).toString()}}
function formatTime(s){{if(s>=3600)return Math.floor(s/3600)+'h '+Math.floor((s%3600)/60)+'m';return Math.floor(s/60)+'m'}}
function toast(msg){{const t=$('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000)}}
function esc(t){{return (t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}
async function toggleFeature(f,e){{try{{const r=await fetch('/api/toggle',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{feature:f,enabled:e}})}});const d=await r.json();toast(d.ok?f+(e?' ON':' OFF'):'Error')}}catch(x){{toast('Connection error')}}}}
async function quickChat(){{const el=$('quick-input');const t=el.value.trim();if(!t)return;el.value='';const box=$('quick-chat');box.innerHTML+='<div class="q-msg user">'+esc(t)+'</div>';try{{const r=await fetch('/api/chat',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:t}})}});const d=await r.json();box.innerHTML+='<div class="q-msg ai">'+esc(d.reply||d.response||'(no reply)')+'</div>'}}catch(x){{box.innerHTML+='<div class="q-msg ai" style="color:var(--danger)">Error</div>'}}box.scrollTop=box.scrollHeight}}
function exportCSV(){{fetch('/api/export').then(r=>r.blob()).then(b=>{{const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download='dikaai_'+new Date().toISOString().slice(0,10)+'.csv';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u);toast('CSV exported!')}}).catch(()=>toast('Export failed'))}}
function drawChart(losses){{const c=$('lossChart');if(!c)return;const ctx=c.getContext('2d');const dpr=window.devicePixelRatio||1;const w=c.offsetWidth||600,h=200;c.width=w*dpr;c.height=h*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);if(!losses||losses.length<2){{ctx.fillStyle='#606078';ctx.font='14px Inter';ctx.textAlign='center';ctx.fillText('Waiting for training data...',w/2,h/2);return}}const maxL=Math.max(...losses)*1.1||1;ctx.strokeStyle='#282838';ctx.lineWidth=1;for(let i=0;i<=4;i++){{const y=(i/4)*h;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();ctx.fillStyle='#606078';ctx.font='10px Inter';ctx.textAlign='left';ctx.fillText((maxL-(i/4)*maxL).toFixed(3),4,y+12)}}const grad=ctx.createLinearGradient(0,0,w,0);grad.addColorStop(0,'#7c5cfc');grad.addColorStop(1,'#00d4aa');ctx.strokeStyle=grad;ctx.lineWidth=2.5;ctx.shadowColor='#7c5cfc';ctx.shadowBlur=6;ctx.beginPath();for(let i=0;i<losses.length;i++){{const x=(i/(losses.length-1))*w;const y=h-(losses[i]/maxL)*h;i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)}}ctx.stroke();ctx.shadowBlur=0;ctx.lineTo(w,h);ctx.lineTo(0,h);ctx.closePath();const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,'rgba(124,92,252,0.15)');g.addColorStop(1,'rgba(124,92,252,0)');ctx.fillStyle=g;ctx.fill()}}
async function fetchStats(){{try{{const r=await fetch('/api/stats');const d=await r.json();updateUI(d)}}catch(e){{}}}}
function updateUI(d){{const db=d.db||{{}},m=d.model||{{}};$('status-badge').textContent=(d.status||'idle').toUpperCase();$('total-msgs').textContent=formatNum(db.total||0);$('unique-chats').textContent=(db.unique_chats||0)+' chats';$('processed').textContent=formatNum(db.processed||0);$('process-bar').style.width=(db.total?Math.round(db.processed/db.total*100):0)+'%';$('train-steps').textContent=formatNum(m.step||0);$('model-params').textContent=formatNum(m.params||0)+' params';const chart=d.loss_chart||{{}},losses=chart.losses||[];if(losses.length>0)$('current-loss').textContent=losses[losses.length-1].toFixed(4);if(d.total_loss!==undefined&&d.total_steps>0)$('avg-loss').textContent='avg: '+(d.total_loss/d.total_steps).toFixed(4);$('vocab-size').textContent=d.vocab_tokens||m.vocab_size||0;$('uptime').textContent=formatTime(d.uptime||0);const t=d.toggles||{{}};if($('toggle-reply'))$('toggle-reply').checked=t.auto_reply!==false;if($('toggle-training'))$('toggle-training').checked=t.training!==false;if($('toggle-scraping'))$('toggle-scraping').checked=t.scraping!==false;drawChart(losses);$('chart-info').textContent=losses.length+' points';const msgs=d.recent_messages||[];$('msg-count').textContent=msgs.length;$('msg-list').innerHTML=msgs.slice().reverse().map(msg=>'<div class="msg-item">'+i('message',12)+'<span>'+esc(msg)+'</span></div>').join('')}}
setInterval(fetchStats,10000);fetchStats();
</script>
</body>
</html>"""


# ============================================================
# CHAT PAGE
# ============================================================

def chat_page():
    i = icon
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0c0c14">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>DikaAI Chat</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{DESIGN_CSS}{HEADER_CSS}{CHAT_PAGE_CSS}
.header-stats{{font-size:11px;color:var(--text-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:42vw}}
@media(max-width:460px){{.header-stats{{display:none}}}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo">{i('brain',26)} DikaAI</div>
  <button class="icon-btn topbar-menu" id="sidebarBtn" onclick="toggleSidebar()" aria-label="Toggle engine panel">{i('menu',18)}<span>Engine</span></button>
  <nav class="topbar-nav">
    <a href="/">{i('chart',14)} Dashboard</a>
    <a href="/chat" class="active">{i('chat',14)} Chat</a>
    <a href="/docs">{i('code',14)} API</a>
  </nav>
  <div class="topbar-right">
    <div class="status-dot">Online</div>
    <div class="header-stats" id="header-stats">Loading...</div>
  </div>
</div>

<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
<div class="chat-wrap">

  <aside class="chat-sidebar" id="sidebar">
    <div class="sidebar-title">{i('layers',14)} Engine</div>
    <div class="mem-list">
      <div class="mem-item"><div class="mem-label">{i('zap',12)} Total Tasks</div><div class="mem-val" id="mem-tasks">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('check',12)} Success Rate</div><div class="mem-val" id="mem-rate">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('clock',12)} Episodes</div><div class="mem-val" id="mem-episodes">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('database',12)} Facts</div><div class="mem-val" id="mem-facts">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('search',12)} Topics</div><div class="mem-val" id="mem-topics">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('cpu',12)} Tokens</div><div class="mem-val" id="mem-tokens">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('activity',12)} Model Step</div><div class="mem-val" id="mem-step">-</div></div>
      <div class="mem-item"><div class="mem-label">{i('layers',12)} Vocab</div><div class="mem-val" id="mem-vocab">-</div></div>
    </div>
  </aside>

  <main class="chat-main">
    <div class="chat-messages" id="messages">
      <div class="welcome-box">
        <h2>DikaAI v3.2</h2>
        <p>AI Coding Agent with memory, context, multi-language code generation, and tools.</p>
        <div class="welcome-chips">
          <div class="welcome-chip" onclick="send('Write a fibonacci function')">{i('code',16)} Fibonacci</div>
          <div class="welcome-chip" onclick="send('Write a binary search in Python')">{i('search',16)} Binary Search</div>
          <div class="welcome-chip" onclick="send('Fix this error: TypeError on line 5')">{i('terminal',16)} Fix Error</div>
          <div class="welcome-chip" onclick="send('git status')">{i('folder',16)} Git Status</div>
          <div class="welcome-chip" onclick="send('Explain quicksort algorithm')">{i('brain',16)} Explain</div>
          <div class="welcome-chip" onclick="send('Write a Rust struct with methods')">{i('code',16)} Rust</div>
          <div class="welcome-chip" onclick="send('Write a JavaScript debounce function')">{i('zap',16)} JS Debounce</div>
          <div class="welcome-chip" onclick="send('Write a C++ vector sort with lambda')">{i('code',16)} C++ Sort</div>
        </div>
      </div>
    </div>
    <div class="chat-input-area">
      <div class="chat-input-wrap">
        <textarea id="input" placeholder="Ask DikaAI anything..." rows="1" autofocus></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendFromInput()" aria-label="Send">{i('send',18)}</button>
      </div>
    </div>
  </main>

</div>

<nav class="nav-bottom">
  <div class="nav-inner">
    <a class="nav-item" href="/">{i('chart',22)}<span>Dashboard</span></a>
    <a class="nav-item active" href="/chat">{i('chat',22)}<span>Chat</span></a>
    <a class="nav-item" href="/docs">{i('code',22)}<span>API</span></a>
  </div>
</nav>

<script>
const messages=document.getElementById('messages');
const input=document.getElementById('input');
const sendBtn=document.getElementById('sendBtn');
let isLoading=false;

function autoGrow(){{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,180)+'px'}}
input.addEventListener('input',autoGrow);
input.addEventListener('keydown',e=>{{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();sendFromInput()}}}});
function sendFromInput(){{const t=input.value.trim();if(!t||isLoading)return;send(t);input.value='';autoGrow()}}
async function send(text){{if(isLoading)return;isLoading=true;sendBtn.disabled=true;
const welcome=messages.querySelector('.welcome-box');if(welcome)welcome.remove();
addMessage('user',text);
const typing=document.createElement('div');typing.className='msg-bubble msg-ai typing-ind';typing.innerHTML='<span></span><span></span><span></span>';messages.appendChild(typing);messages.scrollTop=messages.scrollHeight;
try{{const r=await fetch('/api/chat',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:text}})}});const d=await r.json();typing.remove();addMessage('assistant',d.response||d.reply||'',{{route:d.route,time:d.time,topic:d.topic}});loadStats()}}catch(err){{typing.remove();addMessage('assistant','Error: '+err.message,{{route:'error'}})}}isLoading=false;sendBtn.disabled=false;input.focus()}}
function addMessage(role,content,meta={{}}){{if(content===undefined||content===null)content='';const div=document.createElement('div');div.style.cssText='max-width:82%;margin-bottom:4px';
let metaHtml='';if(meta.route)metaHtml+=`<span class="route-badge ${{meta.route}}">${{meta.route}}</span>`;if(meta.time)metaHtml+=`<span style="display:inline-flex;align-items:center;gap:3px">{i('clock',11)}${{meta.time}}</span>`;if(meta.topic)metaHtml+=`<span style="display:inline-flex;align-items:center;gap:3px">{i('folder',11)}${{meta.topic}}</span>`;
const formatted=formatContent(content);
const cls=role==='user'?'msg-bubble msg-user':'msg-bubble msg-ai';
div.innerHTML=`<div class="${{cls}}">${{formatted}}</div>${{metaHtml?'<div class="msg-meta">'+metaHtml+'</div>':''}}`;
messages.appendChild(div);messages.scrollTop=messages.scrollHeight}}
function escapeHtml(t){{const d=document.createElement('div');d.textContent=t;return d.innerHTML}}
function formatContent(raw){{let html=escapeHtml(raw);
html=html.replace(/```(\\w+)?\\n([\\s\\S]*?)```/g,'<pre><code>$2</code></pre>');
html=html.replace(/`([^`]+)`/g,'<code>$1</code>');
return html}}
function toggleSidebar(){{const s=document.getElementById('sidebar'),o=document.getElementById('sidebarOverlay');const open=s.classList.toggle('open');o.classList.toggle('show',open);document.body.classList.toggle('no-scroll',open)}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape'){{document.getElementById('sidebar').classList.remove('open');document.getElementById('sidebarOverlay').classList.remove('show');document.body.classList.remove('no-scroll')}}}});
async function loadStats(){{try{{const r=await fetch('/api/stats');const d=await r.json();document.getElementById('header-stats').textContent=`${{d.db?.total||0}} tasks | ${{d.status||'idle'}}`;if(d.model)document.getElementById('mem-step').textContent=d.model.step||0;if(d.model)document.getElementById('mem-vocab').textContent=d.model.vocab_size||0;const e=d.engine||{{}};document.getElementById('mem-tasks').textContent=e.total||0;document.getElementById('mem-rate').textContent=e.rate||'0%';document.getElementById('mem-episodes').textContent=e.episodes||0;document.getElementById('mem-facts').textContent=e.facts||0;document.getElementById('mem-topics').textContent=e.topics||0;document.getElementById('mem-tokens').textContent=e.tokens||0}}catch(e){{}}}}
loadStats();setInterval(loadStats,30000);autoGrow();
</script>
</body>
</html>"""


# ============================================================
# API DOCS PAGE
# ============================================================

def docs_page():
    i = icon
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0c0c14">
<title>DikaAI API</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{DESIGN_CSS}{NAVBAR_CSS}{HEADER_CSS}{API_DOCS_CSS}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo">{i('brain',26)} DikaAI</div>
  <nav class="topbar-nav">
    <a href="/">{i('chart',14)} Dashboard</a>
    <a href="/chat">{i('chat',14)} Chat</a>
    <a href="/docs" class="active">{i('code',14)} API</a>
  </nav>
  <div class="topbar-right"><a class="icon-btn" href="/" style="text-decoration:none">{i('arrow_right',14)} Back</a></div>
</div>

<div class="docs-body">

<h1>DikaAI API</h1>
<p class="sub">OpenAI-compatible API for coding, chat, and agent tasks.</p>

<div class="docs-nav">
  <a href="/">{i('chart',12)} Dashboard</a>
  <a href="/chat">{i('chat',12)} Chat</a>
  <a href="/v1/health">{i('zap',12)} Health</a>
  <a href="/v1/models">{i('layers',12)} Models</a>
</div>

<h2>{i('key',18)} Authentication</h2>
<p>All endpoints require a Bearer token:</p>
<pre><code>Authorization: Bearer dka_xxxxxxxx</code></pre>
<p>Get a token: <code>python main.py token my-app</code></p>

<h2>{i('chat',18)} Chat (OpenAI-compatible)</h2>
<div class="docs-section"><span class="method post">POST</span><span class="path">/v1/chat/completions</span><div class="desc">Chat with DikaAI. OpenAI-compatible format.</div><div class="auth">{i('lock',12)} Required: chat scope</div></div>
<pre><code>curl -X POST https://your-app.vercel.app/v1/chat/completions \\
  -H "Authorization: Bearer dka_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{{"messages": [{{"role": "user", "content": "Write a fibonacci function"}}]}}'</code></pre>

<h2>{i('code',18)} Coding Agent</h2>
<div class="docs-section"><span class="method post">POST</span><span class="path">/v1/agent</span><div class="desc">Run coding agent with plan, code, test, debug loop.</div><div class="auth">{i('lock',12)} Required: agent scope</div></div>
<pre><code>curl -X POST https://your-app.vercel.app/v1/agent \\
  -H "Authorization: Bearer dka_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{{"task": "Fix the error in main.py"}}'</code></pre>

<h2>{i('terminal',18)} Tools</h2>
<div class="docs-section"><span class="method post">POST</span><span class="path">/v1/tools/read</span><div class="desc">Read file content.</div><div class="auth">{i('lock',12)} Required: tools scope</div></div>
<div class="docs-section"><span class="method post">POST</span><span class="path">/v1/tools/search</span><div class="desc">Search codebase.</div><div class="auth">{i('lock',12)} Required: tools scope</div></div>
<div class="docs-section"><span class="method post">POST</span><span class="path">/v1/tools/run</span><div class="desc">Run shell command.</div><div class="auth">{i('lock',12)} Required: tools scope</div></div>

<h2>{i('external',18)} Connect External Tools</h2>
<div class="cli-block">
<span class="comment"># Claude Code / Cursor / Codex</span><br>
<span class="cmd">export OPENAI_API_BASE=https://your-app.vercel.app/v1</span><br>
<span class="cmd">export OPENAI_API_KEY=dka_xxx</span><br><br>
<span class="comment"># Or use curl directly</span><br>
<span class="cmd">curl https://your-app.vercel.app/v1/chat/completions \\</span><br>
<span class="cmd">  -H "Authorization: Bearer dka_xxx" \\</span><br>
<span class="cmd">  -d '{{"messages":[{{"role":"user","content":"hello"}}]}}'</span>
</div>

<h2>{i('layers',18)} All Endpoints</h2>
<div class="docs-table-wrap">
<table class="docs-table">
<tr><th>Method</th><th>Path</th><th>Auth</th><th>Description</th></tr>
<tr><td style="color:var(--success)">GET</td><td>/v1/health</td><td style="color:var(--text-3)">No</td><td>Health check</td></tr>
<tr><td style="color:var(--success)">GET</td><td>/v1/models</td><td style="color:var(--text-3)">No</td><td>List models</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/chat/completions</td><td style="color:var(--warning)">chat</td><td>Chat (OpenAI-compat)</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/completions</td><td style="color:var(--warning)">chat</td><td>Completion</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/agent</td><td style="color:var(--warning)">agent</td><td>Coding agent</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/tools/read</td><td style="color:var(--warning)">tools</td><td>Read file</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/tools/search</td><td style="color:var(--warning)">tools</td><td>Search code</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/tools/run</td><td style="color:var(--warning)">tools</td><td>Run command</td></tr>
<tr><td style="color:var(--primary-light)">POST</td><td>/v1/auth/token</td><td style="color:var(--warning)">admin</td><td>Create token</td></tr>
<tr><td style="color:var(--success)">GET</td><td>/v1/auth/tokens</td><td style="color:var(--warning)">admin</td><td>List tokens</td></tr>
</table>
</div>

</div>

<nav class="nav-bottom">
  <div class="nav-inner">
    <a class="nav-item" href="/">{i('chart',22)}<span>Dashboard</span></a>
    <a class="nav-item" href="/chat">{i('chat',22)}<span>Chat</span></a>
    <a class="nav-item active" href="/docs">{i('code',22)}<span>API</span></a>
  </div>
</nav>

</body>
</html>"""
