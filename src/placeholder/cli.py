""" Command-line interface for the application. """

# pylint: disable=no-value-for-parameter

import asyncio

import click

from placeholder.main import main


@click.command()
@click.argument("source", type=str, default=".")
def cli(source: str):
    """
    Main entry point for the CLI. This function is called when the CLI is run as a script.

    It calls the async main function to run the command.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.
    """

    # Main entry point for the CLI. This function is called when the CLI is run as a script.
    asyncio.run(_async_cli(source))


async def _async_cli(
    source: str,
) -> None:
    """
    Analyze a directory or repository and create a text dump of its contents.

    This command analyzes the contents of a specified source directory or repository, applies custom include and
    exclude patterns, and generates a text summary of the analysis and prints it to the console.

    Parameters
    ----------
    source : str
        The source directory or repository to analyze.

    Raises
    ------
    Abort
        If there is an error during the execution of the command, this exception is raised to abort the process.
    """
    try:

        result = main(source)

        click.echo("Analysis complete!\nSummary:")
        click.echo(result)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
