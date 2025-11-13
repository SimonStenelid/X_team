#!/usr/bin/env python3
"""
Render.com Background Worker - Runs the orchestrator on a schedule.

This worker runs continuously and checks every hour if it's time to post.
Unlike a cron job, this has access to persistent disk storage to maintain state.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add Agentos to path
sys.path.insert(0, str(Path(__file__).parent / "Agentos"))

from orchestrator import OrchestratorAgent


async def run_orchestrator():
    """Run the orchestrator once."""
    try:
        print("\n" + "="*60)
        print(f"ORCHESTRATOR CHECK - {datetime.now().isoformat()}")
        print("="*60 + "\n")

        # Initialize orchestrator in production mode
        orchestrator = OrchestratorAgent(dry_run=False)

        # Run daily workflow (will check if it's time to post)
        await orchestrator.run_daily()

        print("\n" + "="*60)
        print("ORCHESTRATOR CHECK COMPLETED")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """
    Main worker loop - runs continuously, checks every hour.
    """
    print("\n" + "="*60)
    print("RENDER BACKGROUND WORKER STARTING")
    print("Checking for posts every hour...")
    print("="*60 + "\n")

    while True:
        try:
            # Run the orchestrator
            await run_orchestrator()

            # Wait 1 hour before next check (3600 seconds)
            print(f"\nSleeping for 1 hour... Next check at {datetime.now().replace(hour=(datetime.now().hour + 1) % 24, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(3600)

        except KeyboardInterrupt:
            print("\n\n⚠️  Worker stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in worker loop: {e}")
            import traceback
            traceback.print_exc()
            # Wait 5 minutes before retrying on error
            print("Waiting 5 minutes before retry...")
            await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
