# WTS - Worktree Management System

CLI for managing git worktrees for parallel AI agent development.

## Installation

```bash
git clone https://github.com/yourusername/wts.git
cd wts
uv sync --extra dev
uv run pre-commit install
```

## Usage

```bash
# Create a worktree (branches from main)
uv run wts create feature-auth

# Branch from current HEAD instead
uv run wts create feature-subtask --from-current
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

```bash
uv run pytest tests/
uv run pytest tests/ --cov=src/wts
uv run pre-commit run --all-files
```

## License

MIT
