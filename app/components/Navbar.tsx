'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from './Icon';

export const ENGINE_SIDEBAR_EVENT = 'toggle-engine-sidebar';

const LINKS = [
  { href: '/', label: 'Dashboard', icon: 'chart' },
  { href: '/chat', label: 'Chat', icon: 'chat' },
  { href: '/docs', label: 'API', icon: 'code' },
];

export default function Navbar() {
  const path = usePathname();
  const isActive = (href: string) =>
    href === '/' ? path === '/' : path.startsWith(href);

  return (
    <header className="topbar">
      <Link href="/" className="topbar-logo">
        <Icon name="brain" size={26} />
        DikaAI
      </Link>
      <nav className="topbar-nav">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={isActive(l.href) ? 'active' : ''}
          >
            <Icon name={l.icon} size={14} />
            {l.label}
          </Link>
        ))}
      </nav>
      <div className="topbar-right">
        {path === '/chat' && (
          <button
            className="icon-btn topbar-menu"
            onClick={() =>
              window.dispatchEvent(new CustomEvent(ENGINE_SIDEBAR_EVENT))
            }
            aria-label="Toggle engine panel"
          >
            <Icon name="menu" /><span>Engine</span>
          </button>
        )}
        <div className="status-dot" id="status-badge">
          IDLE
        </div>
      </div>
    </header>
  );
}
