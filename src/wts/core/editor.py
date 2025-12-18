"""Editor opener for macOS."""

import os
import subprocess
from pathlib import Path
from typing import Callable

from wts.exceptions import EditorNotConfiguredError, UnsupportedEditorError


def _open_cursor(path: Path) -> None:
    subprocess.run(["cursor", str(path)], check=True, capture_output=True)


def _open_code(path: Path) -> None:
    subprocess.run(["code", str(path)], check=True, capture_output=True)


def _open_zed(path: Path) -> None:
    subprocess.run(["zed", str(path)], check=True, capture_output=True)


def _open_subl(path: Path) -> None:
    subprocess.run(["subl", str(path)], check=True, capture_output=True)


EDITOR_OPENERS: dict[str, Callable[[Path], None]] = {
    "cursor": _open_cursor,
    "code": _open_code,
    "zed": _open_zed,
    "subl": _open_subl,
}


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
    if editor := os.environ.get("WTS_EDITOR"):
        return editor
    raise EditorNotConfiguredError("Set WTS_EDITOR or use --editor=<name>")


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
