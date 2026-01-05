"""CLI commands for configuration management."""

import os
import subprocess
from pathlib import Path

import click

from wts.config import CONFIG_SCHEMA, Config, get_active_config_path, get_config


@click.group()
def config() -> None:
    """View and manage WTS configuration."""
    pass


@config.command("show")
def show() -> None:
    """Show current configuration."""
    cfg = get_config()
    config_path = get_active_config_path()

    click.echo(f"Config file: {config_path}")
    click.echo(f"  exists: {config_path.exists()}")
    click.echo()
    click.echo("Current values:")
    click.echo(f"  worktree_base:  {cfg.worktree_base}")
    click.echo(f"  editor:         {cfg.editor or '(not set)'}")
    click.echo(f"  terminal:       {cfg.terminal or '(auto-detect)'}")
    click.echo(f"  terminal_mode:  {cfg.terminal_mode}")
    click.echo(f"  terminal_split: {cfg.terminal_split}")
    click.echo(f"  init_script:    {cfg.init_script or '(not set)'}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_value(key: str, value: str) -> None:
    """Set a configuration value.

    Examples:

        wts config set editor cursor

        wts config set worktree_base ~/worktrees

        wts config set terminal_mode tab
    """
    if key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(CONFIG_SCHEMA.keys())
        raise click.ClickException(f"Unknown config key: {key}. Valid keys: {valid_keys}")

    cfg = get_config()

    if key == "worktree_base":
        cfg.worktree_base = Path(value).expanduser()
    elif key == "editor":
        cfg.editor = value
    elif key == "terminal":
        cfg.terminal = value
    elif key == "terminal_mode":
        if value not in ("split", "tab", "cd"):
            raise click.ClickException("terminal_mode must be: split, tab, or cd")
        cfg.terminal_mode = value  # type: ignore[assignment]
    elif key == "terminal_split":
        if value not in ("vertical", "horizontal"):
            raise click.ClickException("terminal_split must be: vertical or horizontal")
        cfg.terminal_split = value  # type: ignore[assignment]
    elif key == "init_script":
        cfg.init_script = value

    cfg.save()
    click.echo(f"Set {key} = {value}")


@config.command("get")
@click.argument("key")
def get_value(key: str) -> None:
    """Get a configuration value."""
    if key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(CONFIG_SCHEMA.keys())
        raise click.ClickException(f"Unknown config key: {key}. Valid keys: {valid_keys}")

    cfg = get_config()
    value = getattr(cfg, key)
    click.echo(value if value is not None else "")


@config.command("list")
def list_options() -> None:
    """List all available configuration options."""
    click.echo("Available configuration options:\n")
    for key, info in CONFIG_SCHEMA.items():
        click.echo(f"  {key}")
        click.echo(f"    {info['description']}")
        default = info["default"] if info["default"] is not None else "(none)"
        click.echo(f"    Default: {default}")
        click.echo(f"    Env var: {info['env']}")
        click.echo()


@config.command("path")
def show_path() -> None:
    """Show the config file path."""
    click.echo(get_active_config_path())


@config.command("edit")
def edit_config() -> None:
    """Open config file in default editor."""
    config_path = get_active_config_path()
    # Create config file with defaults if it doesn't exist
    if not config_path.exists():
        Config().save()
        click.echo(f"Created default config at {config_path}")

    editor = os.environ.get("EDITOR", "vim")
    subprocess.run([editor, str(config_path)])
