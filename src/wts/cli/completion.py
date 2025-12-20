"""Shell completion helpers for WTS CLI."""

from click.shell_completion import CompletionItem

from wts.core.worktree import WorktreeManager


def complete_worktree_names(ctx: object, param: object, incomplete: str) -> list[CompletionItem]:
    """Provide completion for worktree names.

    Args:
        ctx: Click context (unused but required by signature).
        param: Click parameter (unused but required by signature).
        incomplete: The partial worktree name typed so far.

    Returns:
        List of CompletionItem objects matching the incomplete prefix.
    """
    try:
        manager = WorktreeManager()
        worktrees = manager.list()
        return [CompletionItem(name) for name in worktrees if name.startswith(incomplete)]
    except Exception:
        # If completion fails (e.g., not in a git repo), return empty list
        return []
