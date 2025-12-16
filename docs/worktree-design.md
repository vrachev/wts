# WTS (Worktree Management System) - Architecture & Design Document

## Executive Summary
A Python-based CLI tool to manage git worktrees for multi-agent development workflows. Enables humans to create/manage worktrees while AI agents work within them independently, with status tracking and notifications for asynchronous workflows.

**Core Value Proposition**: Automate and standardize git worktree management to enable parallel development by multiple AI agents without cross-pollination or manual setup overhead. Track work status and notify users when agent work is ready for review.

## Key Architectural Decisions

### 1. **Language: Python (not bash)**
- Better error handling, testing, and maintainability
- Cleaner abstractions for future TUI integration
- Easy subprocess calls to git while maintaining control
- **Tradeoff**: Slightly more overhead than bash, but worth it for maintainability

### 2. **CLI Framework: Click**
- Production-ready with excellent documentation
- Clean command composition and plugin support
- Automatic help generation
- Better than argparse (cleaner syntax) or Typer (less overhead)

### 3. **Configuration Hierarchy** (UPDATED)
```
CLI flags (highest priority)
  ↓
Project config (.wts file in repo root)
  ↓
Built-in defaults
```

**No global config** - keeps it simple and project-focused.

**Default settings:**
```yaml
# .wts (in project root)
worktrees:
  base_path: ~/github/worktrees  # Where to create worktrees
  base_branch: main              # Default base branch
  auto_fetch: true               # Fetch before creating worktree

cleanup:
  delete_branch_policy: ask      # ask | always | never
```

### 4. **Worktree Path Structure**
```
~/github/worktrees/{project-name}/{worktree-name}/
```
Example: `~/github/worktrees/wts/feature-auth/`

### 5. **Status Tracking System** (NEW)
Each worktree maintains its own status via metadata file:

```
~/github/worktrees/{project}/{worktree}/.wts-status
```

**Status values:**
- `todo` - Work not yet started
- `in_progress` - Agent is actively working
- `stuck` - Agent encountered blockers
- `ready_for_review` - Work complete, awaiting human review
- `complete` - Reviewed and approved

**Notification mechanism:**
- When status changes to `ready_for_review`, create marker file: `.ready-for-review`
- User can poll: `wts list --status ready_for_review`
- Future: File watching for real-time notifications

### 6. **Testing Strategy: E2E with TDD** (NEW)
- **Only E2E tests** - no unit or integration tests
- **TDD approach** - write tests first, then implement
- Tests create real git repos, worktrees, and execute actual CLI commands
- Tests verify full workflows from command to filesystem changes
- Keep test count minimal but comprehensive

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User / Agent / CLI                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Click)                       │
│  ┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐     │
│  │ create │ │ delete │ │ list │ │ status │ │ doctor │ ... │
│  └────┬───┘ └───┬────┘ └───┬──┘ └───┬────┘ └───┬────┘     │
└───────┼─────────┼──────────┼────────┼──────────┼───────────┘
        │         │          │        │          │
        └─────────┴──────┬───┴────────┴──────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            WorktreeManager                            │  │
│  │  - create(name, ...) -> Worktree                     │  │
│  │  - delete(name, ...) -> None                         │  │
│  │  - list(filter) -> List[Worktree]                    │  │
│  │  - set_status(name, status) -> None                  │  │
│  │  - get_status(name) -> WorkStatus                    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│         ┌───────────────┼────────────────┐                 │
│         ▼               ▼                ▼                  │
│  ┌──────────┐   ┌──────────────┐   ┌──────────┐          │
│  │ GitRepo  │   │ PathResolver │   │ StatusMgr│          │
│  └─────┬────┘   └──────┬───────┘   └────┬─────┘          │
│        │               │                 │                  │
│        │               │           ┌─────────────┐         │
│        │               │           │   Config    │         │
│        │               │           └──────┬──────┘         │
└────────┼───────────────┼──────────────────┼─────────────────┘
         │               │                  │
         ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Git Commands │  │  Filesystem  │  │  Status Files    │ │
│  │ (subprocess) │  │   (Path)     │  │ (.wts-status)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### New Component: StatusManager

**Responsibility**: Manage worktree status tracking

**Key Methods**:
- `get_status(worktree_path)` -> Read `.wts-status` file
- `set_status(worktree_path, status)` -> Write status + create notification markers
- `list_by_status(status)` -> Find all worktrees with given status
- `mark_ready_for_review(worktree_path)` -> Set status + create `.ready-for-review` marker

**Status File Format** (`.wts-status`):
```yaml
status: in_progress
updated_at: 2025-12-15T10:30:00Z
created_at: 2025-12-15T09:00:00Z
description: "Implementing user authentication"
metadata:
  last_commit: abc1234
  agent: "claude-sonnet-4.5"
```

## Project Structure

```
wts/
├── pyproject.toml              # Modern Python packaging
├── .pre-commit-config.yaml     # Pre-commit hooks
├── AGENTS.md                   # Python coding guidelines for agents
├── README.md                   # User documentation
├── docs/
│   └── worktree-design.md      # This file
│
├── src/wts/
│   ├── __init__.py
│   ├── __main__.py             # Entry point for python -m wts
│   │
│   ├── cli/                    # Click commands (UI layer)
│   │   ├── __init__.py
│   │   ├── main.py             # Main CLI entry + command group
│   │   ├── create.py           # wts create
│   │   ├── delete.py           # wts delete
│   │   ├── list.py             # wts list
│   │   ├── status.py           # wts status (Phase 2)
│   │   └── doctor.py           # wts doctor (Phase 2)
│   │
│   ├── core/                   # Business logic (no CLI deps)
│   │   ├── __init__.py
│   │   ├── git.py              # Git command abstraction
│   │   ├── worktree.py         # Worktree operations
│   │   ├── paths.py            # Path resolution/validation
│   │   ├── config.py           # Configuration management
│   │   └── status.py           # Status tracking (Phase 2)
│   │
│   ├── models/                 # Data classes
│   │   ├── __init__.py
│   │   ├── worktree.py         # Worktree model
│   │   ├── config.py           # Config model
│   │   └── status.py           # WorkStatus enum/model (Phase 2)
│   │
│   ├── exceptions.py           # Custom exceptions
│   └── constants.py            # Constants
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures (temp repos, etc.)
    ├── test_create_e2e.py      # E2E: create command (Phase 1)
    ├── test_delete_e2e.py      # E2E: delete command (Phase 1)
    ├── test_list_e2e.py        # E2E: list command (Phase 1)
    ├── test_status_e2e.py      # E2E: status tracking (Phase 2)
    └── test_doctor_e2e.py      # E2E: doctor command (Phase 2)
```

## Core Commands

### Phase 1 Commands (Core)

```bash
# Create worktree
wts create <name> [options]
  --base-branch <branch>    # Base branch (default: main)
  --no-fetch                # Skip fetching

# Delete worktree
wts delete <name> [options]
  --keep-branch             # Keep branch after deletion
  --force                   # Force delete even if dirty

# List worktrees
wts list [options]
  --verbose                 # Show full details
  --json                    # JSON output
```

### Phase 2 Commands (Status & Doctor)

```bash
# Status management
wts status <name> <status>  # Set worktree status
wts status <name>           # Get current status

# Doctor mode (diagnose and repair)
wts doctor [options]
  --fix                     # Automatically fix issues
  --dry-run                 # Show what would be fixed

# Enhanced list (adds --status filter)
wts list [options]
  --status <status>         # Filter by status (e.g., ready_for_review)

# Enhanced create (adds --description)
wts create <name> [options]
  --description <text>      # Work description for status tracking
```

### Phase 3 Commands (Claude Integration)

```bash
# Complete work
wts complete <name> [options]
  --merge                   # Merge PR after completion
  --no-pr                   # Skip PR creation

# Remote git operations
wts <name> git <command>    # Run git command in worktree
  # Examples:
  wts feature-auth git status
  wts feature-auth git log -1

# Run Claude in worktree
wts <name> claude           # Launch Claude Code in worktree
wts <name> claude --headless <prompt>  # Headless mode

# Change directory helper
wts cd <name>               # Output path for shell integration
```

## Feature Specifications

### MVP Feature 1: Create Worktree with Status

**Command**: `wts create <name> [--description TEXT]`

**Process**:
1. Validate name and preconditions
2. Create worktree at `~/github/worktrees/{project}/{name}`
3. Create `.wts-status` file with status=`todo`
4. Return success message

**Status File Created**:
```yaml
status: todo
created_at: 2025-12-15T10:00:00Z
updated_at: 2025-12-15T10:00:00Z
description: "Implement user authentication"
```

### MVP Feature 2: Status Management

**Commands**:
- `wts status <name> in_progress` - Mark work as started
- `wts status <name> ready_for_review` - Mark work as ready (creates `.ready-for-review` marker)
- `wts status <name>` - Display current status

**When marking as ready_for_review**:
1. Update `.wts-status` with new status and timestamp
2. Create `.ready-for-review` marker file
3. Output message: "Work marked as ready for review. Notification created."

**User polling**:
```bash
$ wts list --status ready_for_review
Worktrees ready for review:
  feature-auth (ready since 2 hours ago)
  bugfix-123 (ready since 30 minutes ago)
```

### MVP Feature 3: Doctor Mode

**Command**: `wts doctor [--fix] [--dry-run]`

**Checks**:
1. Orphaned worktrees (git knows about it but directory missing)
2. Orphaned directories (directory exists but git doesn't know about it)
3. Orphaned branches (branch exists but no worktree)
4. Invalid status files (corrupted `.wts-status`)
5. Missing status files (worktree exists but no status)

**Output**:
```bash
$ wts doctor
Checking for issues...

Found 3 issues:
  ✗ Orphaned worktree: feature-old (directory missing)
  ✗ Orphaned directory: ~/github/worktrees/wts/test (not a worktree)
  ⚠ Missing status file: feature-ui

Run 'wts doctor --fix' to repair automatically.

$ wts doctor --fix
Fixing issues...
  ✓ Pruned orphaned worktree: feature-old
  ✓ Removed orphaned directory: test
  ✓ Created status file for: feature-ui (status=in_progress)

All issues resolved.
```

### MVP Feature 4: Enhanced List

**Command**: `wts list [--status STATUS] [--verbose]`

**Default output**:
```bash
$ wts list
Worktrees for 'wts':
  * main (clean)
    feature-auth [in_progress] (clean) - 2 days old
    feature-ui [ready_for_review] (2 uncommitted) - 5 hours old
    bugfix-123 [stuck] (clean) - 1 day old
```

**Filter by status**:
```bash
$ wts list --status ready_for_review
Worktrees ready for review:
  feature-ui (ready since 5 hours ago)
    Path: ~/github/worktrees/wts/feature-ui
    Description: Implement new UI components
```

## Implementation Phases

### Phase 1: Core Commands

**Goal**: Basic worktree management (create/delete/list)

**Features**:
1. Create worktrees with automatic branch creation
2. Delete worktrees (with branch cleanup options)
3. List worktrees with basic info
4. E2E tests for all commands (TDD approach)

**Files to Create**:
1. Project structure (dirs, pyproject.toml)
2. AGENTS.md (Python guidelines)
3. Pre-commit hooks (.pre-commit-config.yaml)
4. `src/wts/models/worktree.py` - Worktree model
5. `src/wts/models/config.py` - Config model
6. `src/wts/core/git.py` - GitRepo
7. `src/wts/core/paths.py` - PathResolver
8. `src/wts/core/worktree.py` - WorktreeManager
9. `src/wts/core/config.py` - Config loader
10. `src/wts/cli/main.py` - CLI entry point
11. `src/wts/cli/create.py` - Create command
12. `src/wts/cli/delete.py` - Delete command
13. `src/wts/cli/list.py` - List command
14. `src/wts/exceptions.py` - Custom exceptions
15. `src/wts/constants.py` - Constants
16. `tests/conftest.py` - Pytest fixtures
17. `tests/test_create_e2e.py` - E2E test for create
18. `tests/test_delete_e2e.py` - E2E test for delete
19. `tests/test_list_e2e.py` - E2E test for list

**Success Criteria**:
- `wts create <name>` creates worktree at correct path
- `wts delete <name>` removes worktree and optionally branch
- `wts list` shows all worktrees with basic info
- All E2E tests pass
- Pre-commit hooks pass (black, ruff, mypy)

### Phase 2: Status Tracking & Doctor Mode

**Goal**: Add status tracking, notifications, and repair functionality

**Features**:
1. Status tracking (set/get status via `.wts-status` files)
2. File-based notifications (`.ready-for-review` markers)
3. Doctor mode for diagnosing and fixing issues
4. Enhanced list command with status filtering
5. E2E tests for all new functionality

**Files to Create/Modify**:
1. `src/wts/models/status.py` - WorkStatus enum and StatusInfo model
2. `src/wts/core/status.py` - StatusManager
3. `src/wts/cli/status.py` - Status command
4. `src/wts/cli/doctor.py` - Doctor command
5. Modify `src/wts/cli/create.py` - Add `--description` option
6. Modify `src/wts/cli/list.py` - Add `--status` filter
7. Modify `src/wts/core/worktree.py` - Integrate StatusManager
8. `tests/test_status_e2e.py` - E2E test for status
9. `tests/test_doctor_e2e.py` - E2E test for doctor

**Success Criteria**:
- `wts status <name> <status>` sets worktree status
- `wts status <name>` displays current status
- `wts status <name> ready_for_review` creates `.ready-for-review` marker
- `wts list --status ready_for_review` filters by status
- `wts doctor` identifies orphaned worktrees/directories
- `wts doctor --fix` repairs issues
- All E2E tests pass

### Phase 3: Claude Integration

**Goal**: Deep integration with Claude Code workflows

**Features**:
1. Per-worktree Claude settings (`.claude/settings.local.json` copy)
2. `--allow-auto-commit` flag on create
3. `wts complete` command (merge/PR handling)
4. Remote git operations (`wts <name> git <cmd>`)
5. Run Claude in worktree (`wts <name> claude`)
6. Headless Claude support
7. Auto-PR creation when status=ready_for_review

**Files to Create/Modify**:
1. `src/wts/core/claude.py` - Claude settings management
2. `src/wts/cli/complete.py` - Complete command
3. Modify `src/wts/cli/create.py` - Add `--allow-auto-commit`
4. `tests/test_complete_e2e.py` - E2E test for complete
5. `tests/test_claude_e2e.py` - E2E test for Claude integration

**Claude Settings Management**:
```bash
# Create worktree with auto-commit enabled
$ wts create feature-auth --allow-auto-commit

# This copies .claude/settings.local.json and adds:
{
  "git": {
    "allowCommit": true,
    "autoCommitOnComplete": true
  }
}
```

**Complete Command**:
```bash
# Mark complete and merge
$ wts complete feature-auth --merge
Marking feature-auth as complete...
✓ Status updated to: complete
✓ Branch merged to main
✓ Worktree deleted
✓ Branch deleted

# Mark complete but keep worktree
$ wts complete feature-auth --no-pr
Marking feature-auth as complete...
✓ Status updated to: complete
(Worktree kept, no PR created)
```

**Success Criteria**:
- Claude settings properly copied to worktrees
- `wts complete` handles merge/PR workflows
- All E2E tests pass

### Phase 4: Advanced Features

**Goal**: Power user features and automation

**Features**:
1. Shell integration (`wts cd <name>`)
2. Tab completion
3. Worktree templates
4. Batch operations
5. `--json` output for all commands
6. File watching for real-time notifications
7. TUI prototype

**Success Criteria**:
- Shell integration works across bash/zsh/fish
- Tab completion for commands and worktree names
- All E2E tests pass

## Testing Strategy (TDD Approach)

### E2E Test Structure

```python
# tests/test_create_e2e.py

def test_create_worktree_basic(tmp_git_repo, cli_runner):
    """Test creating a basic worktree end-to-end"""
    # Given: A git repository
    os.chdir(tmp_git_repo)

    # When: Creating a worktree
    result = cli_runner.invoke(cli, ['create', 'feature-test'])

    # Then: Command succeeds
    assert result.exit_code == 0
    assert 'Created worktree' in result.output

    # And: Worktree exists on filesystem
    worktree_path = Path.home() / 'github/worktrees' / tmp_git_repo.name / 'feature-test'
    assert worktree_path.exists()

    # And: Git knows about the worktree
    result = subprocess.run(['git', 'worktree', 'list'], capture_output=True, text=True)
    assert str(worktree_path) in result.stdout

    # And: Status file exists with correct status
    status_file = worktree_path / '.wts-status'
    assert status_file.exists()
    status = yaml.safe_load(status_file.read_text())
    assert status['status'] == 'todo'

def test_mark_ready_for_review_creates_marker(tmp_git_repo, cli_runner):
    """Test that marking ready_for_review creates notification marker"""
    # Given: A worktree exists
    os.chdir(tmp_git_repo)
    cli_runner.invoke(cli, ['create', 'feature-test'])
    worktree_path = Path.home() / 'github/worktrees' / tmp_git_repo.name / 'feature-test'

    # When: Marking as ready for review
    result = cli_runner.invoke(cli, ['status', 'feature-test', 'ready_for_review'])

    # Then: Command succeeds
    assert result.exit_code == 0

    # And: Marker file is created
    marker = worktree_path / '.ready-for-review'
    assert marker.exists()

    # And: Status is updated
    status_file = worktree_path / '.wts-status'
    status = yaml.safe_load(status_file.read_text())
    assert status['status'] == 'ready_for_review'
```

### Test Fixtures

```python
# tests/conftest.py

import pytest
import tempfile
import subprocess
from pathlib import Path
from click.testing import CliRunner

@pytest.fixture
def tmp_git_repo():
    """Create a temporary git repository for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / 'test-repo'
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_path)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_path)

        # Create initial commit
        (repo_path / 'README.md').write_text('# Test')
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_path, check=True)

        yield repo_path

@pytest.fixture
def cli_runner():
    """Click CLI test runner"""
    return CliRunner()
```

## AGENTS.md - Python Coding Guidelines

The `AGENTS.md` file should contain:

```markdown
# Python Coding Guidelines for WTS Development

## Code Style

- **Formatter**: Black (line length: 88)
- **Linter**: Ruff (replaces flake8, isort, etc.)
- **Type Checker**: mypy (strict mode)

## Architecture Principles

1. **Separation of Concerns**:
   - CLI layer: Only argument parsing and output formatting
   - Core layer: All business logic, no CLI dependencies
   - Models: Data classes only, no logic

2. **Dependency Injection**:
   - Pass dependencies explicitly (GitRepo, PathResolver, etc.)
   - No global state or singletons

3. **Error Handling**:
   - Use custom exceptions (from `src/wts/exceptions.py`)
   - Catch at CLI layer, display user-friendly messages
   - Always provide suggestions for resolution

4. **Testing**:
   - Write E2E tests first (TDD)
   - Test actual git operations, not mocks
   - Use temp directories for all tests

## Code Patterns

### Click Commands

```python
import click
from wts.core.worktree import WorktreeManager

@click.command()
@click.argument('name')
@click.option('--base-branch', default='main')
@click.pass_context
def create(ctx, name, base_branch):
    """Create a new worktree"""
    try:
        manager = ctx.obj['manager']  # From main.py context
        worktree = manager.create(name, base_branch=base_branch)
        click.echo(f"✓ Created worktree '{worktree.name}'")
        click.echo(f"  Path: {worktree.path}")
    except WtsError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
```

### Core Logic (Business Layer)

```python
from pathlib import Path
from wts.models.worktree import Worktree
from wts.core.git import GitRepo
from wts.exceptions import WorktreeExistsError

class WorktreeManager:
    def __init__(self, git: GitRepo, paths: PathResolver, status: StatusManager):
        self.git = git
        self.paths = paths
        self.status = status

    def create(self, name: str, base_branch: str = 'main') -> Worktree:
        # Validate
        if not self.paths.is_valid_name(name):
            raise InvalidNameError(f"Invalid name: {name}")

        # Check conflicts
        existing = self.git.list_worktrees()
        if any(wt.name == name for wt in existing):
            raise WorktreeExistsError(f"Worktree {name} already exists")

        # Create
        path = self.paths.get_worktree_path(name)
        self.git.create_worktree(path, name, base_branch)

        # Initialize status
        self.status.create_status_file(path, status='todo')

        return Worktree(name=name, path=path, branch=name, ...)
```

### Data Models

```python
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

class WorkStatus(str, Enum):
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    STUCK = 'stuck'
    READY_FOR_REVIEW = 'ready_for_review'
    COMPLETE = 'complete'

@dataclass
class Worktree:
    name: str
    path: Path
    branch: str
    commit: str
    status: WorkStatus
    is_main: bool
```

## Git Commands

Always use subprocess with proper error handling:

```python
import subprocess
from wts.exceptions import GitCommandError

def run_git_command(args: list[str], cwd: Path) -> str:
    """Run git command and return stdout"""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitCommandError(
            command=' '.join(['git'] + args),
            returncode=e.returncode,
            stderr=e.stderr
        )
    except subprocess.TimeoutExpired:
        raise GitCommandError(
            command=' '.join(['git'] + args),
            returncode=-1,
            stderr='Command timed out'
        )
```

## Don'ts

- ❌ Don't use global variables
- ❌ Don't hardcode paths (use PathResolver)
- ❌ Don't silently catch exceptions
- ❌ Don't use mocks in tests (use real git operations)
- ❌ Don't write unit tests (only E2E)
- ❌ Don't add emojis unless user explicitly requests

## Do's

- ✅ Use type hints everywhere
- ✅ Write docstrings for public methods
- ✅ Validate inputs early
- ✅ Provide helpful error messages with suggestions
- ✅ Use pathlib.Path for all file operations
- ✅ Test with temp directories
```

## Dependencies

```toml
# pyproject.toml
[project]
name = "wts"
version = "0.1.0"
description = "Worktree management for multi-agent workflows"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "types-PyYAML>=6.0.0",
]

[project.scripts]
wts = "wts.cli.main:cli"

[tool.black]
line-length = 88
target-version = ['py310']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
strict = true
python_version = "3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## Initial Setup Checklist (Phase 1)

**Repository Structure** (already done):

- [x] Create directory structure
- [x] Create `pyproject.toml` with dependencies
- [x] Create `AGENTS.md` with Python guidelines
- [x] Create `README.md` with basic usage
- [x] Create `.pre-commit-config.yaml`
- [x] Create `.gitignore`

**Phase 1 Implementation** (TDD approach):

- [ ] Write E2E test for `wts create` command
- [ ] Implement create command to pass test
- [ ] Write E2E test for `wts delete` command
- [ ] Implement delete command to pass test
- [ ] Write E2E test for `wts list` command
- [ ] Implement list command to pass test
- [ ] Verify all E2E tests pass
- [ ] Verify pre-commit hooks pass (black, ruff, mypy)

## Next Steps

1. Begin Phase 1 with TDD - write `test_create_e2e.py` first
2. Implement core modules (git.py, paths.py, worktree.py) to pass tests
3. Continue with delete and list commands
4. Complete Phase 1 with all E2E tests passing
5. Move to Phase 2 (status tracking)
