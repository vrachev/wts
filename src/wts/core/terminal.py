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


def open_terminal(path: Path) -> None:
    """Open a new terminal tab/window at the given path."""
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
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_terminal_app(path: Path) -> None:
    script = f"""
    tell application "Terminal"
        activate
        do script "cd {path}"
    end tell
    """
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)


def _open_tmux(path: Path) -> None:
    subprocess.run(["tmux", "new-window", "-c", str(path)], check=True, capture_output=True)


def _open_warp(path: Path) -> None:
    subprocess.run(["open", "-a", "Warp", str(path)], check=True, capture_output=True)
