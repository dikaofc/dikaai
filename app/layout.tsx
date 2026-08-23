import type { Metadata, Viewport } from 'next';
import './globals.css';
import Navbar from './components/Navbar';
import BottomNav from './components/BottomNav';

export const metadata: Metadata = {
  title: 'DikaAI Dashboard',
  description: 'DikaAI — AI coding agent with memory, context, and tools.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#0c0c14',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Navbar />
        <main className="app-main">{children}</main>
        <BottomNav />
        <div className="footer-line">
          DikaAI v3.2 &middot; Vercel + Upstash Redis
        </div>
      </body>
    </html>
  );
}
