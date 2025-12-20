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


class WorktreeNotFoundError(WtsError):
    """Raised when worktree does not exist."""

    pass


class EditorNotConfiguredError(WtsError):
    """Raised when no editor is configured."""

    pass


class UnsupportedEditorError(WtsError):
    """Raised when the specified editor is not supported."""

    pass


class WorktreeNotCleanError(WtsError):
    """Raised when worktree has uncommitted changes."""

    pass


class MergeConflictError(WtsError):
    """Raised when squash merge fails due to conflicts."""

    pass
