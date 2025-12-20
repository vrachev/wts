"""Tests for the terminal functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest
import wts.core.terminal as terminal_module


@pytest.mark.e2e
def test_create_worktree_with_terminal_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --terminal flag opens a terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    worktree_path = worktree_base_path / repo_name / "feature-terminal"
    assert worktree_path.exists()

    # Check that subprocess.run was called (for iTerm2 osascript)
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "osascript"
    assert str(worktree_path) in call_args[2]


@pytest.mark.e2e
def test_create_worktree_with_terminal_short_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t short flag works."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-short", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-short"
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "osascript"
    assert str(worktree_path) in call_args[2]


@pytest.mark.e2e
def test_create_worktree_with_terminal_tmux(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that tmux terminal uses tmux commands."""
    monkeypatch.setenv("WTS_TERMINAL", "tmux")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-tmux", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-tmux"
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "tmux"
    assert "split-window" in call_args
    assert str(worktree_path) in call_args


@pytest.mark.e2e
def test_create_worktree_with_terminal_warp(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that warp terminal uses open command."""
    monkeypatch.setenv("WTS_TERMINAL", "warp")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-warp", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-warp"
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "open"
    assert "-a" in call_args
    assert "Warp" in call_args
    assert str(worktree_path) in call_args


@pytest.mark.e2e
def test_create_worktree_with_terminal_none(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that WTS_TERMINAL=none doesn't open a terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "none")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-none", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-none"
    assert worktree_path.exists()

    # subprocess.run should NOT be called when terminal is "none"
    mock_subprocess.run.assert_not_called()


@pytest.mark.e2e
def test_create_worktree_without_terminal_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that omitting --terminal flag doesn't open a terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-no-terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-no-terminal"
    assert worktree_path.exists()

    # subprocess.run should NOT be called when --terminal is not passed
    mock_subprocess.run.assert_not_called()


@pytest.mark.e2e
def test_create_worktree_with_terminal_mode_tab(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that WTS_TERMINAL_MODE=tab opens a new tab."""
    monkeypatch.setenv("WTS_TERMINAL", "tmux")
    monkeypatch.setenv("WTS_TERMINAL_MODE", "tab")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-tab", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-tab"
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "tmux"
    assert "new-window" in call_args
    assert str(worktree_path) in call_args


@pytest.mark.e2e
def test_create_worktree_with_terminal_split_horizontal(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that WTS_TERMINAL_SPLIT=horizontal creates horizontal split."""
    monkeypatch.setenv("WTS_TERMINAL", "tmux")
    monkeypatch.setenv("WTS_TERMINAL_SPLIT", "horizontal")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-terminal-hsplit", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-terminal-hsplit"
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "tmux"
    assert "split-window" in call_args
    # tmux uses -v for horizontal (stacked panes)
    assert "-v" in call_args
    assert str(worktree_path) in call_args
