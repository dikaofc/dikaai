import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisHgetall } from '@/lib/redis';
import { getSmartReply } from '@/lib/smart_reply';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message = (body.message || '').trim();
    if (!message) {
      return NextResponse.json({ error: 'empty message' }, { status: 400 });
    }

    const start = Date.now();

    // Try to get model-generated reply from Redis (Colab may have written one)
    let modelReply: string | undefined;
    try {
      const engineState = await redisHgetall('dikaai:engine');
      if (engineState && engineState.response) {
        modelReply = engineState.response;
      }
    } catch { /* engine not available */ }

    // Use real smart reply system (same as Colab bot uses)
    const reply = getSmartReply(message, modelReply);

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
