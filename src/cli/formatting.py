"""Rich formatting classes for the CLI."""

from typing import Optional, Any, Dict
from io import StringIO
import sys

import click
from click.formatting import HelpFormatter, term_len
from rich.console import Console

from src.console import custom_theme

class RichClickException(click.ClickException):
    """Custom exception class that uses Rich for styling."""
    def show(self, file=None) -> None:
        if file is None:
            file = sys.stderr
            
        console = Console(file=file, force_terminal=True)
        console.print(f"[red]Error:[/] {self.format_message()}")

class RichUsageError(click.UsageError):
    """Custom usage error that uses Rich for styling."""
    def __init__(self, message: str, ctx: click.Context | None = None, param: click.Parameter | None = None) -> None:
        super().__init__(message, ctx)
        self.message = message
        self.param = param  # Store the parameter that caused the error

    def show(self, file=None) -> None:
        if file is None:
            file = sys.stderr
            
        console = Console(file=file, force_terminal=True)
        
        if self.ctx is not None:
            # Format usage with consistent styling
            usage = self.ctx.get_usage()
            # Remove the "Usage: " prefix from get_usage() result
            usage = usage.replace("Usage: ", "", 1)
            # Split into command parts for custom styling
            parts = usage.split(" ", 2)
            if len(parts) > 1:
                if len(parts) == 3:
                    prog, subcmd, args = parts
                    # Style the command path with terminus in white, subcommand in green
                    styled_usage = f"Usage: [green]{prog} {subcmd}[/] [cyan]{args}[/]"
                else:
                    prog, args = parts
                    # Make sure the first word after prog is green (e.g., 'create')
                    args_parts = args.split(" ", 1)
                    if len(args_parts) > 1:
                        cmd, remaining = args_parts
                        styled_usage = f"Usage: {prog} [green]{cmd}[/] [cyan]{remaining}[/]"
                    else:
                        styled_usage = f"Usage: {prog} [cyan]{args}[/]"
            else:
                styled_usage = f"Usage: [cyan]{usage}[/]"
            
            console.print(styled_usage)
            
            if self.ctx.command.get_help_option(self.ctx) is not None:
                # Style help message with terminus in green and command in cyan, and "Try"/"for help" in gray
                console.print(f"\n[{custom_theme.styles['dark']}]Try[/] '[green]{self.ctx.command_path}[/] [cyan]--help[/]' [{custom_theme.styles['dark']}]for help.[/]\n")
        
        # Get the properly formatted error message from Click
        error_msg = self.format_message()
        console.print(f"[red]Error:[/] {error_msg}")

    def format_message(self) -> str:
        """Format the error message using Click's standard formatting."""
        if self.param is not None:
            if isinstance(self.param, click.Argument):
                return f"Missing argument '[{custom_theme.styles['info']}]{self.param.name.upper()}[/]'."
            return f"Missing parameter: {self.param.name}"
        return str(self)

class RichHelpFormatter(HelpFormatter):
    """Custom help formatter that uses Rich for styling."""
    
    def __init__(self, indent_increment=2, width=None, max_width=None):
        super().__init__(indent_increment, width, max_width)
        self._current_style = {}
        self._last_write_empty = False
    
    def write_usage(self, prog: str, args: str = "", prefix: Optional[str] = None) -> None:
        if prefix is None:
            prefix = "Usage: "
        
        styled_prog = f"[{custom_theme.styles['ok']}]{prog}[/]"
        
        if args:
            args = args.replace("COMMAND", f"[{custom_theme.styles['info']}]COMMAND[/]")
            args = args.replace("OPTIONS", f"[{custom_theme.styles['info']}]OPTIONS[/]")
            args = args.replace("[OPTIONS]", f"[[{custom_theme.styles['info']}]OPTIONS[/]]")
            styled_args = f" {args}"
        else:
            styled_args = ""
        
        usage_prefix = f"[{custom_theme.styles['dark']}]{prefix}[/]{styled_prog}{styled_args}"
        self.write(f"{usage_prefix}\n")

    def write_heading(self, heading: str) -> None:
        if not self._last_write_empty:
            self.write("\n")
        self.write(f"[{custom_theme.styles['warning']}]{heading}:[/]\n")
        self._last_write_empty = False
    
    def write_paragraph(self) -> None:
        if not self._last_write_empty:
            self.write("\n")
            self._last_write_empty = True

    def write_text(self, text: str) -> None:
        if text:
            if not any(tag in text for tag in ["[", "]"]):
                text = f"[{custom_theme.styles['dark']}]{text}[/]"
            self.write(f"{text}\n")
            self._last_write_empty = False
        else:
            if not self._last_write_empty:
                self.write("\n")
                self._last_write_empty = True

    def write_dl(self, rows, col_max=20, col_spacing=2):
        """Write a definition list with rich formatting."""
        for name, desc in rows:
            if isinstance(name, tuple):
                name = ", ".join(name)
            
            if name.startswith("-"):
                styled_name = f"[{custom_theme.styles['info']}]{name}[/]"
            else:
                styled_name = f"[{custom_theme.styles['info']}]{name}[/]"
            
            if "[default:" in desc:
                desc = desc.replace("[default:", f"[{custom_theme.styles['dark']}][default:").replace("]", "][/]")
            if "[required]" in desc:
                desc = desc.replace("[required]", f"[{custom_theme.styles['danger']}][required][/]")
            if "[env var:" in desc:
                desc = desc.replace("[env var:", f"[{custom_theme.styles['info']}][env var:").replace("]", "][/]")
            if not any(tag in desc for tag in ["[", "]"]):
                desc = f"[{custom_theme.styles['dark']}]{desc}[/]"
            
            name_length = term_len(name)
            indent = " " * (col_max - name_length if name_length < col_max else 0)
            self.write(f"  {styled_name}{indent}  {desc}\n")
            self._last_write_empty = False

class RichCommand(click.Command):
    """Custom command class that uses RichHelpFormatter."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('context_settings', {})
        kwargs['context_settings'].setdefault('color', True)
        super().__init__(*args, **kwargs)
    
    def get_help(self, ctx: click.Context) -> str:
        formatter = RichHelpFormatter()
        self.format_help(ctx, formatter)
        
        buffer = StringIO()
        tmp_console = Console(file=buffer, force_terminal=True)
        
        tmp_console.print(formatter.getvalue(), highlight=False, soft_wrap=True)
        
        return buffer.getvalue()

    def make_context(self, info_name, args, parent=None, **extra):
        """Override to use our custom exceptions."""
        try:
            return super().make_context(info_name, args, parent, **extra)
        except click.UsageError as e:
            # Pass through the parameter information
            raise RichUsageError(str(e), e.ctx, getattr(e, 'param', None))
        except click.ClickException as e:
            raise RichClickException(str(e))

class RichGroup(click.Group):
    """Custom group class that uses RichHelpFormatter."""
    
    def __init__(self, name: Optional[str] = None, commands: Optional[Dict[str, click.Command]] = None, **attrs: Any):
        # Remove cls from attrs if it exists to avoid passing it to the superclass
        attrs.setdefault('context_settings', {})
        attrs['context_settings'].setdefault('color', True)
        super().__init__(name=name, commands=commands, **attrs)
    
    def command(self, *args: Any, **kwargs: Any) -> Any:
        """Override command decorator to use RichCommand by default."""
        kwargs.setdefault('cls', RichCommand)
        return super().command(*args, **kwargs)
    
    def group(self, *args: Any, **kwargs: Any) -> Any:
        """Override group decorator to use RichGroup by default for subgroups."""
        kwargs.setdefault('cls', RichGroup)
        return super().group(*args, **kwargs)
    
    def get_help(self, ctx: click.Context) -> str:
        formatter = RichHelpFormatter()
        self.format_help(ctx, formatter)
        
        buffer = StringIO()
        tmp_console = Console(file=buffer, force_terminal=True)
        
        tmp_console.print(formatter.getvalue(), highlight=False, soft_wrap=True)
        
        return buffer.getvalue()

    def main(self, *args: Any, **kwargs: Any) -> Any:
        """Override main to handle errors with rich formatting."""
        try:
            return super().main(*args, **kwargs)
        except click.UsageError as e:
            console = Console(stderr=True)
            if e.ctx is not None:
                console.print(f"{e.ctx.get_usage()}")
                console.print("\nTry", f"[green]{e.ctx.command_path} --help[/]", "for help.\n")
            console.print(f"[red]Error:[/] {str(e)}")
            sys.exit(e.exit_code)
        except click.ClickException as e:
            console = Console(stderr=True)
            console.print(f"[red]Error:[/] {str(e)}")
            sys.exit(e.exit_code)

class RichVersionOption(click.Option):
    """Custom version option that uses Rich for styling."""
    
    def __init__(self, param_decls=None, **kwargs):
        if not param_decls:
            param_decls = ["--version"]
            
        super().__init__(
            param_decls,
            is_flag=True,
            is_eager=True,
            expose_value=False,
            callback=self.version_callback,
            help="Show the version and exit.",
            **kwargs
        )
    
    def version_callback(self, ctx: click.Context, param: click.Parameter, value: bool) -> None:
        if not value or ctx.resilient_parsing:
            return
        
        from .utils import get_console, load_project_config
        console = get_console()
        config = load_project_config()
        
        prog_name = ctx.find_root().info_name
        version = config["version"]
        console.print(f"[cyan]{prog_name}[/cyan] version [green]{version}[/green]")
        ctx.exit() 