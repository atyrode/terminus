"""CLI commands for terminus."""

import os
import sys
import traceback

import click
import httpx
from rich.panel import Panel

from .utils import get_console, get_api_base, print_response, create_terminal_table
from .formatting import RichCommand

console = get_console()

def check_server_health() -> bool:
    """Check if the terminal gateway server is running by calling the health endpoint."""
    try:
        response = httpx.get(f"{get_api_base()}/health", timeout=2.0)
        if response.status_code == 200:
            return True
        console.print(f"[yellow]Warning:[/] Server returned status code {response.status_code}")
        return False
    except httpx.ConnectError:
        console.print("[yellow]Warning:[/] Could not connect to server")
        return False
    except httpx.TimeoutError:
        console.print("[yellow]Warning:[/] Server health check timed out")
        return False
    except Exception as e:
        console.print(f"[yellow]Warning:[/] Unexpected error checking server health: {str(e)}")
        return False

def ensure_server_running():
    """Ensure the server is running, exit with helpful message if not."""
    if not check_server_health():
        console.print("[red]Error:[/] Terminal gateway server is not running")
        console.print("Please start the server first with: [green]terminus start[/]")
        sys.exit(1)

def handle_error(e: Exception, context: str):
    """Handle errors with full traceback."""
    console.print(f"\n[red]Error {context}:[/] {str(e)}")
    console.print("\n[yellow]Full traceback:[/]")
    console.print(traceback.format_exc())
    sys.exit(1)

@click.command(cls=RichCommand)
@click.argument("path")
@click.option("-c", "--command", help="Command to run in terminal", default=os.getenv("DEFAULT_COMMAND", "bash"))
def create(path: str, command: str = "bash"):
    """Create a new terminal instance."""
    ensure_server_running()
    try:
        response = httpx.post(
            f"{get_api_base()}/api/terminals/",
            json={"path": path, "command": command},
            follow_redirects=False,
            timeout=2.0
        )
        response.raise_for_status()
        terminal_data = response.json()
        
        api_url = f"{get_api_base()}/terminals/{path}"
        console.out(api_url)
            
    except httpx.TimeoutException:
        console.print("[red]Error:[/] Failed to create terminal - timeout")
        sys.exit(1)
    except httpx.HTTPError as e:
        handle_error(e, "creating terminal")

@click.command(cls=RichCommand)
def list():
    """List all active terminals."""
    ensure_server_running()
    try:
        response = httpx.get(f"{get_api_base()}/api/terminals/", follow_redirects=True)
        response.raise_for_status()
        terminals = response.json()
        
        if not terminals:
            console.print(Panel("No active terminal sessions found.", title="Status"))
            return
            
        table = create_terminal_table([{"path": path, **info} for path, info in terminals.items()])
        console.print(table)
    except httpx.HTTPError as e:
        handle_error(e, "listing terminals")

@click.command(cls=RichCommand)
@click.argument("path")
def delete(path: str):
    """Delete a terminal instance."""
    ensure_server_running()
    try:
        console.print(f"Deleting terminal at {path}...")
        response = httpx.delete(f"{get_api_base()}/api/terminals/{path.lstrip('/')}/")
        response.raise_for_status()
        console.print("[green]Terminal deleted successfully[/]")
    except httpx.HTTPError as e:
        handle_error(e, "deleting terminal")

@click.command(cls=RichCommand)
@click.option("-p", "--port", help="Port to run the gateway on", type=int)
@click.option("-h", "--host", help="Host interface to bind to")
@click.option("-d", "--debug", is_flag=True, help="Enable debug mode")
def start(port: int | None = None, host: str | None = None, debug: bool = False):
    """Start the terminal gateway server."""
    try:
        import uvicorn
        from server.main import app
        from config import config

        # Override config with CLI arguments if provided
        if port is not None:
            config.port = port
        if host is not None:
            config.host = host

        console.print(f"Starting server on {config.host}:{config.port}")
        uvicorn.run(
            app, 
            host=config.host,
            port=config.port,
            access_log=True,  # Enable FastAPI's default access logging
            log_level="debug" if debug else "info"
        )
    except Exception as e:
        handle_error(e, "starting server")

@click.command(cls=RichCommand)
@click.argument("path")
def logs(path: str):
    """View logs for a terminal instance."""
    ensure_server_running()
    try:
        response = httpx.get(f"{get_api_base()}/api/terminals/{path.lstrip('/')}/logs/", follow_redirects=True)
        response.raise_for_status()
        logs_data = response.json()
        
        if not logs_data.get("logs"):
            console.print(Panel("No logs found for this terminal.", title="Logs"))
            return
            
        console.print(Panel(logs_data["logs"], title=f"Logs for terminal: {path}"))
    except httpx.HTTPError as e:
        handle_error(e, "fetching logs") 