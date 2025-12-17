"""Custom exceptions for WTS."""


class WtsError(Exception):
    """Base exception for WTS errors."""

    pass


class WorktreeExistsError(WtsError):
    """Raised when trying to create a worktree that already exists."""

    pass


class InvalidWorktreeNameError(WtsError):
    """Raised when worktree name is invalid."""

    pass
