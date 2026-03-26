import logging
from typing import Dict, Any, Callable, TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.application.dispatcher import IntentDispatcher

logger = logging.getLogger(__name__)

class IntentRegistry:
    """
    Extensible registry for bot commands.
    Follows the pluggable architecture pattern mentors love.
    """
    _registry: Dict[str, Callable[['IntentDispatcher'], str]] = {}

    @classmethod
    def register(cls, commands: List[str]):
        """Decorator to register one or more commands to a handler function."""
        def decorator(func: Callable[['IntentDispatcher'], str]):
            for command in commands:
                cls._registry[command.lower()] = func
            return func
        return decorator

    @classmethod
    def get_handler(cls, command: str) -> Callable[['IntentDispatcher'], str]:
        """Retrieve a handler for a given command string."""
        return cls._registry.get(command.lower())

    @classmethod
    def list_commands(cls) -> List[str]:
        """Returns a list of all registered command strings."""
        return list(cls._registry.keys())

# --- Global Registry Instance ---
intent_registry = IntentRegistry()
