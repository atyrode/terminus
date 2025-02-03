"""Tests for the CLI module."""

import os
from pathlib import Path

import pytest
import tomllib

from src.cli.utils import load_project_config


def test_project_config_path_resolution():
    """Test that the path resolution in load_project_config is correct."""
    # Get the actual path of cli.py
    cli_path = Path(__file__).parent.parent / "src" / "cli" / "app.py"
    
    # Verify cli.py exists where we expect it
    assert cli_path.exists(), (
        f"cli.py not found at expected path: {cli_path}. "
        "This test ensures the path resolution in load_project_config is correct."
    )
    
    # Calculate the project root the same way load_project_config does
    calculated_root = cli_path.parent.parent.parent
    
    # Verify pyproject.toml exists at the calculated root
    pyproject_path = calculated_root / "pyproject.toml"
    assert pyproject_path.exists(), (
        f"pyproject.toml not found at calculated path: {pyproject_path}. "
        "The path resolution in load_project_config may be incorrect."
    )
    
    # Verify we can actually load and parse the file
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
        assert "project" in pyproject, "pyproject.toml does not contain a [project] section"


def test_load_project_config_content():
    """Test that load_project_config loads the expected content."""
    config = load_project_config()
    
    # Test required fields from pyproject.toml
    assert "name" in config, "Project name not found in config"
    assert "version" in config, "Project version not found in config"
    assert "description" in config, "Project description not found in config"
    
    # Test specific values
    assert config["name"] == "terminus-cli", f"Expected project name 'terminus-cli', got '{config['name']}'"
    assert isinstance(config["version"], str), "Version should be a string"
    assert isinstance(config["description"], str), "Description should be a string"


def test_load_project_config_structure():
    """Test the structure of the loaded config matches pyproject.toml."""
    # Load config through our function
    config = load_project_config()
    
    # Load config directly from pyproject.toml for comparison
    cli_path = Path(__file__).parent.parent / "src" / "cli" / "app.py"
    direct_pyproject_path = cli_path.parent.parent.parent / "pyproject.toml"
    
    with open(direct_pyproject_path, "rb") as f:
        direct_config = tomllib.load(f)["project"]
    
    # Compare the two configurations
    assert config == direct_config, (
        "Config loaded through load_project_config doesn't match "
        "direct loading of pyproject.toml"
    ) 