"""
Test script for the Orchestrator Agent.

This script demonstrates how to use the orchestrator in different modes.
"""

import asyncio
import sys
from pathlib import Path

# Add Agentos to path
sys.path.insert(0, str(Path(__file__).parent / "Agentos"))

from orchestrator import OrchestratorAgent


async def test_dry_run():
    """
    Test orchestrator in dry-run mode (doesn't actually post to X).
    This is safe to run for testing without posting anything.
    """
    print("\n" + "="*60)
    print("TESTING ORCHESTRATOR IN DRY-RUN MODE")
    print("="*60 + "\n")

    # Initialize orchestrator in dry-run mode
    orchestrator = OrchestratorAgent(dry_run=True)

    # Run the daily workflow
    await orchestrator.run_daily()

    print("\n" + "="*60)
    print("DRY-RUN TEST COMPLETE")
    print("="*60 + "\n")


async def test_state_management():
    """
    Test state loading and management without running agents.
    """
    print("\n" + "="*60)
    print("TESTING STATE MANAGEMENT")
    print("="*60 + "\n")

    orchestrator = OrchestratorAgent(dry_run=True)

    # Load state
    state = orchestrator.load_state()
    print("Current state:")
    print(f"  Last post time: {state['last_post_time']}")
    print(f"  Last 7 days: {state['last_7_days_posts']}")
    print(f"  Week counts: {state['week_counts']}")
    print(f"  Next scheduled: {state['next_post_scheduled']}")

    # Load posts database
    posts_db = orchestrator.load_posts_db()
    print(f"\nPosts database: {len(posts_db['posts'])} posts tracked")

    print("\n" + "="*60)
    print("STATE MANAGEMENT TEST COMPLETE")
    print("="*60 + "\n")


async def test_content_selection():
    """
    Test content type selection algorithm.
    """
    print("\n" + "="*60)
    print("TESTING CONTENT TYPE SELECTION")
    print("="*60 + "\n")

    orchestrator = OrchestratorAgent(dry_run=True)
    state = orchestrator.load_state()

    # Test selection 5 times to see variety
    selections = []
    for i in range(5):
        content_type = orchestrator.select_content_type(state)
        selections.append(content_type)
        print(f"\nRound {i+1}: Selected {content_type}")

    print(f"\nSelections: {selections}")
    print("\n" + "="*60)
    print("CONTENT SELECTION TEST COMPLETE")
    print("="*60 + "\n")


async def test_weekly_analysis():
    """
    Test weekly analysis functionality.
    """
    print("\n" + "="*60)
    print("TESTING WEEKLY ANALYSIS")
    print("="*60 + "\n")

    orchestrator = OrchestratorAgent(dry_run=True)
    await orchestrator.run_weekly_analysis()

    print("\n" + "="*60)
    print("WEEKLY ANALYSIS TEST COMPLETE")
    print("="*60 + "\n")


async def run_production():
    """
    Run orchestrator in production mode (WILL POST TO X).
    Only use this when you're ready to post for real.
    """
    print("\n" + "="*60)
    print("⚠️  RUNNING ORCHESTRATOR IN PRODUCTION MODE")
    print("THIS WILL POST TO X FOR REAL!")
    print("="*60 + "\n")

    # Initialize orchestrator in production mode
    orchestrator = OrchestratorAgent(dry_run=False)

    # Run the daily workflow
    await orchestrator.run_daily()

    print("\n" + "="*60)
    print("PRODUCTION RUN COMPLETE")
    print("="*60 + "\n")


async def main():
    """
    Main test menu.
    """
    print("\nOrchestrator Test Script")
    print("=" * 60)
    print("1. Dry-run test (safe, doesn't post)")
    print("2. State management test")
    print("3. Content selection test")
    print("4. Weekly analysis test")
    print("5. Production run (⚠️  WILL POST TO X)")
    print("=" * 60)

    choice = input("\nSelect test (1-5) or press Enter for dry-run: ").strip()

    if choice == "1" or choice == "":
        await test_dry_run()
    elif choice == "2":
        await test_state_management()
    elif choice == "3":
        await test_content_selection()
    elif choice == "4":
        await test_weekly_analysis()
    elif choice == "5":
        confirm = input("Are you sure you want to run in production mode? (yes/no): ")
        if confirm.lower() == "yes":
            await run_production()
        else:
            print("Cancelled.")
    else:
        print("Invalid choice. Running dry-run test...")
        await test_dry_run()


if __name__ == "__main__":
    asyncio.run(main())
