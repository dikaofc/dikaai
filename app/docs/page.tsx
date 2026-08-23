import Link from 'next/link';
import Icon from '../components/Icon';

const ENDPOINTS = [
  { method: 'GET', path: '/v1/health', auth: 'No', authClass: 'text-3', desc: 'Health check' },
  { method: 'GET', path: '/v1/models', auth: 'No', authClass: 'text-3', desc: 'List models' },
  { method: 'POST', path: '/v1/chat/completions', auth: 'chat', desc: 'Chat (OpenAI-compat)' },
  { method: 'POST', path: '/v1/completions', auth: 'chat', desc: 'Completion' },
  { method: 'POST', path: '/v1/agent', auth: 'agent', desc: 'Coding agent' },
  { method: 'POST', path: '/v1/tools/read', auth: 'tools', desc: 'Read file' },
  { method: 'POST', path: '/v1/tools/search', auth: 'tools', desc: 'Search code' },
  { method: 'POST', path: '/v1/tools/run', auth: 'tools', desc: 'Run command' },
  { method: 'POST', path: '/v1/auth/token', auth: 'admin', desc: 'Create token' },
  { method: 'GET', path: '/v1/auth/tokens', auth: 'admin', desc: 'List tokens' },
];

export default function DocsPage() {
  return (
    <div className="docs-body">
      <h1>DikaAI API</h1>
      <p className="sub">OpenAI-compatible API for coding, chat, and agent tasks.</p>

      <div className="docs-nav">
        <Link href="/"><Icon name="chart" size={12} />Dashboard</Link>
        <Link href="/chat"><Icon name="chat" size={12} />Chat</Link>
        <Link href="/v1/health"><Icon name="zap" size={12} />Health</Link>
        <Link href="/v1/models"><Icon name="layers" size={12} />Models</Link>
      </div>

      <h2><Icon name="key" />Authentication</h2>
      <p>All endpoints require a Bearer token:</p>
      <pre><code>Authorization: Bearer dka_xxxxxxxx</code></pre>
      <p>Get a token: <code>python main.py token my-app</code></p>

      <h2><Icon name="chat" />Chat (OpenAI-compatible)</h2>
      <div className="docs-section">
        <span className="method post">POST</span>
        <span className="path">/v1/chat/completions</span>
        <div className="desc">Chat with DikaAI. OpenAI-compatible format.</div>
        <div className="auth"><Icon name="lock" />Required: chat scope</div>
      </div>
      <pre><code>{`curl -X POST https://your-app.vercel.app/v1/chat/completions \\
  -H "Authorization: Bearer dka_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Write a fibonacci function"}]}'`}</code></pre>

      <h2><Icon name="code" />Coding Agent</h2>
      <div className="docs-section">
        <span className="method post">POST</span>
        <span className="path">/v1/agent</span>
        <div className="desc">Run coding agent with plan, code, test, debug loop.</div>
        <div className="auth"><Icon name="lock" />Required: agent scope</div>
      </div>
      <pre><code>{`curl -X POST https://your-app.vercel.app/v1/agent \\
  -H "Authorization: Bearer dka_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{"task": "Fix the error in main.py"}'`}</code></pre>

      <h2><Icon name="terminal" />Tools</h2>
      <div className="docs-section">
        <span className="method post">POST</span>
        <span className="path">/v1/tools/read</span>
        <div className="desc">Read file content.</div>
        <div className="auth"><Icon name="lock" />Required: tools scope</div>
      </div>
      <div className="docs-section">
        <span className="method post">POST</span>
        <span className="path">/v1/tools/search</span>
        <div className="desc">Search codebase.</div>
        <div className="auth"><Icon name="lock" />Required: tools scope</div>
      </div>
      <div className="docs-section">
        <span className="method post">POST</span>
        <span className="path">/v1/tools/run</span>
        <div className="desc">Run shell command.</div>
        <div className="auth"><Icon name="lock" />Required: tools scope</div>
      </div>

      <h2><Icon name="external" />Connect External Tools</h2>
      <div className="cli-block">
        <span className="comment"># Claude Code / Cursor / Codex</span>
        <br />
        <span className="cmd">export OPENAI_API_BASE=https://your-app.vercel.app/v1</span>
        <br />
        <span className="cmd">export OPENAI_API_KEY=dka_xxx</span>
        <br />
        <br />
        <span className="comment"># Or use curl directly</span>
        <br />
        <span className="cmd">curl https://your-app.vercel.app/v1/chat/completions \</span>
        <br />
        <span className="cmd">  -H &quot;Authorization: Bearer dka_xxx&quot; \</span>
        <br />
        <span className="cmd">{`  -d '{"messages":[{"role":"user","content":"hello"}]}'`}</span>
      </div>

      <h2><Icon name="layers" />All Endpoints</h2>
      <div className="docs-table-wrap">
        <table className="docs-table">
          <thead>
            <tr>
              <th>Method</th>
              <th>Path</th>
              <th>Auth</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {ENDPOINTS.map((e) => (
              <tr key={e.path}>
                <td style={{ color: e.method === 'GET' ? 'var(--success)' : 'var(--primary-light)' }}>
                  {e.method}
                </td>
                <td>{e.path}</td>
                <td style={e.auth === 'No' ? { color: 'var(--text-3)' } : { color: 'var(--warning)' }}>
                  {e.auth}
                </td>
                <td>{e.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
