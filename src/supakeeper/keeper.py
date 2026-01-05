"""
Core keep-alive logic for Supabase projects.

Performs health checks on Supabase projects to prevent them from
being paused due to inactivity.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from supakeeper.config import Config, ProjectConfig
from supakeeper.logger import get_logger, setup_logger
from supakeeper.notifier import Notifier


@dataclass
class PingResult:
    """Result of a keep-alive ping operation."""
    
    project_name: str
    success: bool
    message: str
    response_time_ms: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SupaKeeper:
    """
    Main class for keeping Supabase projects alive.
    
    Performs periodic health checks on configured Supabase projects
    to prevent them from being paused due to inactivity.
    """
    
    # Default table for health checks (Supabase auth.users is always available)
    AUTH_USERS_TABLE = "users"  # In auth schema
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize SupaKeeper.
        
        Args:
            config: Configuration object. If None, loads from default sources.
        """
        self.config = config or Config.load()
        self.logger = setup_logger(
            log_file=self.config.log_file,
            log_level=self.config.log_level,
            console_output=self.config.console_output,
        )
        # Initialize notifier if any notification channel is configured
        has_notifications = (
            self.config.webhook_url or 
            (self.config.telegram_bot_token and self.config.telegram_chat_id)
        )
        self.notifier = Notifier(
            webhook_url=self.config.webhook_url,
            telegram_bot_token=self.config.telegram_bot_token,
            telegram_chat_id=self.config.telegram_chat_id,
        ) if has_notifications else None
        self._clients: dict[str, Client] = {}
    
    def _get_client(self, project: ProjectConfig) -> Client:
        """Get or create Supabase client for a project."""
        if project.name not in self._clients:
            self._clients[project.name] = create_client(project.url, project.key)
        return self._clients[project.name]
    
    def _ping_project(self, project: ProjectConfig) -> PingResult:
        """
        Perform a keep-alive ping on a single project.
        
        This creates activity by:
        1. Attempting to query a health check table
        2. If table doesn't exist, uses a simple RPC call or auth check
        
        Args:
            project: Project configuration
            
        Returns:
            PingResult with status and timing information
        """
        self.logger.debug(f"Pinging project", project=project.name)
        start_time = time.time()
        
        for attempt in range(self.config.retry_attempts):
            try:
                client = self._get_client(project)
                
                # Strategy 1: Try to query a specific table if configured
                if project.table:
                    response = client.table(project.table).select("*").limit(1).execute()
                    elapsed_ms = (time.time() - start_time) * 1000
                    return PingResult(
                        project_name=project.name,
                        success=True,
                        message=f"Successfully queried table '{project.table}'",
                        response_time_ms=elapsed_ms,
                    )
                
                # Strategy 2: Query auth.users table (always exists in Supabase)
                try:
                    # Use the auth admin API to count users (generates DB activity)
                    # This queries the auth.users table which always exists
                    response = client.auth.admin.list_users(per_page=1)
                    elapsed_ms = (time.time() - start_time) * 1000
                    return PingResult(
                        project_name=project.name,
                        success=True,
                        message="Successfully queried auth.users table",
                        response_time_ms=elapsed_ms,
                    )
                except Exception as e:
                    self.logger.debug(f"Error querying auth.users: {e}", project=project.name)
                    # May not have admin access, try alternative approach
                    pass
                
                # Strategy 3: Use auth.get_user() - this always works if auth is enabled
                # This is a read-only operation that generates database activity
                try:
                    # Get session info (works even without a logged-in user)
                    client.auth.get_session()
                    elapsed_ms = (time.time() - start_time) * 1000
                    return PingResult(
                        project_name=project.name,
                        success=True,
                        message="Successfully checked auth session",
                        response_time_ms=elapsed_ms,
                    )
                except Exception:
                    pass
                
                # Strategy 4: Direct REST API health check via PostgREST
                # Query the root endpoint which always responds
                import httpx
                health_url = f"{project.url}/rest/v1/"
                headers = {
                    "apikey": project.key,
                    "Authorization": f"Bearer {project.key}",
                }
                with httpx.Client(timeout=30.0) as http_client:
                    response = http_client.get(health_url, headers=headers)
                    if response.status_code in (200, 401, 403):
                        # Any response means the project is active
                        elapsed_ms = (time.time() - start_time) * 1000
                        return PingResult(
                            project_name=project.name,
                            success=True,
                            message=f"Successfully pinged REST API (status: {response.status_code})",
                            response_time_ms=elapsed_ms,
                        )
                
                # If we got here, something unexpected happened
                raise Exception("All ping strategies failed")
                
            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {self.config.retry_delay}s...",
                        project=project.name,
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    elapsed_ms = (time.time() - start_time) * 1000
                    return PingResult(
                        project_name=project.name,
                        success=False,
                        message=f"Failed after {self.config.retry_attempts} attempts: {str(e)}",
                        response_time_ms=elapsed_ms,
                    )
        
        # Should never reach here, but just in case
        return PingResult(
            project_name=project.name,
            success=False,
            message="Unexpected error in ping logic",
        )
    
    def ping_all(self, parallel: bool = True) -> list[PingResult]:
        """
        Ping all enabled projects.
        
        Args:
            parallel: Whether to ping projects in parallel
            
        Returns:
            List of PingResult for each project
        """
        projects = self.config.get_enabled_projects()
        
        if not projects:
            self.logger.warning("No enabled projects to ping")
            return []
        
        self.logger.info(f"Starting keep-alive check for {len(projects)} project(s)")
        results: list[PingResult] = []
        
        if parallel and len(projects) > 1:
            # Use thread pool for parallel execution
            with ThreadPoolExecutor(max_workers=min(len(projects), 10)) as executor:
                futures = {
                    executor.submit(self._ping_project, project): project
                    for project in projects
                }
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    self._log_result(result)
        else:
            # Sequential execution
            for project in projects:
                result = self._ping_project(project)
                results.append(result)
                self._log_result(result)
        
        # Send notification if configured
        self._send_notification(results)
        
        return results
    
    def _log_result(self, result: PingResult) -> None:
        """Log a ping result."""
        if result.success:
            time_info = f" ({result.response_time_ms:.0f}ms)" if result.response_time_ms else ""
            self.logger.success(f"{result.message}{time_info}", project=result.project_name)
        else:
            self.logger.error(result.message, project=result.project_name)
    
    def _send_notification(self, results: list[PingResult]) -> None:
        """Send notification about ping results if notifier is configured."""
        if not self.notifier:
            return
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        # Only notify on failures or if this is a summary notification
        if failed_count > 0:
            failed_projects = [r for r in results if not r.success]
            self.notifier.send_failure_notification(failed_projects)
        else:
            self.notifier.send_success_notification(results)
    
    def run_once(self) -> tuple[int, int]:
        """
        Run a single keep-alive cycle.
        
        Returns:
            Tuple of (success_count, failure_count)
        """
        self.logger.print_banner()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            for error in errors:
                self.logger.error(error)
            if any("No projects" in e for e in errors):
                return (0, 0)
        
        results = self.ping_all()
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        self.logger.print_status(
            total=len(results),
            success=success_count,
            failed=failed_count,
        )
        
        return (success_count, failed_count)
    
    def get_status(self) -> dict:
        """Get current status of all projects."""
        projects = self.config.get_enabled_projects()
        return {
            "total_projects": len(self.config.projects),
            "enabled_projects": len(projects),
            "interval_hours": self.config.interval_hours,
            "projects": [
                {
                    "name": p.name,
                    "url": p.url,
                    "enabled": p.enabled,
                }
                for p in self.config.projects
            ],
        }

