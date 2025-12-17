"""E2E tests for the wts create command."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e
def test_create_worktree_basic(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test creating a basic worktree with just a name."""
    # Given: A git repository
    repo_name = tmp_git_repo.name

    # When: Creating a worktree
    result = cli_runner.invoke(["create", "feature-test"])

    # Then: Command succeeds
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Created worktree" in result.output

    # And: Worktree directory exists at expected path
    worktree_path = worktree_base_path / repo_name / "feature-test"
    assert worktree_path.exists(), f"Worktree path does not exist: {worktree_path}"
    assert worktree_path.is_dir()

    # And: Git knows about the worktree
    git_result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert str(worktree_path) in git_result.stdout, f"Worktree not in git worktree list: {git_result.stdout}"

    # And: Branch was created
    git_branch = subprocess.run(
        ["git", "branch", "--list", "feature-test"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "feature-test" in git_branch.stdout, f"Branch not created: {git_branch.stdout}"


@pytest.mark.e2e
def test_create_worktree_from_current_branch(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test creating a worktree from current branch using --from-current flag."""
    # Given: A git repository where we're on a feature branch (not main)
    subprocess.run(
        ["git", "checkout", "-b", "feature-base"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )
    # Add a commit so feature-base differs from main
    (tmp_git_repo / "feature-base.txt").write_text("feature base content")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "feature base commit"], cwd=tmp_git_repo, check=True, capture_output=True)

    # Get the current branch commit
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # When: Creating a worktree with --from-current flag
    result = cli_runner.invoke(["create", "feature-child", "--from-current"])

    # Then: Command succeeds
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # And: Worktree is based on current branch commit (not main)
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-child"

    worktree_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert worktree_commit == current_commit, f"Worktree not based on current branch. Expected {current_commit}, got {worktree_commit}"


@pytest.mark.e2e
def test_create_worktree_already_exists(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that creating a worktree with an existing name fails."""
    # Given: A worktree already exists
    result1 = cli_runner.invoke(["create", "existing-worktree"])
    assert result1.exit_code == 0, f"Setup failed: {result1.output}"

    # When: Trying to create another worktree with the same name
    result2 = cli_runner.invoke(["create", "existing-worktree"])

    # Then: Command fails with appropriate error
    assert result2.exit_code != 0, "Expected non-zero exit code for duplicate worktree"
    assert "already exists" in result2.output.lower(), f"Expected 'already exists' in output: {result2.output}"


@pytest.mark.e2e
def test_create_worktree_invalid_name_with_slash(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that invalid worktree names are rejected."""
    # When: Trying to create a worktree with invalid name (contains slash)
    result = cli_runner.invoke(["create", "foo/bar"])

    # Then: Command fails with validation error
    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"


@pytest.mark.e2e
def test_create_worktree_invalid_name_with_space(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that worktree names with spaces are rejected."""
    # When: Trying to create a worktree with space in name
    result = cli_runner.invoke(["create", "foo bar"])

    # Then: Command fails with validation error
    assert result.exit_code != 0, "Expected non-zero exit code for invalid name"
    assert "invalid" in result.output.lower(), f"Expected 'invalid' in output: {result.output}"
