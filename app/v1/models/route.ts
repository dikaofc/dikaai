import { NextResponse } from 'next/server';
import { redisGet, redisHgetall } from '@/lib/redis';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const model = await redisHgetall('dikaai:model');
    const vocabSize = Number(model.vocab_size || await redisGet('dikaai:vocab_size') || 0);

    return NextResponse.json({
      data: [
        {
          id: 'dikaai-lstm',
          object: 'model',
          created: Number(model.synced_at) || 0,
          owned_by: 'dikaai',
          permission: [],
          root: 'dikaai-lstm',
          parent: null,
        },
      ],
      info: {
        name: 'DikaAI',
        version: '3.2',
        architecture: 'LSTM',
        params: Number(model.params || 0),
        vocab_size: vocabSize,
        embed_dim: Number(model.embed_dim || 0),
        hidden_dim: Number(model.hidden_dim || 0),
        num_layers: Number(model.num_layers || 0),
        step: Number(model.step || 0),
        device: 'gpu',
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Models error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
