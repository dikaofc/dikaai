import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisLpush, redisLtrim } from '@/lib/redis';
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
    const reqId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

    // 1. Write query to Redis queue for Colab to process
    let reply = '';
    let modelSourced = false;
    try {
      const request = JSON.stringify({ id: reqId, message, ts: Date.now() });
      await redisLpush('dikaai:chat:requests', request);
      await redisLtrim('dikaai:chat:requests', 0, 9);

      // 2. Poll for Colab response (max 8 seconds)
      const deadline = Date.now() + 8000;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 500));
        const respRaw = await redisGet('dikaai:chat:response:' + reqId);
        if (respRaw) {
          const resp = typeof respRaw === 'string' ? JSON.parse(respRaw) : respRaw;
          if (resp && resp.response) {
            reply = resp.response;
            modelSourced = true;
            break;
          }
        }
      }
    } catch { /* Redis unavailable, fall through to local reply */ }

    // 3. Fallback: local smart reply (same system as Colab bot)
    if (!reply) {
      reply = getSmartReply(message);
    }

    const elapsed = ((Date.now() - start) / 1000).toFixed(1);

    return NextResponse.json({
      response: reply,
      reply,
      route: 'chat',
      topic: 'general',
      time: `${elapsed}s`,
      model: modelSourced,
      success: true,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Chat error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
