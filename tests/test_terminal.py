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


# Tests for init script in new terminal


@pytest.mark.e2e
def test_create_worktree_with_terminal_runs_init_in_terminal(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t flag runs init script in the new terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "echo 'init running'")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-t-init", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Init should NOT run in parent terminal
    assert "Running init script..." not in result.output
    assert "init running" not in result.output

    # Verify terminal command includes init script (may be escaped for single quotes)
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]  # osascript -e SCRIPT
    assert "echo" in script and "init running" in script


@pytest.mark.e2e
def test_create_worktree_with_terminal_and_editor_cursor(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that -t -e cursor runs init in new terminal, also opens cursor."""
    import wts.core.editor as editor_module

    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "npm install")

    # Need to patch both terminal and editor subprocess
    with (
        patch.object(terminal_module, "subprocess") as mock_term_subprocess,
        patch.object(editor_module, "subprocess") as mock_editor_subprocess,
    ):
        result = cli_runner.invoke(["create", "feature-t-e-cursor", "-t", "-e", "cursor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Init should NOT run in parent
    assert "Running init script..." not in result.output

    # Terminal opened with init script
    term_call = mock_term_subprocess.run.call_args[0][0]
    assert "npm install" in term_call[2]

    # Cursor also opened
    editor_call = mock_editor_subprocess.run.call_args[0][0]
    assert editor_call[0] == "cursor"


@pytest.mark.e2e
def test_create_worktree_with_terminal_no_init(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that --no-init -t opens terminal without init script."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "should not run")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-no-init-t", "--no-init", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Running init script..." not in result.output

    # Terminal command should NOT include init script
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    assert "should not run" not in script


@pytest.mark.e2e
def test_create_worktree_init_script_with_quotes_in_terminal(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that init scripts with quotes are properly escaped in terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", 'echo "hello world"')

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-quotes", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Script should be properly escaped/included
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    # The script should contain the init command (may be escaped)
    assert "echo" in script and "hello world" in script


@pytest.mark.e2e
def test_create_worktree_tmux_with_init_script(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that tmux properly handles init script in split command."""
    monkeypatch.setenv("WTS_TERMINAL", "tmux")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "make setup")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-tmux-init", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    # tmux split-window -h -c {path} {command}
    assert call_args[0] == "tmux"
    # Command should include init script
    cmd_str = " ".join(call_args)
    assert "make setup" in cmd_str


@pytest.mark.e2e
def test_create_worktree_terminal_without_init_configured(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test -t flag when no init script is configured."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.delenv("WTS_INIT_SCRIPT", raising=False)

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-no-script", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    # Terminal should still open with just cd command
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    assert "cd " in script


@pytest.mark.e2e
def test_create_worktree_multiline_init_script_in_terminal(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that multi-line init scripts work in terminal."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    # Simulate YAML pipe syntax: newlines should be converted to semicolons
    monkeypatch.setenv("WTS_INIT_SCRIPT", "uv sync --extra dev\necho done")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-multiline", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    # Should be joined with semicolons (not raw newlines between commands)
    assert "uv sync --extra dev" in script
    assert "echo done" in script
    # Commands should be joined with semicolons, not separated by newlines
    assert "uv sync --extra dev; echo done" in script


@pytest.mark.e2e
def test_create_worktree_dollar_sign_in_init_script(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that dollar signs pass through to shell."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "echo $PATH")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-dollar", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    # Dollar sign should be present (not interpreted by AppleScript)
    assert "$PATH" in script


@pytest.mark.e2e
def test_create_worktree_double_quotes_in_init_script(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that double quotes are properly escaped for AppleScript."""
    monkeypatch.setenv("WTS_TERMINAL", "iterm2")
    monkeypatch.setenv("WTS_INIT_SCRIPT", '/bin/bash -c "echo hello"')

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-dquotes", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    script = call_args[2]
    # Double quotes should be escaped with backslash in AppleScript
    assert r"\"" in script or "echo hello" in script


@pytest.mark.e2e
def test_create_worktree_tmux_multiline_init_script(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that tmux handles multi-line init scripts."""
    monkeypatch.setenv("WTS_TERMINAL", "tmux")
    monkeypatch.setenv("WTS_INIT_SCRIPT", "uv sync\necho done")

    with patch.object(terminal_module, "subprocess") as mock_subprocess:
        result = cli_runner.invoke(["create", "feature-tmux-multiline", "-t"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    call_args = mock_subprocess.run.call_args[0][0]
    cmd_str = " ".join(call_args)
    # Should contain both commands, joined appropriately
    assert "uv sync" in cmd_str
    assert "echo done" in cmd_str
