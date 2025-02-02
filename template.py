#!/usr/bin/env python3
"""
Template configuration and setup script.
This script combines template configuration and project setup into a single tool.
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from rich.prompt import Confirm, Prompt

from src.console import box, console, header, rule


@dataclass
class TemplateConfig:
    """Template configuration with default values."""

    ############### Start of manual user config ###############

    # Repository
    author: str = field(default="Your Name")
    author_email: str = field(default="your.email@example.com")
    author_social: str = field(default="https://your-social-link.com")
    author_nickname: str = field(default="@your_nickname")
    security_email: str = field(default="your.email@example.com")
    github_username: str = field(default="your_github_username")
    github_repository: str = field(default="your_github_repository")

    # Package
    package_name: str = field(default="your_package_name")
    package_version: str = field(default="0.1.0")
    package_description: str = field(default="A brief description of your package")
    package_keywords: str = field(
        default="AI tools, LLM integration, Context, Prompt, Git workflow, Git repository, Git automation, prompt-friendly"
    )

    # Project
    project_name: str = field(default="Projectname")
    project_url: str = field(default="https://your-project-url.com")
    project_domain: str = field(default="your-project-domain.com")
    chrome_extension_url: str = field(default="https://chromewebstore.google.com/detail/example")
    firefox_extension_url: str = field(default="https://addons.mozilla.org/firefox/addon/example")
    edge_extension_url: str = field(default="https://microsoftedge.microsoft.com/addons/detail/example")
    discord_invite: str = field(default="https://discord.com/invite/example")
    project_description: str = field(default="A description of your project, will appear at the top of the README.md")
    project_badges: str = field(
        default="""
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/example.svg)](https://badge.fury.io/py/example)
[![GitHub stars](https://img.shields.io/github/stars/example?style=social)](https://github.com/example)
[![Downloads](https://pepy.tech/badge/example)](https://pepy.tech/project/example)
""".strip()
    )
    project_features: str = field(default="Describe the features of the project")
    project_stack: str = field(default="Stack used for the project")
    project_command_line_usage: str = field(default="Describes the steps to use the command line tool")
    project_python_package_usage: str = field(default="Describes the steps to use the Python package")
    project_self_host_steps: str = field(default="Describes the steps to self-host the project")
    project_extension_informations: str = field(
        default="This flavor text will appear in the README.md file under the extension badges"
    )

    ############### End of manual user config ###############

    # Template README content
    readme_template: str = field(
        default="""# {{ project_name }}

[![Image](./docs/frontpage.png "{{ project_name }} main page")]({{ project_url }})

{{ project_badges }}

[![Discord](https://dcbadge.limes.pink/api/server/{{ discord_invite }})]({{ discord_invite }})

{{ project_description }}

{{ project_url }} · [Chrome Extension]({{ chrome_extension_url }}) · [Firefox Add-on]({{ firefox_extension_url }})

## 🚀 Features

{{ project_features }}

## 📦 Installation

``` bash
pip install {{ package_name }}
```

## 🧩 Browser Extension Usage

<!-- markdownlint-disable MD033 -->
<a href="{{ chrome_extension_url }}" target="_blank" title="Get {{ project_name }} Extension from Chrome Web Store"><img height="48" src="https://github.com/user-attachments/assets/20a6e44b-fd46-4e6c-8ea6-aad436035753" alt="Available in the Chrome Web Store" /></a>
<a href="{{ firefox_extension_url }}" target="_blank" title="Get {{ project_name }} Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/c0e99e6b-97cf-4af2-9737-099db7d3538b" alt="Get The Add-on for Firefox" /></a>
<a href="{{ edge_extension_url }}" target="_blank" title="Get {{ project_name }} Extension from Edge Add-ons"><img height="48" src="https://github.com/user-attachments/assets/204157eb-4cae-4c0e-b2cb-db514419fd9e" alt="Get from the Edge Add-ons" /></a>
<!-- markdownlint-enable MD033 -->

{{ project_extension_informations }}

## 💡 Command line usage

{{ project_command_line_usage }}

## 🐛 Python package usage

{{ project_python_package_usage }}

## 🌐 Self-host

1. Build the image:

   ``` bash
   docker build -t {{ package_name }} .
   ```

2. Run the container:

   ``` bash
   docker run -d --name {{ package_name }} -p 8000:8000 {{ package_name }}
   ```

The application will be available at `http://localhost:8000`.

If you are hosting it on a domain, you can specify the allowed hostnames via env variable `ALLOWED_HOSTS`.

   ```bash
   # Default: "{{ project_domain }}, *.{{ project_domain }}, localhost, 127.0.0.1".
   ALLOWED_HOSTS="example.com, localhost, 127.0.0.1"
   ```

## ✔️ Contributing to {{ project_name }}

### Non-technical ways to contribute

- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/{{ github_username }}/{{ github_repository }}/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like {{ project_name }}, please share it with your friends, colleagues, and on social media. This will help us grow the community and make {{ project_name }} even better.
- **Use {{ project_name }}**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/{{ github_username }}/{{ github_repository }}/issues/new) on GitHub or by reaching out to us on [Discord]({{ discord_invite }}).

### Technical ways to contribute

{{ project_name }} aims to be friendly for first time contributors, with a simple python and html codebase. If you need any help while working with the code, reach out to us on [Discord]({{ discord_invite }}). For detailed instructions on how to make a pull request, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com) - Frontend
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com) - HTML templating
- [apianalytics.dev](https://www.apianalytics.dev) - Simple Analytics

## Project Growth

[![Star History Chart](https://api.star-history.com/svg?repos={{ github_username }}/{{ github_repository }}&type=Date)](https://star-history.com/#{{ github_username }}/{{ github_repository }}&Date)
"""
    )

    # Files to be processed
    templated_files: list[str] = field(
        default_factory=lambda: [
            "README.md",
            "pyproject.toml",
            "SECURITY.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "src/static/robots.txt",
            "src/placeholder/__init__.py",
            "src/server/query_processor.py",
            "src/server/main.py",
            # Note: In .jinja files, we use the {!{ ... }!} syntax instead of {{ ... }}.
            "src/server/templates/base.jinja",
            "src/server/templates/components/footer.jinja",
            "src/server/templates/components/navbar.jinja",
            "src/server/templates/api.jinja",
        ]
    )

    def interactive_setup(self) -> None:
        """Interactive configuration setup."""
        header("Interactive Configuration Setup")
        console.print("[info]Press Enter to use the default value shown in brackets[/info]\n")

        self.author = Prompt.ask("Author name", default=self.author, show_default=True)
        self.author_email = Prompt.ask("Author email", default=self.author_email, show_default=True)
        self.github_username = Prompt.ask("GitHub username", default=self.github_username, show_default=True)
        self.github_repository = Prompt.ask("GitHub repository", default=self.github_repository, show_default=True)
        self.package_name = Prompt.ask("Package name", default=self.package_name, show_default=True)
        self.project_name = Prompt.ask("Project name", default=self.project_name, show_default=True)
        self.package_description = Prompt.ask(
            "Project description", default=self.package_description, show_default=True
        )
        self.project_url = Prompt.ask("Project URL", default=self.project_url, show_default=True)


class TemplateProcessor:
    def __init__(self, config: TemplateConfig, auto_yes: bool = False):
        self.config = config
        self.auto_yes = auto_yes

    def process_files(self) -> None:
        """Process all template files."""
        header("Processing template files")

        # Handle README.md
        if Path("README.md").exists():
            if self.auto_yes or Confirm.ask("Would you like to use the template README instead of the current one?"):
                Path("README.md").rename("README.template.md")
                console.print("[warn]Backed up existing README.md to README.template.md[/warn]")
                # Create new README from template
                Path("README.md").write_text(self.config.readme_template)
                console.print("[ok]✓ Created[/ok] new README.md from template")

        for file_path in self.config.templated_files:
            path = Path(file_path)
            if not path.exists():
                console.print(f"[danger]✗ File not found:[/danger] {file_path}")
                continue

            console.print(f"[ok]Processing[/ok] {file_path}")
            self._process_file(path)

        # Rename placeholder directory
        placeholder_dir = Path("src/placeholder")
        if placeholder_dir.exists():
            new_dir = Path(f"src/{self.config.package_name}")
            placeholder_dir.rename(new_dir)
            console.print(f"[ok]✓ Renamed[/ok] {placeholder_dir} to {new_dir}")

            # Update imports in all Python files
            for py_file in Path("src").rglob("*.py"):
                self._update_imports(py_file)

    def _process_file(self, file_path: Path) -> None:
        """Process a single template file."""
        content = file_path.read_text()

        # Handle Jinja templates
        if file_path.suffix == ".jinja":
            pattern = r"{\!{\s*(\w+)\s*}\!}"
            repl = lambda m: getattr(self.config, m.group(1), m.group(0))
        else:
            pattern = r"{{\s*(\w+)\s*}}"
            repl = lambda m: getattr(self.config, m.group(1), m.group(0))

        content = re.sub(pattern, repl, content)
        file_path.write_text(content)

    def _update_imports(self, file_path: Path) -> None:
        """Update Python imports in a file."""
        content = file_path.read_text()
        replacements = [
            (r"from placeholder\.", f"from {self.config.package_name}."),
            (r"import placeholder", f"import {self.config.package_name}"),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        file_path.write_text(content)


class ProjectSetup:
    def __init__(self, auto_yes: bool = False):
        self.auto_yes = auto_yes

    def setup_environment(self) -> None:
        """Set up the development environment."""
        header("Setting up development environment")

        # Create virtual environment
        if not Path("venv").exists():
            console.print("[warn]Creating virtual environment...[/warn]")
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

        # Install dependencies using pip
        with console.status("[yellow]Installing dependencies...[/yellow]", spinner="dots"):
            if Path("requirements-dev.txt").exists():
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
                    check=True,
                    capture_output=True,
                )
            elif Path("requirements.txt").exists():
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True, capture_output=True
                )

            console.print("[ok]✓ Installed dependencies[/ok]")

        header("Installing pre-commit hooks")

        # Install pre-commit hooks
        if Path(".pre-commit-config.yaml").exists():
            if self.auto_yes or Confirm.ask("Would you like to install pre-commit hooks?"):
                with console.status("[yellow]Installing pre-commit hooks...[/yellow]", spinner="dots"):
                    # Ensure pre-commit is installed in the virtual environment
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "pre-commit"], check=True, capture_output=True
                    )
                    # Use the full path to pre-commit in the virtual environment
                    subprocess.run(
                        [f"{sys.executable}", "-m", "pre_commit", "install"], check=True, capture_output=True
                    )
                    console.print("[ok]✓ Pre-commit hooks installed successfully[/ok]")
            else:
                console.print("[yellow]Skipping pre-commit hooks installation.[/yellow]")


def print_config(config: TemplateConfig) -> None:
    """Print the current configuration."""
    header("Template Configuration")
    console.print(
        box(
            f"""[bold underline]Project Details:[/bold underline]
  [cyan]Project Name:[/cyan] {config.project_name}
  [cyan]Package Name:[/cyan] {config.package_name}
  [cyan]Description:[/cyan] {config.package_description}

[bold underline]Author Details:[/bold underline]
  [cyan]Author:[/cyan] {config.author}
  [cyan]GitHub:[/cyan] {config.github_username}

[bold]URLs:[/bold]
  [cyan]Repository:[/cyan] {config.github_repository}
  [cyan]Project URL:[/cyan] {config.project_url}

  ... (more in template.py)""",
            title="Configuration Summary",
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Template configuration and setup tool")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-accept all prompts")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run interactive configuration setup")
    args = parser.parse_args()

    try:
        # Create configuration with default values
        config = TemplateConfig()

        # Run interactive setup if requested
        if args.interactive:
            config.interactive_setup()

        print_config(config)

        if not args.yes and not Confirm.ask("\nWould you like to apply this configuration?"):
            console.print("[yellow]Template application cancelled.[/yellow]")
            return

        # Set up development environment
        setup = ProjectSetup(args.yes)
        setup.setup_environment()

        # Process template files
        processor = TemplateProcessor(config, args.yes)
        processor.process_files()

        header("Finished!", style="ok")

        console.print("[info]You can now run the project with the following commands:[/info]")
        console.print("\ncd src && python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000\n")

        rule()

    except Exception as e:
        console.print(f"[danger]Error:[/danger] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
