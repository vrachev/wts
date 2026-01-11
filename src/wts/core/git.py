"""Git command utilities with proper error surfacing."""

import subprocess
from pathlib import Path
from typing import Any


def run_git_command(
    args: list[str],
    cwd: Path,
    check: bool = True,
    capture_output: bool = True,
    text: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess[Any]:
    """Run a git command and surface errors with full context.

    Args:
        args: Command arguments (e.g., ["git", "status"]).
        cwd: Working directory for the command.
        check: If True, raise CalledProcessError on non-zero exit.
        capture_output: If True, capture stdout and stderr.
        text: If True, decode output as text.
        **kwargs: Additional arguments passed to subprocess.run.

    Returns:
        CompletedProcess instance.

    Raises:
        subprocess.CalledProcessError: If check=True and command fails.
            The stderr attribute contains a formatted error message.
    """
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        **kwargs,
    )

    if check and result.returncode != 0:
        # Extract stderr for the error message
        if text:
            stderr = (result.stderr or "").strip()
        else:
            stderr = result.stderr.decode().strip() if result.stderr else ""

        cmd_str = " ".join(args)
        if stderr:
            error_msg = f"Git command '{cmd_str}' failed: {stderr}"
        else:
            error_msg = f"Git command '{cmd_str}' failed with exit code {result.returncode}"

        raise subprocess.CalledProcessError(
            result.returncode,
            args,
            output=result.stdout,
            stderr=error_msg,
        )

    return result
