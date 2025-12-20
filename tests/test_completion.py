"""Tests for shell completion functionality."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clean_wts_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure clean WTS environment for each test."""
    monkeypatch.delenv("WTS_TERMINAL", raising=False)
    monkeypatch.delenv("WTS_EDITOR", raising=False)


@pytest.mark.e2e
def test_completion_suggests_worktree_names_for_select(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that select command completes worktree names."""
    # Setup: Create some worktrees
    cli_runner.invoke(["create", "feature-alpha"])
    cli_runner.invoke(["create", "feature-beta"])
    cli_runner.invoke(["create", "bugfix-gamma"])

    # Test completion using Click's completion mechanism
    from click.shell_completion import ShellComplete
    from wts.cli import cli

    complete = ShellComplete(cli, {}, "wts", "_WTS_COMPLETE")

    # Simulate completing "wts select feat"
    completions = complete.get_completions(["select"], "feat")
    names = [c.value for c in completions]

    assert "feature-alpha" in names
    assert "feature-beta" in names
    assert "bugfix-gamma" not in names


@pytest.mark.e2e
def test_completion_suggests_worktree_names_for_delete(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that delete command completes worktree names."""
    # Setup: Create some worktrees
    cli_runner.invoke(["create", "feature-one"])
    cli_runner.invoke(["create", "feature-two"])

    from click.shell_completion import ShellComplete
    from wts.cli import cli

    complete = ShellComplete(cli, {}, "wts", "_WTS_COMPLETE")

    # Simulate completing "wts delete feature-"
    completions = complete.get_completions(["delete"], "feature-")
    names = [c.value for c in completions]

    assert "feature-one" in names
    assert "feature-two" in names


@pytest.mark.e2e
def test_completion_suggests_all_worktrees_with_empty_prefix(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that empty prefix returns all worktrees."""
    cli_runner.invoke(["create", "alpha"])
    cli_runner.invoke(["create", "beta"])

    from click.shell_completion import ShellComplete
    from wts.cli import cli

    complete = ShellComplete(cli, {}, "wts", "_WTS_COMPLETE")

    completions = complete.get_completions(["select"], "")
    names = [c.value for c in completions]

    assert "alpha" in names
    assert "beta" in names


@pytest.mark.e2e
def test_completion_returns_empty_when_no_worktrees(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that completion returns empty list when no worktrees exist."""
    from click.shell_completion import ShellComplete
    from wts.cli import cli

    complete = ShellComplete(cli, {}, "wts", "_WTS_COMPLETE")

    completions = complete.get_completions(["select"], "")

    assert len(completions) == 0


@pytest.mark.e2e
def test_completion_command_generates_bash_script(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that 'wts completion bash' generates a bash script."""
    result = cli_runner.invoke(["completion", "bash"])

    assert result.exit_code == 0
    # Bash completion scripts contain _wts_completion function or complete builtin
    assert "_wts_completion" in result.output or "complete" in result.output.lower()


@pytest.mark.e2e
def test_completion_command_generates_zsh_script(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that 'wts completion zsh' generates a zsh script."""
    result = cli_runner.invoke(["completion", "zsh"])

    assert result.exit_code == 0
    # Zsh completion scripts use compdef or define _wts function
    assert "compdef" in result.output or "_wts" in result.output


@pytest.mark.e2e
def test_completion_command_generates_fish_script(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that 'wts completion fish' generates a fish script."""
    result = cli_runner.invoke(["completion", "fish"])

    assert result.exit_code == 0
    # Fish completion scripts use 'complete' command
    assert "complete" in result.output


@pytest.mark.e2e
def test_completion_command_rejects_invalid_shell(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that invalid shell name is rejected."""
    result = cli_runner.invoke(["completion", "powershell"])

    assert result.exit_code != 0
