"""DikaAI Task Planner - Breaks down coding tasks into actionable steps."""

from enum import Enum


class StepType(Enum):
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    RUN = "run"
    TEST = "test"
    DEBUG = "debug"
    SEARCH = "search"
    THINK = "think"
    EXPLAIN = "explain"


class Step:
    def __init__(self, step_type: StepType, description: str, params: dict = None):
        self.step_type = step_type
        self.description = description
        self.params = params or {}
        self.result = None
        self.success = None

    def __repr__(self):
        return f"Step({self.step_type.value}: {self.description})"


class Planner:
    """Plans coding tasks by breaking them into steps."""

    def plan(self, task: str, context: dict = None) -> list:
        """Create a plan for a coding task."""
        context = context or {}
        action = context.get('action', 'chat')
        language = context.get('language')

        if action in ('create', 'write'):
            return self._plan_create(task, language)
        elif action in ('edit', 'fix', 'refactor'):
            return self._plan_edit(task, context)
        elif action == 'debug':
            return self._plan_debug(task, context)
        elif action == 'run':
            return self._plan_run(task, context)
        elif action == 'explain':
            return self._plan_explain(task, context)
        elif action == 'search':
            return self._plan_search(task, context)
        else:
            return self._plan_general(task, context)

    def _plan_create(self, task: str, language: str = None) -> list:
        """Plan for creating new code."""
        steps = [
            Step(StepType.THINK, "Analyze requirements and plan code structure"),
            Step(StepType.WRITE, "Write the code", {'language': language}),
            Step(StepType.RUN, "Run the code to verify it works"),
        ]
        return steps

    def _plan_edit(self, task: str, context: dict) -> list:
        """Plan for editing/fixing existing code."""
        file_path = context.get('file_path', '')
        steps = []

        if file_path:
            steps.append(Step(StepType.READ, f"Read {file_path} to understand current code"))

        steps.extend([
            Step(StepType.THINK, "Analyze the issue and plan changes"),
            Step(StepType.EDIT, "Apply the fix/modification"),
            Step(StepType.RUN, "Run the code to verify the fix"),
        ])

        return steps

    def _plan_debug(self, task: str, context: dict) -> list:
        """Plan for debugging an error."""
        error = context.get('error', '')
        file_path = context.get('file_path', '')

        steps = []

        if file_path:
            steps.append(Step(StepType.READ, f"Read {file_path} to find the bug"))

        steps.extend([
            Step(StepType.THINK, f"Analyze error: {error[:100]}"),
            Step(StepType.SEARCH, "Search for similar errors and solutions"),
            Step(StepType.EDIT, "Apply the fix"),
            Step(StepType.RUN, "Run to verify fix works"),
        ])

        return steps

    def _plan_run(self, task: str, context: dict) -> list:
        """Plan for running code."""
        file_path = context.get('file_path', '')
        return [
            Step(StepType.READ, f"Check {file_path}" if file_path else "Check code"),
            Step(StepType.RUN, "Execute the code"),
        ]

    def _plan_explain(self, task: str, context: dict) -> list:
        """Plan for explaining code."""
        file_path = context.get('file_path', '')
        steps = []
        if file_path:
            steps.append(Step(StepType.READ, f"Read {file_path}"))
        steps.append(Step(StepType.THINK, "Analyze and explain the code"))
        return steps

    def _plan_search(self, task: str, context: dict) -> list:
        """Plan for searching."""
        return [
            Step(StepType.SEARCH, f"Search for: {task}"),
        ]

    def _plan_general(self, task: str, context: dict) -> list:
        """General plan."""
        return [
            Step(StepType.THINK, "Analyze the request"),
            Step(StepType.EXPLAIN, "Provide response"),
        ]
