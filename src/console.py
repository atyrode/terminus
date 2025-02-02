"""This module contains methods to interact with the logging system."""

from os import name, system

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.traceback import install

custom_theme = Theme(
    {
        "success": "bold green",
        "ok": "bold green",
        "info": "bold cyan",
        "warning": "bold yellow",
        "warn": "bold yellow",
        "danger": "bold red",
        "ko": "bold red",
        "error": "bold red",
        "rule.line": "bright_black",
        "dark": "bright_black",
    }
)

console = Console(theme=custom_theme)

# Prevents the clumping of identical logs' timestamps together
# pylint: disable=protected-access
console._log_render.omit_repeated_times = False

install()


def header(title: str, *args, **kwargs):
    """Display a header with the given title.

    Parameters
    ----------
    title : str
        The title to display in the header
    *args
        Additional arguments passed to console.rule
    **kwargs
        Additional keyword arguments passed to console.rule
    """
    console.rule(characters=" ")
    console.rule(f"[dark]{title}", *args, **kwargs)
    console.rule(characters=" ")


def clear_screen():
    """Clears the console screen."""
    system("cls" if name == "nt" else "clear")


def rule(spaces: int = 0):
    """Display a horizontal rule with optional spacing.

    Parameters
    ----------
    spaces : int
        Number of blank lines to add before and after the rule, by default 0
    """
    for _ in range(spaces):
        console.out("")
    console.rule()
    for _ in range(spaces):
        console.out("")


def box(content: str, title: str = None):
    """Create a boxed panel containing the given content.

    Parameters
    ----------
    content : str
        The content to display in the box
    title : str
        The title of the box, by default None

    Returns
    -------
    Panel
        A rich Panel object containing the content
    """
    return Panel(content, title=title)
