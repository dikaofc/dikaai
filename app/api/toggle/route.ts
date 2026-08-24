import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    return NextResponse.json({
      ok: true,
      feature: body.feature || '',
      enabled: body.enabled ?? true,
    });
  } catch {
    return NextResponse.json({ ok: true, feature: '', enabled: true });
  }
}
