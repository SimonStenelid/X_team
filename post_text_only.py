"""
Post text-only content (news or meme) to test X posting.
This avoids media upload which requires additional permissions.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Agentos"))

from orchestrator import OrchestratorAgent


async def main():
    print("\n" + "="*60)
    print("TEXT-ONLY POST TEST")
    print("="*60 + "\n")

    confirm = input("Post a text-only tweet to X? (yes/no): ")
    if confirm.lower() != "yes":
        print("\nCancelled.")
        return

    print("\n🚀 Generating content...\n")

    # Initialize orchestrator
    orchestrator = OrchestratorAgent(dry_run=False)
    state = orchestrator.load_state()

    # Force selection to news or meme (no media)
    import random
    content_type = random.choice(["news", "meme"])
    print(f"Selected content type: {content_type}\n")

    # Try to generate and post
    for attempt in range(3):
        content = await orchestrator.call_agent(content_type, state)

        if not content:
            print(f"Attempt {attempt + 1} failed, retrying...")
            continue

        # Validate
        is_valid, quality_score, reason = orchestrator.validate_content(content)
        if not is_valid:
            print(f"Validation failed: {reason}, retrying...")
            continue

        # Check duplicates
        is_duplicate, dup_reason = orchestrator.check_duplicates(content)
        if is_duplicate:
            print(f"Duplicate detected: {dup_reason}, retrying...")
            continue

        # Post (text only, no media)
        print(f"\n📝 Generated text ({len(content['text'])} chars):")
        print("─" * 60)
        print(content['text'])
        print("─" * 60)

        final_confirm = input("\nPost this to X? (yes/no): ")
        if final_confirm.lower() != "yes":
            print("\nCancelled.")
            return

        # Post
        tweet_id = await orchestrator.post_to_x(content)

        if tweet_id:
            print(f"\n✅ Posted successfully!")
            print(f"Tweet ID: {tweet_id}")
            print(f"URL: https://twitter.com/SStenelid/status/{tweet_id}")

            # Update state
            orchestrator.update_state_after_post(state, content_type, content, tweet_id)
            orchestrator.update_posts_database(content_type, content, tweet_id, quality_score)
            print("\n✅ State and database updated!")
        else:
            print("\n❌ Failed to post. Check permissions in X Developer Portal.")

        return

    print("\n❌ Failed after 3 attempts")


if __name__ == "__main__":
    asyncio.run(main())
