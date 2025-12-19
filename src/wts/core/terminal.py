"""Terminal opener for macOS."""

import os
import subprocess
from pathlib import Path


def detect_terminal() -> str:
    """Detect the current terminal application.

    Returns:
        Terminal identifier: 'iterm2', 'terminal', 'tmux', 'warp', or 'none'
    """
    if override := os.environ.get("WTS_TERMINAL"):
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
    return os.environ.get("WTS_TERMINAL_MODE", "split")


def _get_split_direction() -> str:
    """Get split direction: 'vertical' (default) or 'horizontal'."""
    return os.environ.get("WTS_TERMINAL_SPLIT", "vertical")


def open_terminal(path: Path) -> None:
    """Open a new terminal split/tab/window at the given path.

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
        _open_iterm2(path)
    elif terminal == "tmux":
        _open_tmux(path)
    elif terminal == "warp":
        _open_warp(path)
    else:
        _open_terminal_app(path)


def _open_iterm2(path: Path) -> None:
    mode = _get_terminal_mode()

    if mode == "cd":
        # Just cd in current session, no new split/tab
        script = f"""
        tell application "iTerm2"
            tell current session of current window
                write text "cd {path}"
            end tell
        end tell
        """
    elif mode == "tab":
        script = f"""
        tell application "iTerm2"
            tell current window
                create tab with default profile
                tell current session
                    write text "cd {path}"
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
                write text "cd {path}"
            end tell
        end tell
        """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_terminal_app(path: Path) -> None:
    mode = _get_terminal_mode()

    if mode == "cd":
        # Just cd in current window
        script = f"""
        tell application "Terminal"
            do script "cd {path}" in front window
        end tell
        """
    else:
        # Terminal.app doesn't support splits, always opens new window for split/tab
        script = f"""
        tell application "Terminal"
            activate
            do script "cd {path}"
        end tell
        """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_tmux(path: Path) -> None:
    mode = _get_terminal_mode()

    if mode == "cd":
        # Just cd in current pane, no new split/window
        subprocess.run(["tmux", "send-keys", f"cd {path}", "Enter"], check=True, capture_output=True)
    elif mode == "tab":
        subprocess.run(["tmux", "new-window", "-c", str(path)], check=True, capture_output=True)
    else:
        direction = _get_split_direction()
        # tmux: -h splits horizontally (panes side by side), -v splits vertically (panes stacked)
        # This is opposite of iTerm2's naming, so we flip it to match user expectations
        split_flag = "-h" if direction == "vertical" else "-v"
        subprocess.run(["tmux", "split-window", split_flag, "-c", str(path)], check=True, capture_output=True)


def _open_warp(path: Path) -> None:
    # Warp doesn't have a CLI API for splits, always opens new window
    subprocess.run(["open", "-a", "Warp", str(path)], check=True, capture_output=True)
