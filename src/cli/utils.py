"""Utility functions for the CLI."""

import os
from typing import Dict, Any
from pathlib import Path
import tomllib

from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from config import config
from src.console import console as _console

def get_console() -> Console:
    """Get the global console instance."""
    return _console

def get_api_base() -> str:
    """Get the API base URL."""
    return f"http://localhost:{config.port}"

def load_project_config() -> Dict[str, Any]:
    """Load project configuration from pyproject.toml.
    
    Returns:
        Dict containing the project configuration from pyproject.toml.
        
    Raises:
        FileNotFoundError: If pyproject.toml cannot be found
        KeyError: If the project section is missing
        tomllib.TOMLDecodeError: If the TOML file is invalid
    """
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path}. "
            "Are you running from the correct directory?"
        )
    
    with open(pyproject_path, "rb") as f:
        try:
            pyproject = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise tomllib.TOMLDecodeError(
                f"Failed to parse {pyproject_path}: {str(e)}"
            ) from e
            
        if "project" not in pyproject:
            raise KeyError(
                f"No [project] section found in {pyproject_path}"
            )
            
        return pyproject["project"]

def print_response(data: Dict[str, Any]) -> None:
    """Print formatted response data."""
    console = get_console()
    console.print()
    console.print(Panel.fit(
        console.print_json(data=data, ensure_ascii=False),
        title="Response Details",
        border_style="cyan"
    ))
    console.print()

def create_terminal_table(terminals: list) -> Table:
    """Create a table for terminal listing."""
    table = Table(show_header=True, header_style="white", border_style="bright_black")
    table.add_column("PATH", style="cyan")
    table.add_column("PORT", justify="center", style="cyan")
    table.add_column("PID", justify="right", style="cyan")
    table.add_column("API URL", style="blue")
    
    for term in terminals:
        api_url = f"{get_api_base()}/terminals/{term['path']}"
        table.add_row(term['path'], str(term['port']), str(term['pid']), api_url)
    
    return table 