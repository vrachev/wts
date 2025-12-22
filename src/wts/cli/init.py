"""CLI command for initializing WTS configuration."""

import click

from wts.config import config_exists, create_default_config


def prompt_config_location() -> bool:
    """Prompt user to choose config location.

    Returns:
        True for local config, False for project config.
    """
    click.echo("Where should WTS store configuration?")
    click.echo("  [1] Local (personal settings in .wts/settings.local.yaml, gitignored)")
    click.echo("  [2] Project (shared settings in .wts/settings.yaml, tracked in git)")
    choice: int = click.prompt("Choice", type=click.IntRange(1, 2), default=1)
    return choice == 1


def run_init(force: bool = False) -> bool:
    """Run the init flow.

    Args:
        force: If True, run even if config already exists.

    Returns:
        True if config was created, False if skipped.
    """
    if not force and config_exists():
        return False

    local = prompt_config_location()
    config_path = create_default_config(local=local)
    click.echo(f"Created config at {config_path}")
    return True


@click.command()
@click.option("--force", "-f", is_flag=True, help="Reinitialize even if config exists")
def init(force: bool) -> None:
    """Initialize WTS configuration.

    Creates a config file with default values. You can choose between:

    \b
    - Local: Personal settings stored in .wts/settings.local.yaml (gitignored)
    - Project: Shared settings stored in .wts/settings.yaml (tracked in git)
    """
    if not force and config_exists():
        click.echo("WTS is already initialized. Use --force to reinitialize.")
        return

    run_init(force=True)
