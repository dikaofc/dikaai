import { NextResponse } from 'next/server';
import { redisLrange } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const raw = await redisLrange('dikaai:training', 0, -1);
    const history: any[] = [];
    for (const h of raw || []) {
      try {
        const e = typeof h === 'string' ? JSON.parse(h) : h;
        if (e && typeof e === 'object' && 'loss' in e) history.push(e);
      } catch { /* skip */ }
    }

    // Build CSV
    const lines = ['timestamp,datetime,loss,steps,total_steps,avg_loss,total_messages'];
    for (const h of history) {
      const ts = Number(h.ts || 0);
      const dt = new Date(ts * 1000).toISOString().replace('T', ' ').slice(0, 19);
      lines.push(
        `${ts.toFixed(3)},${dt},${Number(h.loss || 0).toFixed(6)},${h.steps || 0},${h.total_steps || 0},${Number(h.avg_loss || 0).toFixed(6)},${h.total_messages || 0}`
      );
    }

    return new NextResponse(lines.join('\n'), {
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': 'attachment; filename="dikaai_training.csv"',
      },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Export error' }, { status: 500 });
  }
}
