import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisSet } from '@/lib/redis';

export const dynamic = 'force-dynamic';

const VALID_FEATURES = ['auto_reply', 'training', 'scraping'];

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const feature = (body.feature || '').trim();

    if (!VALID_FEATURES.includes(feature)) {
      return NextResponse.json(
        { error: `Invalid feature. Must be one of: ${VALID_FEATURES.join(', ')}` },
        { status: 400 },
      );
    }

    const key = `dikaai:toggle:${feature}`;

    // If enabled is provided, set it; otherwise toggle current state
    if (body.enabled !== undefined) {
      const value = body.enabled ? '1' : '0';
      await redisSet(key, value);
      return NextResponse.json({ ok: true, feature, enabled: body.enabled });
    } else {
      // Toggle: read current, flip it
      const current = await redisGet(key);
      const newEnabled = current === '0' ? true : false;
      await redisSet(key, newEnabled ? '1' : '0');
      return NextResponse.json({ ok: true, feature, enabled: newEnabled });
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Toggle error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function GET() {
  try {
    const autoReply = await redisGet('dikaai:toggle:auto_reply');
    const training = await redisGet('dikaai:toggle:training');
    const scraping = await redisGet('dikaai:toggle:scraping');

    return NextResponse.json({
      auto_reply: autoReply !== '0',
      training: training !== '0',
      scraping: scraping !== '0',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Toggle error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
