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
        "WTS_INIT_SCRIPT",
    ]:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def isolate_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use temporary config path to avoid writing to user's real config."""
    import wts.cli.config
    import wts.cli.init
    import wts.cli.main
    import wts.config

    config_dir = tmp_path / "config" / "wts"

    def mock_get_config_path(repo_root=None, local: bool = True):
        filename = wts.config.CONFIG_FILENAME_LOCAL if local else wts.config.CONFIG_FILENAME_PROJECT
        return config_dir / filename

    def mock_get_active_config_path(repo_root=None):
        local_path = config_dir / wts.config.CONFIG_FILENAME_LOCAL
        if local_path.exists():
            return local_path
        return config_dir / wts.config.CONFIG_FILENAME_PROJECT

    def mock_config_exists(repo_root=None):
        local_path = config_dir / wts.config.CONFIG_FILENAME_LOCAL
        project_path = config_dir / wts.config.CONFIG_FILENAME_PROJECT
        return local_path.exists() or project_path.exists()

    # Patch in the config module
    monkeypatch.setattr(wts.config, "get_config_path", mock_get_config_path)
    monkeypatch.setattr(wts.config, "get_active_config_path", mock_get_active_config_path)
    monkeypatch.setattr(wts.config, "config_exists", mock_config_exists)

    # Also patch in modules that import these functions directly
    monkeypatch.setattr(wts.cli.init, "config_exists", mock_config_exists)
    monkeypatch.setattr(wts.cli.main, "config_exists", mock_config_exists)
    monkeypatch.setattr(wts.cli.config, "get_active_config_path", mock_get_active_config_path)

    return config_dir


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
def cli_runner(
    tmp_git_repo: Path, worktree_base_path: Path, isolate_config_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """CLI runner configured for test repository."""
    monkeypatch.chdir(tmp_git_repo)
    monkeypatch.setenv("WTS_WORKTREE_BASE", str(worktree_base_path))

    # Pre-create config to skip auto-init for most tests
    import wts.config

    config_path = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(f"worktree_base: {worktree_base_path}\n")

    class WtsCliRunner:
        """Wrapper around Click's CliRunner with simpler interface."""

        def invoke(self, args: list[str], input: str | None = None):
            """Invoke CLI command with given arguments."""
            from click.testing import CliRunner
            from wts.cli import cli

            runner = CliRunner()
            return runner.invoke(cli, args, input=input)

    return WtsCliRunner()
