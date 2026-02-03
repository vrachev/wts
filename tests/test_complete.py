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
    assert "Squash merged worktree" in result.output
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
    assert "Squash merged worktree" in result.output
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


@pytest.mark.e2e
def test_complete_use_latest_msg_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test squash merge using --use-latest-msg flag."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-latest"

    cli_runner.invoke(["create", "feature-latest"])
    # Make commits with specific messages
    (worktree_path / "file1.txt").write_text("content1")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "First commit"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )
    (worktree_path / "file2.txt").write_text("content2")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Latest commit message"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "feature-latest", "--use-latest-msg"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Squash merged worktree" in result.output

    # Verify the commit message is the latest one
    git_log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Latest commit message" in git_log.stdout, f"Expected 'Latest commit message' in: {git_log.stdout}"


@pytest.mark.e2e
def test_complete_use_latest_msg_shorthand(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test squash merge using -l shorthand."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-short"

    cli_runner.invoke(["create", "feature-short"])
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Shorthand test commit"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "feature-short", "-l"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    git_log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Shorthand test commit" in git_log.stdout


@pytest.mark.e2e
def test_complete_error_both_message_and_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test error when both message and --use-latest-msg are provided."""
    cli_runner.invoke(["create", "feature-both"])

    result = cli_runner.invoke(["complete", "feature-both", "Some message", "--use-latest-msg"])

    assert result.exit_code != 0, "Expected non-zero exit code"
    assert "Cannot specify both" in result.output


@pytest.mark.e2e
def test_complete_error_neither_message_nor_flag(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test error when neither message nor --use-latest-msg is provided."""
    result = cli_runner.invoke(["complete", "feature-none"])

    assert result.exit_code != 0, "Expected non-zero exit code"
    assert "Must specify either" in result.output


@pytest.mark.e2e
def test_complete_main_repo_not_clean(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that completing fails when main repo has uncommitted changes."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-main-dirty"

    cli_runner.invoke(["create", "feature-main-dirty"])
    _make_commit_in_worktree(worktree_path, "feature.txt", "feature content")

    # Create uncommitted changes in main repo
    (tmp_git_repo / "dirty.txt").write_text("uncommitted in main")

    result = cli_runner.invoke(["complete", "feature-main-dirty", "Try to complete"])

    assert result.exit_code != 0, "Expected non-zero exit code for dirty main repo"
    assert (
        "uncommitted" in result.output.lower() or "unmerged" in result.output.lower()
    ), f"Expected error about uncommitted/unmerged files: {result.output}"


@pytest.mark.e2e
def test_complete_auto_resolve_short_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -a short flag is recognized for --auto-resolve-claude."""
    # Just verify the flag is recognized (we don't actually test Claude resolution)
    result = cli_runner.invoke(["complete", "--help"])

    assert "-a, --auto-resolve-claude" in result.output, f"Expected '-a' alias in help output: {result.output}"


@pytest.mark.e2e
def test_complete_preserve_commits_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test regular merge with --preserve-commits flag preserves individual commits."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-preserve"

    cli_runner.invoke(["create", "feature-preserve"])
    _make_commit_in_worktree(worktree_path, "file1.txt", "content1")
    _make_commit_in_worktree(worktree_path, "file2.txt", "content2")

    result = cli_runner.invoke(["complete", "feature-preserve", "--preserve-commits"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
    assert "Merged worktree" in result.output
    assert "Squash" not in result.output
    assert "cleaned up" in result.output

    # Verify both commits are preserved (not squashed into one)
    git_log = subprocess.run(
        ["git", "log", "--oneline", "-3"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Add file1.txt" in git_log.stdout, f"Expected 'Add file1.txt' in: {git_log.stdout}"
    assert "Add file2.txt" in git_log.stdout, f"Expected 'Add file2.txt' in: {git_log.stdout}"


@pytest.mark.e2e
def test_complete_preserve_commits_short_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -p short flag is recognized for --preserve-commits."""
    result = cli_runner.invoke(["complete", "--help"])

    assert "-p, --preserve-commits" in result.output, f"Expected '-p' alias in help output: {result.output}"


@pytest.mark.e2e
def test_complete_preserve_commits_no_message_required(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that --preserve-commits does not require a message."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-no-msg"

    cli_runner.invoke(["create", "feature-no-msg"])
    _make_commit_in_worktree(worktree_path, "file.txt", "content")

    # Should succeed without message
    result = cli_runner.invoke(["complete", "feature-no-msg", "-p"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"


@pytest.mark.e2e
def test_complete_no_coauthor_short_flag(
    tmp_git_repo: Path,
    cli_runner,
) -> None:
    """Test that -n short flag is recognized for --no-coauthor."""
    result = cli_runner.invoke(["complete", "--help"])

    assert "-n, --no-coauthor" in result.output, f"Expected '-n' alias in help output: {result.output}"


@pytest.mark.e2e
def test_complete_no_coauthor_strips_trailer_with_use_latest_msg(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -n strips Co-Authored-By trailers when using -l."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-coauthor"

    cli_runner.invoke(["create", "feature-coauthor"])

    # Create a commit with a Co-Authored-By trailer
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    commit_msg = "Add feature\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "feature-coauthor", "-l", "-n"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Verify the commit message does NOT contain Co-Authored-By
    git_log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Co-Authored-By" not in git_log.stdout, f"Expected no Co-Authored-By in: {git_log.stdout}"
    assert "Add feature" in git_log.stdout, f"Expected 'Add feature' in: {git_log.stdout}"


@pytest.mark.e2e
def test_complete_preserves_coauthor_with_coauthor_flag(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that Co-Authored-By trailers are preserved with --coauthor flag."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-keep-coauthor"

    cli_runner.invoke(["create", "feature-keep-coauthor"])

    # Create a commit with a Co-Authored-By trailer
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    commit_msg = "Add feature\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    # Use --coauthor to explicitly preserve co-author (overrides default config)
    result = cli_runner.invoke(["complete", "feature-keep-coauthor", "-l", "--coauthor"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Verify the commit message DOES contain Co-Authored-By
    git_log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Co-Authored-By" in git_log.stdout, f"Expected Co-Authored-By in: {git_log.stdout}"


@pytest.mark.e2e
def test_complete_no_coauthor_strips_multiple_trailers(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -n strips multiple Co-Authored-By trailers."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-multi-coauthor"

    cli_runner.invoke(["create", "feature-multi-coauthor"])

    # Create a commit with multiple Co-Authored-By trailers
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    commit_msg = """Add feature

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
Co-Authored-By: Another Author <author@example.com>"""
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "feature-multi-coauthor", "-l", "-n"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Verify no Co-Authored-By lines remain
    git_log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Co-Authored-By" not in git_log.stdout, f"Expected no Co-Authored-By in: {git_log.stdout}"
    assert "Add feature" in git_log.stdout


@pytest.mark.e2e
def test_complete_no_coauthor_with_explicit_message(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -n flag is accepted with explicit message (no effect but no error)."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-explicit-msg"

    cli_runner.invoke(["create", "feature-explicit-msg"])
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Some commit"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    # -n with explicit message should work (flag has no effect on explicit message)
    result = cli_runner.invoke(["complete", "feature-explicit-msg", "Explicit message", "-n"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"


@pytest.mark.e2e
def test_complete_strips_coauthor_by_default(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that Co-Authored-By trailers are stripped by default (config default is true)."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-default-strip"

    cli_runner.invoke(["create", "feature-default-strip"])

    # Create a commit with a Co-Authored-By trailer
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    commit_msg = "Add feature\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    # No -n flag, but default config has no_coauthor=true
    result = cli_runner.invoke(["complete", "feature-default-strip", "-l"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Verify the commit message does NOT contain Co-Authored-By (stripped by default)
    git_log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Co-Authored-By" not in git_log.stdout, f"Expected no Co-Authored-By in: {git_log.stdout}"
    assert "Add feature" in git_log.stdout


@pytest.mark.e2e
def test_complete_no_coauthor_with_no_trailer_present(
    tmp_git_repo: Path,
    cli_runner,
    worktree_base_path: Path,
) -> None:
    """Test that -n works correctly when no Co-Authored-By trailer is present."""
    repo_name = tmp_git_repo.name
    worktree_path = worktree_base_path / repo_name / "feature-no-trailer"

    cli_runner.invoke(["create", "feature-no-trailer"])

    # Create a commit WITHOUT a Co-Authored-By trailer
    (worktree_path / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature without co-author"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )

    result = cli_runner.invoke(["complete", "feature-no-trailer", "-l", "-n"])

    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"

    # Verify the commit message is preserved
    git_log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True,
    )
    assert "Add feature without co-author" in git_log.stdout, f"Expected original message in: {git_log.stdout}"
