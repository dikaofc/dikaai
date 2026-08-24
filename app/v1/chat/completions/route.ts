import { NextRequest, NextResponse } from 'next/server';
import { redisGet, redisHgetall, redisLpush, redisLtrim } from '@/lib/redis';
import { getSmartReply } from '@/lib/smart_reply';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages = body.messages || [];
    const lastMsg = messages[messages.length - 1];
    const message = (lastMsg?.content || body.message || '').trim();

    if (!message) {
      return NextResponse.json({ error: 'No message provided' }, { status: 400 });
    }

    const start = Date.now();
    const reqId = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

    let reply = '';
    let modelSourced = false;

    // 1. Write to Redis queue for Colab model
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
    } catch { /* Redis unavailable */ }

    // 3. Fallback: local smart reply
    if (!reply) {
      reply = getSmartReply(message);
    }

    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    const model = await redisHgetall('dikaai:model');
    const modelName = body.model || 'dikaai-lstm';

    // OpenAI-compatible response format
    return NextResponse.json({
      id: 'chatcmpl-' + reqId,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: modelName,
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: reply,
          },
          finish_reason: 'stop',
        },
      ],
      usage: {
        prompt_tokens: message.split(/\s+/).length,
        completion_tokens: reply.split(/\s+/).length,
        total_tokens: message.split(/\s+/).length + reply.split(/\s+/).length,
      },
      x_dikaai: {
        model_step: Number(model.step || 0),
        vocab_size: Number(model.vocab_size || 0),
        params: Number(model.params || 0),
        model_sourced: modelSourced,
        response_time: `${elapsed}s`,
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Chat completion error';
    return NextResponse.json({ error: { message, type: 'server_error' } }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'POST a message to /v1/chat/completions',
    format: {
      model: 'dikaai-lstm',
      messages: [{ role: 'user', content: 'Hello!' }],
    },
  });
}
