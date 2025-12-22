"""Configuration management for WTS."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

CONFIG_DIR = ".wts"
CONFIG_FILENAME_LOCAL = "settings.local.yaml"
CONFIG_FILENAME_PROJECT = "settings.yaml"


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


def get_config_path(repo_root: Path | None = None, local: bool = True) -> Path:
    """Get the config file path for a repository.

    Args:
        repo_root: Repository root. If None, detects from current directory.
        local: If True, return path to local config. If False, return path to project config.

    Returns:
        Path to the config file.
    """
    if repo_root is None:
        repo_root = get_repo_root()
    filename = CONFIG_FILENAME_LOCAL if local else CONFIG_FILENAME_PROJECT
    return repo_root / CONFIG_DIR / filename


def config_exists(repo_root: Path | None = None) -> bool:
    """Check if any config file exists (local or project).

    Args:
        repo_root: Repository root. If None, detects from current directory.

    Returns:
        True if either local or project config exists.
    """
    try:
        if repo_root is None:
            repo_root = get_repo_root()
        local_path = repo_root / CONFIG_DIR / CONFIG_FILENAME_LOCAL
        project_path = repo_root / CONFIG_DIR / CONFIG_FILENAME_PROJECT
        return local_path.exists() or project_path.exists()
    except RuntimeError:
        # Not in a git repository
        return False


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
    def _apply_file_config(cls, config: "Config", file_config: dict[str, Any]) -> None:
        """Apply config values from a file config dict."""
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

    @classmethod
    def load(cls, repo_root: Path | None = None) -> "Config":
        """Load config from file, with env var overrides.

        Loading precedence (later overrides earlier):
        1. Default values
        2. Project config (.wts/settings.yaml)
        3. Local config (.wts/settings.local.yaml)
        4. Environment variables

        Args:
            repo_root: Repository root path. If None, detects from current directory.
        """
        config = cls()

        try:
            # Layer 1: Load project config if exists (shared settings)
            project_path = get_config_path(repo_root, local=False)
            if project_path.exists():
                with open(project_path) as f:
                    file_config = yaml.safe_load(f) or {}
                cls._apply_file_config(config, file_config)

            # Layer 2: Load local config if exists (personal settings override project)
            local_path = get_config_path(repo_root, local=True)
            if local_path.exists():
                with open(local_path) as f:
                    file_config = yaml.safe_load(f) or {}
                cls._apply_file_config(config, file_config)
        except RuntimeError:
            # Not in a git repository, use defaults
            pass

        # Layer 3: Env vars override file
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

    def _serialize_value(self, key: str) -> str | None:
        """Serialize a config value to string for YAML output.

        Returns None if the value should be commented out.
        """
        value = getattr(self, key)
        if value is None:
            return None
        if key == "worktree_base":
            # Use ~ shorthand for home directory
            path_str = str(value)
            home = str(Path.home())
            if path_str.startswith(home):
                return "~" + path_str[len(home) :]
            return path_str
        return str(value)

    def save(self, repo_root: Path | None = None, local: bool = True) -> None:
        """Save current config to file with documentation comments.

        Args:
            repo_root: Repository root path. If None, detects from current directory.
            local: If True, save to local config. If False, save to project config.
        """
        config_path = get_config_path(repo_root, local=local)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = []
        for key, schema in CONFIG_SCHEMA.items():
            # Add description comment
            lines.append(f"# {schema['description']}")
            # Add env var comment
            lines.append(f"# Env: {schema['env']}")
            # Add the key: value (commented out if None)
            value = self._serialize_value(key)
            if value is None:
                lines.append(f"# {key}:")
            else:
                lines.append(f"{key}: {value}")
            lines.append("")  # Blank line between settings

        # Remove trailing blank line
        if lines and lines[-1] == "":
            lines.pop()

        with open(config_path, "w") as f:
            f.write("\n".join(lines) + "\n")


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


def create_default_config(repo_root: Path | None = None, local: bool = True) -> Path:
    """Create default config file.

    Args:
        repo_root: Repository root path. If None, detects from current directory.
        local: If True, create local config. If False, create project config.

    Returns:
        Path to the created config file.
    """
    config_path = get_config_path(repo_root, local=local)
    Config().save(repo_root, local=local)
    return config_path
