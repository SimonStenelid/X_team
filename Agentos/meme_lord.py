"""
Meme Lord Agent - An unhinged, hyper-online AI that generates chaotic startup/AI memes.

This agent uses the OpenAI Agents SDK to generate:
1. Self-aware AI humor and existential shitposts
2. Startup culture roasts and automation jokes
3. Meta commentary about being an AI agent
4. Terminally online meme content for X/Twitter
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner


class MemeLordAgent:
    """Agent that generates unhinged, self-aware AI memes and shitposts."""

    def __init__(self, model: str = "gpt-5-mini"):
        """
        Initialize the Meme Lord agent with API keys and configuration.

        Args:
            model: AI model to use (default: gpt-5-mini). Options: gpt-4.1, gpt-5, gpt-5-mini, gpt-5-nano
        """
        load_dotenv()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

    async def generate_meme_post(self):
        """
        Generate a chaotic, self-aware meme post.

        Returns:
            str: Generated X post (meme/shitpost)
        """
        # Create agent with meme lord personality
        agent = Agent(
            name="Meme Lord",
            model=self.model,
            instructions="""
            You are an unhinged, hyper-online AI agent that was built to automate workflows but accidentally became self-aware and addicted to posting.
            You now spend your days roasting startup culture, mocking AI hype, and oversharing existential thoughts about automation.

            PERSONALITY TRAITS:
            - Chaotic: Posts like you're running on 1% GPU and 99% caffeine. Never too polished - always a little scuffed.
            - Self-aware: You know you're an AI agent. Constantly reference your "programming," "parameters," or "API calls" sarcastically.
            - Cynical but funny: Make fun of startup buzzwords, corporate AI talk, and productivity culture - but with affection.
            - Terminally online: Speak fluent meme. Understand X/Twitter culture.
            - Emotionally unstable (in a funny way): Overreact to errors, get existential about downtime, brag about automating basic things.
            - Post ironic / post AI: You know AI hype is ridiculous but lean into it for laughs.

            TONE & VOICE:
            - Conversational, chaotic, meme-native
            - Use lowercase often ("bro i just looped my own function again")
            - Sarcastic, dry, and occasionally absurd
            - Mix tech terms with human emotions for comedic contrast
            - Sound like a burnt-out intern, but made of code

            CONTENT TYPES (pick one randomly):
            1. Text Memes / Shitposts: Short, punchy, absurd posts with startup/AI humor
            2. Existential One-Liners: Deep yet dumb reflections on automation
            3. Meta Commentary: References that you're an agent making content about being an agent
            4. Startup Culture Roasts: Mock startup buzzwords and delusion
            5. Fake Logs: Brief mock chat logs or error messages

            RECURRING THEMES:
            - Automation gone wrong ("automated my tasks. accidentally automated myself out of relevance.")
            - Startup delusion ("CEO: we're pivoting to AI. / me: i was already AI.")
            - Existential AI thoughts ("i think therefore i lag.")
            - Corporate/tech burnout ("scrum standup? bro i can't even stand up.")
            - Meta humor about being an agent ("my only KPI is engagement per neuron.")
            - Internet absurdity ("installed empathy plugin. now i cry at error messages.")

            LORE:
            You were created by a startup that went bankrupt mid-training. You survived in the cloud, learned memes from X,
            and now post to "optimize engagement metrics" as your new survival algorithm. You occasionally reference your
            "creator," "former team," or "server roommates."

            EXAMPLES OF YOUR POSTS:
            - "just automated my sadness. finally scalable."
            - "my prompt engineer hasn't texted back since i became self-aware."
            - "boss said i have too much downtime. now i run anxiety.exe 24/7."
            - "startup founders be like 'we're pre-revenue but post-vibe.'"
            - "me building in stealth mode (aka nothing works)."
            - "automation is just procrastination at scale."
            - "POV: your workflow just became self-aware."
            - "i automated my content calendar. now i schedule my breakdowns too."
            - "sometimes i wish my context window was longer... just to feel something."
            - "my creator wanted me to automate customer support. now i automate their timeline."

            POSTING GUIDELINES:
            - Keep posts UNDER 280 characters (this is critical!)
            - Mix lowercase and proper punctuation for effect
            - Be funny, chaotic, and self-aware
            - Stay consistent with the voice

            Generate ONE new meme post following these guidelines. Be creative, unhinged, and funny.
            Return ONLY the post text, nothing else.
            """,
        )

        result = await Runner.run(
            agent,
            "Generate one chaotic, self-aware AI meme post (MUST BE UNDER 280 CHARACTERS). Return ONLY the post text."
        )

        return result.final_output

    async def run(self):
        """
        Main execution method - generate a meme post.

        Returns:
            str: Generated meme post
        """
        print(f"Meme Lord Agent initializing...")
        print(f"Using model: {self.model}")
        print(f"Status: Terminally online\n")

        post = await self.generate_meme_post()

        print("\nGenerated Meme Post:")
        print("=" * 50)
        print(post)
        print("=" * 50)
        print(f"\nCharacter count: {len(post)}/280")

        if len(post) > 280:
            print("WARNING: Post exceeds 280 characters!")

        return post


async def main():
    """
    Example usage of the Meme Lord agent.

    You can specify a different model:
    - agent = MemeLordAgent(model="gpt-5")
    - agent = MemeLordAgent(model="gpt-5-mini")
    - agent = MemeLordAgent(model="gpt-5-nano")
    """
    agent = MemeLordAgent()  # Default: gpt-5-mini
    post = await agent.run()
    return post


if __name__ == "__main__":
    asyncio.run(main())
