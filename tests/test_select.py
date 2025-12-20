"""Tests for the wts select command."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e
def test_select_worktree_basic(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test selecting an existing worktree outputs the path."""
    repo_name = tmp_git_repo.name
    # Setup: create a worktree first
    cli_runner.invoke(["create", "feature-select"])
    worktree_path = worktree_base_path / repo_name / "feature-select"

    result = cli_runner.invoke(["select", "feature-select"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Selected worktree" in result.output
    assert str(worktree_path) in result.output


@pytest.mark.e2e
def test_select_worktree_not_found(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that selecting a non-existent worktree fails."""
    result = cli_runner.invoke(["select", "nonexistent-worktree"])

    assert result.exit_code != 0, "Expected non-zero exit code for non-existent worktree"
    assert "not found" in result.output.lower(), f"Expected 'not found' in output: {result.output}"


@pytest.mark.e2e
def test_select_worktree_invalid_name(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that invalid worktree names are rejected."""
    result = cli_runner.invoke(["select", "foo/bar"])

    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"


@pytest.mark.e2e
def test_select_worktree_with_terminal_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --terminal flag is accepted when selecting a worktree."""
    monkeypatch.setenv("WTS_TERMINAL", "none")
    repo_name = tmp_git_repo.name
    # Setup: create a worktree first
    cli_runner.invoke(["create", "feature-terminal"])
    worktree_path = worktree_base_path / repo_name / "feature-terminal"

    result = cli_runner.invoke(["select", "feature-terminal", "--terminal"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert str(worktree_path) in result.output


@pytest.mark.e2e
def test_select_worktree_with_short_terminal_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t short flag works for terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "none")
    cli_runner.invoke(["create", "feature-t"])

    result = cli_runner.invoke(["select", "feature-t", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"


@pytest.mark.e2e
def test_select_worktree_with_editor_default(
    tmp_git_repo: Path,
    cli_runner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=default uses WTS_EDITOR env var."""
    monkeypatch.setenv("WTS_EDITOR", "cursor")
    cli_runner.invoke(["create", "feature-editor"])

    # Mock subprocess to avoid actually opening editor
    original_run = subprocess.run
    calls = []

    def mock_run(*args, **kwargs):
        if args and args[0] and args[0][0] in ("cursor", "code", "zed", "subl"):
            calls.append(args[0])
            return subprocess.CompletedProcess(args[0], 0)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = cli_runner.invoke(["select", "feature-editor", "--editor=default"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert len(calls) == 1, f"Expected cursor to be called once, got {len(calls)} calls"
    assert calls[0][0] == "cursor"


@pytest.mark.e2e
def test_select_worktree_with_editor_explicit(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=cursor explicitly specifies editor."""
    original_run = subprocess.run
    calls = []

    def mock_run(*args, **kwargs):
        if args and args[0] and args[0][0] == "cursor":
            calls.append(args[0])
            return subprocess.CompletedProcess(args[0], 0)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    cli_runner.invoke(["create", "feature-cursor"])

    result = cli_runner.invoke(["select", "feature-cursor", "--editor=cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert len(calls) == 1, f"Expected cursor to be called once, got {len(calls)} calls"
    assert calls[0][0] == "cursor"


@pytest.mark.e2e
def test_select_worktree_with_short_editor_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -e short flag works for editor."""
    original_run = subprocess.run
    calls = []

    def mock_run(*args, **kwargs):
        if args and args[0] and args[0][0] == "cursor":
            calls.append(args[0])
            return subprocess.CompletedProcess(args[0], 0)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    cli_runner.invoke(["create", "feature-e"])

    result = cli_runner.invoke(["select", "feature-e", "-e", "cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"


@pytest.mark.e2e
def test_select_worktree_editor_not_configured(
    tmp_git_repo: Path,
    cli_runner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=default fails when WTS_EDITOR not set."""
    monkeypatch.delenv("WTS_EDITOR", raising=False)
    cli_runner.invoke(["create", "feature-no-editor"])

    result = cli_runner.invoke(["select", "feature-no-editor", "--editor=default"])

    assert result.exit_code != 0, "Expected non-zero exit code when editor not configured"
    assert "wts_editor" in result.output.lower() or "editor" in result.output.lower()


@pytest.mark.e2e
def test_select_worktree_unsupported_editor(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that unsupported editor is rejected."""
    cli_runner.invoke(["create", "feature-unsupported"])

    result = cli_runner.invoke(["select", "feature-unsupported", "--editor=unsupported-editor"])

    assert result.exit_code != 0, "Expected non-zero exit code for unsupported editor"
    assert "unsupported" in result.output.lower() or "unknown" in result.output.lower()


@pytest.mark.e2e
def test_select_worktree_with_both_flags(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test using both --terminal and --editor flags together."""
    monkeypatch.setenv("WTS_TERMINAL", "none")

    original_run = subprocess.run
    calls = []

    def mock_run(*args, **kwargs):
        if args and args[0] and args[0][0] == "cursor":
            calls.append(args[0])
            return subprocess.CompletedProcess(args[0], 0)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    cli_runner.invoke(["create", "feature-both"])

    result = cli_runner.invoke(["select", "feature-both", "--terminal", "--editor=cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert len(calls) == 1, f"Expected cursor to be called once, got {len(calls)} calls"
