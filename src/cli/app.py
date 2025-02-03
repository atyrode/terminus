"""Main CLI application setup."""

from dotenv import load_dotenv
load_dotenv()

import click

from .formatting import RichGroup, RichVersionOption
from .commands import create, list, delete, start
from .utils import load_project_config

# Load project configuration
config = load_project_config()

@click.group(cls=RichGroup)
@click.option("--version", cls=RichVersionOption)
def cli():
    """%(description)s""" % config

# Register commands
cli.add_command(create)
cli.add_command(list)
cli.add_command(delete)
cli.add_command(start)

if __name__ == "__main__":
    cli() 