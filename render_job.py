#!/usr/bin/env python3
"""
Render.com Cron Job Script - Runs the orchestrator daily.

This script is executed by Render's cron job scheduler.
It runs the orchestrator which handles:
- Content type selection
- Agent coordination
- Posting to X
- State management
"""

import asyncio
import sys
from pathlib import Path

# Add Agentos to path
sys.path.insert(0, str(Path(__file__).parent / "Agentos"))

from orchestrator import OrchestratorAgent


async def main():
    """
    Main entry point for Render cron job.
    Runs the orchestrator in production mode.
    """
    print("\n" + "="*60)
    print("RENDER CRON JOB - ORCHESTRATOR STARTING")
    print("="*60 + "\n")

    try:
        # Initialize orchestrator in production mode
        orchestrator = OrchestratorAgent(dry_run=False)

        # Run daily workflow
        await orchestrator.run_daily()

        print("\n" + "="*60)
        print("RENDER CRON JOB - COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
