#!/usr/bin/env python3
"""
Supakeeper - Keep your Supabase projects alive

Main entry point for running Supakeeper directly with Python.
For CLI usage, install the package and use the 'supakeeper' command.

Usage:
    python main.py              # Run once
    python main.py --daemon     # Run as daemon
    python main.py --help       # Show help
"""

import argparse
import sys
from pathlib import Path

# Add src to path for direct execution
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from supakeeper.config import Config
from supakeeper.scheduler import create_scheduler


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Supakeeper - Keep your Supabase projects alive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    Run once and exit
    python main.py --daemon           Run continuously
    
Configuration:
    Set environment variables in .env file:
    - SUPABASE_URL and SUPABASE_KEY for single project
    - SUPABASE_URL_1, SUPABASE_KEY_1, etc. for multiple projects
    
    See env.example for detailed configuration options.
        """,
    )
    
    parser.add_argument(
        "-d", "--daemon",
        help="Run as daemon (continuous mode)",
        action="store_true",
    )
    parser.add_argument(
        "--no-immediate",
        help="Don't run immediately in daemon mode",
        action="store_true",
    )
    parser.add_argument(
        "-v", "--version",
        help="Show version and exit",
        action="store_true",
    )
    
    args = parser.parse_args()
    
    if args.version:
        from supakeeper import __version__
        print(f"Supakeeper v{__version__}")
        return 0
    
    try:
        config = Config.load()
        
        # Validate
        errors = config.validate()
        if any("No projects" in e for e in errors):
            print("Error: No projects configured")
            print("Set SUPABASE_URL and SUPABASE_KEY in your .env file.")
            print("See env.example for configuration examples.")
            return 1
        
        scheduler = create_scheduler(config)
        
        if args.daemon:
            scheduler.run_daemon(run_immediately=not args.no_immediate)
        else:
            success, failed = scheduler.run_once()
            return 1 if failed > 0 else 0
            
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
