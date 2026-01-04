"""
Scheduler for periodic keep-alive operations.

Provides both daemon mode (continuous running) and single-run mode.
"""

from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

import schedule

from supakeeper.config import Config
from supakeeper.keeper import SupaKeeper
from supakeeper.logger import get_logger


class Scheduler:
    """Schedule and run keep-alive operations."""
    
    def __init__(self, keeper: SupaKeeper) -> None:
        """
        Initialize scheduler.
        
        Args:
            keeper: SupaKeeper instance to use for pings
        """
        self.keeper = keeper
        self.logger = get_logger()
        self._running = False
        self._next_run: Optional[datetime] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info("Received shutdown signal, stopping scheduler...")
        self._running = False
    
    def _run_job(self) -> None:
        """Execute the keep-alive job."""
        self.logger.info("=" * 50)
        self.logger.info(f"Running scheduled keep-alive at {datetime.now()}")
        
        success, failed = self.keeper.run_once()
        
        # Calculate next run time
        interval_hours = self.keeper.config.interval_hours
        self._next_run = datetime.now() + timedelta(hours=interval_hours)
        
        self.logger.info(f"Next run scheduled for: {self._next_run}")
    
    def run_daemon(self, run_immediately: bool = True) -> None:
        """
        Run the scheduler as a daemon (continuous mode).
        
        Args:
            run_immediately: Whether to run immediately on start
        """
        interval_hours = self.keeper.config.interval_hours
        
        self.logger.info(f"Starting Supakeeper daemon (interval: {interval_hours} hours)")
        
        if run_immediately:
            self._run_job()
        
        # Schedule recurring job
        schedule.every(interval_hours).hours.do(self._run_job)
        
        self._running = True
        
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        
        self.logger.info("Scheduler stopped")
    
    def run_once(self) -> tuple[int, int]:
        """
        Run a single keep-alive cycle.
        
        Returns:
            Tuple of (success_count, failure_count)
        """
        return self.keeper.run_once()


def create_scheduler(config: Optional[Config] = None) -> Scheduler:
    """
    Create a scheduler with the given or default configuration.
    
    Args:
        config: Optional configuration. If None, loads from default sources.
        
    Returns:
        Configured Scheduler instance
    """
    keeper = SupaKeeper(config)
    return Scheduler(keeper)

