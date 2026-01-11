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

    result = cli_runner.invoke(["delete", "-f", "feature-to-delete"])

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
    result = cli_runner.invoke(["delete", "-f", "nonexistent-worktree"])

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

    result = cli_runner.invoke(["delete", "-f", "branch-to-delete"])

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

    result = cli_runner.invoke(["delete", "-f", "keep-my-branch", "--keep-branch"])

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
    result = cli_runner.invoke(["delete", "-f", "foo/bar"])

    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"


@pytest.mark.e2e
def test_delete_multiple_worktrees(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test deleting multiple worktrees in one command."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "wt-one"])
    cli_runner.invoke(["create", "wt-two"])
    cli_runner.invoke(["create", "wt-three"])
    wt_one_path = worktree_base_path / repo_name / "wt-one"
    wt_two_path = worktree_base_path / repo_name / "wt-two"
    wt_three_path = worktree_base_path / repo_name / "wt-three"
    assert wt_one_path.exists() and wt_two_path.exists() and wt_three_path.exists()

    result = cli_runner.invoke(["delete", "-f", "wt-one", "wt-two", "wt-three"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Deleted worktree 'wt-one'" in result.output
    assert "Deleted worktree 'wt-two'" in result.output
    assert "Deleted worktree 'wt-three'" in result.output
    assert not wt_one_path.exists()
    assert not wt_two_path.exists()
    assert not wt_three_path.exists()


@pytest.mark.e2e
def test_delete_confirmation_abort(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that confirmation prompt aborts when user says no."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "abort-test"])
    worktree_path = worktree_base_path / repo_name / "abort-test"
    assert worktree_path.exists()

    result = cli_runner.invoke(["delete", "abort-test"], input="n\n")

    assert result.exit_code != 0, "Expected non-zero exit code when aborting"
    assert worktree_path.exists(), "Worktree should still exist after abort"


@pytest.mark.e2e
def test_delete_confirmation_confirm(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that confirmation prompt proceeds when user says yes."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "confirm-test"])
    worktree_path = worktree_base_path / repo_name / "confirm-test"
    assert worktree_path.exists()

    result = cli_runner.invoke(["delete", "confirm-test"], input="y\n")

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert not worktree_path.exists(), "Worktree should be deleted after confirmation"


@pytest.mark.e2e
def test_delete_best_effort_with_nonexistent(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that valid worktrees are deleted even if some don't exist."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "exists-one"])
    cli_runner.invoke(["create", "exists-two"])
    exists_one_path = worktree_base_path / repo_name / "exists-one"
    exists_two_path = worktree_base_path / repo_name / "exists-two"
    assert exists_one_path.exists() and exists_two_path.exists()

    result = cli_runner.invoke(["delete", "-f", "exists-one", "nonexistent", "exists-two"])

    assert result.exit_code != 0, "Expected non-zero exit code due to error"
    assert "Deleted worktree 'exists-one'" in result.output
    assert "Deleted worktree 'exists-two'" in result.output
    assert "not found" in result.output.lower()
    assert not exists_one_path.exists()
    assert not exists_two_path.exists()


@pytest.mark.e2e
def test_delete_force_with_untracked_files(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that --force deletes worktrees with untracked files."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "dirty-worktree"])
    worktree_path = worktree_base_path / repo_name / "dirty-worktree"
    assert worktree_path.exists()

    # Create an untracked file in the worktree
    (worktree_path / "untracked.txt").write_text("untracked content")

    # Without --force, git worktree remove would fail, but -f skips confirmation
    # and passes --force to git, so it should succeed
    result = cli_runner.invoke(["delete", "-f", "dirty-worktree"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Deleted worktree" in result.output
    assert not worktree_path.exists()
