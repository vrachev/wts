"""Tests for configuration system."""

from pathlib import Path

import pytest
import wts.config
from wts.config import Config, get_config, reset_config


def test_default_config() -> None:
    """Test default configuration values."""
    config = Config()
    assert config.worktree_base == Path.home() / "github" / "worktrees"
    assert config.editor is None
    assert config.terminal is None
    assert config.terminal_mode == "split"
    assert config.terminal_split == "vertical"


def test_config_load_defaults() -> None:
    """Test loading config with defaults when no file exists."""
    config = Config.load()
    assert config.worktree_base == Path.home() / "github" / "worktrees"
    assert config.editor is None
    assert config.terminal is None
    assert config.terminal_mode == "split"
    assert config.terminal_split == "vertical"


def test_config_from_file() -> None:
    """Test loading config from file."""
    config_path = wts.config.CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
worktree_base: ~/my-worktrees
editor: cursor
terminal: iterm2
terminal_mode: tab
terminal_split: horizontal
"""
    )

    config = Config.load()
    assert config.worktree_base == Path.home() / "my-worktrees"
    assert config.editor == "cursor"
    assert config.terminal == "iterm2"
    assert config.terminal_mode == "tab"
    assert config.terminal_split == "horizontal"


def test_env_overrides_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that env vars override file config."""
    config_path = wts.config.CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("editor: cursor")

    monkeypatch.setenv("WTS_EDITOR", "code")

    config = Config.load()
    assert config.editor == "code"


def test_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that env vars override defaults."""
    monkeypatch.setenv("WTS_WORKTREE_BASE", "/custom/path")
    monkeypatch.setenv("WTS_TERMINAL_MODE", "cd")

    config = Config.load()
    assert config.worktree_base == Path("/custom/path")
    assert config.terminal_mode == "cd"


def test_config_save() -> None:
    """Test saving config."""
    config = Config()
    config.editor = "zed"
    config.save()

    assert wts.config.CONFIG_PATH.exists()
    loaded = Config.load()
    assert loaded.editor == "zed"


def test_config_save_only_non_defaults() -> None:
    """Test that save only writes non-default values."""
    config = Config()
    config.save()

    content = wts.config.CONFIG_PATH.read_text()
    # worktree_base is always written
    assert "worktree_base" in content
    # defaults are not written
    assert "terminal_mode" not in content
    assert "terminal_split" not in content


def test_get_config_singleton() -> None:
    """Test that get_config returns same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_reset_config_clears_singleton() -> None:
    """Test that reset_config clears the singleton."""
    config1 = get_config()
    reset_config()
    config2 = get_config()
    assert config1 is not config2


def test_config_path_expansion() -> None:
    """Test that ~ is expanded in paths."""
    config_path = wts.config.CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("worktree_base: ~/custom/worktrees")

    config = Config.load()
    assert config.worktree_base == Path.home() / "custom" / "worktrees"


def test_config_cli_show(cli_runner) -> None:
    """Test wts config show command."""
    result = cli_runner.invoke(["config", "show"])
    assert result.exit_code == 0
    assert "worktree_base:" in result.output
    assert "editor:" in result.output
    assert "terminal:" in result.output


def test_config_cli_list(cli_runner) -> None:
    """Test wts config list command."""
    result = cli_runner.invoke(["config", "list"])
    assert result.exit_code == 0
    assert "worktree_base" in result.output
    assert "editor" in result.output
    assert "terminal" in result.output
    assert "terminal_mode" in result.output
    assert "terminal_split" in result.output
    # Check for description content rather than literal word "Description"
    assert "Base directory" in result.output


def test_config_cli_set_and_get(cli_runner) -> None:
    """Test wts config set and get commands."""
    result = cli_runner.invoke(["config", "set", "editor", "cursor"])
    assert result.exit_code == 0
    assert "editor = cursor" in result.output

    result = cli_runner.invoke(["config", "get", "editor"])
    assert result.exit_code == 0
    assert "cursor" in result.output


def test_config_cli_set_invalid_key(cli_runner) -> None:
    """Test wts config set with invalid key."""
    result = cli_runner.invoke(["config", "set", "invalid_key", "value"])
    assert result.exit_code != 0
    assert "Unknown config key" in result.output


def test_config_cli_set_invalid_terminal_mode(cli_runner) -> None:
    """Test wts config set with invalid terminal_mode value."""
    result = cli_runner.invoke(["config", "set", "terminal_mode", "invalid"])
    assert result.exit_code != 0
    assert "split, tab, or cd" in result.output


def test_config_cli_set_invalid_terminal_split(cli_runner) -> None:
    """Test wts config set with invalid terminal_split value."""
    result = cli_runner.invoke(["config", "set", "terminal_split", "invalid"])
    assert result.exit_code != 0
    assert "vertical or horizontal" in result.output


def test_config_cli_path(cli_runner) -> None:
    """Test wts config path command."""
    result = cli_runner.invoke(["config", "path"])
    assert result.exit_code == 0
    assert "config.yaml" in result.output
