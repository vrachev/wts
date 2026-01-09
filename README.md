# WTS - Git Worktree Manager

Run parallel AI agents on the same repo without conflicts.

## Quick Start (my typical workflow)

```bash
uv tool install -e .                    # Install
wts config set editor claude            # Set Claude as default editor
wts create task-y -e.                   # Create worktree + open new terminal tabl with Claude.
                                        # Proceed to do Claude things
wts complete task-y -l                  # Squash merge using latest commit when done
```

## More options

```bash
wts list                                # List all worktrees

wts create task-y -t                    # Create + open in terminal
wts create task-y -e                    # Create worktree + open in default editor set in config

wts complete task-y -l -a               # Squash merge and have Claude fix any merge conflicts
wts complete task-y -p                  # Merge and preserve commits
wts complete task-y "my commit msg"     # Squash merge with your own commit message"

wts select task-y -e code               # Select existing worktree and open in vscode
wts delete task-y                       # Delete worktree
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

wts supports init scripts that run when a new worktree is created (eg: install deps, create virtualenv etc..)
Add init script to config. Eg: `init_script: uv sync --extra dev` in this project.

## Development

```bash
uv sync --extra dev && uv run pre-commit install
uv run wts        # Run from source
uv run pytest     # Run tests
```

## Notes
* This is mostly a personal tool for me, so I haven't spent time testing it on terminals/editors I don't use. I use iterm2, Claude and VSCode, and it works well with those.
* There are more polished tools that aim to solve the same problem as this, such as https://github.com/max-sixty/worktrunk. Feel free to check them out if the workflow here is not your speed.

## License

MIT
