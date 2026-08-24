import { NextResponse } from 'next/server';
import { redisGet, redisHgetall, redisLrange } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const total = Number(await redisGet('dikaai:total') || 0);
    const processed = Number(await redisGet('dikaai:processed') || 0);
    const uniqueChats = Number(await redisGet('dikaai:unique_chats') || 0);
    const model = await redisHgetall('dikaai:model');
    const recent = await redisLrange('dikaai:recent', 0, 14);

    // Training history
    let history: any[] = [];
    try {
      const raw = await redisLrange('dikaai:training', 0, -1);
      for (const h of raw || []) {
        try {
          const e = typeof h === 'string' ? JSON.parse(h) : h;
          if (e && typeof e === 'object' && 'loss' in e) history.push(e);
        } catch { /* skip */ }
      }
    } catch { /* skip */ }

    const losses = history.map((h) => Number(h.loss || 0));
    const uptime = history.length > 0
      ? Math.max(0, Math.floor(Date.now() / 1000 - Number(history[0].ts || 0)))
      : 0;

    return NextResponse.json({
      db: { total, processed, unprocessed: total - processed, unique_chats: uniqueChats },
      model: {
        params: Number(model.params || 0),
        step: Number(model.step || 0),
        vocab_size: Number(model.vocab_size || 0),
      },
      vocab_tokens: Number(model.vocab_size || 0),
      status: Number(model.step || 0) > 0 ? 'ready' : 'idle',
      uptime,
      toggles: { auto_reply: true, training: true, scraping: true },
      loss_chart: {
        timestamps: history.map((h) => Number(h.ts || 0)),
        losses,
        steps: history.map((h) => Number(h.steps || 0)),
      },
      recent_messages: (recent || []).map((m) => {
        try {
          const d = typeof m === 'string' ? JSON.parse(m) : m;
          return d?.m || d?.message || String(m || '');
        } catch {
          return String(m || '');
        }
      }),
      total_loss: history.reduce((sum, h) => sum + (Number(h.avg_loss || 0) * Number(h.steps || 0)), 0),
      total_steps: history.reduce((sum, h) => sum + Number(h.steps || 0), 0),
      source: 'redis',
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message || 'Failed to load stats', source: 'error' },
      { status: 500 }
    );
  }
}
