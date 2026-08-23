"""DikaAi Trainer - Fully Automatic, no manual steps"""
import time
import random
import gc
from model import DikaModel, get_lr
from tokenizer import DikaTokenizer, _is_noise, _is_indonesian
from database import DikaDB
from config import (
    BATCH_SIZE, MAX_TRAIN_STEPS, CONTEXT_LEN, CHUNK_SIZE,
    MODEL_DIR, TRAIN_INTERVAL, GRAD_ACCUM, LR, LR_MIN
)

try:
    from dashboard import record_loss, set_state
except ImportError:
    record_loss = lambda *a: None
    set_state = lambda **a: None


class DikaTrainer:
    def __init__(self, db: DikaDB):
        self.db = db
        self.model = DikaModel()
        self.tokenizer = DikaTokenizer()
        self.training = False
        self.total_loss = 0.0
        self.total_steps = 0
        self.best_loss = float('inf')
        self._last_msg_count = self.db.get_stats()['total']

        MODEL_DIR.mkdir(exist_ok=True)

        if self.model.load():
            print(f"  [TRAINER] Loaded model at step {self.model.step}")
        else:
            print("  [TRAINER] No saved model, starting fresh")

        if self.tokenizer.load():
            print(f"  [TRAINER] Loaded vocab: {self.tokenizer.vocab_size} tokens")
        else:
            print("  [TRAINER] No vocab, will build from DB")

    def build_vocab(self):
        """Rebuild vocabulary from all messages."""
        messages = self.db.get_all_messages(limit=50000)
        if not messages:
            print("  [TRAINER] No messages in DB yet")
            return False

        self.tokenizer.build_vocab(messages)
        self.tokenizer.save()

        # Check if vocab size changed - need to recreate model
        if self.model.vocab_size != self.tokenizer.vocab_size:
            old_step = self.model.step
            print(f"  [TRAINER] Vocab changed {self.model.vocab_size}→{self.tokenizer.vocab_size}, recreating model...")
            self.model = DikaModel(vocab_size=self.tokenizer.vocab_size)
            # Keep old step count for continuity
            self.model.step = old_step

        print(f"  [TRAINER] Built vocab: {self.tokenizer.vocab_size} tokens from {len(messages)} messages")
        return True

    def _check_rebuild_vocab(self):
        """Auto-rebuild vocab if new messages arrived."""
        # Skip if vocab is already loaded
        if self.tokenizer._loaded and self.tokenizer.vocab_size > 0:
            return False
        stats = self.db.get_stats()
        current = stats['total']
        if current - self._last_msg_count > 5000:
            print(f"  [TRAINER] {current - self._last_msg_count} new msgs, rebuilding vocab...")
            self.build_vocab()
            self._last_msg_count = current
            return True
        return False

        if current - self._last_msg_count > 5000:
            print(f"  [TRAINER] {current - self._last_msg_count} new msgs, rebuilding vocab...")
            self.build_vocab()
            self._last_msg_count = current
            return True
        return False

    def _prepare_batch(self):
        """Prepare training pairs - pick random messages, no filtering."""
        all_msgs = self.db.get_all_messages(limit=500)
        if len(all_msgs) < 5:
            return []

        # Pick random messages - INDONESIAN ONLY
        indo_msgs = [m for m in all_msgs if _is_indonesian(m)]
        if len(indo_msgs) < 5:
            indo_msgs = all_msgs[:50]  # Fallback
        sampled = random.sample(indo_msgs, min(16, len(indo_msgs)))

        pairs = []
        for message in sampled:
            tokens = self.tokenizer.encode(message, max_length=CONTEXT_LEN)
            real = [t for t in tokens if t != 0]
            if len(real) < 2:
                continue
            pos = random.randint(1, len(real) - 1)
            context = real[:pos]
            target = real[pos]
            pairs.append((context, target, -1))

        return pairs

    def train_one_epoch(self):
        """Run one training epoch."""
        if not self.tokenizer._loaded:
            if not self.build_vocab():
                return 0.0, 0

        pairs = self._prepare_batch()
        if not pairs:
            return 0.0, 0

        total_loss = 0.0
        count = 0
        processed_ids = set()

        random.shuffle(pairs)

        for input_tokens, target, msg_id in pairs:
            try:
                padded = input_tokens + [0] * (CONTEXT_LEN - len(input_tokens))
                padded = padded[:CONTEXT_LEN]
                loss = self.model.train_step_chunked(padded, target)
                total_loss += loss
                count += 1
                if msg_id != -1:
                    processed_ids.add(msg_id)
            except Exception as e:
                if count == 0 and epoch <= 2:
                    print(f"  [TRAINER] Train error: {e}")
                continue

        if processed_ids:
            self.db.mark_processed(list(processed_ids))

        avg_loss = total_loss / max(count, 1)
        return avg_loss, count

    def continuous_train(self, max_hours=None):
        """Run continuous training loop - fully automatic."""
        self.training = True
        start_time = time.time()
        epoch = 0

        print("\n" + "=" * 55)
        print("  DikaAi Training Started! 🧠 (Fully Automatic)")
        print("=" * 55)

        while self.training:
            epoch += 1

            if max_hours:
                elapsed_hours = (time.time() - start_time) / 3600
                if elapsed_hours >= max_hours:
                    print(f"\n  [TRAINER] Reached {max_hours}h limit")
                    break

            try:
                loss, count = self.train_one_epoch()

                if count > 0:
                    self.total_loss += loss
                    self.total_steps += count
                    record_loss(loss, count)
                    set_state(status='training')

                    avg_all = self.total_loss / max(self.total_steps, 1)
                    stats = self.db.get_stats()
                    current_lr = get_lr(self.model.step)

                    improved = ""
                    if loss < self.best_loss:
                        self.best_loss = loss
                        improved = " ⬇️"

                    print(
                        f"  [Ep {epoch:3d}] "
                        f"loss={loss:.4f}{improved} "
                        f"lr={current_lr:.5f} "
                        f"steps={count:3d} "
                        f"total={self.model.step:5d} "
                        f"| msgs={stats['total']} "
                        f"unproc={stats['unprocessed']} "
                        f"chats={stats['unique_chats']}"
                    )

                    if self.model.step % 50 == 0:
                        self.model.save()
                        self.tokenizer.save()

                    if epoch % 20 == 0:
                        gc.collect()

                else:
                    print(f"  [Ep {epoch:3d}] Waiting for data...")
                    set_state(status='idle')
                    # Auto-rebuild vocab when data arrives
                    self._check_rebuild_vocab()

            except Exception as e:
                print(f"  [TRAINER] Error: {e}")

            time.sleep(TRAIN_INTERVAL)

        self.model.save()
        self.tokenizer.save()
        self.training = False

        print("\n" + "=" * 55)
        print(f"  Training stopped at step {self.model.step}")
        print("=" * 55)

    def stop(self):
        self.training = False


from config import LR_WARMUP
