# WTS - Worktree Management System

A command-line tool for managing git worktrees to enable parallel development by multiple AI agents.

## What is WTS?

WTS automates git worktree creation and management, making it easy to:
- Run multiple AI agents on different features simultaneously
- Track work status (todo, in_progress, ready_for_review, complete)
- Get notified when agent work is ready for review
- Clean up and organize worktrees across projects

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wts.git
cd wts

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Quick Start

```bash
# Create a new worktree
wts create feature-auth

# List all worktrees
wts list

# Set status to ready for review
wts status feature-auth ready_for_review

# Delete a worktree
wts delete feature-auth
```

## Core Concepts

### Worktrees

Git worktrees allow you to have multiple working trees from the same repository. WTS organizes them in a centralized location:

```
~/github/worktrees/{project-name}/{worktree-name}/
```

For example:
```
~/github/worktrees/wts/feature-auth/
~/github/worktrees/wts/feature-ui/
~/github/worktrees/wts/bugfix-123/
```

### Status Tracking

Each worktree maintains a status that tracks the work progress:

- `todo` - Work not yet started
- `in_progress` - Agent is actively working
- `stuck` - Agent encountered blockers
- `ready_for_review` - Work complete, awaiting human review
- `complete` - Reviewed and approved

### Notifications

When a worktree is marked as `ready_for_review`, a `.ready-for-review` marker file is created. You can find all worktrees ready for review:

```bash
wts list --status ready_for_review
```

## Commands

### create

Create a new worktree:

```bash
wts create <name> [OPTIONS]

Options:
  --base-branch TEXT    Base branch to branch from (default: main)
  --description TEXT    Work description for status tracking
  --no-fetch           Skip fetching from remote
```

Examples:
```bash
# Basic creation
wts create feature-auth

# With description
wts create feature-auth --description "Implement JWT authentication"

# From different base branch
wts create hotfix-123 --base-branch production
```

### delete

Delete a worktree:

```bash
wts delete <name> [OPTIONS]

Options:
  --keep-branch    Keep the branch after removing worktree
  --force          Force deletion even if dirty or branch not merged
```

Examples:
```bash
# Delete worktree (prompts for branch deletion)
wts delete feature-auth

# Keep the branch
wts delete feature-auth --keep-branch

# Force delete even if uncommitted changes
wts delete feature-auth --force
```

### list

List all worktrees for the current project:

```bash
wts list [OPTIONS]

Options:
  --verbose            Show full details
  --status TEXT        Filter by status
  --json              JSON output for programmatic use
```

Examples:
```bash
# List all worktrees
wts list

# Show detailed information
wts list --verbose

# Filter by status
wts list --status ready_for_review

# JSON output
wts list --json
```

### status

Get or set worktree status:

```bash
# Get current status
wts status <name>

# Set status
wts status <name> <status>
```

Available statuses: `todo`, `in_progress`, `stuck`, `ready_for_review`, `complete`

Examples:
```bash
# Start work
wts status feature-auth in_progress

# Mark as ready for review
wts status feature-auth ready_for_review

# Check current status
wts status feature-auth
```

### doctor

Diagnose and fix common issues:

```bash
wts doctor [OPTIONS]

Options:
  --fix        Automatically fix issues
  --dry-run    Show what would be fixed
```

Examples:
```bash
# Check for issues
wts doctor

# Fix issues automatically
wts doctor --fix

# Preview fixes
wts doctor --dry-run
```

## Multi-Agent Workflow Example

```bash
# Create worktrees for 4 parallel features
cd ~/github/my-project
wts create feature-auth --description "Add authentication"
wts create feature-ui --description "Redesign UI"
wts create feature-api --description "Integrate external API"
wts create feature-db --description "Optimize database"

# Agents work in parallel, each in their own worktree
# Agent 1 in ~/github/worktrees/my-project/feature-auth
# Agent 2 in ~/github/worktrees/my-project/feature-ui
# Agent 3 in ~/github/worktrees/my-project/feature-api
# Agent 4 in ~/github/worktrees/my-project/feature-db

# When agent completes work, it marks status
wts status feature-auth ready_for_review

# Human checks what's ready for review
wts list --status ready_for_review

# Review and merge
cd ~/github/my-project
git merge feature-auth
wts delete feature-auth
```

## Configuration

Project-level configuration in `.wts` file at repository root:

```yaml
worktrees:
  base_path: ~/github/worktrees  # Where to create worktrees
  base_branch: main              # Default base branch
  auto_fetch: true               # Fetch before creating worktree

cleanup:
  delete_branch_policy: ask      # ask | always | never
```

## Development

### Running Tests

```bash
# Run all E2E tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/wts --cov-report=html

# Run specific test
pytest tests/test_create_e2e.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type check
mypy src/

# Run all checks (automatically via pre-commit)
pre-commit run --all-files
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Contributing

See [AGENTS.md](AGENTS.md) for coding guidelines.

## License

MIT
