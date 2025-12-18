"""Pytest fixtures for WTS tests."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def worktree_base_path(tmp_path: Path) -> Path:
    """Temporary directory for worktree storage."""
    base = tmp_path / "worktrees"
    base.mkdir()
    return base


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create temporary git repository with initial commit."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    readme = repo / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


@pytest.fixture
def cli_runner(tmp_git_repo: Path, worktree_base_path: Path, monkeypatch: pytest.MonkeyPatch):
    """CLI runner configured for test repository."""
    monkeypatch.chdir(tmp_git_repo)
    monkeypatch.setenv("WTS_WORKTREE_BASE", str(worktree_base_path))

    class WtsCliRunner:
        """Wrapper around Click's CliRunner with simpler interface."""

        def invoke(self, args: list[str]):
            """Invoke CLI command with given arguments."""
            from click.testing import CliRunner
            from wts.cli import cli

            runner = CliRunner()
            return runner.invoke(cli, args)

    return WtsCliRunner()
