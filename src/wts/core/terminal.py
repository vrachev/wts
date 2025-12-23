"""Terminal opener for macOS."""

import os
import subprocess
from pathlib import Path

from wts.config import get_config


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
        parts.append(init_script)
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


def _open_iterm2(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    mode = _get_terminal_mode()
    cmd_text = _build_command_chain(path, init_script, command)

    if mode == "cd":
        # Just cd in current session, no new split/tab
        script = f"""
        tell application "iTerm2"
            tell current session of current window
                write text "{cmd_text}"
            end tell
        end tell
        """
    elif mode == "tab":
        script = f"""
        tell application "iTerm2"
            tell current window
                create tab with default profile
                tell current session
                    write text "{cmd_text}"
                end tell
            end tell
        end tell
        """
    else:
        direction = _get_split_direction()
        split_cmd = "split vertically" if direction == "vertical" else "split horizontally"
        # Capture reference to new session and write to it directly
        script = f"""
        tell application "iTerm2"
            tell current session of current window
                set newSession to ({split_cmd} with default profile)
            end tell
            tell newSession
                select
                write text "{cmd_text}"
            end tell
        end tell
        """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_terminal_app(path: Path, command: str | None = None, init_script: str | None = None) -> None:
    mode = _get_terminal_mode()
    cmd_text = _build_command_chain(path, init_script, command)

    if mode == "cd":
        # Just cd in current window
        script = f"""
        tell application "Terminal"
            do script "{cmd_text}" in front window
        end tell
        """
    else:
        # Terminal.app doesn't support splits, always opens new window for split/tab
        script = f"""
        tell application "Terminal"
            activate
            do script "{cmd_text}"
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
        subprocess.run(
            ["tmux", "new-window", "-c", str(path), f"bash -c '{full_command}; exec bash'"],
            check=True,
            capture_output=True,
        )
    else:
        direction = _get_split_direction()
        # tmux: -h splits horizontally (panes side by side), -v splits vertically (panes stacked)
        # This is opposite of iTerm2's naming, so we flip it to match user expectations
        split_flag = "-h" if direction == "vertical" else "-v"
        subprocess.run(
            ["tmux", "split-window", split_flag, "-c", str(path), f"bash -c '{full_command}; exec bash'"],
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
        cmd_parts.append(init_script)
    if command:
        cmd_parts.append(command)

    if cmd_parts:
        import time

        time.sleep(0.5)  # Give Warp time to open
        full_cmd = " && ".join(cmd_parts)
        script = f"""
        tell application "Warp"
            activate
            tell application "System Events"
                keystroke "{full_cmd}"
                key code 36
            end tell
        end tell
        """
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
