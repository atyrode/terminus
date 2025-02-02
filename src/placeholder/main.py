""" Main entry point for the application. """

from typing import Any

from console import console


async def main(
    source: str,
) -> Any:
    """
    This is the main entry point for the application. This is where the core logic
    of the application starts.

    Parameters
    ----------
    source : str
        The source to analyze, which can be a URL (for a Git repository) or a local directory path.

    Returns
    -------
    Any
        The resulting information from your implementation, to be used by the CLI or the API.
    """

    console.log(f"New query: '{source}'")

    return "This website was generated with the default values of the template! It does not do anything by default."
