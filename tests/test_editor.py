"""Tests for the editor functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest
import wts.core.editor as editor_module


@pytest.mark.e2e
def test_create_worktree_with_editor_default(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=default uses WTS_EDITOR env var."""
    monkeypatch.setenv("WTS_EDITOR", "cursor")
    repo_name = tmp_git_repo.name

    # Patch subprocess.run within the editor module
    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-editor", "--editor=default"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    worktree_path = worktree_base_path / repo_name / "feature-editor"
    assert worktree_path.exists()

    # Check that subprocess.run was called with cursor
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "cursor"
    assert str(worktree_path) == call_args[1]


@pytest.mark.e2e
def test_create_worktree_with_editor_override(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=value overrides WTS_EDITOR env var."""
    monkeypatch.setenv("WTS_EDITOR", "code")

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-editor-override", "--editor=zed"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Check that zed was called, not code (override worked)
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "zed"


@pytest.mark.e2e
def test_create_worktree_with_editor_short_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -e short flag works."""
    monkeypatch.setenv("WTS_EDITOR", "subl")

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-editor-short", "-e", "default"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "subl"


@pytest.mark.e2e
def test_create_worktree_editor_not_configured_error(
    tmp_git_repo: Path,
    cli_runner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test error when --editor=default used without WTS_EDITOR configured."""
    monkeypatch.delenv("WTS_EDITOR", raising=False)

    result = cli_runner.invoke(["create", "feature-no-editor", "--editor=default"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    assert "WTS_EDITOR" in result.output or "editor" in result.output.lower()


@pytest.mark.e2e
def test_create_worktree_unsupported_editor_error(
    tmp_git_repo: Path,
    cli_runner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test error when unsupported editor specified."""
    result = cli_runner.invoke(["create", "feature-bad-editor", "--editor=emacs"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    assert "emacs" in result.output.lower()
    assert "supported" in result.output.lower()
