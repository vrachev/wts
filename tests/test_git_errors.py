"""Tests for git error surfacing."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e
def test_delete_worktree_with_uncommitted_changes_shows_git_error(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that deleting worktree with uncommitted changes shows git's error."""
    repo_name = tmp_git_repo.name
    cli_runner.invoke(["create", "dirty-worktree"])
    worktree_path = worktree_base_path / repo_name / "dirty-worktree"

    # Add uncommitted changes to the worktree
    (worktree_path / "dirty.txt").write_text("uncommitted changes")
    subprocess.run(["git", "add", "dirty.txt"], cwd=worktree_path, check=True)

    # Don't use -f flag (which force-deletes), answer 'y' to confirmation prompt
    result = cli_runner.invoke(["delete", "dirty-worktree"], input="y\n")

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    # Should show git's actual error message about uncommitted changes
    output_lower = result.output.lower()
    assert (
        "error" in output_lower or "changes" in output_lower or "modified" in output_lower
    ), f"Expected git error message about changes. Output: {result.output}"


@pytest.mark.e2e
def test_create_worktree_with_nonexistent_base_shows_git_error(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that creating worktree from non-existent base ref shows git's error."""
    # Delete the main branch reference to force an error when creating from main
    # Instead, we'll test by trying to create when there's no 'main' branch
    # First, rename main to something else
    subprocess.run(
        ["git", "branch", "-m", "main", "master"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["create", "test-feature"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    # Should show git's error about main not existing
    output_lower = result.output.lower()
    assert (
        "error" in output_lower or "main" in output_lower or "not" in output_lower
    ), f"Expected git error message. Output: {result.output}"


@pytest.mark.e2e
def test_create_worktree_branch_already_exists_shows_error(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that creating worktree when branch already exists shows error."""
    # Create a branch without a worktree
    subprocess.run(
        ["git", "branch", "existing-branch"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["create", "existing-branch"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    # Should show error about branch already existing
    assert "already exists" in result.output.lower(), f"Expected 'already exists' error. Output: {result.output}"


@pytest.mark.e2e
def test_complete_with_merge_conflict_shows_git_error(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that merge conflict shows git's error message."""
    repo_name = tmp_git_repo.name

    # Create a worktree
    cli_runner.invoke(["create", "conflict-branch"])
    worktree_path = worktree_base_path / repo_name / "conflict-branch"

    # Modify a file in the worktree
    (worktree_path / "README.md").write_text("# Changes from worktree\n")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "worktree changes"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    # Modify the same file in main
    (tmp_git_repo / "README.md").write_text("# Changes from main\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "main changes"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "conflict-branch", "-m", "test merge"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    # Should show error about merge conflict
    output_lower = result.output.lower()
    assert (
        "conflict" in output_lower or "error" in output_lower or "failed" in output_lower
    ), f"Expected merge conflict error. Output: {result.output}"


@pytest.mark.e2e
def test_operations_outside_git_repo_shows_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that running wts outside a git repo shows git's error message."""
    from click.testing import CliRunner
    from wts.cli import cli

    # Create a non-git directory
    non_git_dir = tmp_path / "not-a-repo"
    non_git_dir.mkdir()
    monkeypatch.chdir(non_git_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ["list"])

    assert result.exit_code != 0, f"Expected non-zero exit code. Output: {result.output}"
    # Should show error about not being in a git repository
    output_lower = result.output.lower()
    assert (
        "git" in output_lower or "repository" in output_lower or "error" in output_lower
    ), f"Expected git error message. Output: {result.output}"


@pytest.mark.e2e
def test_complete_autoresolve_updates_local_main_before_retry(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
    tmp_path: Path,
) -> None:
    """Test that autoresolve updates local main to origin/main before retry merge.

    This tests the scenario where:
    1. A worktree branch modifies README.md
    2. Local main also modifies README.md (creates conflict with initial merge)
    3. origin/main is then reset to match worktree's expected state
    4. Using -a flag should:
       - Fail the initial merge (conflict with local main's README)
       - Rebase worktree onto origin/main (succeeds)
       - Update local main to origin/main before retry merge
       - Successfully merge
    """
    repo_name = tmp_git_repo.name

    # Create a bare repo to act as origin
    origin_repo = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "--bare", str(tmp_git_repo), str(origin_repo)], check=True, capture_output=True)

    # Add origin remote to test repo
    subprocess.run(
        ["git", "remote", "add", "origin", str(origin_repo)], cwd=tmp_git_repo, check=True, capture_output=True
    )

    # Create a worktree that modifies README.md
    cli_runner.invoke(["create", "feature-readme"])
    worktree_path = worktree_base_path / repo_name / "feature-readme"

    # Modify README.md in the worktree
    (worktree_path / "README.md").write_text("# Feature Branch Changes\n")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "modify readme in feature branch"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    # Modify README.md DIFFERENTLY in local main (this creates the conflict)
    (tmp_git_repo / "README.md").write_text("# Local Main Changes\n")
    subprocess.run(["git", "add", "."], cwd=tmp_git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "modify readme in local main"],
        cwd=tmp_git_repo,
        check=True,
        capture_output=True,
    )

    # Push local main to origin (so origin/main now has "Local Main Changes")
    subprocess.run(["git", "push", "origin", "main"], cwd=tmp_git_repo, check=True, capture_output=True)

    # Now from a clone, reset origin/main back to original state and add other.txt
    # This simulates origin/main being in a state that the worktree can cleanly rebase onto
    clone_path = tmp_path / "clone"
    subprocess.run(["git", "clone", str(origin_repo), str(clone_path)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=clone_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=clone_path, check=True, capture_output=True)

    # Reset README to original and add another file
    (clone_path / "README.md").write_text("# Test Repository\n")  # Back to original
    (clone_path / "other.txt").write_text("other content from origin\n")
    subprocess.run(["git", "add", "."], cwd=clone_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "reset readme and add other file"],
        cwd=clone_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "push", "-f", "origin", "main"], cwd=clone_path, check=True, capture_output=True)

    # State:
    # - local main: "# Local Main Changes" (diverged from origin)
    # - origin/main: "# Test Repository" + other.txt (reset + new file)
    # - worktree: "# Feature Branch Changes" (based on original "# Test Repository")
    #
    # Initial merge fails: worktree's README ("Feature") conflicts with local main's ("Local")
    # Rebase succeeds: worktree's README change applies cleanly on origin's "# Test Repository"
    # Without fix: retry merge fails because local main ("Local") != origin/main ("Test Repository")
    # With fix: local main is updated to origin/main, then merge succeeds

    # Use -a (autoresolve) and -l (use latest message)
    result = cli_runner.invoke(["complete", "feature-readme", "-l", "-a"])

    # This should succeed after the fix
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Squash merged worktree" in result.output

    # Verify changes are on main
    readme_content = (tmp_git_repo / "README.md").read_text()
    assert "Feature Branch" in readme_content, f"Expected feature branch README. Content: {readme_content}"
    # After updating local main from origin, other.txt should also be present
    assert (tmp_git_repo / "other.txt").exists(), "other.txt should exist on main after pulling from origin"
