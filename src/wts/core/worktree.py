"""Worktree management core logic."""

import re
import subprocess
from pathlib import Path

from wts.config import get_config
from wts.exceptions import (
    InvalidWorktreeNameError,
    MergeConflictError,
    WorktreeExistsError,
    WorktreeNotCleanError,
    WorktreeNotFoundError,
)


class WorktreeManager:
    """Manages git worktree operations."""

    def __init__(self, repo_path: Path | None = None, worktree_base: Path | None = None) -> None:
        """Initialize WorktreeManager.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
            worktree_base: Base path for worktrees. Defaults to WTS_WORKTREE_BASE env var
                          or ~/github/worktrees.
        """
        self.repo_path = repo_path or Path.cwd()
        self.worktree_base = worktree_base or self._get_worktree_base()
        self.repo_name = self._get_repo_name()

    def _get_worktree_base(self) -> Path:
        """Get the base path for worktrees."""
        return get_config().worktree_base

    def _get_repo_name(self) -> str:
        """Get the repository name from the git root directory."""
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).name

    def _validate_name(self, name: str) -> None:
        """Validate worktree name.

        Args:
            name: The worktree name to validate.

        Raises:
            InvalidWorktreeNameError: If the name is invalid.
        """
        if "/" in name:
            raise InvalidWorktreeNameError(f"Invalid worktree name '{name}': cannot contain '/'")
        if " " in name:
            raise InvalidWorktreeNameError(f"Invalid worktree name '{name}': cannot contain spaces")
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise InvalidWorktreeNameError(
                f"Invalid worktree name '{name}': must contain only alphanumeric characters, hyphens, and underscores"
            )

    def _get_worktree_path(self, name: str) -> Path:
        """Get the path where a worktree should be created."""
        return self.worktree_base / self.repo_name / name

    def _branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return branch_name in result.stdout

    def _worktree_exists(self, name: str) -> bool:
        """Check if a worktree with the given name already exists (path or git)."""
        worktree_path = self._get_worktree_path(name)
        if worktree_path.exists():
            return True
        return self._is_git_worktree(name)

    def _is_git_worktree(self, name: str) -> bool:
        """Check if a worktree is registered with git."""
        worktree_path = self._get_worktree_path(name)
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                path = line[9:]  # Remove "worktree " prefix
                if path == str(worktree_path):
                    return True
        return False

    def create(self, name: str, from_current: bool = False) -> Path:
        """Create a new worktree.

        Args:
            name: Name for the worktree and branch.
            from_current: If True, branch from current HEAD. Otherwise, branch from main.

        Returns:
            Path to the created worktree.

        Raises:
            InvalidWorktreeNameError: If the name is invalid.
            WorktreeExistsError: If a worktree with the name already exists.
        """
        self._validate_name(name)

        if self._worktree_exists(name):
            raise WorktreeExistsError(f"Worktree '{name}' already exists")

        if self._branch_exists(name):
            raise WorktreeExistsError(f"Branch '{name}' already exists")

        worktree_path = self._get_worktree_path(name)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        if from_current:
            base_ref = "HEAD"
        else:
            base_ref = "main"

        subprocess.run(
            ["git", "worktree", "add", "-b", name, str(worktree_path), base_ref],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        return worktree_path

    def delete(self, name: str, keep_branch: bool = False) -> None:
        """Delete a worktree.

        Args:
            name: Name of the worktree to delete.
            keep_branch: If True, keep the branch after removing the worktree.

        Raises:
            InvalidWorktreeNameError: If the name is invalid.
            WorktreeNotFoundError: If the worktree does not exist.
        """
        self._validate_name(name)

        if not self._is_git_worktree(name):
            raise WorktreeNotFoundError(f"Worktree '{name}' not found")

        worktree_path = self._get_worktree_path(name)

        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        if not keep_branch:
            subprocess.run(
                ["git", "branch", "-D", name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

    def list(self) -> list[str]:
        """List all worktrees for this repository.

        Returns:
            List of worktree names.
        """
        worktree_dir = self.worktree_base / self.repo_name
        if not worktree_dir.exists():
            return []
        return sorted([d.name for d in worktree_dir.iterdir() if d.is_dir()])

    def _is_worktree_clean(self, worktree_path: Path) -> bool:
        """Check if a worktree has no uncommitted changes.

        Args:
            worktree_path: Path to the worktree.

        Returns:
            True if worktree is clean, False otherwise.
        """
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() == ""

    def _get_current_branch(self) -> str:
        """Get the current branch name in the main repo.

        Returns:
            Current branch name.
        """
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def _get_latest_commit_message(self, branch: str) -> str:
        """Get the latest commit message from a branch.

        Args:
            branch: The branch name to get the commit message from.

        Returns:
            The latest commit message.
        """
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B", branch],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def complete(
        self,
        name: str,
        message: str | None = None,
        into: str = "main",
        cleanup: bool = True,
        use_latest_msg: bool = False,
    ) -> None:
        """Squash merge a worktree branch into target branch.

        Args:
            name: Name of the worktree/branch to merge.
            message: Commit message for the squash merge. Required unless use_latest_msg is True.
            into: Target branch to merge into. Defaults to "main".
            cleanup: If True, delete worktree and branch after merge.
            use_latest_msg: If True, use the latest commit message from the branch.

        Raises:
            InvalidWorktreeNameError: If the name is invalid.
            WorktreeNotFoundError: If the worktree does not exist.
            WorktreeNotCleanError: If worktree has uncommitted changes.
            MergeConflictError: If squash merge fails due to conflicts.
        """
        self._validate_name(name)

        if not self._is_git_worktree(name):
            raise WorktreeNotFoundError(f"Worktree '{name}' not found")

        worktree_path = self._get_worktree_path(name)
        if not self._is_worktree_clean(worktree_path):
            raise WorktreeNotCleanError(
                f"Worktree '{name}' has uncommitted changes. " "Please commit or stash changes before merging."
            )

        if use_latest_msg:
            message = self._get_latest_commit_message(name)

        assert message is not None, "Message must be provided or use_latest_msg must be True"

        original_branch = self._get_current_branch()

        subprocess.run(
            ["git", "checkout", into],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        try:
            subprocess.run(
                ["git", "merge", "--squash", name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["git", "merge", "--abort"],
                cwd=self.repo_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "checkout", original_branch],
                cwd=self.repo_path,
                capture_output=True,
            )
            raise MergeConflictError(f"Squash merge failed for '{name}' into '{into}'")

        if cleanup:
            self.delete(name, keep_branch=False)
