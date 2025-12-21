"""Pytest fixtures for WTS tests."""

import subprocess
from pathlib import Path

import pytest
from wts.config import reset_config


@pytest.fixture(autouse=True)
def reset_wts_config() -> None:
    """Reset config singleton between tests."""
    reset_config()
    yield
    reset_config()


@pytest.fixture(autouse=True)
def isolate_wts_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all WTS env vars to prevent test pollution."""
    for var in [
        "WTS_WORKTREE_BASE",
        "WTS_EDITOR",
        "WTS_TERMINAL",
        "WTS_TERMINAL_MODE",
        "WTS_TERMINAL_SPLIT",
    ]:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def isolate_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use temporary config path to avoid writing to user's real config."""
    import wts.config

    config_path = tmp_path / "config" / "wts" / "config.yaml"
    monkeypatch.setattr(wts.config, "get_config_path", lambda repo_root=None: config_path)
    return config_path


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

        def invoke(self, args: list[str], input: str | None = None):
            """Invoke CLI command with given arguments."""
            from click.testing import CliRunner
            from wts.cli import cli

            runner = CliRunner()
            return runner.invoke(cli, args, input=input)

    return WtsCliRunner()
