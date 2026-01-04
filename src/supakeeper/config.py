"""
Configuration management for Supakeeper.

Loads configuration from environment variables (.env file supported).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


@dataclass
class ProjectConfig:
    """Configuration for a single Supabase project."""
    
    name: str
    url: str
    key: str
    table: Optional[str] = None
    enabled: bool = True
    
    def __post_init__(self) -> None:
        """Validate project configuration."""
        if not self.url:
            raise ValueError(f"Project '{self.name}': URL is required")
        if not self.key:
            raise ValueError(f"Project '{self.name}': API key is required")
        if not self.url.startswith("https://"):
            raise ValueError(f"Project '{self.name}': URL must start with https://")


@dataclass
class Config:
    """Main configuration for Supakeeper."""
    
    projects: list[ProjectConfig] = field(default_factory=list)
    interval_hours: float = 48.0
    retry_attempts: int = 3
    retry_delay: int = 30
    log_level: str = "INFO"
    log_file: str = "logs/supakeeper.log"
    webhook_url: Optional[str] = None
    console_output: bool = True
    
    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from environment variables.
        
        Supports .env file via python-dotenv.
            
        Returns:
            Config instance with loaded settings
        """
        # Load .env file if exists
        load_dotenv()
        
        projects = []
        
        # Check for single project configuration (SUPABASE_URL / SUPABASE_KEY)
        single_url = os.getenv("SUPABASE_URL")
        single_key = os.getenv("SUPABASE_KEY")
        
        if single_url and single_key:
            projects.append(ProjectConfig(
                name=os.getenv("SUPABASE_NAME", "Default Project"),
                url=single_url,
                key=single_key,
                table=os.getenv("SUPABASE_TABLE"),
            ))
        
        # Check for numbered project configurations (SUPABASE_URL_1, SUPABASE_URL_2, etc.)
        env_pattern = re.compile(r"SUPABASE_URL_(\d+)")
        project_indices = set()
        
        for key in os.environ:
            match = env_pattern.match(key)
            if match:
                project_indices.add(match.group(1))
        
        # Sort indices numerically
        for idx in sorted(project_indices, key=int):
            url = os.getenv(f"SUPABASE_URL_{idx}")
            api_key = os.getenv(f"SUPABASE_KEY_{idx}")
            
            if url and api_key:
                projects.append(ProjectConfig(
                    name=os.getenv(f"SUPABASE_NAME_{idx}", f"Project {idx}"),
                    url=url,
                    key=api_key,
                    table=os.getenv(f"SUPABASE_TABLE_{idx}"),
                ))
        
        return cls(
            projects=projects,
            interval_hours=float(os.getenv("KEEPALIVE_INTERVAL_HOURS", "48")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            log_file=os.getenv("LOG_FILE", "logs/supakeeper.log"),
            webhook_url=os.getenv("WEBHOOK_URL"),
            console_output=os.getenv("CONSOLE_OUTPUT", "true").lower() == "true",
        )
    
    def get_enabled_projects(self) -> list[ProjectConfig]:
        """Get list of enabled projects."""
        return [p for p in self.projects if p.enabled]
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not self.projects:
            errors.append("No projects configured")
        
        for project in self.projects:
            try:
                project.__post_init__()
            except ValueError as e:
                errors.append(str(e))
        
        if self.interval_hours <= 0:
            errors.append("Interval hours must be positive")
        
        if self.interval_hours > 168:
            errors.append(
                "Warning: Interval exceeds 168 hours (7 days). "
                "Supabase pauses projects after 7 days of inactivity."
            )
        
        return errors
