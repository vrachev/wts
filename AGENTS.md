# Python Coding Guidelines for WTS Development

This document provides coding standards and patterns for AI agents and developers working on the WTS (Worktree Management System) project.

## Code Style

- **Formatter**: Black (line length: 120)
- **Linter**: Ruff (replaces flake8, isort, etc.)
- **Type Checker**: mypy (strict mode)
- **Python Version**: 3.10+

Run formatters and linters:
```bash
black src/ tests/
ruff check src/ tests/ --fix
mypy src/
```

## Architecture Principles

### 1. Separation of Concerns

**Three-Layer Architecture:**

1. **CLI Layer** (`src/wts/cli/`):
   - Only argument parsing and output formatting
   - No business logic
   - Delegates to core layer

2. **Core Layer** (`src/wts/core/`):
   - All business logic
   - No CLI dependencies (no `click` imports)
   - Pure Python functions and classes

3. **Models** (`src/wts/models/`):
   - Data classes only
   - No logic beyond property methods
   - Use `@dataclass` decorator

**Example:**
```python
# ❌ BAD: Business logic in CLI layer
@click.command()
def create(name):
    path = Path.home() / "github/worktrees" / name
    subprocess.run(["git", "worktree", "add", str(path)])

# ✅ GOOD: CLI delegates to core
@click.command()
@click.pass_context
def create(ctx, name):
    manager = ctx.obj['manager']
    worktree = manager.create(name)
    click.echo(f"✓ Created worktree '{worktree.name}'")
```

### 2. Dependency Injection

- Pass dependencies explicitly through constructors
- No global state or singletons
- Makes testing easier and code more maintainable

**Example:**
```python
# ✅ GOOD: Dependencies injected
class WorktreeManager:
    def __init__(self, git: GitRepo, paths: PathResolver, status: StatusManager):
        self.git = git
        self.paths = paths
        self.status = status

# ❌ BAD: Global dependencies
git_repo = GitRepo()  # Global

class WorktreeManager:
    def create(self, name):
        git_repo.create_worktree(...)  # Uses global
```

### 3. Error Handling

- Use custom exceptions from `src/wts/exceptions.py`
- Catch at CLI layer, display user-friendly messages
- Always provide suggestions for resolution
- Use specific exception types, not generic `Exception`

**Exception Hierarchy:**
```python
class WtsError(Exception):
    """Base exception for all WTS errors"""

class ValidationError(WtsError):
    """Input validation failed"""

class WorktreeExistsError(ValidationError):
    """Worktree already exists"""

class GitCommandError(WtsError):
    """Git command failed"""
```

**Example:**
```python
# Core layer: Raise specific exceptions
def create(self, name: str) -> Worktree:
    if not self.paths.is_valid_name(name):
        raise InvalidNameError(
            f"Worktree name '{name}' contains invalid characters. "
            f"Use only alphanumeric, hyphens, and underscores."
        )

# CLI layer: Catch and display user-friendly messages
try:
    worktree = manager.create(name)
    click.echo(f"✓ Created worktree '{worktree.name}'")
except InvalidNameError as e:
    click.echo(f"Error: {e}", err=True)
    click.echo("Examples of valid names: feature-auth, bugfix-123", err=True)
    sys.exit(2)
```

### 4. Testing Strategy

- **Only E2E (end-to-end) tests** - no unit or integration tests
- **TDD approach** - write tests first, then implement
- Test actual git operations, not mocks
- Use temporary directories for all tests

## Code Patterns

### Click Commands (CLI Layer)

```python
import click
import sys
from wts.core.worktree import WorktreeManager
from wts.exceptions import WtsError, ValidationError

@click.command()
@click.argument('name')
@click.option('--from-current', is_flag=True, help='Branch from current branch instead of main')
@click.option('--description', help='Work description for status tracking')
@click.pass_context
def create(ctx, name: str, from_current: bool, description: str | None) -> None:
    """Create a new worktree"""
    try:
        manager: WorktreeManager = ctx.obj['manager']
        worktree = manager.create(
            name=name,
            from_current=from_current,
            description=description
        )

        # Success output
        click.echo(f"✓ Created worktree '{worktree.name}'")
        click.echo(f"  Path: {worktree.path}")
        click.echo(f"  Branch: {worktree.branch}")

    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    except GitCommandError as e:
        click.echo(f"Error: Git command failed", err=True)
        click.echo(f"  {e.stderr}", err=True)
        sys.exit(3)
    except WtsError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
```

### Core Logic (Business Layer)

```python
from pathlib import Path
from wts.models.worktree import Worktree
from wts.models.status import WorkStatus
from wts.core.git import GitRepo
from wts.core.paths import PathResolver
from wts.core.status import StatusManager
from wts.exceptions import WorktreeExistsError, InvalidNameError

class WorktreeManager:
    """Manages worktree operations"""

    def __init__(
        self,
        git: GitRepo,
        paths: PathResolver,
        status: StatusManager
    ) -> None:
        self.git = git
        self.paths = paths
        self.status = status

    def create(
        self,
        name: str,
        from_current: bool = False,
        description: str | None = None
    ) -> Worktree:
        """Create a new worktree with status tracking

        Args:
            name: Worktree/branch name
            from_current: If True, branch from current branch; if False, branch from main
            description: Optional work description

        Returns:
            Worktree object

        Raises:
            InvalidNameError: If name contains invalid characters
            WorktreeExistsError: If worktree already exists
            GitCommandError: If git command fails
        """
        # Validate name
        if not self.paths.is_valid_name(name):
            raise InvalidNameError(
                f"Invalid name: '{name}'. Use only alphanumeric, hyphens, and underscores."
            )

        # Check for conflicts
        existing = self.git.list_worktrees()
        if any(wt.name == name for wt in existing):
            raise WorktreeExistsError(f"Worktree '{name}' already exists")

        # Determine base branch
        base_branch = self.git.get_current_branch() if from_current else 'main'

        # Create worktree
        path = self.paths.get_worktree_path(name)
        self.git.create_worktree(path, name, base_branch)

        # Initialize status
        self.status.create_status_file(
            path,
            status=WorkStatus.TODO,
            description=description
        )

        # Return worktree model
        return Worktree(
            name=name,
            path=path,
            branch=name,
            commit=self.git.get_head_commit(path),
            status=WorkStatus.TODO,
            is_main=False
        )
```

### Data Models

```python
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from datetime import datetime

class WorkStatus(str, Enum):
    """Worktree work status"""
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    STUCK = 'stuck'
    READY_FOR_REVIEW = 'ready_for_review'
    COMPLETE = 'complete'

@dataclass
class Worktree:
    """Worktree information"""
    name: str
    path: Path
    branch: str
    commit: str
    status: WorkStatus
    is_main: bool
    created_at: datetime | None = None

    @property
    def is_clean(self) -> bool:
        """Check if worktree has uncommitted changes"""
        # This would call git status
        pass
```

### Git Commands

Always use subprocess with proper error handling:

```python
import subprocess
from pathlib import Path
from wts.exceptions import GitCommandError

def run_git_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 30
) -> str:
    """Run git command and return stdout

    Args:
        args: Git command arguments (without 'git')
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        Command stdout (stripped)

    Raises:
        GitCommandError: If command fails or times out
    """
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitCommandError(
            command=' '.join(['git'] + args),
            returncode=e.returncode,
            stderr=e.stderr.strip()
        )
    except subprocess.TimeoutExpired:
        raise GitCommandError(
            command=' '.join(['git'] + args),
            returncode=-1,
            stderr=f'Command timed out after {timeout}s'
        )
```

### E2E Tests

```python
import pytest
import subprocess
from pathlib import Path
from click.testing import CliRunner
from wts.cli.main import cli

def test_create_worktree_basic(tmp_git_repo: Path, cli_runner: CliRunner) -> None:
    """Test creating a basic worktree end-to-end"""
    # Given: A git repository
    import os
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
    result = subprocess.run(
        ['git', 'worktree', 'list'],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    )
    assert str(worktree_path) in result.stdout

    # And: Status file exists with correct status
    import yaml
    status_file = worktree_path / '.wts-status'
    assert status_file.exists()
    status = yaml.safe_load(status_file.read_text())
    assert status['status'] == 'todo'
```

## Don'ts

- ❌ Don't use global variables or singletons
- ❌ Don't hardcode paths (use PathResolver)
- ❌ Don't silently catch exceptions
- ❌ Don't use mocks in tests (use real git operations)
- ❌ Don't write unit tests (only E2E)
- ❌ Don't add emojis unless user explicitly requests
- ❌ Don't import from CLI layer in core layer
- ❌ Don't use `print()` (use logging or return values)
- ❌ Don't use `os.path` (use `pathlib.Path`)
- ❌ Don't catch generic `Exception` (use specific exception types)

## Do's

- ✅ Use type hints everywhere (function args, returns, variables)
- ✅ Write docstrings for public methods (Google style)
- ✅ Validate inputs early and fail fast
- ✅ Provide helpful error messages with suggestions
- ✅ Use `pathlib.Path` for all file operations
- ✅ Test with temporary directories
- ✅ Use dataclasses for data structures
- ✅ Use enums for constants with fixed values
- ✅ Keep functions small and focused
- ✅ Write tests before implementation (TDD)

## Type Hints Best Practices

```python
# Use specific types, not Any
def create(name: str, options: dict[str, Any]) -> Worktree:  # ❌ dict[str, Any]
def create(name: str, from_current: bool = False) -> Worktree:  # ✅ Specific types

# Use Optional or | None for nullable types
def get_description(path: Path) -> str | None:  # ✅ Python 3.10+
from typing import Optional
def get_description(path: Path) -> Optional[str]:  # ✅ Also valid

# Use collections from typing for generics
from typing import List, Dict  # Python <3.9
def list_all() -> list[Worktree]:  # ✅ Python 3.10+
```

## Documentation Style (Google Docstrings)

```python
def create_worktree(
    name: str,
    from_current: bool = False,
    description: str | None = None
) -> Worktree:
    """Create a new git worktree with status tracking.

    Args:
        name: Worktree/branch name. Must contain only alphanumeric
            characters, hyphens, and underscores.
        from_current: If True, branch from current branch; if False,
            branch from main. Defaults to False.
        description: Optional description of the work to be done.

    Returns:
        Worktree object with path, status, and metadata.

    Raises:
        InvalidNameError: If name contains invalid characters.
        WorktreeExistsError: If worktree with same name already exists.
        GitCommandError: If git command fails.

    Example:
        >>> manager = WorktreeManager(git, paths, status)
        >>> wt = manager.create('feature-auth', description='Add JWT auth')
        >>> print(wt.path)
        /Users/vlad/github/worktrees/my-project/feature-auth
    """
```

## Git Operations Best Practices

1. **Always use subprocess, not os.system**
2. **Always capture and handle errors**
3. **Always set timeout (default 30s)**
4. **Always use text mode (text=True)**
5. **Parse output carefully (use --porcelain when available)**

```python
# ✅ GOOD: Proper git command execution
def list_worktrees(self, repo_path: Path) -> list[dict[str, str]]:
    """List all worktrees using --porcelain format"""
    output = self.run_git_command(
        ['worktree', 'list', '--porcelain'],
        cwd=repo_path
    )
    return self._parse_porcelain_output(output)

# ❌ BAD: Parsing human-readable output
def list_worktrees(self, repo_path: Path) -> list[str]:
    output = self.run_git_command(['worktree', 'list'], cwd=repo_path)
    return [line.split()[0] for line in output.split('\n')]  # Fragile!
```

## File Operations Best Practices

```python
from pathlib import Path
import yaml

# ✅ GOOD: Use pathlib
def read_status(worktree_path: Path) -> dict[str, Any]:
    status_file = worktree_path / '.wts-status'
    if not status_file.exists():
        raise FileNotFoundError(f"Status file not found: {status_file}")
    return yaml.safe_load(status_file.read_text())

# ❌ BAD: Use os.path and string concatenation
import os
def read_status(worktree_path: str) -> dict[str, Any]:
    status_file = os.path.join(worktree_path, '.wts-status')
    if not os.path.exists(status_file):
        raise FileNotFoundError(f"Status file not found: {status_file}")
    with open(status_file) as f:
        return yaml.safe_load(f)
```

## Exit Codes

Use consistent exit codes across all commands:

- `0`: Success
- `1`: General error
- `2`: Validation error (bad input)
- `3`: Git command error
- `4`: Configuration error
- `5`: System error (permissions, disk full)

## Pre-commit Checklist

Before committing code:

1. ✅ All E2E tests pass: `pytest tests/`
2. ✅ Code formatted: `black src/ tests/`
3. ✅ No linting errors: `ruff check src/ tests/`
4. ✅ Type checking passes: `mypy src/`
5. ✅ Pre-commit hooks installed: `pre-commit install`

## Questions?

When in doubt:
1. Look at existing code for patterns
2. Refer to this document
3. Ask for clarification rather than guessing
4. Keep it simple - don't over-engineer
