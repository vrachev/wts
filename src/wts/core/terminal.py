"""Terminal opener for macOS."""

import os
import subprocess
from pathlib import Path

from wts.config import get_config


def _get_user_shell() -> str:
    """Get the user's default shell."""
    return os.environ.get("SHELL", "/bin/bash")


def detect_terminal() -> str:
    """Detect the current terminal application.

    Returns:
        Terminal identifier: 'iterm2', 'terminal', 'tmux', 'warp', or 'none'
    """
    if override := get_config().terminal:
        return override

    term_program = os.environ.get("TERM_PROGRAM", "")

    if term_program == "iTerm.app":
        return "iterm2"
    if os.environ.get("TMUX"):
        return "tmux"
    if term_program == "WarpTerminal":
        return "warp"
    if term_program == "Apple_Terminal":
        return "terminal"

    return "terminal"


def _get_terminal_mode() -> str:
    """Get terminal mode: 'split' (default), 'tab', or 'cd'."""
    return get_config().terminal_mode


def _get_split_direction() -> str:
    """Get split direction: 'vertical' (default) or 'horizontal'."""
    return get_config().terminal_split


def _build_command_chain(path: Path, init_script: str | None, command: str | None) -> str:
    """Build the command chain for terminal execution.

    Args:
        path: Directory path to cd into
        init_script: Optional init script to run after cd
        command: Optional command to run after init script (e.g., "claude")

    Returns:
        Command string like "cd /path && init_script && command"
    """
    parts = [f"cd {path}"]
    if init_script:
        # Normalize multi-line scripts to single line
        normalized = _normalize_multiline_script(init_script)
        parts.append(normalized)
    if command:
        parts.append(command)
    return " && ".join(parts)


def open_terminal(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    """Open a new terminal split/tab/window at the given path.

    Args:
        path: Directory path to open terminal in
        command: Optional command to run after cd and init (e.g., "claude" for Claude Code)
        init_script: Optional init script to run before command

    Behavior controlled by environment variables:
        WTS_TERMINAL_MODE: 'split' (default), 'tab', or 'cd'
        WTS_TERMINAL_SPLIT: 'vertical' (default) or 'horizontal'

    Modes:
        split: Open a new split pane (default)
        tab: Open a new tab/window
        cd: Just cd in the current terminal, no new split/tab

    Note: Terminal.app and Warp don't support splits, so they open new windows instead.
    """
    terminal = detect_terminal()

    if terminal == "none":
        return

    if terminal == "iterm2":
        _open_iterm2(path, command, init_script)
    elif terminal == "tmux":
        _open_tmux(path, command, init_script)
    elif terminal == "warp":
        _open_warp(path, command, init_script)
    else:
        _open_terminal_app(path, command, init_script)


def _escape_for_single_quotes(s: str) -> str:
    """Escape a string for use inside single quotes in bash."""
    # Replace ' with '\'' (end quote, escaped quote, start quote)
    return s.replace("'", "'\\''")


def _normalize_multiline_script(script: str) -> str:
    """Convert a multi-line script to a single-line command chain.

    Args:
        script: Script that may contain newlines

    Returns:
        Single-line script with commands joined by semicolons
    """
    if not script:
        return script
    # Split by newlines, strip whitespace, filter empty lines
    lines = [line.strip() for line in script.split("\n")]
    lines = [line for line in lines if line]
    # Join with semicolons
    return "; ".join(lines)


def _escape_for_applescript(s: str) -> str:
    """Escape a string for use inside AppleScript double-quoted strings.

    AppleScript double-quoted strings only require escaping:
    - Backslash (\\) -> \\\\
    - Double quote (") -> \\"

    Note: Dollar signs ($) pass through unchanged to the shell.

    Args:
        s: String to escape

    Returns:
        Escaped string safe for AppleScript double-quoted context
    """
    # Order matters: escape backslashes first, then quotes
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


def _open_iterm2(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    mode = _get_terminal_mode()
    cmd_text = _build_command_chain(path, init_script, command)

    if mode == "cd":
        # Just cd in current session, no new split/tab - shell is already ready
        escaped_cmd_text = _escape_for_applescript(cmd_text)
        script = f"""
        tell application "iTerm2"
            tell current session of current window
                write text "{escaped_cmd_text}"
            end tell
        end tell
        """
    elif mode == "tab":
        # Use command parameter to run reliably at session start
        # Wrap in user's login shell to load their config, exec $SHELL keeps shell alive after
        user_shell = _get_user_shell()
        escaped_cmd = _escape_for_single_quotes(cmd_text)
        shell_cmd = f"{user_shell} -l -i -c '{escaped_cmd}; exec $SHELL'"
        escaped_shell_cmd = _escape_for_applescript(shell_cmd)
        script = f"""
        tell application "iTerm2"
            tell current window
                create tab with default profile command "{escaped_shell_cmd}"
            end tell
        end tell
        """
    else:
        direction = _get_split_direction()
        split_cmd = "split vertically" if direction == "vertical" else "split horizontally"
        # Use command parameter to run reliably at session start
        user_shell = _get_user_shell()
        escaped_cmd = _escape_for_single_quotes(cmd_text)
        shell_cmd = f"{user_shell} -l -i -c '{escaped_cmd}; exec $SHELL'"
        escaped_shell_cmd = _escape_for_applescript(shell_cmd)
        script = f"""
        tell application "iTerm2"
            tell current session of current window
                {split_cmd} with default profile command "{escaped_shell_cmd}"
            end tell
        end tell
        """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_terminal_app(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    mode = _get_terminal_mode()
    cmd_text = _build_command_chain(path, init_script, command)
    escaped_cmd_text = _escape_for_applescript(cmd_text)

    if mode == "cd":
        # Just cd in current window
        script = f"""
        tell application "Terminal"
            do script "{escaped_cmd_text}" in front window
        end tell
        """
    else:
        # Terminal.app doesn't support splits, always opens new window for split/tab
        script = f"""
        tell application "Terminal"
            activate
            do script "{escaped_cmd_text}"
        end tell
        """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_tmux(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    mode = _get_terminal_mode()
    # Build the full command chain for tmux
    full_command = _build_command_chain(path, init_script, command)

    if mode == "cd":
        # Just cd in current pane, no new split/window
        subprocess.run(["tmux", "send-keys", full_command, "Enter"], check=True, capture_output=True)
    elif mode == "tab":
        # tmux new-window runs command directly, so we need to wrap it
        user_shell = _get_user_shell()
        escaped_cmd = _escape_for_single_quotes(full_command)
        shell_cmd = f"{user_shell} -l -i -c '{escaped_cmd}; exec $SHELL'"
        subprocess.run(
            ["tmux", "new-window", "-c", str(path), shell_cmd],
            check=True,
            capture_output=True,
        )
    else:
        direction = _get_split_direction()
        # tmux: -h splits horizontally (panes side by side), -v splits vertically (panes stacked)
        # This is opposite of iTerm2's naming, so we flip it to match user expectations
        split_flag = "-h" if direction == "vertical" else "-v"
        user_shell = _get_user_shell()
        escaped_cmd = _escape_for_single_quotes(full_command)
        shell_cmd = f"{user_shell} -l -i -c '{escaped_cmd}; exec $SHELL'"
        subprocess.run(
            ["tmux", "split-window", split_flag, "-c", str(path), shell_cmd],
            check=True,
            capture_output=True,
        )


def _open_warp(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    # Warp doesn't have a CLI API for splits, always opens new window
    subprocess.run(["open", "-a", "Warp", str(path)], check=True, capture_output=True)
    # If init_script or command is specified, use AppleScript to send it to Warp
    # Build the command chain (without cd since Warp opens in the path already)
    cmd_parts = []
    if init_script:
        # Normalize multi-line scripts
        normalized = _normalize_multiline_script(init_script)
        cmd_parts.append(normalized)
    if command:
        cmd_parts.append(command)

    if cmd_parts:
        import time

        time.sleep(0.5)  # Give Warp time to open
        full_cmd = " && ".join(cmd_parts)
        escaped_full_cmd = _escape_for_applescript(full_cmd)
        script = f"""
        tell application "Warp"
            activate
            tell application "System Events"
                keystroke "{escaped_full_cmd}"
                key code 36
            end tell
        end tell
        """
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
