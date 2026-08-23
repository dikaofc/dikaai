"""DikaAI v2 Orchestrator - Complete AI Operating System Brain.

Pipeline:
  User → InputProcessor → StateManager → ContextManager
  → Router → Memory/RAG/Project → Agent → Model
  → Observer → Validator → Send/Regenerate
"""

import time
from core.router import Router, TaskType
from core.input_processor import InputProcessor
from core.context import ContextManager, ConversationState
from core.state_manager import StateManager
from core.token_budget import TokenBudget
from core.validator import Validator
from core.observer import Observer
from core.project_index import ProjectIndex
from core.config import ROUTER, AGENT
from agent.executor import Executor
from memory.short_term import ConversationContext
from memory.coding_memory import CodingMemory
from rag.retriever import Retriever


class Orchestrator:
    """Main brain - orchestrates all DikaAI components."""

    def __init__(self, workspace: str = None, model=None, tokenizer=None):
        self.workspace = workspace
        self.model = model
        self.tokenizer = tokenizer

        # === FOUNDATION ===
        self.input_processor = InputProcessor()
        self.state_manager = StateManager()
        self.context_manager = ContextManager()
        self.token_budget = TokenBudget(total=4000)
        self.validator = Validator()
        self.observer = Observer()

        # === CORE ===
        self.router = Router()
        self.executor = Executor(workspace, model, tokenizer)
        self.memory = ConversationContext()
        self.coding_memory = CodingMemory()
        self.retriever = Retriever()
        self.project_index = ProjectIndex(workspace)

        # === STATS ===
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.regenerations = 0
        self.start_time = time.time()

    def process(self, user_input: str) -> dict:
        """Full pipeline: input → analyze → route → execute → validate → respond."""
        start = time.time()
        self.total_tasks += 1

        # === STEP 1: INPUT PROCESSING ===
        input_analysis = self.input_processor.process(user_input)
        self.observer.log_tool_call('input_process', True, 0)

        # === STEP 2: INTENT RESOLUTION (handle vague references) ===
        ctx_result = self.context_manager.process_message(user_input)
        intent = ctx_result['intent']
        topic_info = ctx_result['topic']

        # Use resolved intent if reference
        effective_input = intent.get('context', user_input) if intent.get('resolved') else user_input

        # === STEP 3: ROUTING ===
        route = self.router.route(effective_input)
        self.observer.log_tool_call('router', True, 0)

        # === STEP 4: STATE MANAGEMENT ===
        task_state = self.state_manager.start_task(user_input[:200])

        # === STEP 5: MEMORY RETRIEVAL ===
        memory_context = self.coding_memory.get_context(user_input, input_analysis.get('language'))

        # === STEP 6: RAG RETRIEVAL ===
        rag_context = self.retriever.retrieve(user_input)

        # === STEP 7: PROJECT CONTEXT ===
        project_context = ""
        if self.project_index.indexed:
            project_context = self.project_index.get_context(user_input)

        # === STEP 8: BUILD HIERARCHICAL CONTEXT ===
        self.token_budget = TokenBudget(total=4000)  # Reset per request
        context_str = self.context_manager.build_context(
            effective_input, memory_context, project_context
        )

        # === STEP 9: EXECUTE ===
        full_context = {
            'language': input_analysis.get('language'),
            'action': route.action,
            'input_analysis': input_analysis,
            'topic': topic_info,
            'memory': memory_context,
            'rag': rag_context,
            'project': project_context,
            'context_str': context_str,
        }

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

        # === STEP 10: VALIDATION ===
        response = result.get('response', '')
        validation = self.validator.validate(
            response, user_input,
            state=self.context_manager.state,
            context=full_context
        )
        self.observer.log_validation(validation.passed, validation.issues)

        # Regenerate if validation fails
        if validation.should_regenerate and self.regenerations < 3:
            self.regenerations += 1
            self.observer.log_retry(self.regenerations, validation.regenerate_reason)
            # For now, send as-is (regeneration needs model call)
            pass

        # === STEP 11: UPDATE STATE ===
        self.context_manager.update_after_response(user_input, response)
        self.state_manager.complete_current(response[:200])

        # === STEP 12: SAVE EXPERIENCE ===
        self.memory.add_user_message(user_input)
        self.memory.add_assistant_message(response, {
            'route': route.task_type.value,
            'success': result.get('success', True),
            'topic': topic_info.get('topic', ''),
        })

        # === STEP 13: BUILD FINAL RESPONSE ===
        elapsed = time.time() - start
        if result.get('success', True):
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        return {
            'response': response,
            'route': route.task_type.value,
            'success': result.get('success', True),
            'time': f'{elapsed:.1f}s',
            'topic': topic_info.get('topic', ''),
            'intent': intent.get('intent', ''),
            'complexity': input_analysis.get('complexity', ''),
            'validation': validation.to_dict(),
            'task_id': self.total_tasks,
            'state': self.state_manager.get_current(),
        }

    # === HANDLERS ===

    def _handle_code(self, user_input, route, context):
        task_state = self.state_manager.current_task
        if task_state:
            task_state.start("executing code task")

        result = self.executor.execute(user_input, context, max_retries=AGENT['max_retries'])
        self.observer.log_tool_call('code_agent', result.success, result.total_time)

        response = self._generate_code_response(user_input, result, context)
        return {'response': response, 'success': result.success, 'type': 'code'}

    def _handle_reason(self, user_input, route, context):
        response = self._generate_response(user_input, context,
                                           temperature=ROUTER['temperature_reason'])
        return {'response': response, 'success': True, 'type': 'reason'}

    def _handle_search(self, user_input, route, context):
        from tools.filesystem import FilesystemTools
        fs = FilesystemTools(self.workspace)
        query = user_input
        for word in ['cari', 'find', 'search', 'look', 'dimana', 'where']:
            query = query.replace(word, '').strip()
        results = fs.search_code(query, self.workspace or '.')
        self.observer.log_tool_call('search', results.get('success', False), 0)

        if results.get('matches'):
            lines = [f"Found {len(results['matches'])} matches:"]
            for m in results['matches'][:5]:
                lines.append(f"  {m['file']}:{m['line']} → {m['content'][:80]}")
            response = '\n'.join(lines)
        else:
            response = self._generate_response(user_input, context)
        return {'response': response, 'success': True, 'type': 'search'}

    def _handle_tool(self, user_input, route, context):
        from tools.terminal import TerminalTools
        from tools.git_tools import GitTools
        terminal = TerminalTools(self.workspace)
        git = GitTools(self.workspace)

        if 'git' in user_input.lower():
            if 'status' in user_input:
                result = git.status()
            elif 'diff' in user_input:
                result = git.diff()
            elif 'log' in user_input:
                result = git.log()
            else:
                result = terminal.run_command(user_input.strip())
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

        self.observer.log_tool_call('terminal', True, 0)
        return {'response': response, 'success': True, 'type': 'tool'}

    def _handle_chat(self, user_input, route, context):
        from smart_reply import get_smart_reply
        response = get_smart_reply(user_input)
        return {'response': response, 'success': True, 'type': 'chat'}

    # === RESPONSE GENERATION ===

    def _generate_code_response(self, task, result, context):
        lines = []
        if result.success:
            lines.append("✅ Task completed!")
            if result.output:
                output_lines = result.output.strip().split('\n')
                if len(output_lines) > 10:
                    lines.append(f"Output ({len(output_lines)} lines):")
                    for line in output_lines[:5]:
                        lines.append(f"  {line}")
                    lines.append(f"  ... ({len(output_lines) - 5} more)")
                else:
                    for line in output_lines:
                        lines.append(f"  {line}")
        else:
            lines.append(f"❌ Failed after {result.retries} retries")
            if result.error:
                lines.append(f"Error: {result.error[:200]}")
        lines.append(f"⏱️ {result.total_time:.1f}s | {len(result.steps_executed)} steps")
        return '\n'.join(lines)

    def _generate_response(self, prompt, context, temperature=0.7):
        if self.model and self.tokenizer and self.tokenizer._loaded:
            try:
                from config import CONTEXT_LEN
                tokens = self.tokenizer.encode(prompt, max_length=CONTEXT_LEN)
                generated = self.model.generate(tokens, max_len=256, temperature=temperature)
                response = self.tokenizer.decode(generated)
                if response and len(response.strip()) > 3:
                    return response.strip()
            except Exception:
                pass
        from smart_reply import get_smart_reply
        return get_smart_reply(prompt)

    # === STATS ===

    def get_stats(self):
        return {
            'total_tasks': self.total_tasks,
            'successful': self.successful_tasks,
            'failed': self.failed_tasks,
            'regenerations': self.regenerations,
            'success_rate': f'{self.successful_tasks/max(self.total_tasks,1)*100:.0f}%',
            'uptime': f'{(time.time()-self.start_time)/3600:.1f}h',
            'coding_memory': self.coding_memory.get_stats(),
            'rag': self.retriever.get_stats(),
            'observer': self.observer.get_stats(),
            'state': self.state_manager.to_dict(),
            'project_indexed': self.project_index.indexed,
            'conversation': len(self.memory.short_term.messages),
        }
