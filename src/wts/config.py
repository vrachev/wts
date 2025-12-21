"""Configuration management for WTS."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

CONFIG_DIR = ".wts"
CONFIG_FILENAME = "settings.local.yaml"


def get_repo_root(cwd: Path | None = None) -> Path:
    """Get the git repository root directory.

    Args:
        cwd: Directory to start search from. Defaults to current directory.

    Returns:
        Path to the repository root.

    Raises:
        RuntimeError: If not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise RuntimeError("Not in a git repository")


def get_config_path(repo_root: Path | None = None) -> Path:
    """Get the config file path for a repository.

    Args:
        repo_root: Repository root. If None, detects from current directory.

    Returns:
        Path to the config file.
    """
    if repo_root is None:
        repo_root = get_repo_root()
    return repo_root / CONFIG_DIR / CONFIG_FILENAME


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
    "init_script": {
        "type": "string",
        "default": None,
        "env": "WTS_INIT_SCRIPT",
        "description": "Shell command to run after creating a worktree",
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
    init_script: str | None = None

    @classmethod
    def load(cls, repo_root: Path | None = None) -> "Config":
        """Load config from file, with env var overrides.

        Args:
            repo_root: Repository root path. If None, detects from current directory.
        """
        config = cls()

        # Layer 1: Load from file if exists
        try:
            config_path = get_config_path(repo_root)
            if config_path.exists():
                with open(config_path) as f:
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
                if "init_script" in file_config:
                    config.init_script = file_config["init_script"]
        except RuntimeError:
            # Not in a git repository, use defaults
            pass

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
        if env_init := os.environ.get("WTS_INIT_SCRIPT"):
            config.init_script = env_init

        return config

    def save(self, repo_root: Path | None = None) -> None:
        """Save current config to file.

        Args:
            repo_root: Repository root path. If None, detects from current directory.
        """
        config_path = get_config_path(repo_root)
        config_path.parent.mkdir(parents=True, exist_ok=True)

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
        if self.init_script:
            data["init_script"] = self.init_script

        with open(config_path, "w") as f:
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


def create_default_config(repo_root: Path | None = None) -> None:
    """Create default config file if it doesn't exist.

    Args:
        repo_root: Repository root path. If None, detects from current directory.
    """
    config_path = get_config_path(repo_root)
    if not config_path.exists():
        Config().save(repo_root)
        print(f"Created default config at {config_path}")
    else:
        print(f"Config already exists at {config_path}")
