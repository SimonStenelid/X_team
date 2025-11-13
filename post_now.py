"""
Production post script - Posts to X for real.

This script will:
1. Run the orchestrator in production mode (dry_run=False)
2. Generate content using one of the agents
3. Validate and check for duplicates
4. Actually post to X
"""

import asyncio
import sys
from pathlib import Path

# Add Agentos to path
sys.path.insert(0, str(Path(__file__).parent / "Agentos"))

from orchestrator import OrchestratorAgent


async def main():
    print("\n" + "="*60)
    print("⚠️  PRODUCTION MODE - WILL POST TO X")
    print("="*60 + "\n")

    # Confirm
    confirm = input("Are you sure you want to post to X? (yes/no): ")
    if confirm.lower() != "yes":
        print("\nCancelled. No post was made.")
        return

    print("\n🚀 Starting orchestrator in production mode...\n")

    # Initialize orchestrator in PRODUCTION mode (dry_run=False)
    orchestrator = OrchestratorAgent(dry_run=False)

    # Run the daily workflow
    await orchestrator.run_daily()

    print("\n✅ Production run complete!")
    print("\nCheck your X account to see the post!")


if __name__ == "__main__":
    asyncio.run(main())
