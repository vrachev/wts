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
    """Test that -t -e claude opens TWO terminals (plain + claude)."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "pip install -e .")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-term-plus-editor", "-t", "-e", "claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Should open TWO terminals (plain terminal + claude terminal)
    assert mock_subprocess.run.call_count == 2

    # First terminal (plain) should have init script but no claude command
    first_call = mock_subprocess.run.call_args_list[0][0][0]
    first_script = first_call[2]
    assert "pip install -e ." in first_script
    assert "&& claude" not in first_script  # No claude command (path may contain 'claude')

    # Second terminal (claude) should have claude command
    second_call = mock_subprocess.run.call_args_list[1][0][0]
    second_script = second_call[2]
    assert "&& claude" in second_script


# Tests for multiple editor flags


@pytest.mark.e2e
def test_create_worktree_with_multiple_gui_editors(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that multiple -e flags with GUI editors opens all of them."""
    repo_name = tmp_git_repo.name

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-multi-gui", "-e", "code", "-e", "cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    worktree_path = worktree_base_path / repo_name / "feature-multi-gui"
    assert worktree_path.exists()

    # Should open both editors
    assert mock_subprocess.run.call_count == 2

    # Check both editors were called
    calls = [call[0][0][0] for call in mock_subprocess.run.call_args_list]
    assert "code" in calls
    assert "cursor" in calls


@pytest.mark.e2e
def test_create_worktree_with_multiple_editors_mixed(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -e claude -e code opens terminal with claude AND code editor."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with (
        patch.object(terminal_module, "subprocess") as mock_terminal,
        patch.object(editor_module, "subprocess") as mock_editor,
    ):
        result = cli_runner.invoke(["create", "feature-mixed", "-e", "claude", "-e", "code"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-mixed"
    assert worktree_path.exists()

    # Terminal should be opened with claude
    mock_terminal.run.assert_called_once()
    terminal_call = mock_terminal.run.call_args[0][0]
    assert "claude" in terminal_call[2]

    # Code editor should be opened
    mock_editor.run.assert_called_once()
    editor_call = mock_editor.run.call_args[0][0]
    assert editor_call[0] == "code"


@pytest.mark.e2e
def test_create_worktree_with_terminal_and_multiple_editors(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t -e claude -e code opens plain terminal + claude terminal + code."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    repo_name = tmp_git_repo.name

    with (
        patch.object(terminal_module, "subprocess") as mock_terminal,
        patch.object(editor_module, "subprocess") as mock_editor,
    ):
        result = cli_runner.invoke(["create", "feature-all", "-t", "-e", "claude", "-e", "code"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-all"
    assert worktree_path.exists()

    # Two terminals: plain + claude
    assert mock_terminal.run.call_count == 2

    # First call is plain terminal (no claude command)
    first_script = mock_terminal.run.call_args_list[0][0][0][2]
    assert "claude" not in first_script

    # Second call is claude terminal
    second_script = mock_terminal.run.call_args_list[1][0][0][2]
    assert "claude" in second_script

    # Code editor should be opened
    mock_editor.run.assert_called_once()
    editor_call = mock_editor.run.call_args[0][0]
    assert editor_call[0] == "code"


@pytest.mark.e2e
def test_create_worktree_multiple_editors_init_script_runs_once(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that init script only runs in the first terminal opened."""
    import wts.core.terminal as terminal_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "echo init_marker")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-init-once", "-t", "-e", "claude"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Two terminals opened
    assert mock_subprocess.run.call_count == 2

    # First terminal should have init script
    first_script = mock_subprocess.run.call_args_list[0][0][0][2]
    assert "echo init_marker" in first_script

    # Second terminal should NOT have init script
    second_script = mock_subprocess.run.call_args_list[1][0][0][2]
    assert "echo init_marker" not in second_script


@pytest.mark.e2e
def test_create_worktree_multiple_bare_editor_flags(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that multiple bare -e flags use default editor multiple times."""
    monkeypatch.setenv("WTS_EDITOR", "cursor")
    repo_name = tmp_git_repo.name

    with patch.object(editor_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-bare-multi", "-e", "-e"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    worktree_path = worktree_base_path / repo_name / "feature-bare-multi"
    assert worktree_path.exists()

    # Should open cursor twice
    assert mock_subprocess.run.call_count == 2
    for call in mock_subprocess.run.call_args_list:
        assert call[0][0][0] == "cursor"
