"""Brain service — coordinates story generation via an injected Brain implementation."""

from ai_content_studio.brain.interfaces import Brain
from ai_content_studio.shared.models import Story


class BrainService:
    """Orchestrates story generation using an injected Brain implementation."""

    def __init__(self, brain: Brain) -> None:
        self._brain = brain

    def generate_story(self, idea: str) -> Story:
        """Delegate story generation to the Brain implementation."""
        return self._brain.generate_story(idea)
