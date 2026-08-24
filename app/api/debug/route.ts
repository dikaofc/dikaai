import { NextResponse } from 'next/server';
import { redisGet, REDIS_URL, REDIS_TOKEN } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function GET() {
  // Show masked env vars and test connection
  const url = REDIS_URL ? REDIS_URL.slice(0, 30) + '...' : '(not set)';
  const token = REDIS_TOKEN ? REDIS_TOKEN.slice(0, 10) + '...' : '(not set)';

  let total = 'N/A';
  let connected = false;
  try {
    const val = await redisGet('dikaai:total');
    total = String(val ?? '(null)');
    connected = true;
  } catch (err: unknown) {
    total = 'error: ' + (err instanceof Error ? err.message : String(err));
  }

  return NextResponse.json({
    url,
    token,
    connected,
    dikaai_total: total,
  });
}
