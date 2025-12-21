"""Tests for the wts complete command."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clean_wts_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure clean WTS environment for each test."""
    monkeypatch.delenv("WTS_TERMINAL", raising=False)
    monkeypatch.delenv("WTS_EDITOR", raising=False)


def _make_commit_in_worktree(worktree_path: Path, filename: str, content: str) -> None:
    """Helper to create a file and commit it in a worktree."""
    (worktree_path / filename).write_text(content)
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Add {filename}"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )


@pytest.mark.e2e
def test_complete_worktree_not_found(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that completing a non-existent worktree fails."""
    result = cli_runner.invoke(["complete", "nonexistent", "Some message"])

    assert result.exit_code != 0, "Expected non-zero exit code for non-existent worktree"
    assert "not found" in result.output.lower(), f"Expected 'not found' in output: {result.output}"


@pytest.mark.e2e
def test_complete_invalid_worktree_name(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that invalid worktree names are rejected."""
    result = cli_runner.invoke(["complete", "foo/bar", "Some message"])

    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"


@pytest.mark.e2e
def test_complete_worktree_with_uncommitted_changes(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that completing a worktree with uncommitted changes fails."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-dirty"

    cli_runner.invoke(["create", "feature-dirty"])
    # Create uncommitted changes
    (worktree_path / "uncommitted.txt").write_text("uncommitted content")

    result = cli_runner.invoke(["complete", "feature-dirty", "Try to complete"])

    assert result.exit_code != 0, "Expected non-zero exit code for dirty worktree"
    assert "uncommitted" in result.output.lower(), f"Expected 'uncommitted' in output: {result.output}"


@pytest.mark.e2e
def test_complete_basic_squash_merge(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test basic squash merge with cleanup."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-squash"

    # Create worktree and make commits
    cli_runner.invoke(["create", "feature-squash"])
    _make_commit_in_worktree(worktree_path, "feature.txt", "feature content")
    _make_commit_in_worktree(worktree_path, "feature2.txt", "feature2 content")

    # Complete (squash merge)
    result = cli_runner.invoke(["complete", "feature-squash", "Add feature"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Merged worktree" in result.output
    assert "cleaned up" in result.output

    # Verify worktree is deleted
    assert not worktree_path.exists(), f"Worktree still exists: {worktree_path}"

    # Verify branch is deleted
    git_branch = subprocess.run(
        ["git", "branch", "--list", "feature-squash"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "feature-squash" not in git_branch.stdout, f"Branch still exists: {git_branch.stdout}"

    # Verify changes are on main
    git_log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Add feature" in git_log.stdout, f"Commit message not found: {git_log.stdout}"

    # Verify files exist on main
    assert (tmp_git_repo / "feature.txt").exists()
    assert (tmp_git_repo / "feature2.txt").exists()


@pytest.mark.e2e
def test_complete_with_no_cleanup(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test squash merge with --no-cleanup flag."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-keep"

    cli_runner.invoke(["create", "feature-keep"])
    _make_commit_in_worktree(worktree_path, "keep.txt", "keep content")

    result = cli_runner.invoke(["complete", "feature-keep", "Add keep feature", "--no-cleanup"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Merged worktree" in result.output
    assert "cleaned up" not in result.output

    # Verify worktree still exists
    assert worktree_path.exists(), f"Worktree was deleted: {worktree_path}"

    # Verify branch still exists
    git_branch = subprocess.run(
        ["git", "branch", "--list", "feature-keep"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "feature-keep" in git_branch.stdout, f"Branch was deleted: {git_branch.stdout}"


@pytest.mark.e2e
def test_complete_into_different_branch(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test squash merge into a non-main branch."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-develop"

    # Create develop branch
    subprocess.run(
        ["git", "checkout", "-b", "develop"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )

    cli_runner.invoke(["create", "feature-develop"])
    _make_commit_in_worktree(worktree_path, "develop.txt", "develop content")

    result = cli_runner.invoke(["complete", "feature-develop", "Add develop feature", "--into", "develop"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "into 'develop'" in result.output

    # Verify changes are on develop, not main
    subprocess.run(["git", "checkout", "develop"], cwd=tmp_git_repo, check=True, capture_output=True)
    assert (tmp_git_repo / "develop.txt").exists()

    subprocess.run(["git", "checkout", "main"], cwd=tmp_git_repo, check=True, capture_output=True)
    assert not (tmp_git_repo / "develop.txt").exists()
