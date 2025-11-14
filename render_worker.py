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
from datetime import datetime, timedelta

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
        # Use persistent disk path if on Render
        db_dir = "/opt/render/project/src/data" if Path("/opt/render").exists() else None
        orchestrator = OrchestratorAgent(dry_run=False, db_dir=db_dir)

        # Print state info for debugging
        state = orchestrator.load_state()
        print(f"DB Directory: {orchestrator.db_dir}")
        print(f"Last post time: {state.get('last_post_time')}")
        print(f"Next scheduled: {state.get('next_post_scheduled')}")

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
    print(f"Working directory: {Path.cwd()}")
    print(f"Script location: {Path(__file__).parent}")

    # Check if persistent disk is available
    if Path("/opt/render").exists():
        print(f"Render environment detected - using persistent disk")
        data_path = Path("/opt/render/project/src/data")
        print(f"Persistent disk path: {data_path}")
        print(f"Persistent disk exists: {data_path.exists()}")
        if data_path.exists():
            print(f"Files in persistent disk: {list(data_path.iterdir())}")
    print("="*60 + "\n")

    while True:
        try:
            # Run the orchestrator
            await run_orchestrator()

            # Wait 1 hour before next check (3600 seconds)
            next_check = datetime.now() + timedelta(hours=1)
            print(f"\n💤 Sleeping for 1 hour... Next check at {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
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
