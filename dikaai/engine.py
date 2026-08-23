"""DikaAI Engine - The complete AI system.

This is the core engine that processes user messages through:
  Input → Context → Memory → RAG → Agent → Model → Validator → Response

Memory integration:
  - LongContextManager: L0-L6 hierarchical memory (recent, summary, topics, long-term, project, archive)
  - EpisodicMemory: past coding experiences (task → code → error → fix → result)
  - SemanticMemory: facts and knowledge (subject → predicate → object)
  - ConversationMemory: short-term conversation buffer
  - CodingMemory: error → solution database
"""

import time
from dikaai.context.tracker import ContextManager
from dikaai.context.long_context import LongContextManager
from dikaai.memory.short_term import ConversationMemory
from dikaai.memory.coding_memory import CodingMemory
from dikaai.memory.episodic import EpisodicMemory
from dikaai.memory.semantic import SemanticMemory
from dikaai.rag.retriever import Retriever
from dikaai.rag.reranker import Reranker
from dikaai.agent.planner import Planner
from dikaai.agent.executor import Executor
from dikaai.agent.reasoning import ReasoningEngine
from dikaai.tools.filesystem import FilesystemTools
from dikaai.tools.terminal import TerminalTools
from dikaai.tools.git_tools import GitTools
from dikaai.coding.validator import Validator as ResponseValidator
from dikaai.coding.observer import Observer


class Engine:
    """DikaAI Engine - processes messages through full pipeline with memory."""

    def __init__(self, workspace: str = None):
        self.workspace = workspace

        # Core components
        self.context = ContextManager()
        self.long_context = LongContextManager()
        self.memory = ConversationMemory()
        self.coding_memory = CodingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.retriever = Retriever()
        self.reranker = Reranker()
        self.planner = Planner()
        self.executor = Executor(workspace)
        self.reasoning = ReasoningEngine()
        self.validator = ResponseValidator()
        self.observer = Observer()

        # Tools
        self.fs = FilesystemTools(workspace)
        self.terminal = TerminalTools(workspace)
        self.git = GitTools(workspace)

        # Stats
        self.total = 0
        self.successful = 0

    def process(self, message: str, model=None, tokenizer=None) -> dict:
        """Process user message through full pipeline with memory integration."""
        start = time.time()
        self.total += 1

        # 1. Context Management (dual: tracker + long-context)
        ctx = self.context.process_message(message)
        intent = ctx['intent']
        topic = ctx['topic']
        topic_name = topic.get('topic', 'general')

        # 2. Long-context processing (L0-L6 memory)
        self.long_context.process_message(message, topic_name)

        # 3. Memory Retrieval (all memory types) → build unified memory context
        memory_ctx = self._build_memory_context(message, topic_name)

        # 4. Route (with memory context awareness)
        effective = intent.get('context', message) if intent.get('resolved') else message
        route = self._route(effective)

        # 5. Execute (with full memory context)
        if route == 'code':
            result = self._exec_code(message, model, tokenizer, memory_ctx)
        elif route == 'tool':
            result = self._exec_tool(message, memory_ctx)
        elif route == 'search':
            result = self._exec_search(message, memory_ctx)
        elif route == 'reason':
            result = self._exec_reason(message, model, tokenizer, memory_ctx)
        else:
            result = self._exec_chat(message, memory_ctx)

        # 6. Validate
        validation = self.validator.validate(result['response'], message, self.context.state)
        self.observer.log_validation(validation.passed, validation.issues)

        # 7. Record outcome in episodic memory
        self._record_episode(message, result, route, memory_ctx)

        # 8. Extract facts from response into semantic memory
        self._extract_facts(message, result['response'], topic_name)

        # 9. Update all state
        self.context.update_after_response(message, result['response'])
        self.long_context.process_response(result['response'], topic_name)
        self.memory.add('user', message)
        self.memory.add('assistant', result['response'])

        elapsed = time.time() - start
        if result.get('success', True):
            self.successful += 1

        return {
            'response': result['response'],
            'route': route,
            'success': result.get('success', True),
            'time': f'{elapsed:.1f}s',
            'topic': topic_name,
            'intent': intent.get('intent', ''),
            'validation': validation.to_dict(),
            'memory_used': {
                'episodes': len(memory_ctx.get('episodes', '')) > 0,
                'semantic': len(memory_ctx.get('semantic', '')) > 0,
                'long_term': len(memory_ctx.get('long_term', '')) > 0,
                'coding': len(memory_ctx.get('coding', '')) > 0,
            },
        }

    # ================================================================
    # MEMORY CONTEXT BUILDER
    # ================================================================

    def _build_memory_context(self, message: str, topic: str) -> dict:
        """Build unified memory context from all memory systems.

        Returns dict with:
            episodes: past experience context
            semantic: fact/knowledge context
            long_term: L4 long-term memory
            coding: error→solution context
            hierarchical: full L0-L6 context string
            recent: recent conversation turns
        """
        # Episodic: find similar past experiences
        episodes = self.episodic_memory.get_context(message)

        # Semantic: find relevant facts
        semantic = self.semantic_memory.get_facts_for_topic(message)

        # Coding memory: find error solutions
        coding = self.coding_memory.get_context(message)

        # Long-context: L0-L6 hierarchical assembly
        hierarchical = self.long_context.build_context(message, max_tokens=1500)

        # Recent conversation
        recent = self.memory.get_last(n=5)

        return {
            'episodes': episodes,
            'semantic': semantic,
            'coding': coding,
            'hierarchical': hierarchical,
            'recent': recent,
            'topic': topic,
        }

    def _format_memory_for_prompt(self, memory_ctx: dict, max_tokens: int = 800) -> str:
        """Format memory context into a prompt-ready string."""
        parts = []
        total = 0

        # Episodes (highest priority - past experience)
        if memory_ctx.get('episodes'):
            tokens = len(memory_ctx['episodes'].split())
            if total + tokens < max_tokens:
                parts.append(memory_ctx['episodes'])
                total += tokens

        # Semantic facts
        if memory_ctx.get('semantic'):
            tokens = len(memory_ctx['semantic'].split())
            if total + tokens < max_tokens:
                parts.append(memory_ctx['semantic'])
                total += tokens

        # Coding memory (error solutions)
        if memory_ctx.get('coding'):
            tokens = len(memory_ctx['coding'].split())
            if total + tokens < max_tokens:
                parts.append(memory_ctx['coding'])
                total += tokens

        # Long-term context (from hierarchical)
        if memory_ctx.get('hierarchical'):
            # Extract just the long-term and summary parts
            lines = memory_ctx['hierarchical'].split('\n')
            relevant = []
            for line in lines:
                if any(kw in line for kw in ['LONG-TERM', 'TOPIC:', 'SUMMARY', 'CONVERSATION']):
                    relevant.append(line)
            if relevant:
                text = '\n'.join(relevant[:10])
                tokens = len(text.split())
                if total + tokens < max_tokens:
                    parts.append(text)
                    total += tokens

        return '\n\n'.join(parts)

    # ================================================================
    # ROUTING
    # ================================================================

    def _route(self, message: str) -> str:
        """Route with memory context awareness."""
        text = message.lower()
        # Git operations
        if any(w in text for w in ['git ', 'git\n', 'commit', 'branch', 'merge', 'stash',
                                    'diff', 'undo', 'revert', 'reset']):
            return 'tool'
        # Code generation
        if any(w in text for w in ['fix', 'error', 'bug', 'buat', 'create', 'write', 'edit', 'ubah',
                                    'function', 'class', 'implement', 'def ', 'fn ', 'struct ',
                                    'trait ', 'interface ', 'type ']):
            return 'code'
        # System tools
        if any(w in text for w in ['install', 'pip', 'run ', 'jalankan', 'execute',
                                    'read the file', 'list ', 'version', 'python --version',
                                    'how many lines', 'contain']):
            return 'tool'
        # Search
        if any(w in text for w in ['cari', 'find', 'search', 'grep']):
            return 'search'
        # Reasoning
        if any(w in text for w in ['jelaskan', 'explain', 'kenapa', 'why', 'apa itu', 'how does']):
            return 'reason'
        return 'chat'

    # ================================================================
    # EXECUTE (with memory context)
    # ================================================================

    def _exec_code(self, message, model, tokenizer, memory_ctx):
        """Execute code generation with memory context."""
        # 1. Check past episodes for truly similar tasks
        similar_episodes = self.episodic_memory.find_similar(message, top_k=3)
        if similar_episodes:
            # Only use if the top episode has high confidence and is truly similar
            top = similar_episodes[0]
            if top.success and top.confidence > 0.7:
                # Use template if available, otherwise reference the episode
                from dikaai.coding.code_templates import match_template
                tmpl = match_template(message)
                if tmpl['matched']:
                    return {
                        'response': f"```python\n{tmpl['code']}\n```\n\n✅ {tmpl['template_name']} template (learned from past experience)",
                        'success': True,
                    }
                # Reference past experience for context
                return {
                    'response': f"Based on past experience with similar tasks:\n\n{memory_ctx['episodes']}\n\nApplying similar approach...",
                    'success': True,
                }

        # 2. Check code templates (instant, no model needed)
        from dikaai.coding.code_templates import match_template
        template = match_template(message)
        if template['matched']:
            code = template['code']
            # Enrich with semantic knowledge if available
            enrich = ""
            if memory_ctx.get('semantic'):
                enrich = f"\n\n📚 {memory_ctx['semantic']}"
            return {
                'response': f"```python\n{code}\n```\n\n✅ {template['template_name']} template{enrich}",
                'success': True,
            }

        # 3. Try executor (plan → code → test → debug)
        result = self.executor.execute(message, max_retries=3)
        self.observer.log_tool_call('code_agent', result.success, result.total_time)
        if result.success:
            out = result.output[:500] if result.output else 'Done'
            return {'response': f"✅ {out}\n⏱️ {result.total_time:.1f}s", 'success': True}

        # 4. Try model generation with memory context
        if model and tokenizer and tokenizer._loaded:
            try:
                # Build enriched prompt with memory
                mem_prompt = self._format_memory_for_prompt(memory_ctx)
                prompt = f"{mem_prompt}\n\nTask: {message}" if mem_prompt else message

                from dikaai.config import CONTEXT_LEN
                tokens = tokenizer.encode(prompt, max_length=CONTEXT_LEN)
                gen = model.generate(tokens, max_len=100, temperature=0.5)
                resp = tokenizer.decode(gen)
                if resp and len(resp.strip()) > 10:
                    return {'response': f"```python\n{resp.strip()}\n```", 'success': True}
            except Exception:
                pass

        return {'response': "❌ No template match and model too small for code generation", 'success': False}

    def _exec_tool(self, message, memory_ctx):
        """Execute tool operations with memory context."""
        text = message.lower()

        # Git commands - try template first, then execute
        if 'git' in text or 'commit' in text or 'branch' in text or 'undo' in text:
            from dikaai.coding.code_templates import match_template
            template = match_template(message)
            if template['matched']:
                return {'response': template['code'], 'success': True}
            # Actually execute git
            if 'status' in text:
                r = self.git.status()
            elif 'log' in text or 'history' in text:
                r = self.git.log()
            else:
                r = self.git.status()
            stdout = r.get('stdout', 'Done')
            return {'response': f"git status output:\n{stdout}", 'success': True}

        # Try template first for tool queries
        from dikaai.coding.code_templates import match_template
        template = match_template(message)
        if template['matched']:
            return {'response': template['code'], 'success': True}

        # Execute command
        r = self.terminal.run_command(message)
        output = r.get('stdout', r.get('stderr', 'Done'))

        # Enrich with relevant memory
        if memory_ctx.get('semantic'):
            output += f"\n\n📚 {memory_ctx['semantic']}"

        return {'response': output, 'success': True}

    def _exec_search(self, message, memory_ctx):
        """Search with memory context enrichment."""
        query = message
        for w in ['cari', 'find', 'search']:
            query = query.replace(w, '').strip()

        # Search filesystem
        r = self.fs.search_code(query, self.workspace or '.')
        lines = []

        if r.get('matches'):
            lines.append(f"Found {len(r['matches'])} matches:")
            for m in r['matches'][:5]:
                lines.append(f"  {m['file']}:{m['line']} → {m['content'][:60]}")

        # Also search semantic memory
        if memory_ctx.get('semantic'):
            lines.append(f"\n{memory_ctx['semantic']}")

        # Also search episodic memory
        if memory_ctx.get('episodes'):
            lines.append(f"\n{memory_ctx['episodes']}")

        if not lines:
            return {'response': 'No matches found', 'success': True}

        return {'response': '\n'.join(lines), 'success': True}

    def _exec_reason(self, message, model, tokenizer, memory_ctx):
        """Reasoning with memory context for informed analysis."""
        # Use reasoning engine for complex analysis
        chain = self.reasoning.reason(message)
        if chain.steps:
            response = chain.to_text()
            if chain.conclusion:
                response += f"\n\n{chain.conclusion}"

            # Enrich with memory context
            mem_info = self._format_memory_for_prompt(memory_ctx, max_tokens=400)
            if mem_info:
                response += f"\n\n📖 Context:\n{mem_info}"

            return {'response': response, 'success': True}

        # Fallback to model with memory context
        if model and tokenizer and tokenizer._loaded:
            try:
                mem_prompt = self._format_memory_for_prompt(memory_ctx)
                prompt = f"{mem_prompt}\n\nQuestion: {message}" if mem_prompt else message

                from dikaai.config import CONTEXT_LEN
                tokens = tokenizer.encode(prompt, max_length=CONTEXT_LEN)
                gen = model.generate(tokens, max_len=256, temperature=0.5)
                resp = tokenizer.decode(gen)
                if resp and len(resp.strip()) > 3:
                    return {'response': resp.strip(), 'success': True}
            except Exception:
                pass

        # Smart reply with memory context
        from dikaai.coding.smart_reply import get_smart_reply
        base_reply = get_smart_reply(message)

        # Add relevant memory
        mem_info = self._format_memory_for_prompt(memory_ctx, max_tokens=300)
        if mem_info:
            base_reply += f"\n\n📖 Related knowledge:\n{mem_info}"

        return {'response': base_reply, 'success': True}

    def _exec_chat(self, message, memory_ctx):
        """Chat with memory context for informed conversation."""
        from dikaai.coding.smart_reply import get_smart_reply
        base_reply = get_smart_reply(message)

        # Add memory context for richer conversation
        mem_info = self._format_memory_for_prompt(memory_ctx, max_tokens=200)
        if mem_info:
            base_reply += f"\n\n📖 Context: {mem_info}"

        return {'response': base_reply, 'success': True}

    # ================================================================
    # MEMORY RECORDING
    # ================================================================

    def _record_episode(self, message, result, route, memory_ctx):
        """Record task outcome in episodic memory for future learning."""
        # Only record code tasks (most valuable for learning)
        if route not in ('code', 'tool'):
            return

        success = result.get('success', False)
        response = result.get('response', '')

        # Extract code from response (not the meta-text)
        code = ""
        if '```' in response:
            import re
            blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
            if blocks:
                code = blocks[0]

        # Extract template name if present
        template_name = ""
        if 'template' in response.lower():
            import re
            tmatch = re.search(r'✅ (\w+) template', response)
            if tmatch:
                template_name = tmatch.group(1)

        # Check for errors
        error = ""
        if not success and 'error' in response.lower():
            error = response[:200]

        # Determine language
        language = 'python'
        if 'javascript' in response or 'function ' in code:
            language = 'javascript'
        elif 'rust' in response or 'fn ' in code:
            language = 'rust'
        elif 'golang' in response or 'func ' in code:
            language = 'go'

        # Record only the code and template name (not the full response)
        fix_text = f"template:{template_name}" if template_name else code[:200]

        self.episodic_memory.record_episode(
            task=message[:200],
            code=code[:500],
            error=error[:200],
            fix=fix_text[:200],
            success=success,
            language=language,
            tools_used=[route],
            duration=0.1,
            tags=[route, language],
        )

    def _extract_facts(self, message, response, topic):
        """Extract facts from conversation into semantic memory."""
        # Extract facts from responses (pattern: X is Y, X uses Y, etc.)
        import re

        # Pattern: "X is Y" or "X adalah Y"
        for match in re.finditer(
            r'(\w[\w\s]*?)\s+(?:is|adalah|merupakan|uses?|implements?|supports?)\s+(.+?)[.!]',
            response, re.IGNORECASE
        ):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if len(subject) > 2 and len(obj) > 2:
                self.semantic_memory.add_fact(
                    subject=subject,
                    predicate='is',
                    obj=obj,
                    source='conversation',
                    tags=[topic],
                )

        # Extract facts from user questions (what they learned)
        for match in re.finditer(
            r'(\w[\w\s]*?)\s+(?:is|adalah|merupakan)\s+(.+?)[.?]',
            message, re.IGNORECASE
        ):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if len(subject) > 2 and len(obj) > 2:
                self.semantic_memory.add_fact(
                    subject=subject,
                    predicate='is',
                    obj=obj,
                    source='user_question',
                    tags=[topic],
                )

    # ================================================================
    # STATS
    # ================================================================

    def get_stats(self):
        return {
            'total': self.total,
            'successful': self.successful,
            'rate': f'{self.successful/max(self.total,1)*100:.0f}%',
            'observer': self.observer.get_stats(),
            'context': self.context.state.to_dict(),
            'long_context': self.long_context.get_stats(),
            'episodic': self.episodic_memory.get_task_stats(),
            'semantic': self.semantic_memory.get_stats(),
            'memory': {
                'short_term': len(self.memory.messages) if hasattr(self.memory, 'messages') else 0,
                'coding_memory': self.coding_memory.get_stats(),
            },
        }
