"""DikaAI Engine - The complete AI system.

This is the core engine that processes user messages through:
  Input → Context → Memory → RAG → Agent → Model → Validator → Response
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
    """DikaAI Engine - processes messages through full pipeline."""

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
        """Process user message through full pipeline."""
        start = time.time()
        self.total += 1

        # 1. Context Management (dual: tracker + long-context)
        ctx = self.context.process_message(message)
        intent = ctx['intent']
        topic = ctx['topic']

        # 2. Long-context processing (L0-L6 memory)
        self.long_context.process_message(message, topic.get('topic', ''))

        # 3. Memory Retrieval (all memory types)
        mem_ctx = self.coding_memory.get_context(message)
        episodic_ctx = self.episodic_memory.get_context(message)
        semantic_ctx = self.semantic_memory.get_facts_for_topic(message)

        # 4. Route
        effective = intent.get('context', message) if intent.get('resolved') else message
        route = self._route(effective)

        # 5. Build hierarchical context (L0-L6)
        long_ctx = self.long_context.build_context(message, max_tokens=2000)

        # 6. Execute
        if route == 'code':
            result = self._exec_code(message, model, tokenizer)
        elif route == 'tool':
            result = self._exec_tool(message)
        elif route == 'search':
            result = self._exec_search(message)
        elif route == 'reason':
            result = self._exec_reason(message, model, tokenizer)
        else:
            result = self._exec_chat(message)

        # 7. Validate
        validation = self.validator.validate(result['response'], message, self.context.state)
        self.observer.log_validation(validation.passed, validation.issues)

        # 8. Update all state
        self.context.update_after_response(message, result['response'])
        self.long_context.process_response(result['response'], topic.get('topic', ''))
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
            'topic': topic.get('topic', ''),
            'intent': intent.get('intent', ''),
            'validation': validation.to_dict(),
        }

    def _route(self, message: str) -> str:
        """Simple routing."""
        text = message.lower()
        if any(w in text for w in ['fix', 'error', 'bug', 'buat', 'create', 'write', 'edit', 'ubah']):
            return 'code'
        if any(w in text for w in ['git', 'install', 'pip', 'run', 'jalankan']):
            return 'tool'
        if any(w in text for w in ['cari', 'find', 'search']):
            return 'search'
        if any(w in text for w in ['jelaskan', 'explain', 'kenapa', 'why', 'apa itu']):
            return 'reason'
        return 'chat'

    def _exec_code(self, message, model, tokenizer):
        # First: check code templates (instant, no model needed)
        from dikaai.coding.code_templates import match_template
        template = match_template(message)
        if template['matched']:
            code = template['code']
            return {
                'response': f"```python\n{code}\n```\n\n✅ {template['template_name']} template",
                'success': True,
            }

        # Second: try executor (plan → code → test → debug)
        result = self.executor.execute(message, max_retries=3)
        self.observer.log_tool_call('code_agent', result.success, result.total_time)
        if result.success:
            out = result.output[:500] if result.output else 'Done'
            return {'response': f"✅ {out}\n⏱️ {result.total_time:.1f}s", 'success': True}

        # Third: try model generation
        if model and tokenizer and tokenizer._loaded:
            try:
                from dikaai.config import CONTEXT_LEN
                tokens = tokenizer.encode(message, max_length=CONTEXT_LEN)
                gen = model.generate(tokens, max_len=100, temperature=0.5)
                resp = tokenizer.decode(gen)
                if resp and len(resp.strip()) > 10:
                    return {'response': f"```python\n{resp.strip()}\n```", 'success': True}
            except Exception:
                pass

        return {'response': f"❌ No template match and model too small for code generation", 'success': False}

    def _exec_tool(self, message):
        if 'git' in message.lower():
            r = self.git.status() if 'status' in message else self.git.log()
            return {'response': r.get('stdout', 'Done'), 'success': True}
        r = self.terminal.run_command(message)
        return {'response': r.get('stdout', r.get('stderr', 'Done')), 'success': True}

    def _exec_search(self, message):
        query = message
        for w in ['cari', 'find', 'search']:
            query = query.replace(w, '').strip()
        r = self.fs.search_code(query, self.workspace or '.')
        if r.get('matches'):
            lines = [f"Found {len(r['matches'])}:"]
            for m in r['matches'][:5]:
                lines.append(f"  {m['file']}:{m['line']} → {m['content'][:60]}")
            return {'response': '\n'.join(lines), 'success': True}
        return {'response': 'No matches found', 'success': True}

    def _exec_reason(self, message, model, tokenizer):
        # Use reasoning engine for complex analysis
        chain = self.reasoning.reason(message)
        if chain.steps:
            response = chain.to_text()
            if chain.conclusion:
                response += f"\n\n{chain.conclusion}"
            return {'response': response, 'success': True}

        # Fallback to model
        if model and tokenizer and tokenizer._loaded:
            try:
                from dikaai.config import CONTEXT_LEN
                tokens = tokenizer.encode(message, max_length=CONTEXT_LEN)
                gen = model.generate(tokens, max_len=256, temperature=0.5)
                resp = tokenizer.decode(gen)
                if resp and len(resp.strip()) > 3:
                    return {'response': resp.strip(), 'success': True}
            except Exception:
                pass
        from dikaai.coding.smart_reply import get_smart_reply
        return {'response': get_smart_reply(message), 'success': True}

    def _exec_chat(self, message):
        from dikaai.coding.smart_reply import get_smart_reply
        return {'response': get_smart_reply(message), 'success': True}

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
        }
