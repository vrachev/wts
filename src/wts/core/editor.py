"""Editor opener for macOS."""

import subprocess
from pathlib import Path
from typing import Callable

from wts.config import get_config
from wts.exceptions import EditorNotConfiguredError, UnsupportedEditorError


def _open_cursor(path: Path) -> None:
    subprocess.run(["cursor", str(path)], check=True, capture_output=True)


def _open_code(path: Path) -> None:
    subprocess.run(["code", str(path)], check=True, capture_output=True)


def _open_zed(path: Path) -> None:
    subprocess.run(["zed", str(path)], check=True, capture_output=True)


def _open_subl(path: Path) -> None:
    subprocess.run(["subl", str(path)], check=True, capture_output=True)


def _open_claude_code(path: Path) -> None:
    from wts.core.terminal import open_terminal

    open_terminal(path, command="claude")


EDITOR_OPENERS: dict[str, Callable[[Path], None]] = {
    "cursor": _open_cursor,
    "code": _open_code,
    "zed": _open_zed,
    "subl": _open_subl,
    "claude": _open_claude_code,
}

TERMINAL_EDITORS = {"claude"}


def is_terminal_editor(editor: str) -> bool:
    """Return True if editor runs in a terminal (like claude)."""
    return editor in TERMINAL_EDITORS


def get_editor(override: str | None = None) -> str:
    """Get the editor to use.

    Args:
        override: Explicit editor name (from --editor=X flag)

    Returns:
        Editor name like 'cursor', 'code', 'zed'

    Raises:
        EditorNotConfiguredError: If no editor configured
    """
    if override:
        return override
    if editor := get_config().editor:
        return editor
    raise EditorNotConfiguredError("Set editor via 'wts config set editor <name>' or use --editor=<name>")


def open_editor(path: Path, override: str | None = None) -> None:
    """Open the given path in an editor.

    Args:
        path: Directory path to open
        override: Explicit editor name (overrides WTS_EDITOR env var)

    Raises:
        EditorNotConfiguredError: If no editor configured
        UnsupportedEditorError: If editor is not supported
    """
    editor = get_editor(override)

    opener = EDITOR_OPENERS.get(editor)
    if not opener:
        supported = ", ".join(EDITOR_OPENERS.keys())
        raise UnsupportedEditorError(f"Unknown editor: {editor}. Supported: {supported}")
    opener(path)
