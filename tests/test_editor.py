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


@pytest.mark.e2e
def test_create_worktree_with_editor_claude(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --editor=claude opens a terminal with claude command."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-claude", "--editor=claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    worktree_path = worktree_base_path / repo_name / "feature-claude"
    assert worktree_path.exists()

    # Check that subprocess.run was called with osascript containing claude command
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "osascript"
    script = call_args[2]
    assert str(worktree_path) in script
    assert "claude" in script


@pytest.mark.e2e
def test_create_worktree_with_bare_editor_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that bare -e flag (without value) uses the default editor from config."""
    monkeypatch.setenv("WTS_EDITOR", "cursor")
    repo_name = tmp_git_repo.name

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        # Key: using just "-e" without any value
        result = cli_runner.invoke(["create", "feature-bare-e", "-e"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    worktree_path = worktree_base_path / repo_name / "feature-bare-e"
    assert worktree_path.exists()

    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "cursor"  # Should use the configured editor


@pytest.mark.e2e
def test_create_worktree_with_bare_editor_long_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that bare --editor flag (without value) uses the default editor."""
    monkeypatch.setenv("WTS_EDITOR", "zed")
    repo_name = tmp_git_repo.name

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        # Key: using just "--editor" without any value
        result = cli_runner.invoke(["create", "feature-bare-editor", "--editor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-bare-editor"
    assert worktree_path.exists()

    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "zed"


@pytest.mark.e2e
def test_select_worktree_with_bare_editor_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that select command with bare -e flag works."""
    monkeypatch.setenv("WTS_EDITOR", "code")

    # First create the worktree
    result = cli_runner.invoke(["create", "feature-select-bare-e"])
    assert result.exit_code == 0

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["select", "feature-select-bare-e", "-e"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "code"


@pytest.mark.e2e
def test_select_worktree_with_editor_claude(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that select --editor=claude opens a terminal with claude command."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    # First create the worktree
    result = cli_runner.invoke(["create", "feature-claude-select"])
    assert result.exit_code == 0

    worktree_path = worktree_base_path / repo_name / "feature-claude-select"

    # Now select it with --editor=claude
    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["select", "feature-claude-select", "--editor=claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Selected worktree" in result.output

    # Check that subprocess.run was called with osascript containing claude command
    mock_subprocess.run.assert_called_once()
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "osascript"
    script = call_args[2]
    assert str(worktree_path) in script
    assert "claude" in script


# Tests for init script behavior with editors


@pytest.mark.e2e
def test_create_worktree_with_editor_claude_runs_init_in_terminal(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -e claude runs init script in terminal before claude."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "uv sync")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-init-test", "-e", "claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Init should NOT run in parent terminal
    assert "Running init script..." not in result.output

    # Verify terminal command includes: cd, init script, then claude
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    assert "uv sync" in script
    # Check the command chain is in the correct order: init_script && claude
    assert "uv sync && claude" in script


@pytest.mark.e2e
def test_create_worktree_with_editor_cursor_runs_init_in_parent(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -e cursor runs init in parent terminal (not new terminal)."""
    monkeypatch.setenv("WTS_INIT_SCRIPT", "echo 'parent init'")

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-cursor-init", "-e", "cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Init SHOULD run in parent terminal
    assert "Running init script..." in result.output
    assert "parent init" in result.output
    assert "Init script completed successfully" in result.output

    # Cursor should be opened
    call_args = mock_subprocess.run.call_args[0][0]
    assert call_args[0] == "cursor"


@pytest.mark.e2e
def test_create_worktree_with_terminal_and_editor_claude(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t -e claude runs init then claude in terminal (no duplicate terminal)."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "pip install -e .")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-t-e-claude", "-t", "-e", "claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Should only open ONE terminal (not two)
    assert mock_subprocess.run.call_count == 1

    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    assert "pip install -e ." in script
    assert "claude" in script
