"""Tests for the wts delete command."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e
def test_delete_worktree_basic(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test deleting an existing worktree."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "feature-to-delete"])
    worktree_path = worktree_base_path / repo_name / "feature-to-delete"
    assert worktree_path.exists(), "Setup failed: worktree not created"

    result = cli_runner.invoke(["delete", "feature-to-delete"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Deleted worktree" in result.output
    assert not worktree_path.exists(), f"Worktree path still exists: {worktree_path}"

    git_result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert str(worktree_path) not in git_result.stdout, f"Worktree still in git worktree list: {git_result.stdout}"


@pytest.mark.e2e
def test_delete_worktree_not_found(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that deleting a non-existent worktree fails."""
    result = cli_runner.invoke(["delete", "nonexistent-worktree"])

    assert result.exit_code != 0, "Expected non-zero exit code for non-existent worktree"
    assert "not found" in result.output.lower(), f"Expected 'not found' in output: {result.output}"


@pytest.mark.e2e
def test_delete_worktree_removes_branch(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that deleting a worktree also removes its branch."""
    cli_runner.invoke(["create", "branch-to-delete"])

    git_branch = subprocess.run(
        ["git", "branch", "--list", "branch-to-delete"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "branch-to-delete" in git_branch.stdout, "Setup failed: branch not created"

    result = cli_runner.invoke(["delete", "branch-to-delete"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    git_branch = subprocess.run(
        ["git", "branch", "--list", "branch-to-delete"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "branch-to-delete" not in git_branch.stdout, f"Branch still exists: {git_branch.stdout}"


@pytest.mark.e2e
def test_delete_worktree_keep_branch(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that --keep-branch flag preserves the branch."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "keep-my-branch"])
    worktree_path = worktree_base_path / repo_name / "keep-my-branch"

    result = cli_runner.invoke(["delete", "keep-my-branch", "--keep-branch"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert not worktree_path.exists(), f"Worktree path still exists: {worktree_path}"

    git_branch = subprocess.run(
        ["git", "branch", "--list", "keep-my-branch"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "keep-my-branch" in git_branch.stdout, f"Branch was deleted but should be kept: {git_branch.stdout}"


@pytest.mark.e2e
def test_delete_worktree_invalid_name(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that invalid worktree names are rejected."""
    result = cli_runner.invoke(["delete", "foo/bar"])

    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"
