"""Tests for init command and auto-initialization."""

from pathlib import Path

import wts.config


def test_init_local_config(cli_runner, isolate_config_path: Path) -> None:
    """Test wts init with local config choice."""
    # Remove the pre-created config
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    if local_config.exists():
        local_config.unlink()

    result = cli_runner.invoke(["init"], input="1\n")
    assert result.exit_code == 0
    assert "Created config at" in result.output
    assert "settings.local.yaml" in result.output

    assert local_config.exists()


def test_init_project_config(cli_runner, isolate_config_path: Path) -> None:
    """Test wts init with project config choice."""
    # Remove the pre-created config
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    if local_config.exists():
        local_config.unlink()

    result = cli_runner.invoke(["init"], input="2\n")
    assert result.exit_code == 0
    assert "Created config at" in result.output
    assert "settings.yaml" in result.output
    # Should NOT contain .local
    assert ".local" not in result.output.split("settings.yaml")[0].split("settings")[-1]

    project_config = isolate_config_path / wts.config.CONFIG_FILENAME_PROJECT
    assert project_config.exists()


def test_init_already_initialized(cli_runner, isolate_config_path: Path) -> None:
    """Test wts init when config already exists."""
    # First init
    cli_runner.invoke(["init"], input="1\n")

    # Second init should show already initialized
    result = cli_runner.invoke(["init"])
    assert result.exit_code == 0
    assert "already initialized" in result.output


def test_init_force_reinitialize(cli_runner, isolate_config_path: Path) -> None:
    """Test wts init --force reinitializes config."""
    # First init with local
    cli_runner.invoke(["init"], input="1\n")

    # Force reinit with project
    result = cli_runner.invoke(["init", "--force"], input="2\n")
    assert result.exit_code == 0
    assert "Created config at" in result.output

    project_config = isolate_config_path / wts.config.CONFIG_FILENAME_PROJECT
    assert project_config.exists()


def test_auto_init_on_first_command(cli_runner, isolate_config_path: Path) -> None:
    """Test that running a command without config triggers init."""
    # Remove the pre-created config
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    if local_config.exists():
        local_config.unlink()

    # Run list command without any config
    result = cli_runner.invoke(["list"], input="1\n")

    # Should have prompted for init
    assert "WTS needs to be initialized" in result.output
    assert "Created config at" in result.output

    # Config should now exist
    assert local_config.exists()


def test_auto_init_skipped_for_init_command(cli_runner, isolate_config_path: Path) -> None:
    """Test that init command doesn't trigger auto-init."""
    # Remove the pre-created config
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    if local_config.exists():
        local_config.unlink()

    result = cli_runner.invoke(["init"], input="1\n")

    # Should only show init prompt once (from the init command itself)
    assert result.output.count("Where should WTS store configuration?") == 1


def test_auto_init_skipped_for_autocomplete_command(cli_runner, isolate_config_path: Path) -> None:
    """Test that autocomplete command doesn't trigger auto-init."""
    # Remove the pre-created config
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    if local_config.exists():
        local_config.unlink()

    result = cli_runner.invoke(["autocomplete", "bash"])

    # Should NOT prompt for init
    assert "WTS needs to be initialized" not in result.output


def test_no_auto_init_when_config_exists(cli_runner, isolate_config_path: Path) -> None:
    """Test that auto-init is skipped when config exists."""
    # First init
    cli_runner.invoke(["init"], input="1\n")

    # Run list command
    result = cli_runner.invoke(["list"])

    # Should NOT prompt for init
    assert "WTS needs to be initialized" not in result.output
    assert "Where should WTS store configuration?" not in result.output


def test_config_precedence_local_over_project(cli_runner, isolate_config_path: Path) -> None:
    """Test that local config takes precedence over project config."""
    # Create project config with specific editor
    project_config = isolate_config_path / wts.config.CONFIG_FILENAME_PROJECT
    project_config.parent.mkdir(parents=True, exist_ok=True)
    project_config.write_text("editor: cursor\n")

    # Create local config with different editor
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    local_config.write_text("editor: code\n")

    # Load config - local should take precedence
    config = wts.config.Config.load()
    assert config.editor == "code"


def test_config_loads_project_when_no_local(cli_runner, isolate_config_path: Path) -> None:
    """Test that project config is used when local doesn't exist."""
    # Create only project config
    project_config = isolate_config_path / wts.config.CONFIG_FILENAME_PROJECT
    project_config.parent.mkdir(parents=True, exist_ok=True)
    project_config.write_text("editor: cursor\n")

    # Load config - should use project
    config = wts.config.Config.load()
    assert config.editor == "cursor"


def test_config_exists_checks_both_files(isolate_config_path: Path) -> None:
    """Test that config_exists checks both local and project files."""
    # Neither exists
    assert not wts.config.config_exists()

    # Create project config
    project_config = isolate_config_path / wts.config.CONFIG_FILENAME_PROJECT
    project_config.parent.mkdir(parents=True, exist_ok=True)
    project_config.write_text("editor: cursor\n")
    assert wts.config.config_exists()

    # Remove project, create local
    project_config.unlink()
    local_config = isolate_config_path / wts.config.CONFIG_FILENAME_LOCAL
    local_config.write_text("editor: code\n")
    assert wts.config.config_exists()
