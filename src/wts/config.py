"""Configuration management for WTS."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

CONFIG_PATH = Path.home() / ".config" / "wts" / "config.yaml"

# Schema for documentation and wts config list
CONFIG_SCHEMA: dict[str, dict[str, str | None]] = {
    "worktree_base": {
        "type": "path",
        "default": "~/github/worktrees",
        "env": "WTS_WORKTREE_BASE",
        "description": "Base directory for storing worktrees",
    },
    "editor": {
        "type": "string",
        "default": None,
        "env": "WTS_EDITOR",
        "description": "Default editor (cursor, code, zed, subl)",
    },
    "terminal": {
        "type": "string",
        "default": None,
        "env": "WTS_TERMINAL",
        "description": "Terminal override (iterm2, tmux, warp, terminal, none)",
    },
    "terminal_mode": {
        "type": "string",
        "default": "split",
        "env": "WTS_TERMINAL_MODE",
        "description": "Terminal mode (split, tab, cd)",
    },
    "terminal_split": {
        "type": "string",
        "default": "vertical",
        "env": "WTS_TERMINAL_SPLIT",
        "description": "Split direction (vertical, horizontal)",
    },
}


@dataclass
class Config:
    """WTS configuration."""

    worktree_base: Path = field(default_factory=lambda: Path.home() / "github" / "worktrees")
    editor: str | None = None
    terminal: str | None = None  # None means auto-detect
    terminal_mode: Literal["split", "tab", "cd"] = "split"
    terminal_split: Literal["vertical", "horizontal"] = "vertical"

    @classmethod
    def load(cls) -> "Config":
        """Load config from file, with env var overrides."""
        config = cls()

        # Layer 1: Load from file if exists
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                file_config = yaml.safe_load(f) or {}

            if "worktree_base" in file_config:
                config.worktree_base = Path(file_config["worktree_base"]).expanduser()
            if "editor" in file_config:
                config.editor = file_config["editor"]
            if "terminal" in file_config:
                config.terminal = file_config["terminal"]
            if "terminal_mode" in file_config:
                config.terminal_mode = file_config["terminal_mode"]
            if "terminal_split" in file_config:
                config.terminal_split = file_config["terminal_split"]

        # Layer 2: Env vars override file
        if env_base := os.environ.get("WTS_WORKTREE_BASE"):
            config.worktree_base = Path(env_base).expanduser()
        if env_editor := os.environ.get("WTS_EDITOR"):
            config.editor = env_editor
        if env_terminal := os.environ.get("WTS_TERMINAL"):
            config.terminal = env_terminal
        if env_mode := os.environ.get("WTS_TERMINAL_MODE"):
            config.terminal_mode = env_mode  # type: ignore[assignment]
        if env_split := os.environ.get("WTS_TERMINAL_SPLIT"):
            config.terminal_split = env_split  # type: ignore[assignment]

        return config

    def save(self) -> None:
        """Save current config to file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, str] = {
            "worktree_base": str(self.worktree_base),
        }
        # Only write non-default values
        if self.editor:
            data["editor"] = self.editor
        if self.terminal:
            data["terminal"] = self.terminal
        if self.terminal_mode != "split":
            data["terminal_mode"] = self.terminal_mode
        if self.terminal_split != "vertical":
            data["terminal_split"] = self.terminal_split

        with open(CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Module-level singleton (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reset_config() -> None:
    """Reset config singleton (for testing)."""
    global _config
    _config = None


def create_default_config() -> None:
    """Create default config file if it doesn't exist."""
    if not CONFIG_PATH.exists():
        Config().save()
        print(f"Created default config at {CONFIG_PATH}")
    else:
        print(f"Config already exists at {CONFIG_PATH}")
