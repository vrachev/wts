"""Worktree management core logic."""

import re
import subprocess
import sys
from pathlib import Path

from wts.config import Config
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
        return Config.load(self.repo_path).worktree_base

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

    def _run_init_script(self, worktree_path: Path, script: str) -> bool:
        """Run the init script in a worktree directory.

        Args:
            worktree_path: Path to the worktree.
            script: Shell command to run.

        Returns:
            True if script succeeded, False otherwise.
        """
        try:
            result = subprocess.run(
                script,
                shell=True,
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Warning: init script failed with exit code {result.returncode}", file=sys.stderr)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                return False
            return True
        except Exception as e:
            print(f"Warning: init script failed: {e}", file=sys.stderr)
            return False

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

    def create(self, name: str, from_current: bool = False, run_init: bool = True) -> Path:
        """Create a new worktree.

        Args:
            name: Name for the worktree and branch.
            from_current: If True, branch from current HEAD. Otherwise, branch from main.
            run_init: If True, run the init script after creating the worktree.

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

        # Run init script if configured
        if run_init:
            config = Config.load(self.repo_path)
            if config.init_script:
                self._run_init_script(worktree_path, config.init_script)

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
        auto_resolve_claude: bool = False,
    ) -> None:
        """Squash merge a worktree branch into target branch.

        Args:
            name: Name of the worktree/branch to merge.
            message: Commit message for the squash merge. Required unless use_latest_msg is True.
            into: Target branch to merge into. Defaults to "main".
            cleanup: If True, delete worktree and branch after merge.
            use_latest_msg: If True, use the latest commit message from the branch.
            auto_resolve_claude: If True, attempt to auto-resolve conflicts using Claude CLI.

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
        except subprocess.CalledProcessError as e:
            # Capture error details before aborting
            error_details = e.stderr.decode() if e.stderr else str(e)

            # Abort the failed merge
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

            if not auto_resolve_claude:
                raise MergeConflictError(f"Squash merge failed for '{name}' into '{into}':\n{error_details}")

            # Try rebase in worktree
            try:
                subprocess.run(
                    ["git", "fetch", "origin", into],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "rebase", f"origin/{into}"],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                # Rebase failed, call Claude to resolve
                subprocess.run(
                    ["git", "rebase", "--abort"],
                    cwd=worktree_path,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        "claude",
                        "--print",
                        "-p",
                        f"Rebase this branch onto origin/{into} and resolve any conflicts. "
                        f"Keep the changes from this branch's commit: {message}",
                    ],
                    cwd=worktree_path,
                    check=True,
                )

            # Retry the squash merge
            subprocess.run(
                ["git", "checkout", into],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
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

        if cleanup:
            self.delete(name, keep_branch=False)
