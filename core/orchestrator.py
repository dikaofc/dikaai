"""DikaAI Orchestrator - The Brain.

Routes tasks → Plans execution → Runs coding agent → Learns from results.

Architecture:
  User → Router → Planner → Executor → Memory → Response
                  ↑                         ↓
                  └──── RAG ──── Coding Memory
"""

import time
import json
from core.router import Router, TaskType, Route
from core.context import ContextManager, ConversationState
from core.config import ROUTER, AGENT
from agent.executor import Executor
from memory.short_term import ConversationContext
from memory.coding_memory import CodingMemory
from rag.retriever import Retriever


class Orchestrator:
    """Main brain of DikaAI - orchestrates all components."""

    def __init__(self, workspace: str = None, model=None, tokenizer=None):
        self.workspace = workspace
        self.model = model
        self.tokenizer = tokenizer

        # Core components
        self.router = Router()
        self.executor = Executor(workspace, model, tokenizer)
        self.context = ConversationContext()
        self.coding_memory = CodingMemory()
        self.retriever = Retriever()
        self.ctx_manager = ContextManager()  # Context management

        # Stats
        self.total_tasks = 0
        self.successful_tasks = 0
        self.start_time = time.time()

    def process(self, user_input: str) -> dict:
        """Process user input through full pipeline with context management."""
        start = time.time()
        self.total_tasks += 1

        # 1. Context Management: resolve intent + track topic
        ctx_result = self.ctx_manager.process_message(user_input)
        intent = ctx_result['intent']
        topic_info = ctx_result['topic']

        # 2. Add to conversation memory
        self.context.add_user_message(user_input)

        # 3. Route the task (use resolved intent if reference)
        effective_input = intent.get('context', user_input) if intent.get('resolved') else user_input
        route = self.router.route(effective_input)

        # Override route with topic context
        if topic_info.get('topic') and topic_info['topic'] != 'general':
            if route.task_type == TaskType.CHAT and topic_info['confidence'] > 0.5:
                # Keep topic context even for chat
                pass

        # 4. Build hierarchical context (L0-L5)
        full_context = self._build_context(user_input, route)

        # 5. Execute based on route type
        if route.task_type == TaskType.CODE:
            result = self._handle_code(user_input, route, full_context)
        elif route.task_type == TaskType.REASON:
            result = self._handle_reason(user_input, route, full_context)
        elif route.task_type == TaskType.SEARCH:
            result = self._handle_search(user_input, route, full_context)
        elif route.task_type == TaskType.TOOL:
            result = self._handle_tool(user_input, route, full_context)
        else:
            result = self._handle_chat(user_input, route, full_context)

        # 6. Validate response (anti-topic-drift)
        response = result.get('response', '')
        validation = self.ctx_manager.validate_response(response, user_input)
        if validation.get('should_regenerate') and self.model:
            # Try to regenerate with better context
            pass  # For now, send as-is

        # 7. Update context state after response
        self.ctx_manager.update_after_response(user_input, response)

        # 8. Add response to memory
        self.context.add_assistant_message(response, {
            'route': route.task_type.value,
            'success': result.get('success', True),
            'topic': topic_info.get('topic', ''),
            'time': f'{time.time() - start:.1f}s',
        })

        # 6. Update stats
        if result.get('success', True):
            self.successful_tasks += 1

        result['route'] = route.task_type.value
        result['time'] = f'{time.time() - start:.1f}s'
        result['task_id'] = self.total_tasks

        return result

    def _build_context(self, user_input: str, route: Route) -> dict:
        """Build full context for execution."""
        ctx = {
            'language': route.language,
            'action': route.action,
            'conversation': self.context.short_term.get_context(max_tokens=300),
            'project': self.context.project.to_dict(),
        }

        # Add RAG context
        rag_context = self.retriever.retrieve(user_input)
        if rag_context:
            ctx['rag_context'] = rag_context

        # Add coding memory
        mem_context = self.coding_memory.get_context(user_input, route.language)
        if mem_context:
            ctx['memory_context'] = mem_context

        return ctx

    def _handle_code(self, user_input: str, route: Route, context: dict) -> dict:
        """Handle coding tasks - the core capability."""
        # Update context
        self.context.set_task(user_input)
        if route.language:
            self.context.project.languages = [route.language]

        # Execute coding task
        result = self.executor.execute(user_input, context, max_retries=AGENT['max_retries'])

        # Generate response
        response = self._generate_code_response(user_input, result, context)

        return {
            'response': response,
            'success': result.success,
            'execution': result.to_dict(),
            'type': 'code',
        }

    def _handle_reason(self, user_input: str, route: Route, context: dict) -> dict:
        """Handle complex reasoning tasks."""
        # Use model for reasoning
        response = self._generate_response(user_input, context,
                                           temperature=ROUTER['temperature_reason'])

        return {
            'response': response,
            'success': True,
            'type': 'reason',
        }

    def _handle_search(self, user_input: str, route: Route, context: dict) -> dict:
        """Handle search/lookup tasks."""
        # Search codebase
        from tools.filesystem import FilesystemTools
        fs = FilesystemTools(self.workspace)

        # Extract search query
        query = user_input
        for word in ['cari', 'find', 'search', 'look', 'dimana', 'where']:
            query = query.replace(word, '').strip()

        results = fs.search_code(query, self.workspace or '.')

        if results.get('matches'):
            lines = [f"Found {len(results['matches'])} matches:"]
            for m in results['matches'][:5]:
                lines.append(f"  {m['file']}:{m['line']} → {m['content'][:80]}")
            response = '\n'.join(lines)
        else:
            response = self._generate_response(user_input, context)

        return {
            'response': response,
            'success': True,
            'search_results': results,
            'type': 'search',
        }

    def _handle_tool(self, user_input: str, route: Route, context: dict) -> dict:
        """Handle tool operations (git, install, etc)."""
        from tools.terminal import TerminalTools
        from tools.git_tools import GitTools

        terminal = TerminalTools(self.workspace)
        git = GitTools(self.workspace)

        # Detect git commands
        if 'git' in user_input.lower():
            if 'status' in user_input:
                result = git.status()
                response = result.get('stdout', 'No changes')
            elif 'diff' in user_input:
                result = git.diff()
                response = result.get('stdout', 'No diff')
            elif 'log' in user_input:
                result = git.log()
                response = result.get('stdout', 'No commits')
            elif 'commit' in user_input:
                msg = user_input.split('commit')[-1].strip().strip('"').strip("'")
                if not msg:
                    msg = "Update from DikaAI"
                result = git.commit(msg, add_all=True)
                response = result.get('stdout', result.get('stderr', 'Commit done'))
            else:
                # Run git command
                cmd = user_input.strip()
                result = terminal.run_command(cmd)
                response = result.get('stdout', result.get('stderr', 'Done'))
        elif 'install' in user_input.lower() or 'pip' in user_input.lower():
            cmd = user_input.strip()
            if not cmd.startswith('pip'):
                cmd = f'pip install {cmd.split("install")[-1].strip()}'
            result = terminal.run_command(cmd)
            response = result.get('stdout', result.get('stderr', 'Installed'))
        else:
            result = terminal.run_command(user_input.strip())
            response = result.get('stdout', result.get('stderr', 'Done'))

        return {
            'response': response,
            'success': True,
            'type': 'tool',
        }

    def _handle_chat(self, user_input: str, route: Route, context: dict) -> dict:
        """Handle simple chat/conversation."""
        # Use smart_reply as fallback
        from smart_reply import get_smart_reply
        response = get_smart_reply(user_input)

        return {
            'response': response,
            'success': True,
            'type': 'chat',
        }

    def _generate_code_response(self, task: str, result, context: dict) -> str:
        """Generate a response for coding tasks."""
        lines = []

        if result.success:
            lines.append(f"✅ Task completed successfully!")
            if result.output:
                # Show relevant output
                output_lines = result.output.strip().split('\n')
                if len(output_lines) > 10:
                    lines.append(f"Output ({len(output_lines)} lines):")
                    for line in output_lines[:5]:
                        lines.append(f"  {line}")
                    lines.append(f"  ... ({len(output_lines) - 5} more lines)")
                else:
                    lines.append(f"Output:")
                    for line in output_lines:
                        lines.append(f"  {line}")
        else:
            lines.append(f"❌ Task failed after {result.retries} retries")
            if result.error:
                lines.append(f"Error: {result.error[:200]}")
            if result.fixes_applied:
                lines.append(f"Attempted fixes: {', '.join(result.fixes_applied[:3])}")

        lines.append(f"\n⏱️ Time: {result.total_time:.1f}s | Steps: {len(result.steps_executed)}")

        return '\n'.join(lines)

    def _generate_response(self, prompt: str, context: dict, temperature: float = 0.7) -> str:
        """Generate response using local LLM."""
        if self.model and self.tokenizer and self.tokenizer._loaded:
            try:
                # Build prompt with context
                full_prompt = prompt
                if context.get('rag_context'):
                    full_prompt = f"{context['rag_context']}\n\nUser: {prompt}"
                elif context.get('memory_context'):
                    full_prompt = f"{context['memory_context']}\n\nUser: {prompt}"

                from core.config import ROUTER
                from config import CONTEXT_LEN
                tokens = self.tokenizer.encode(full_prompt, max_length=CONTEXT_LEN)
                generated = self.model.generate(
                    tokens,
                    max_len=ROUTER['code_max_tokens'],
                    temperature=temperature,
                )
                response = self.tokenizer.decode(generated)
                if response and len(response.strip()) > 3:
                    return response.strip()
            except Exception:
                pass

        # Fallback to smart_reply
        from smart_reply import get_smart_reply
        return get_smart_reply(prompt)

    def get_stats(self) -> dict:
        """Get orchestrator statistics."""
        return {
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'success_rate': f'{self.successful_tasks/max(self.total_tasks,1)*100:.0f}%',
            'uptime': f'{(time.time() - self.start_time)/3600:.1f}h',
            'coding_memory': self.coding_memory.get_stats(),
            'rag': self.retriever.get_stats(),
            'conversation_messages': len(self.context.short_term.messages),
        }
