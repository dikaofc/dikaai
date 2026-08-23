"""DikaAi Model - PyTorch LSTM (GPU-accelerated, batched training)

Architecture: Embedding -> LSTM -> Linear -> Softmax (next-token predictor)

Backend is selected at import time:
  * If PyTorch is available -> nn.Module on CUDA/CPU (used by Colab training).
  * If PyTorch is missing    -> falls back to a plain `object` base so that
    importing this module (and the `dikaai` package) does NOT fail on the
    torch-free Vercel/API server. The heavy weights live in a `.pt` file; a
    small `.json` sidecar (with `params`, `step`, `vocab_size`) is what the
    dashboard reads, so no torch is needed server-side.
"""
import math
import random
import json
from pathlib import Path

from dikaai.config import (
    VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, CONTEXT_LEN, CHUNK_SIZE,
    NUM_LAYERS, MODEL_DIR, LR, LR_MIN, LR_WARMUP, LR_DECAY
)

try:
    import torch
    from torch import nn
    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - torchless environments (Vercel)
    torch = None
    nn = object
    TORCH_AVAILABLE = False


_BASE = nn.Module if TORCH_AVAILABLE else object


def get_lr(step, base_lr=LR, min_lr=LR_MIN, warmup=LR_WARMUP, decay=LR_DECAY):
    """Cosine learning rate with linear warmup (matches old schedule)."""
    if step < warmup:
        return base_lr * (step + 1) / warmup
    progress = min((step - warmup) / max(decay, 1), 1.0)
    return min_lr + 0.5 * (base_lr - min_lr) * (1 + math.cos(math.pi * progress))


class DikaModel(_BASE):
    """
    LSTM text predictor (PyTorch).

    Public interface preserved for all callers:
      DikaModel() / DikaModel(vocab_size=...)
      .step, .vocab_size, .embed_dim, .hidden_dim, .seq_len, .lr
      .resize_vocab(n), .get_param_count()
      .generate(tokens, max_len, temperature, tokenizer=None)
      .predict(tokens, top_k)
      .train_step_chunked(padded, target)        # single-seq shim (train_coding)
      .train_on_batch(pairs)                       # batched (GPU)
      .save() / .load()
    """

    def __init__(self, vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM,
                 hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS,
                 seq_len=CONTEXT_LEN, lr=LR):
        if TORCH_AVAILABLE:
            super().__init__()

        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.seq_len = seq_len
        self.lr = lr
        self.step = 0

        if not TORCH_AVAILABLE:
            return  # Vercel/API: never instantiated, but importable.

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

        # Adam optimizer (LR set per-step via get_lr).
        self.optimizer = torch.optim.Adam(self.parameters(), lr=self.lr)
        self._init_weights()
        self.to(self.device)

    def _init_weights(self):
        with torch.no_grad():
            nn.init.xavier_uniform_(self.embedding.weight)
            for name, p in self.lstm.named_parameters():
                if 'weight' in name:
                    nn.init.xavier_uniform_(p)
                else:
                    nn.init.zeros_(p)
            nn.init.xavier_uniform_(self.fc.weight)
            nn.init.zeros_(self.fc.bias)

    # ----------------------------------------------------------------
    # Forward
    # ----------------------------------------------------------------
    def forward(self, x):
        """
        x: either a 1-D list[int] (single sequence) or a 2-D (B, L) tensor/list.
        Returns logits shaped (L, V) for single-seq or (B, L, V) for batch.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available; model cannot run forward.")

        single = isinstance(x, (list, tuple)) and (len(x) == 0 or not isinstance(x[0], (list, tuple)))
        if isinstance(x, list):
            x = torch.tensor(x, dtype=torch.long, device=self.device)
        if x.dim() == 1:
            x = x.unsqueeze(0)  # (1, L)

        emb = self.embedding(x)               # (B, L, E)
        out, _ = self.lstm(emb)              # (B, L, H)
        logits = self.fc(out)                # (B, L, V)

        if single:
            return logits[0]                 # (L, V)
        return logits                        # (B, L, V)

    # ----------------------------------------------------------------
    # Generation (used by bot / engine / executor / dashboard)
    # ----------------------------------------------------------------
    def generate(self, tokens, max_len=30, temperature=0.7, tokenizer=None):
        """Greedy + nucleus sampling. tokens: list[int]. Returns list[int]."""
        if not TORCH_AVAILABLE:
            return list(tokens)
        self.eval()
        generated = list(tokens)
        with torch.no_grad():
            for _ in range(max_len):
                seq = generated[-self.seq_len:]
                x = torch.tensor(seq, dtype=torch.long, device=self.device).unsqueeze(0)
                logits = self.forward(x)[-1].float() / max(temperature, 1e-3)
                probs = torch.softmax(logits, dim=-1).cpu().tolist()

                indexed = sorted(enumerate(probs), key=lambda kv: -kv[1])
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
                nxt = chosen[0][0]
                for idx, p in chosen:
                    cum += p
                    if cum >= r:
                        nxt = idx
                        break
                if nxt == 0:
                    break
                generated.append(nxt)
        return generated

    def predict(self, tokens, top_k=5):
        """Return top-k (idx, prob) for the next token."""
        if not TORCH_AVAILABLE:
            return []
        self.eval()
        with torch.no_grad():
            x = torch.tensor(tokens, dtype=torch.long, device=self.device).unsqueeze(0)
            logits = self.forward(x)[-1].float()
            probs = torch.softmax(logits, dim=-1).cpu().tolist()
        indexed = sorted(enumerate(probs), key=lambda kv: -kv[1])[:top_k]
        return [(idx, prob) for idx, prob in indexed]

    # ----------------------------------------------------------------
    # Resize vocab (called by trainer when new tokens appear)
    # ----------------------------------------------------------------
    def resize_vocab(self, new_vocab_size):
        if not TORCH_AVAILABLE:
            self.vocab_size = new_vocab_size
            return
        if new_vocab_size == self.vocab_size:
            return
        old_size = self.vocab_size
        with torch.no_grad():
            # Grow embedding rows.
            new_emb = nn.Embedding(new_vocab_size, self.embed_dim).to(self.device)
            copy = min(old_size, new_vocab_size)
            new_emb.weight[:copy] = self.embedding.weight[:copy]
            if new_vocab_size > old_size:
                nn.init.xavier_uniform_(new_emb.weight[copy:])
            self.embedding = new_emb

            # Grow output layer columns.
            new_fc = nn.Linear(self.hidden_dim, new_vocab_size).to(self.device)
            new_fc.weight[:copy] = self.fc.weight[:copy]
            new_fc.bias[:copy] = self.fc.bias[:copy]
            if new_vocab_size > old_size:
                nn.init.xavier_uniform_(new_fc.weight[copy:])
                nn.init.zeros_(new_fc.bias[copy:])
            self.fc = new_fc

        self.vocab_size = new_vocab_size
        self.optimizer = torch.optim.Adam(self.parameters(), lr=get_lr(self.step))
        print(f"  [MODEL] Resized vocab: {old_size} -> {new_vocab_size}")

    # ----------------------------------------------------------------
    # Training
    # ----------------------------------------------------------------
    def _collate(self, pairs):
        """pairs: list of (context_tokens:list[int], target:int).
        Returns (x_tensor (B,L), y_tensor (B,), real_len (list))."""
        xs = [torch.tensor(c, dtype=torch.long) for c, _ in pairs]
        ys = torch.tensor([t for _, t in pairs], dtype=torch.long, device=self.device)
        x = torch.nn.utils.rnn.pad_sequence(xs, batch_first=True,
                                            padding_value=0).to(self.device)
        real_len = [len(c) for c, _ in pairs]
        return x, ys, real_len

    def train_on_batch(self, pairs):
        """Batched next-token training step. pairs -> single (B,L)/(B,) forward.
        Returns average NLL loss (float). Increments self.step by 1."""
        if not TORCH_AVAILABLE or not pairs:
            return 0.0
        self.train()
        x, y, real_len = self._collate(pairs)
        self.optimizer.zero_grad(set_to_none=True)

        logits = self.forward(x)                      # (B, L, V)
        # Predict the token right after each context (last real position).
        idx = torch.tensor([max(l - 1, 0) for l in real_len],
                           dtype=torch.long, device=self.device)
        batch_idx = torch.arange(x.size(0), device=self.device)
        last_logits = logits[batch_idx, idx]          # (B, V)

        loss = torch.nn.functional.cross_entropy(last_logits, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), 5.0)

        for g in self.optimizer.param_groups:
            g['lr'] = get_lr(self.step)
        self.optimizer.step()
        self.step += 1
        return float(loss.item())

    def train_step_chunked(self, input_tokens, target_token, chunk_size=None):
        """Single-sequence shim (used by trainer.train_coding)."""
        if not TORCH_AVAILABLE:
            return 0.0
        return self.train_on_batch([(list(input_tokens), int(target_token))])

    # ----------------------------------------------------------------
    # Save / load  (.pt weights + .json sidecar for torch-free dashboards)
    # ----------------------------------------------------------------
    def get_param_count(self):
        if not TORCH_AVAILABLE:
            return 0
        return sum(p.numel() for p in self.parameters())

    def save(self, path=None):
        MODEL_DIR.mkdir(exist_ok=True)
        if path is None:
            path = MODEL_DIR / "dikaai_latest.json"
        pt_path = MODEL_DIR / "dikaai_latest.pt"

        if TORCH_AVAILABLE:
            state = {
                'vocab_size': self.vocab_size,
                'embed_dim': self.embed_dim,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers,
                'seq_len': self.seq_len,
                'step': self.step,
                'state_dict': self.state_dict(),
            }
            torch.save(state, str(pt_path))

        # JSON sidecar (torch-free): what the Vercel dashboard reads.
        data = {
            'vocab_size': self.vocab_size,
            'embed_dim': self.embed_dim,
            'hidden_dim': self.hidden_dim,
            'num_layers': self.num_layers,
            'step': self.step,
            'params': self.get_param_count(),
        }
        with open(str(path), 'w') as f:
            json.dump(data, f)
        return str(path)

    def load(self, path=None):
        if path is None:
            path = MODEL_DIR / "dikaai_latest.json"
        pt_path = MODEL_DIR / "dikaai_latest.pt"

        if TORCH_AVAILABLE and Path(pt_path).exists():
            try:
                state = torch.load(str(pt_path), map_location=self.device)
                # Resize to match checkpoint if needed.
                self.vocab_size = state['vocab_size']
                self.embed_dim = state['embed_dim']
                self.hidden_dim = state['hidden_dim']
                self.num_layers = state.get('num_layers', self.num_layers)
                self.seq_len = state.get('seq_len', self.seq_len)
                # Rebuild layers at the right size, then load weights.
                self.embedding = nn.Embedding(self.vocab_size, self.embed_dim).to(self.device)
                self.lstm = nn.LSTM(self.embed_dim, self.hidden_dim,
                                    num_layers=self.num_layers, batch_first=True).to(self.device)
                self.fc = nn.Linear(self.hidden_dim, self.vocab_size).to(self.device)
                self.load_state_dict(state['state_dict'], strict=False)
                self.step = state.get('step', 0)
                self.optimizer = torch.optim.Adam(self.parameters(), lr=get_lr(self.step))
                self.to(self.device)
                return True
            except Exception:
                pass

        # Fallback: read JSON metadata only (no torch weights).
        if Path(path).exists():
            try:
                with open(str(path), 'r') as f:
                    data = json.load(f)
                self.vocab_size = data.get('vocab_size', self.vocab_size)
                self.step = data.get('step', 0)
                return True
            except Exception:
                return False
        return False
