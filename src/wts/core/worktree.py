"""Worktree management core logic."""

import re
import subprocess
import sys
from pathlib import Path

from wts.config import Config
from wts.exceptions import (
    InvalidWorktreeNameError,
    MergeConflictError,
    RepoNotCleanError,
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
        print("Running init script...")
        try:
            # Use Popen for real-time output streaming
            # Use bash explicitly to support bash-specific commands like 'source'
            process = subprocess.Popen(
                ["bash", "-c", script],
                cwd=worktree_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified output
                text=True,
                bufsize=1,  # Line buffered
            )

            # Stream output in real-time
            if process.stdout:
                for line in process.stdout:
                    print(line, end="")

            process.wait()

            if process.returncode != 0:
                print(f"Warning: init script failed with exit code {process.returncode}", file=sys.stderr)
                return False

            print("Init script completed successfully")
            return True
        except Exception as e:
            print(f"Warning: init script failed: {e}", file=sys.stderr)
            return False

    def get_init_script(self) -> str | None:
        """Get the init script command if configured.

        Returns:
            The init script command string, or None if not configured.
        """
        config = Config.load(self.repo_path)
        return config.init_script

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
        squash: bool = True,
    ) -> None:
        """Merge a worktree branch into target branch.

        Args:
            name: Name of the worktree/branch to merge.
            message: Commit message for squash merge. Required for squash merge unless use_latest_msg is True.
            into: Target branch to merge into. Defaults to "main".
            cleanup: If True, delete worktree and branch after merge.
            use_latest_msg: If True, use the latest commit message from the branch.
            auto_resolve_claude: If True, attempt to auto-resolve conflicts using Claude CLI.
            squash: If True (default), perform squash merge. If False, perform regular merge.

        Raises:
            InvalidWorktreeNameError: If the name is invalid.
            WorktreeNotFoundError: If the worktree does not exist.
            WorktreeNotCleanError: If worktree has uncommitted changes.
            MergeConflictError: If merge fails due to conflicts.
        """
        self._validate_name(name)

        if not self._is_git_worktree(name):
            raise WorktreeNotFoundError(f"Worktree '{name}' not found")

        worktree_path = self._get_worktree_path(name)
        if not self._is_worktree_clean(worktree_path):
            raise WorktreeNotCleanError(
                f"Worktree '{name}' has uncommitted changes. " "Please commit or stash changes before merging."
            )

        if squash:
            if use_latest_msg:
                message = self._get_latest_commit_message(name)
            assert message is not None, "Message must be provided or use_latest_msg must be True for squash merge"

        # Check if main repo is clean before attempting checkout
        if not self._is_worktree_clean(self.repo_path):
            raise RepoNotCleanError(
                "Main repository has uncommitted changes or unmerged files. "
                "Please run 'git status' to see the state and resolve before merging."
            )

        original_branch = self._get_current_branch()

        try:
            subprocess.run(
                ["git", "checkout", into],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            if squash:
                assert message is not None
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
            else:
                subprocess.run(
                    ["git", "merge", name],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
        except subprocess.CalledProcessError as e:
            # Capture error details before aborting
            error_details = e.stderr.decode() if e.stderr else str(e)

            # Clean up the failed merge - reset to clean state
            subprocess.run(
                ["git", "merge", "--abort"],
                cwd=self.repo_path,
                capture_output=True,
            )
            # Reset any uncommitted changes from the failed merge/checkout
            subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "checkout", original_branch],
                cwd=self.repo_path,
                capture_output=True,
            )

            if not auto_resolve_claude:
                merge_type = "Squash merge" if squash else "Merge"
                raise MergeConflictError(f"{merge_type} failed for '{name}' into '{into}':\n{error_details}")

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
                prompt = f"Rebase this branch onto origin/{into} and resolve any conflicts."
                if message:
                    prompt += f" Keep the changes from this branch's commit: {message}"
                subprocess.run(
                    [
                        "claude",
                        "--print",
                        "-p",
                        prompt,
                    ],
                    cwd=worktree_path,
                    check=True,
                )

            # Retry the merge
            subprocess.run(
                ["git", "checkout", into],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            if squash:
                assert message is not None
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
            else:
                subprocess.run(
                    ["git", "merge", name],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )

        if cleanup:
            self.delete(name, keep_branch=False)
