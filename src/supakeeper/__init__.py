"""
Supakeeper - Keep your Supabase projects alive

A utility to prevent Supabase free-tier projects from being paused
due to inactivity by performing periodic health checks.
"""

__version__ = "1.0.0"
__author__ = "Jeffrey"

from supakeeper.keeper import SupaKeeper
from supakeeper.config import Config, ProjectConfig

__all__ = ["SupaKeeper", "Config", "ProjectConfig"]

