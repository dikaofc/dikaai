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

    // Training history — lpush means index 0 = newest, last = oldest
    let history: { ts: number; loss: number; steps: number }[] = [];
    try {
      const raw = await redisLrange('dikaai:training', 0, -1);
      for (const h of raw || []) {
        try {
          const e = typeof h === 'string' ? JSON.parse(h) : h;
          if (e && typeof e === 'object' && 'loss' in e) {
            history.push({
              ts: Number(e.ts || 0),
              loss: Number(e.loss || 0),
              steps: Number(e.steps || 0),
            });
          }
        } catch { /* skip corrupt entry */ }
      }
    } catch { /* skip */ }

    // history[0] = newest (lpush order), history[last] = oldest
    const losses = history.map((h) => h.loss);

    // Uptime = now - oldest training timestamp
    const oldestTs = history.length > 0 ? history[history.length - 1].ts : 0;
    const uptime = oldestTs > 0 ? Math.max(0, Math.floor(Date.now() / 1000 - oldestTs)) : 0;

    // Total accumulated loss = sum of (loss * steps) for each epoch
    const totalLoss = history.reduce(
      (sum, h) => sum + h.loss * h.steps,
      0,
    );
    const totalSteps = history.reduce((sum, h) => sum + h.steps, 0);

    // Read toggles from Redis
    const toggleAutoReply = await redisGet('dikaai:toggle:auto_reply');
    const toggleTraining = await redisGet('dikaai:toggle:training');
    const toggleScraping = await redisGet('dikaai:toggle:scraping');

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
      toggles: {
        auto_reply: toggleAutoReply !== '0',
        training: toggleTraining !== '0',
        scraping: toggleScraping !== '0',
      },
      loss_chart: {
        // Reverse so chart shows chronological (oldest first)
        timestamps: history.map((h) => h.ts).reverse(),
        losses: losses.reverse(),
        steps: history.map((h) => h.steps).reverse(),
      },
      recent_messages: (recent || []).map((m: string) => {
        try {
          const d = typeof m === 'string' ? JSON.parse(m) : m;
          return d?.m || d?.message || String(m || '');
        } catch {
          return String(m || '');
        }
      }),
      total_loss: totalLoss,
      total_steps: totalSteps,
      source: 'redis',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to load stats';
    return NextResponse.json(
      { error: message, source: 'error' },
      { status: 500 },
    );
  }
}
