# WTS - Worktree Management System

CLI for managing git worktrees for parallel AI agent development.

## Installation

```bash
git clone https://github.com/yourusername/wts.git
cd wts
uv tool install -e .
```

If `wts` command is not found, run `uv tool update-shell` and restart your shell.

### Development Setup

```bash
git clone https://github.com/yourusername/wts.git
cd wts
uv sync --extra dev
uv run pre-commit install
```

Use `uv run wts` to run the development version from your local source.

## Usage

```bash
# Create a worktree (branches from main)
wts create feature-auth

# Branch from current HEAD instead
wts create feature-subtask --from-current
```

Worktrees are created at `~/github/worktrees/{project}/{name}/` (override with `WTS_WORKTREE_BASE` env var).

## Shell Completion

Enable tab completion for commands, flags, and worktree names.

**Zsh:**
```bash
wts completion zsh >> ~/.zshrc
source ~/.zshrc
```

**Bash:**
```bash
wts completion bash >> ~/.bashrc
source ~/.bashrc
```

**Fish:**
```bash
wts completion fish > ~/.config/fish/completions/wts.fish
```

## Development

Run tests and linting with the project's virtual environment:

```bash
uv run pytest tests/
uv run pytest tests/ --cov=src/wts
uv run pre-commit run --all-files
```

To test your local changes, use `uv run wts` instead of the installed `wts` command.

## License

MIT
