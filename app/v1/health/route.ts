import { NextResponse } from 'next/server';
import { redisGet, redisHgetall } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const total = Number(await redisGet('dikaai:total') || 0);
    const model = await redisHgetall('dikaai:model');
    const step = Number(model.step || 0);

    return NextResponse.json({
      status: 'ok',
      version: '3.2',
      uptime: process.uptime(),
      redis: 'connected',
      messages: total,
      model_step: step,
      timestamp: new Date().toISOString(),
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Health check failed';
    return NextResponse.json({ status: 'error', error: message }, { status: 500 });
  }
}
