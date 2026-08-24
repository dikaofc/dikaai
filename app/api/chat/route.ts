import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisHgetall } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message = (body.message || '').trim();
    if (!message) {
      return NextResponse.json({ error: 'empty message' }, { status: 400 });
    }

    const start = Date.now();

    // Try to get the latest response from the engine stored in Redis
    let reply = '';
    try {
      const engineState = await redisHgetall('dikaai:engine');
      if (engineState && engineState.response) {
        reply = engineState.response;
      }
    } catch { /* engine not available */ }

    // The AI runs remotely on Colab — Vercel is just the dashboard.
    // No fake replies. Return what we have.
    if (!reply) {
      reply = '🧠 DikaAI sedang memproses di remote server. Model sedang training — balasan cerdas akan tersedia setelah training selesai.';
    }

    const elapsed = ((Date.now() - start) / 1000).toFixed(1);

    return NextResponse.json({
      response: reply,
      reply,
      route: 'chat',
      topic: 'general',
      time: `${elapsed}s`,
      success: true,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Chat error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
