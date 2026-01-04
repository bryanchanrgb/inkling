#!/usr/bin/env python3
"""Main entry point for the Inkling learning application."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inkling.cli import CLI


def main():
    """Run the application."""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

