"""
Logging configuration for Supakeeper.

Provides both file and console logging with rich formatting.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


# Custom theme for console output
SUPAKEEPER_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "project": "bold magenta",
    "timestamp": "dim",
})

console = Console(theme=SUPAKEEPER_THEME)


class SupakeeperLogger:
    """Custom logger for Supakeeper with file and console handlers."""
    
    def __init__(
        self,
        name: str = "supakeeper",
        log_file: str = "logs/supakeeper.log",
        log_level: str = "INFO",
        console_output: bool = True,
    ) -> None:
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_file: Path to log file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            console_output: Whether to output to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # Create log directory if needed
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler with detailed format
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler with rich formatting
        if console_output:
            rich_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
            rich_handler.setLevel(getattr(logging, log_level.upper()))
            self.logger.addHandler(rich_handler)
        
        self.console_output = console_output
    
    def info(self, message: str, project: Optional[str] = None) -> None:
        """Log info message."""
        if project:
            self.logger.info(f"[{project}] {message}")
        else:
            self.logger.info(message)
    
    def success(self, message: str, project: Optional[str] = None) -> None:
        """Log success message (info level with success styling)."""
        if project:
            msg = f"[{project}] ✓ {message}"
        else:
            msg = f"✓ {message}"
        self.logger.info(msg)
    
    def warning(self, message: str, project: Optional[str] = None) -> None:
        """Log warning message."""
        if project:
            self.logger.warning(f"[{project}] {message}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, project: Optional[str] = None) -> None:
        """Log error message."""
        if project:
            self.logger.error(f"[{project}] {message}")
        else:
            self.logger.error(message)
    
    def debug(self, message: str, project: Optional[str] = None) -> None:
        """Log debug message."""
        if project:
            self.logger.debug(f"[{project}] {message}")
        else:
            self.logger.debug(message)
    
    def print_banner(self) -> None:
        """Print the Supakeeper banner."""
        if self.console_output:
            console.print()
            console.print("[bold cyan]╔═══════════════════════════════════════════╗[/]")
            console.print("[bold cyan]║[/]   [bold green]Supakeeper[/]  -  Keep Supabase Alive      [bold cyan]║[/]")
            console.print("[bold cyan]╚═══════════════════════════════════════════╝[/]")
            console.print()
    
    def print_status(
        self,
        total: int,
        success: int,
        failed: int,
        next_run: Optional[datetime] = None,
    ) -> None:
        """Print status summary."""
        if self.console_output:
            console.print()
            console.print(f"[bold]Status Summary:[/]")
            console.print(f"  Total projects: {total}")
            console.print(f"  [green]Successful: {success}[/]")
            if failed > 0:
                console.print(f"  [red]Failed: {failed}[/]")
            if next_run:
                console.print(f"  Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print()


# Global logger instance
_logger: Optional[SupakeeperLogger] = None


def get_logger() -> SupakeeperLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = SupakeeperLogger()
    return _logger


def setup_logger(
    log_file: str = "logs/supakeeper.log",
    log_level: str = "INFO",
    console_output: bool = True,
) -> SupakeeperLogger:
    """Setup and return the global logger instance."""
    global _logger
    _logger = SupakeeperLogger(
        log_file=log_file,
        log_level=log_level,
        console_output=console_output,
    )
    return _logger

