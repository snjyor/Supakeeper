"""
Command-line interface for Supakeeper.

Provides commands for running keep-alive checks and viewing status.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from supakeeper import __version__
from supakeeper.config import Config
from supakeeper.keeper import SupaKeeper
from supakeeper.scheduler import create_scheduler

app = typer.Typer(
    name="supakeeper",
    help="Keep your Supabase projects alive and prevent them from being paused.",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"Supakeeper v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Supakeeper - Keep your Supabase projects alive."""
    pass


@app.command()
def run(
    once: bool = typer.Option(
        False,
        "--once",
        "-1",
        help="Run once and exit (default: run as daemon)",
    ),
    no_immediate: bool = typer.Option(
        False,
        "--no-immediate",
        help="Don't run immediately in daemon mode, wait for first scheduled time",
    ),
) -> None:
    """
    Run Supakeeper to keep your Supabase projects active.
    
    By default, runs as a daemon that periodically pings all configured projects.
    Use --once to run a single check and exit.
    
    Configuration is loaded from .env file or environment variables.
    """
    try:
        cfg = Config.load()
        
        # Validate configuration
        errors = cfg.validate()
        for error in errors:
            if "Warning" in error:
                console.print(f"[yellow]⚠ {error}[/]")
            else:
                console.print(f"[red]✗ {error}[/]")
        
        if any("No projects" in e for e in errors):
            console.print("\n[red]No projects configured.[/]")
            console.print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
            console.print("See env.example for configuration examples.")
            raise typer.Exit(1)
        
        scheduler = create_scheduler(cfg)
        
        if once:
            success, failed = scheduler.run_once()
            raise typer.Exit(1 if failed > 0 else 0)
        else:
            scheduler.run_daemon(run_immediately=not no_immediate)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show status of configured Supabase projects."""
    try:
        cfg = Config.load()
        keeper = SupaKeeper(cfg)
        status_info = keeper.get_status()
        
        console.print()
        console.print("[bold cyan]Supakeeper Status[/]")
        console.print()
        
        if not status_info["projects"]:
            console.print("[yellow]No projects configured.[/]")
            console.print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
            return
        
        # Create status table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Project", style="cyan")
        table.add_column("URL")
        table.add_column("Status", justify="center")
        
        for project in status_info["projects"]:
            status_icon = "[green]✓ Enabled[/]" if project["enabled"] else "[dim]○ Disabled[/]"
            # Truncate URL for display
            url = project["url"]
            if len(url) > 40:
                url = url[:37] + "..."
            table.add_row(project["name"], url, status_icon)
        
        console.print(table)
        console.print()
        console.print(f"Total projects: {status_info['total_projects']}")
        console.print(f"Enabled: {status_info['enabled_projects']}")
        console.print(f"Check interval: every {status_info['interval_hours']} hours")
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def ping(
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Ping a specific project by name",
    ),
) -> None:
    """
    Ping Supabase projects to keep them active.
    
    This is equivalent to 'run --once' but with simpler output.
    """
    try:
        cfg = Config.load()
        
        # Filter to specific project if requested
        if project:
            matching = [p for p in cfg.projects if p.name.lower() == project.lower()]
            if not matching:
                console.print(f"[red]Project '{project}' not found[/]")
                console.print("Available projects:")
                for p in cfg.projects:
                    console.print(f"  - {p.name}")
                raise typer.Exit(1)
            cfg.projects = matching
        
        keeper = SupaKeeper(cfg)
        results = keeper.ping_all()
        
        success = sum(1 for r in results if r.success)
        failed = len(results) - success
        
        if failed > 0:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def validate() -> None:
    """Validate the configuration from .env file."""
    try:
        cfg = Config.load()
        errors = cfg.validate()
        
        if not errors:
            console.print("[green]✓ Configuration is valid[/]")
            console.print(f"  Found {len(cfg.projects)} project(s)")
            for p in cfg.projects:
                console.print(f"    - {p.name}: {p.url[:40]}...")
            raise typer.Exit(0)
        
        for error in errors:
            if "Warning" in error:
                console.print(f"[yellow]⚠ {error}[/]")
            else:
                console.print(f"[red]✗ {error}[/]")
        
        # Exit with error only for actual errors, not warnings
        has_errors = any("Warning" not in e for e in errors)
        raise typer.Exit(1 if has_errors else 0)
        
    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
