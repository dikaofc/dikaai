"""DikaAi Bot - Telegram Userbot + Auto-Reply (Parallel Scraping)

Scrape semua chat dari Telegram secara PARALEL + auto-reply:
- Private chats
- Groups
- Channels
- Bots
"""
import asyncio
import time
import random
import sys
from datetime import datetime
from telethon import TelegramClient, events, functions
from telethon.tl.types import (
    Message,
    User,
    Chat,
    Channel,
    Dialog
)
from dikaai.database import DikaDB
from dikaai.config import (
    API_ID, API_HASH, PHONE, TARGET_ENTITIES,
    AUTO_REPLY_ENABLED, AUTO_REPLY_DELAY, AUTO_REPLY_MIN_LEN,
    TG_CONCURRENT
)

# Use auto-detected concurrent value
MAX_CONCURRENT = TG_CONCURRENT


class DikaBot:
    def __init__(self, db: DikaDB, model=None, tokenizer=None):
        self.db = db
        self.model = model
        self.tokenizer = tokenizer
        self.client = None
        self.running = False
        self.my_id = None
        self.stats = {
            'scraped': 0,
            'new': 0,
            'duplicates': 0,
            'replies': 0
        }
        self._reply_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self._print_lock = asyncio.Lock()

    async def _log(self, msg):
        """Thread-safe print."""
        async with self._print_lock:
            print(msg)

    async def connect(self):
        """Connect to Telegram."""
        if not API_ID or not API_HASH:
            print("  [BOT] ❌ API_ID and API_HASH not set!")
            print("  [BOT] Edit config.env with your credentials from https://my.telegram.org")
            return False

        print("  [BOT] Connecting to Telegram...")
        self.client = TelegramClient(
            'dikaai_session',
            API_ID,
            API_HASH
        )

        await self.client.start(phone=PHONE)

        me = await self.client.get_me()
        self.my_id = me.id
        print(f"  [BOT] ✅ Logged in as: {me.first_name} (@{me.username})")
        return True

    async def scrape_entity(self, entity, limit=None):
        """Scrape messages from a single entity (thread-safe)."""
        async with self._semaphore:
            try:
                title = entity.title if hasattr(entity, 'title') else 'Private'
                chat_id = entity.id
                count = 0

                await self._log(f"  [BOT] 📥 Scraping: {title}...")

                async for message in self.client.iter_messages(
                    entity,
                    limit=limit,
                    reverse=True
                ):
                    if not message.text:
                        continue

                    sender_name = ''
                    if message.sender:
                        if hasattr(message.sender, 'first_name'):
                            sender_name = message.sender.first_name or ''
                        elif hasattr(message.sender, 'title'):
                            sender_name = message.sender.title or ''

                    timestamp = message.date.timestamp() if message.date else time.time()

                    is_new = self.db.add_message(
                        chat_id=chat_id,
                        chat_title=title,
                        sender_name=sender_name,
                        message=message.text,
                        timestamp=timestamp
                    )

                    self.stats['scraped'] += 1
                    if is_new:
                        self.stats['new'] += 1
                        count += 1
                    else:
                        self.stats['duplicates'] += 1

                    if count % 100 == 0 and count > 0:
                        await self._log(f"    -> {count} new messages from {title}")

                await self._log(f"  [BOT] ✅ {title}: {count} new messages")
                return count

            except Exception as e:
                await self._log(f"  [BOT] ⚠️ Error scraping {getattr(entity, 'title', 'unknown')}: {e}")
                return 0

    async def scrape_all(self, limit_per_chat=None):
        """Scrape ALL dialogs in PARALLEL."""
        print("\n" + "=" * 50)
        print("  DikaAi Telegram Scraper 📱 (Parallel)")
        print("=" * 50)

        dialogs = await self.client.get_dialogs()
        print(f"  [BOT] Found {len(dialogs)} dialogs")

        # Categorize dialogs
        entities = []
        for dialog in dialogs:
            if not dialog.entity:
                continue

            entity = dialog.entity

            if TARGET_ENTITIES:
                entity_id = str(entity.id)
                entity_title = getattr(entity, 'title', '')
                if entity_id not in TARGET_ENTITIES and entity_title not in TARGET_ENTITIES:
                    continue

            entities.append(entity)

        # Count by type
        private = sum(1 for e in entities if not hasattr(e, 'title'))
        groups = sum(1 for e in entities if hasattr(e, 'title') and hasattr(e, 'megagroup') and e.megagroup)
        channels = sum(1 for e in entities if hasattr(e, 'title') and not getattr(e, 'megagroup', False))
        bots = sum(1 for e in entities if hasattr(e, 'bot') and e.bot)

        await self._log(f"  [BOT] 📊 Categories:")
        await self._log(f"       Private: {private} | Groups: {groups} | Channels: {channels} | Bots: {bots}")

        # Run all scrapes in PARALLEL (with semaphore limit)
        await self._log(f"\n  [BOT] 🚀 Starting PARALLEL scrape ({MAX_CONCURRENT} concurrent)...")
        start_time = time.time()

        tasks = [
            self.scrape_entity(entity, limit=limit_per_chat)
            for entity in entities
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        total_new = sum(r for r in results if isinstance(r, int))

        await self._log(f"\n" + "=" * 50)
        await self._log(f"  [BOT] 📊 SCRAPE COMPLETE!")
        await self._log(f"  [BOT] Time: {elapsed:.1f}s")
        await self._log(f"  [BOT] Total scraped: {self.stats['scraped']}")
        await self._log(f"  [BOT] New (unique): {self.stats['new']}")
        await self._log(f"  [BOT] Duplicates: {self.stats['duplicates']}")
        await self._log(f"  [BOT] Speed: {self.stats['scraped']/max(elapsed,1):.0f} msgs/sec")
        await self._log("=" * 50)

        return total_new

    async def scrape_recent(self, hours=24):
        """Scrape recent messages (parallel)."""
        print(f"\n  [BOT] Scraping messages from last {hours} hours...")

        dialogs = await self.client.get_dialogs()
        since = datetime.now().timestamp() - (hours * 3600)

        tasks = []
        for dialog in dialogs:
            if not dialog.entity:
                continue
            tasks.append(self._scrape_recent_entity(dialog.entity, since))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _scrape_recent_entity(self, entity, since):
        """Scrape recent messages from a single entity."""
        try:
            title = getattr(entity, 'title', 'Private')
            count = 0

            async for message in self.client.iter_messages(
                entity,
                offset_date=datetime.fromtimestamp(since),
                reverse=True
            ):
                if not message.text:
                    continue

                sender_name = ''
                if message.sender:
                    if hasattr(message.sender, 'first_name'):
                        sender_name = message.sender.first_name or ''

                is_new = self.db.add_message(
                    chat_id=entity.id,
                    chat_title=title,
                    sender_name=sender_name,
                    message=message.text,
                    timestamp=message.date.timestamp()
                )

                if is_new:
                    count += 1

            if count > 0:
                await self._log(f"    -> {title}: {count} new")

        except Exception:
            pass

    def setup_auto_reply(self):
        """Setup real-time listener + auto-reply."""
        print("  [BOT] 👂 Listening for new messages + auto-reply...")

        if not self.model or not self.tokenizer:
            print("  [BOT] ⚠️ Model not loaded, auto-reply disabled")
            return

        @self.client.on(events.NewMessage)
        async def handler(event):
            try:
                message = event.message
                if not message.text:
                    return

                chat = await event.get_chat()
                title = getattr(chat, 'title', 'Private')

                sender = await event.get_sender()
                sender_name = ''
                sender_id = None
                if sender:
                    if hasattr(sender, 'first_name'):
                        sender_name = sender.first_name or ''
                    sender_id = sender.id if hasattr(sender, 'id') else None

                # Save to DB
                is_new = self.db.add_message(
                    chat_id=event.chat_id,
                    chat_title=title,
                    sender_name=sender_name,
                    message=message.text,
                    timestamp=time.time()
                )

                if is_new:
                    self.stats['new'] += 1

                # Auto-reply: skip if message is from me or toggle off
                try:
                    from dashboard import _state as _dash_state
                    auto_reply_on = _dash_state.get('auto_reply', True)
                except ImportError:
                    auto_reply_on = True

                if AUTO_REPLY_ENABLED and auto_reply_on and sender_id != self.my_id:
                    if len(message.text) < AUTO_REPLY_MIN_LEN:
                        return

                    # Random chance to reply (not every message)
                    if random.random() > 0.3:
                        return

                    # Add delay for natural feel
                    await asyncio.sleep(AUTO_REPLY_DELAY + random.uniform(0, 1))

                    # Generate reply
                    reply_text = self._generate_reply(message.text)
                    if reply_text:
                        try:
                            async with self._reply_lock:
                                await message.reply(reply_text)
                                self.stats['replies'] += 1
                                await self._log(f"  [BOT] 💬 Replied in {title}: {reply_text[:60]}...")
                        except Exception as e:
                            pass

            except Exception:
                pass

    def _generate_reply(self, text):
        """Generate a smart reply - model + fallback system."""
        from dikaai.coding.smart_reply import get_smart_reply

        model_reply = None
        if self.model and self.tokenizer and self.tokenizer._loaded:
            try:                    from dikaai.config import CONTEXT_LEN
                tokens = self.tokenizer.encode(text, max_length=CONTEXT_LEN)
                if len(tokens) >= 1:
                    generated = self.model.generate(
                        tokens, max_len=25, temperature=0.75, tokenizer=self.tokenizer
                    )
                    model_reply = self.tokenizer.decode(generated)
            except Exception:
                pass

        return get_smart_reply(text, model_reply)

    def close(self):
        """Disconnect."""
        if self.client:
            self.client.disconnect()
