"""DikaAi Model - Pure Python, optimized for fast convergence

Architecture: Tiny LSTM text predictor
- Pure Python only (no numpy)
- ~122K parameters (tuned from 780K)
- ~4.8 steps/sec (tuned from 0.9)
- Proper BPTT + LR scheduler
"""
import math
import random
import json
from pathlib import Path
from dikaai.config import (
    VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, CONTEXT_LEN, CHUNK_SIZE,
    NUM_LAYERS, MODEL_DIR, LR, LR_MIN, LR_WARMUP, LR_DECAY
)


# ============================================================
# Pure Python Matrix Operations (optimized)
# ============================================================

def _randn(rows, cols, scale=None):
    """Xavier init"""
    if scale is None:
        scale = math.sqrt(2.0 / (rows + cols))
    return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]


def _zeros(rows, cols=0):
    if cols == 0:
        return [0.0] * rows
    return [[0.0] * cols for _ in range(rows)]


def _vecmat(x, W):
    """x: [n], W: [n][m] -> [m]"""
    m = len(W[0])
    n = len(W)
    out = [0.0] * m
    for j in range(m):
        s = 0.0
        Wi = [W[i] for i in range(n)]
        for i in range(n):
            s += x[i] * Wi[i][j]
        out[j] = s
    return out


def _matvec(W, x):
    """W: [m][n], x: [n] -> [m]"""
    m = len(W)
    out = [0.0] * m
    for i in range(m):
        s = 0.0
        Wi = W[i]
        for j in range(len(x)):
            s += Wi[j] * x[j]
        out[i] = s
    return out


def _add(a, b):
    return [a[i] + b[i] for i in range(len(a))]


def _mul(a, b):
    return [a[i] * b[i] for i in range(len(a))]


def _sub(a, b):
    return [a[i] - b[i] for i in range(len(a))]


def _scale(a, s):
    return [x * s for x in a]


def _clip(a, lo=-5.0, hi=5.0):
    return [max(lo, min(hi, x)) for x in a]


# ============================================================
# Activation functions
# ============================================================

def _sigmoid(x):
    return [1.0 / (1.0 + math.exp(-max(-500, min(500, v)))) for v in x]


def _sigmoid_grad(s):
    return [v * (1.0 - v) for v in s]


def _tanh(x):
    return [math.tanh(v) for v in x]


def _tanh_grad(x):
    return [1.0 - v * v for v in x]


def _softmax(x):
    mx = max(x)
    e = [math.exp(v - mx) for v in x]
    s = sum(e)
    return [v / s for v in e]


def _mat_scale(A, s):
    return [_scale(row, s) for row in A]


def _transpose(M):
    rows = len(M)
    cols = len(M[0])
    return [[M[i][j] for i in range(rows)] for j in range(cols)]


def _outer_add(M, a, b):
    """M += outer(a, b) in-place"""
    for i in range(len(a)):
        ai = a[i]
        Mi = M[i]
        for j in range(len(b)):
            Mi[j] += ai * b[j]


def _vec_add(v, a):
    for i in range(len(a)):
        v[i] += a[i]


# ============================================================
# Learning Rate Scheduler
# ============================================================

def get_lr(step, base_lr=LR, min_lr=LR_MIN, warmup=LR_WARMUP, decay=LR_DECAY):
    """Cosine learning rate with warmup."""
    if step < warmup:
        # Linear warmup
        return base_lr * (step + 1) / warmup
    else:
        # Cosine decay
        progress = min((step - warmup) / max(decay, 1), 1.0)
        return min_lr + 0.5 * (base_lr - min_lr) * (1 + math.cos(math.pi * progress))


# ============================================================
# DikaModel
# ============================================================

class DikaModel:
    """
    Ultra-light LSTM text predictor (Pure Python):
    Input token -> Embedding -> LSTM -> Dense -> Softmax -> Next token
    """

    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM,
                 hidden_dim=HIDDEN_DIM, seq_len=CONTEXT_LEN, lr=LR):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        self.lr = lr
        self.step = 0

        # Embedding
        self.embedding = _randn(vocab_size, embed_dim)

        # LSTM gates
        self.W_i = _randn(embed_dim, hidden_dim)
        self.U_i = _randn(hidden_dim, hidden_dim)
        self.b_i = [0.0] * hidden_dim

        self.W_f = _randn(embed_dim, hidden_dim)
        self.U_f = _randn(hidden_dim, hidden_dim)
        self.b_f = [0.1] * hidden_dim

        self.W_g = _randn(embed_dim, hidden_dim)
        self.U_g = _randn(hidden_dim, hidden_dim)
        self.b_g = [0.0] * hidden_dim

        self.W_o = _randn(embed_dim, hidden_dim)
        self.U_o = _randn(hidden_dim, hidden_dim)
        self.b_o = [0.0] * hidden_dim

        # Output layer
        self.W_out = _randn(hidden_dim, vocab_size)
        self.b_out = [0.0] * vocab_size

        # Cache transposes for faster backprop
        self._cache = None
        self._transpose_cache = {}

        self._pnames = [
            'W_i', 'U_i', 'b_i',
            'W_f', 'U_f', 'b_f',
            'W_g', 'U_g', 'b_g',
            'W_o', 'U_o', 'b_o',
            'W_out', 'b_out'
        ]

        self._init_adam()

    def _get_transpose(self, name):
        """Cache transposed matrices for reuse."""
        if name not in self._transpose_cache:
            self._transpose_cache[name] = _transpose(getattr(self, name))
        return self._transpose_cache[name]

    def _invalidate_transpose(self):
        self._transpose_cache.clear()

    def _init_adam(self):
        """Initialize Adam optimizer moments."""
        self.adam_m = {}
        self.adam_v = {}
        self.adam_t = 0

        for name in self._pnames:
            p = getattr(self, name)
            if isinstance(p[0], list):
                self.adam_m[name] = _zeros(len(p), len(p[0]))
                self.adam_v[name] = _zeros(len(p), len(p[0]))
            else:
                self.adam_m[name] = _zeros(len(p))
                self.adam_v[name] = _zeros(len(p))

    def _apply_adam(self, name, grad, lr):
        """Adam update with gradient clipping."""
        self.adam_t += 1
        beta1, beta2, eps = 0.9, 0.999, 1e-8

        if isinstance(grad[0], list):
            m = self.adam_m[name]
            v = self.adam_v[name]
            param = getattr(self, name)
            for i in range(len(param)):
                row_p = param[i]
                row_m = m[i]
                row_v = v[i]
                row_g = grad[i]
                for j in range(len(row_p)):
                    g = max(-5.0, min(5.0, row_g[j]))
                    row_m[j] = beta1 * row_m[j] + (1 - beta1) * g
                    row_v[j] = beta2 * row_v[j] + (1 - beta2) * g * g
                    mh = row_m[j] / (1 - beta1 ** self.adam_t)
                    vh = row_v[j] / (1 - beta2 ** self.adam_t)
                    row_p[j] -= lr * mh / (math.sqrt(vh) + eps)
        else:
            m = self.adam_m[name]
            v = self.adam_v[name]
            param = getattr(self, name)
            for i in range(len(param)):
                g = max(-5.0, min(5.0, grad[i]))
                m[i] = beta1 * m[i] + (1 - beta1) * g
                v[i] = beta2 * v[i] + (1 - beta2) * g * g
                mh = m[i] / (1 - beta1 ** self.adam_t)
                vh = v[i] / (1 - beta2 ** self.adam_t)
                param[i] -= lr * mh / (math.sqrt(vh) + eps)

    def get_current_lr(self):
        """Get current learning rate with schedule."""
        return get_lr(self.step)

    def forward(self, tokens):
        """Forward pass through LSTM."""
        seq_len = len(tokens)
        embeds = [self.embedding[t] for t in tokens]

        cache = {'embeds': embeds, 'seq_len': seq_len}
        h = [0.0] * self.hidden_dim
        c = [0.0] * self.hidden_dim

        for t in range(seq_len):
            x = embeds[t]

            i_t = _sigmoid(_add(_add(_vecmat(x, self.W_i), _vecmat(h, self.U_i)), self.b_i))
            f_t = _sigmoid(_add(_add(_vecmat(x, self.W_f), _vecmat(h, self.U_f)), self.b_f))
            g_t = _tanh(_add(_add(_vecmat(x, self.W_g), _vecmat(h, self.U_g)), self.b_g))
            o_t = _sigmoid(_add(_add(_vecmat(x, self.W_o), _vecmat(h, self.U_o)), self.b_o))

            c_prev = c[:]
            c = _add(_mul(f_t, c), _mul(i_t, g_t))
            h = _mul(o_t, _tanh(c))

            cache[f'c_prev_{t}'] = c_prev
            cache[f'i_{t}'] = i_t
            cache[f'f_{t}'] = f_t
            cache[f'g_{t}'] = g_t
            cache[f'o_{t}'] = o_t
            cache[f'c_{t}'] = c
            cache[f'h_{t}'] = h

        cache['h_final'] = h
        logits = _add(_vecmat(h, self.W_out), self.b_out)
        cache['logits'] = logits
        self._cache = cache

        return logits

    def predict(self, tokens, top_k=5):
        """Predict next token with probabilities."""
        logits = self.forward(tokens)
        probs = _softmax(logits)
        indexed = sorted(enumerate(probs), key=lambda x: -x[1])[:top_k]
        return [(idx, prob) for idx, prob in indexed]

    def generate(self, tokens, max_len=30, temperature=0.7, tokenizer=None):
        """Generate text continuation."""
        generated = list(tokens)

        for _ in range(max_len):
            input_seq = generated[-self.seq_len:]
            logits = self.forward(input_seq)
            logits = [v / temperature for v in logits]
            probs = _softmax(logits)

            # Nucleus sampling
            indexed = sorted(enumerate(probs), key=lambda x: -x[1])
            cumsum = 0.0
            cutoff = 0.92
            chosen = []
            for idx, p in indexed:
                chosen.append((idx, p))
                cumsum += p
                if cumsum >= cutoff:
                    break

            total = sum(p for _, p in chosen)
            r = random.random() * total
            cum = 0.0
            next_token = chosen[0][0]
            for idx, p in chosen:
                cum += p
                if cum >= r:
                    next_token = idx
                    break

            if next_token == 0:
                break
            generated.append(next_token)

        return generated

    def train_step(self, input_tokens, target_token):
        """Single training step with BPTT + LR schedule."""
        # Get scheduled LR
        current_lr = get_lr(self.step)

        seq_len = len(input_tokens)
        logits = self.forward(input_tokens)
        probs = _softmax(logits)

        # Cross-entropy loss
        loss = -math.log(probs[target_token] + 1e-8)

        # Backprop through output layer
        d_logits = _sub(probs, [1.0 if i == target_token else 0.0 for i in range(self.vocab_size)])
        h_final = self._cache['h_final']

        d_W_out = [[h_final[i] * d_logits[j] for j in range(len(d_logits))] for i in range(len(h_final))]
        d_b_out = d_logits

        # Gradient into LSTM
        d_h = _matvec(self.W_out, d_logits)
        d_c = [0.0] * self.hidden_dim

        # Accumulated gradients
        gW_i = _zeros(self.embed_dim, self.hidden_dim)
        gU_i = _zeros(self.hidden_dim, self.hidden_dim)
        gb_i = [0.0] * self.hidden_dim
        gW_f = _zeros(self.embed_dim, self.hidden_dim)
        gU_f = _zeros(self.hidden_dim, self.hidden_dim)
        gb_f = [0.0] * self.hidden_dim
        gW_g = _zeros(self.embed_dim, self.hidden_dim)
        gU_g = _zeros(self.hidden_dim, self.hidden_dim)
        gb_g = [0.0] * self.hidden_dim
        gW_o = _zeros(self.embed_dim, self.hidden_dim)
        gU_o = _zeros(self.hidden_dim, self.hidden_dim)
        gb_o = [0.0] * self.hidden_dim
        g_embeds = [None] * seq_len

        zero_h = [0.0] * self.hidden_dim

        # Get transposed matrices (cached)
        tW_i = self._get_transpose('W_i')
        tW_f = self._get_transpose('W_f')
        tW_g = self._get_transpose('W_g')
        tW_o = self._get_transpose('W_o')
        tU_i = self._get_transpose('U_i')
        tU_f = self._get_transpose('U_f')
        tU_g = self._get_transpose('U_g')
        tU_o = self._get_transpose('U_o')

        for t in range(seq_len - 1, -1, -1):
            x_t = self._cache['embeds'][t]
            c_t = self._cache[f'c_{t}']
            c_prev = self._cache[f'c_prev_{t}']
            i_t = self._cache[f'i_{t}']
            f_t = self._cache[f'f_{t}']
            g_t = self._cache[f'g_{t}']
            o_t = self._cache[f'o_{t}']
            h_prev = self._cache.get(f'h_{t-1}', zero_h)

            tanh_c = _tanh(c_t)
            d_o = _mul(_mul(d_h, tanh_c), _sigmoid_grad(o_t))
            d_c_new = _add(d_c, _mul(_mul(d_h, o_t), _tanh_grad(tanh_c)))

            d_i = _mul(_mul(d_c_new, g_t), _sigmoid_grad(i_t))
            d_f = _mul(_mul(d_c_new, c_prev), _sigmoid_grad(f_t))
            d_g = _mul(_mul(d_c_new, i_t), _tanh_grad(g_t))

            _outer_add(gW_i, x_t, d_i)
            _outer_add(gU_i, h_prev, d_i)
            _vec_add(gb_i, d_i)

            _outer_add(gW_f, x_t, d_f)
            _outer_add(gU_f, h_prev, d_f)
            _vec_add(gb_f, d_f)

            _outer_add(gW_g, x_t, d_g)
            _outer_add(gU_g, h_prev, d_g)
            _vec_add(gb_g, d_g)

            _outer_add(gW_o, x_t, d_o)
            _outer_add(gU_o, h_prev, d_o)
            _vec_add(gb_o, d_o)

            # Embedding grad (use cached transposes)
            d_embed = _add(
                _add(_vecmat(d_i, tW_i), _vecmat(d_f, tW_f)),
                _add(_vecmat(d_g, tW_g), _vecmat(d_o, tW_o))
            )
            g_embeds[t] = d_embed

            # Flow gradient back (use cached transposes)
            d_h = _add(
                _add(_vecmat(d_i, tU_i), _vecmat(d_f, tU_f)),
                _add(_vecmat(d_g, tU_g), _vecmat(d_o, tU_o))
            )
            d_c = _mul(d_c_new, f_t)

        # Apply gradients with scheduled LR
        n = max(seq_len, 1)
        self._apply_adam('W_out', _mat_scale(d_W_out, 1.0 / n), current_lr)
        self._apply_adam('b_out', _scale(d_b_out, 1.0 / n), current_lr)
        self._apply_adam('W_i', _mat_scale(gW_i, 1.0 / n), current_lr)
        self._apply_adam('U_i', _mat_scale(gU_i, 1.0 / n), current_lr)
        self._apply_adam('b_i', _scale(gb_i, 1.0 / n), current_lr)
        self._apply_adam('W_f', _mat_scale(gW_f, 1.0 / n), current_lr)
        self._apply_adam('U_f', _mat_scale(gU_f, 1.0 / n), current_lr)
        self._apply_adam('b_f', _scale(gb_f, 1.0 / n), current_lr)
        self._apply_adam('W_g', _mat_scale(gW_g, 1.0 / n), current_lr)
        self._apply_adam('U_g', _mat_scale(gU_g, 1.0 / n), current_lr)
        self._apply_adam('b_g', _scale(gb_g, 1.0 / n), current_lr)
        self._apply_adam('W_o', _mat_scale(gW_o, 1.0 / n), current_lr)
        self._apply_adam('U_o', _mat_scale(gU_o, 1.0 / n), current_lr)
        self._apply_adam('b_o', _scale(gb_o, 1.0 / n), current_lr)

        # Embedding gradients
        for t in range(seq_len):
            idx = input_tokens[t]
            if g_embeds[t] is not None:
                g = _clip(g_embeds[t], -5.0, 5.0)
                emb = self.embedding[idx]
                for j in range(self.embed_dim):
                    emb[j] -= current_lr * g[j] / (n + 1e-8)

        self._cache = None
        self.step += 1
        return loss

    def train_step_chunked(self, input_tokens, target_token, chunk_size=None):
        """
        Truncated BPTT: split long sequences into chunks.
        This keeps training fast while allowing long contexts.
        """
        if chunk_size is None:
            chunk_size = CHUNK_SIZE

        seq_len = len(input_tokens)

        # If short enough, use normal training
        if seq_len <= chunk_size:
            return self.train_step(input_tokens, target_token)

        # Split into chunks and train each
        total_loss = 0.0
        num_chunks = 0

        for start in range(0, seq_len, chunk_size):
            end = min(start + chunk_size, seq_len)
            chunk = input_tokens[start:end]

            if len(chunk) < 2:
                continue

            # Target is the token after this chunk (or final target)
            if end < seq_len:
                chunk_target = input_tokens[end]  # Next token prediction
            else:
                chunk_target = target_token

            loss = self.train_step(chunk, chunk_target)
            total_loss += loss
            num_chunks += 1

        return total_loss / max(num_chunks, 1)

    def generate_long(self, tokens, max_len=50, temperature=0.7, chunk_size=None):
        """
        Generate text with sliding window for long outputs.
        """
        if chunk_size is None:
            chunk_size = CHUNK_SIZE

        generated = list(tokens)

        for _ in range(max_len):
            # Use last chunk_size tokens as context
            input_seq = generated[-chunk_size:]
            logits = self.forward(input_seq)
            logits = [v / temperature for v in logits]
            probs = _softmax(logits)

            # Nucleus sampling
            indexed = sorted(enumerate(probs), key=lambda x: -x[1])
            cumsum = 0.0
            chosen = []
            for idx, p in indexed:
                chosen.append((idx, p))
                cumsum += p
                if cumsum >= 0.92:
                    break

            total = sum(p for _, p in chosen)
            r = random.random() * total
            cum = 0.0
            next_token = chosen[0][0]
            for idx, p in chosen:
                cum += p
                if cum >= r:
                    next_token = idx
                    break

            if next_token == 0:
                break
            generated.append(next_token)

        return generated

    def save(self, path=None):
        """Save model weights to JSON."""
        MODEL_DIR.mkdir(exist_ok=True)
        if path is None:
            path = MODEL_DIR / "dikaai_latest.json"

        data = {
            'vocab_size': self.vocab_size,
            'embed_dim': self.embed_dim,
            'hidden_dim': self.hidden_dim,
            'step': self.step,
            'embedding': self.embedding,
            'W_i': self.W_i, 'U_i': self.U_i, 'b_i': self.b_i,
            'W_f': self.W_f, 'U_f': self.U_f, 'b_f': self.b_f,
            'W_g': self.W_g, 'U_g': self.U_g, 'b_g': self.b_g,
            'W_o': self.W_o, 'U_o': self.U_o, 'b_o': self.b_o,
            'W_out': self.W_out, 'b_out': self.b_out,
        }

        with open(str(path), 'w') as f:
            json.dump(data, f)

        return str(path)

    def load(self, path=None):
        """Load model weights from JSON."""
        if path is None:
            path = MODEL_DIR / "dikaai_latest.json"

        if not Path(path).exists():
            return False

        try:
            with open(str(path), 'r') as f:
                data = json.load(f)

            self.vocab_size = data['vocab_size']
            self.embed_dim = data['embed_dim']
            self.hidden_dim = data['hidden_dim']
            self.step = data['step']
            self.embedding = data['embedding']
            self.W_i = data['W_i']
            self.U_i = data['U_i']
            self.b_i = data['b_i']
            self.W_f = data['W_f']
            self.U_f = data['U_f']
            self.b_f = data['b_f']
            self.W_g = data['W_g']
            self.U_g = data['U_g']
            self.b_g = data['b_g']
            self.W_o = data['W_o']
            self.U_o = data['U_o']
            self.b_o = data['b_o']
            self.W_out = data['W_out']
            self.b_out = data['b_out']

            self._init_adam()
            self._invalidate_transpose()
            return True
        except Exception:
            return False

    def get_param_count(self) -> int:
        """Count total parameters."""
        count = len(self.embedding) * len(self.embedding[0])
        for name in self._pnames:
            p = getattr(self, name)
            if isinstance(p[0], list):
                count += len(p) * len(p[0])
            else:
                count += len(p)
        return count
