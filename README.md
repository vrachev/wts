# WTS - Git Worktree Manager

Run parallel AI agents on the same repo without conflicts.

## Quick Start

```bash
uv tool install -e .          # Install
wts create feature-x          # Create worktree
wts create task-y -e claude   # Create + open in Claude
wts complete task-y -l        # Squash merge when done
```

## Commands

| Command | Description |
|---------|-------------|
| `create NAME` | Create worktree (use `-t` for terminal, `-e` for editor) |
| `complete NAME MSG` | Squash merge into main and cleanup |
| `select NAME` | Open existing worktree |
| `list` | Show all worktrees |
| `delete NAME` | Remove worktree |
| `config` | Manage settings |

## Install

```bash
git clone https://github.com/yourusername/wts.git && cd wts && uv tool install -e .
```

Shell completions: `wts autocomplete zsh >> ~/.zshrc`

## Development

```bash
uv sync --extra dev && uv run pre-commit install
uv run wts        # Run from source
uv run pytest     # Run tests
```

## License

MIT
