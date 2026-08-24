/**
 * Upstash Redis REST API client — Node.js version.
 * No external dependencies; uses native fetch.
 */

const REDIS_URL = process.env.UPSTASH_REDIS_REST_URL || 'https://touched-rat-161428.upstash.io';
const REDIS_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN || 'gQAAAAAAAnaUAAIgcDE4YTNmYTljNWZkNTg0YTU5ODY2MjA5YmNhOWQ0Mzg4ZQ';

function requireRedis() {
  if (!REDIS_URL || !REDIS_TOKEN) {
    throw new Error(
      'UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set in Vercel Environment Variables'
    );
  }
}

async function redisApi(cmd: string, ...args: string[]): Promise<any> {
  requireRedis();
  const parts = args.map((a) => encodeURIComponent(a));
  const path = [cmd, ...parts].join('/');
  const res = await fetch(`${REDIS_URL}/${path}`, {
    headers: { Authorization: `Bearer ${REDIS_TOKEN}` },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Redis ${cmd} failed (${res.status}): ${body}`);
  }
  const data = await res.json();
  return data.result ?? data;
}

export async function redisGet(key: string) {
  return redisApi('get', key);
}

export async function redisSet(key: string, value: string, ex?: number) {
  if (ex) return redisApi('set', key, value, 'EX', String(ex));
  return redisApi('set', key, value);
}

export async function redisHgetall(key: string): Promise<Record<string, string>> {
  const result = await redisApi('hgetall', key);
  if (!result) return {};
  if (Array.isArray(result)) {
    const obj: Record<string, string> = {};
    for (let i = 0; i < result.length; i += 2) {
      obj[result[i]] = result[i + 1];
    }
    return obj;
  }
  return typeof result === 'object' ? result : {};
}

export async function redisHget(key: string, field: string): Promise<string | null> {
  const result = await redisApi('hget', key, field);
  return result ?? null;
}

export async function redisHset(key: string, ...args: string[]) {
  return redisApi('hset', key, ...args);
}

export async function redisLrange(key: string, start: number, end: number) {
  return redisApi('lrange', key, String(start), String(end));
}

export async function redisLpush(key: string, ...values: string[]) {
  let result = 0;
  for (const v of values) {
    result = await redisApi('lpush', key, v);
  }
  return result;
}

export async function redisLtrim(key: string, start: number, end: number) {
  return redisApi('ltrim', key, String(start), String(end));
}

export async function redisIncr(key: string) {
  return redisApi('incr', key);
}

export async function redisSmembers(key: string): Promise<string[]> {
  const result = await redisApi('smembers', key);
  if (!result) return [];
  if (typeof result === 'string') return [result];
  return Array.isArray(result) ? result : [];
}

export async function redisSadd(key: string, member: string) {
  return redisApi('sadd', key, member);
}

export { REDIS_URL, REDIS_TOKEN };
