'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from './Icon';

const LINKS = [
  { href: '/', label: 'Dashboard', icon: 'chart' },
  { href: '/chat', label: 'Chat', icon: 'chat' },
  { href: '/docs', label: 'API', icon: 'code' },
];

export default function BottomNav() {
  const path = usePathname();
  const isActive = (href: string) =>
    href === '/' ? path === '/' : path.startsWith(href);

  return (
    <nav className="nav-bottom">
      <div className="nav-inner">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`nav-item ${isActive(l.href) ? 'active' : ''}`}
          >
            <Icon name={l.icon} size={22} />
            <span>{l.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
