"""DikaAI Executor - Executes coding plans with retry/debug loop.

The core loop:
  Plan → Execute → Test → If fail → Debug → Retry → If pass → Done
"""

import time
import traceback
from dikaai.agent.planner import Planner, Step, StepType
from dikaai.tools.filesystem import FilesystemTools
from dikaai.tools.terminal import TerminalTools
from dikaai.tools.git_tools import GitTools
from dikaai.memory.coding_memory import CodingMemory


class ExecutionResult:
    def __init__(self):
        self.steps_executed = []
        self.success = False
        self.output = ""
        self.error = ""
        self.retries = 0
        self.fixes_applied = []
        self.total_time = 0

    def to_dict(self):
        return {
            'success': self.success,
            'steps': len(self.steps_executed),
            'retries': self.retries,
            'output': self.output[:2000],
            'error': self.error[:1000],
            'fixes': self.fixes_applied,
            'time': f'{self.total_time:.1f}s',
        }


class Executor:
    """Executes coding plans with automatic retry and debug loop."""

    def __init__(self, workspace: str = None, model=None, tokenizer=None):
        self.workspace = workspace
        self.planner = Planner()
        self.filesystem = FilesystemTools(workspace)
        self.terminal = TerminalTools(workspace)
        self.git = GitTools(workspace)
        self.memory = CodingMemory()
        self.model = model
        self.tokenizer = tokenizer

    def execute(self, task: str, context: dict = None, max_retries: int = 5) -> ExecutionResult:
        """Execute a coding task with automatic retry loop."""
        context = context or {}
        result = ExecutionResult()
        start_time = time.time()

        # Plan
        steps = self.planner.plan(task, context)

        # Execute with retry loop
        for retry in range(max_retries):
            result.retries = retry
            step_results = []

            for step in steps:
                step_result = self._execute_step(step, context)
                step.result = step_result
                step.success = step_result.get('success', False)
                step_results.append(step_result)
                result.steps_executed.append(step)

                # If step failed, try to debug
                if not step.success and step.step_type in (StepType.RUN, StepType.TEST):
                    error = step_result.get('error', '') or step_result.get('stderr', '')
                    if error:
                        result.error = error
                        # Try to fix
                        fix = self._auto_fix(step, error, context)
                        if fix:
                            result.fixes_applied.append(fix)
                            break  # Retry from beginning
                    # No fix possible, continue to next step

            # Check if all critical steps passed
            critical_steps = [s for s in result.steps_executed
                              if s.step_type in (StepType.WRITE, StepType.EDIT, StepType.RUN)]
            if critical_steps and all(s.success for s in critical_steps):
                result.success = True
                break

            # Check if we should retry
            if not result.fixes_applied or retry >= max_retries - 1:
                break

        # Collect output
        run_steps = [s for s in result.steps_executed if s.step_type == StepType.RUN]
        if run_steps:
            last_run = run_steps[-1].result
            result.output = last_run.get('stdout', '')

        result.total_time = time.time() - start_time

        # Save experience to memory
        self.memory.save_experience(
            task=task,
            success=result.success,
            error=result.error,
            fixes=result.fixes_applied,
            context=context,
        )

        return result

    def _execute_step(self, step: Step, context: dict) -> dict:
        """Execute a single step."""
        try:
            if step.step_type == StepType.READ:
                path = step.params.get('path') or context.get('file_path', '')
                if path:
                    return self.filesystem.read_file(path)
                return {'success': True, 'content': 'No file specified'}

            elif step.step_type == StepType.WRITE:
                path = step.params.get('path') or context.get('file_path', '')
                content = step.params.get('content', '')
                if path and content:
                    return self.filesystem.write_file(path, content)
                return {'success': False, 'error': 'No path or content specified'}

            elif step.step_type == StepType.EDIT:
                path = context.get('file_path', '')
                old = step.params.get('old_text', '')
                new = step.params.get('new_text', '')
                if path and old and new:
                    return self.filesystem.edit_file(path, old, new)
                return {'success': False, 'error': 'No edit parameters specified'}

            elif step.step_type == StepType.RUN:
                cmd = step.params.get('command', '')
                file_path = context.get('file_path', '')
                if cmd:
                    return self.terminal.run_command(cmd)
                elif file_path:
                    return self.terminal.run_file(file_path)
                return {'success': False, 'error': 'No command or file to run'}

            elif step.step_type == StepType.TEST:
                cmd = step.params.get('test_command', '')
                if cmd:
                    return self.terminal.run_command(cmd)
                return {'success': True, 'output': 'No test command specified'}

            elif step.step_type == StepType.SEARCH:
                pattern = step.params.get('pattern', '')
                path = step.params.get('path', '.')
                if pattern:
                    return self.filesystem.search_code(pattern, path)
                return {'success': False, 'error': 'No search pattern'}

            elif step.step_type == StepType.THINK:
                # Use model for reasoning if available
                if self.model and self.tokenizer and self.tokenizer._loaded:
                    from dikaai.config import CONTEXT_LEN
                    tokens = self.tokenizer.encode(step.description, max_length=CONTEXT_LEN)
                    generated = self.model.generate(tokens, max_len=100, temperature=0.5)
                    response = self.tokenizer.decode(generated)
                    return {'success': True, 'reasoning': response}
                return {'success': True, 'reasoning': step.description}

            elif step.step_type == StepType.EXPLAIN:
                return {'success': True, 'explanation': step.description}

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}

    def _auto_fix(self, failed_step: Step, error: str, context: dict) -> str:
        """Try to automatically fix an error."""
        # Check coding memory for similar errors
        experience = self.memory.find_solution(error)
        if experience:
            fix = experience.get('solution', '')
            if fix:
                # Try to apply the fix
                try:
                    file_path = context.get('file_path', '')
                    if file_path and 'import' in error.lower():
                        # Module not found - try to install
                        module = error.split('ModuleNotFoundError:')[-1].strip().split("'")[1] if "'" in error else ''
                        if module:
                            self.terminal.run_command(f'pip install {module}')
                            return f'Installed missing module: {module}'
                except Exception:
                    pass

        # Common fixes
        if 'ModuleNotFoundError' in error:
            module = error.split("'")[1] if "'" in error else ''
            if module:
                self.terminal.run_command(f'pip install {module}')
                return f'Installed: {module}'

        if 'SyntaxError' in error:
            return f'Syntax error needs manual fix: {error[:100]}'

        if 'IndentationError' in error:
            return f'Indentation error needs manual fix'

        return None
