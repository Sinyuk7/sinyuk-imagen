"""Private task orchestration exceptions."""


class InvalidTaskTransition(RuntimeError):
    """Raised when the runtime attempts an impossible task state change."""
