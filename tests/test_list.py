"""Tests for the wts list command."""

from pathlib import Path

import pytest


@pytest.mark.e2e
def test_list_no_worktrees(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test listing when no worktrees exist."""
    result = cli_runner.invoke(["list"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"


@pytest.mark.e2e
def test_list_single_worktree(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test listing shows a created worktree."""
    cli_runner.invoke(["create", "feature-one"])

    result = cli_runner.invoke(["list"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "feature-one" in result.output, f"Expected 'feature-one' in output: {result.output}"


@pytest.mark.e2e
def test_list_multiple_worktrees(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test listing shows all created worktrees."""
    cli_runner.invoke(["create", "feature-one"])
    cli_runner.invoke(["create", "feature-two"])
    cli_runner.invoke(["create", "feature-three"])

    result = cli_runner.invoke(["list"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "feature-one" in result.output, f"Expected 'feature-one' in output: {result.output}"
    assert "feature-two" in result.output, f"Expected 'feature-two' in output: {result.output}"
    assert "feature-three" in result.output, f"Expected 'feature-three' in output: {result.output}"
