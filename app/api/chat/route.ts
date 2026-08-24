import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisHgetall, redisLpush, redisLtrim, redisIncr } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message = (body.message || '').trim();
    if (!message) {
      return NextResponse.json({ error: 'empty message' }, { status: 400 });
    }

    const start = Date.now();

    // Try to get a reply from the engine stored in Redis
    let reply = '';
    try {
      const engineState = await redisHgetall('dikaai:engine');
      if (engineState && engineState.response) {
        reply = engineState.response;
      }
    } catch { /* engine not available */ }

    // Fallback: simple pattern-based reply
    if (!reply) {
      reply = generateSimpleReply(message);
    }

    const elapsed = ((Date.now() - start) / 1000).toFixed(1);

    // Store in recent messages
    try {
      const msg = JSON.stringify({ m: message, t: Date.now() });
      await redisLpush('dikaai:recent', msg);
      await redisLtrim('dikaai:recent', 0, 49);
      await redisIncr('dikaai:total');
    } catch { /* best effort */ }

    return NextResponse.json({
      response: reply,
      reply,
      route: 'chat',
      topic: 'general',
      time: `${elapsed}s`,
      success: true,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message || 'Chat error' },
      { status: 500 }
    );
  }
}

function generateSimpleReply(message: string): string {
  const lower = message.toLowerCase();

  if (lower.includes('halo') || lower.includes('hai') || lower.includes('hello') || lower.includes('hi')) {
    return 'Halo! 👋 Ada yang bisa saya bantu?';
  }
  if (lower.includes('apa kabar') || lower.includes('how are you')) {
    return 'Saya baik, terima kasih! Siap membantu Anda. 😊';
  }
  if (lower.includes('siapa kamu') || lower.includes('who are you')) {
    return 'Saya DikaAI, AI coding agent dengan memory dan tools. Dibuat oleh Dika! 🤖';
  }
  if (lower.includes('terima kasih') || lower.includes('thank')) {
    return 'Sama-sama! Senang bisa membantu. 🙏';
  }

  return `Saya menerima pesan Anda: "${message}". DikaAI sedang dalam mode sederhana — training model sedang berjalan di background. Silakan coba lagi nanti untuk respons yang lebih cerdas! 🧠`;
}
