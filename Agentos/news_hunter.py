"""
News Hunter Agent - Searches for viral AI news and generates X posts.

This agent uses the OpenAI Agents SDK with Serper MCP integration to:
1. Search for the latest AI news, trends, and updates
2. Focus on AI agents and automation news
3. Select the most viral-worthy news item
4. Generate professional, tech-focused X posts
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio


class NewsHunterAgent:
    """Agent that hunts for viral AI news and creates X posts."""

    def __init__(self, model: str = "gpt-4.1"):
        """
        Initialize the News Hunter agent with API keys and configuration.

        Args:
            model: AI model to use (default: gpt-4.1). Options: gpt-4.1, gpt-5, gpt-5-mini, gpt-5-nano
        """
        load_dotenv()

        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY not found in environment")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Detect serper-mcp-server path dynamically
        # First try: same directory as Python executable (virtual environment)
        python_dir = Path(sys.executable).parent
        self.serper_server_path = python_dir / "serper-mcp-server"

        # If not found, try global installation
        if not self.serper_server_path.exists():
            import shutil
            global_path = shutil.which("serper-mcp-server")
            if global_path:
                self.serper_server_path = Path(global_path)
            else:
                raise ValueError("serper-mcp-server not found. Install with: pip install serper-mcp-server")

    async def search_and_generate(self):
        """
        Search for viral AI news and generate an X post.

        Returns:
            str: Generated X post
        """
        async with MCPServerStdio(
            name="Serper Search",
            params={
                "command": str(self.serper_server_path),
                "args": [],
                "env": {
                    "SERPER_API_KEY": self.serper_api_key
                }
            }
        ) as serper_server:
            # Get today's date for context
            today = datetime.now().strftime("%B %d, %Y")

            # Create agent with Serper MCP tools
            agent = Agent(
                name="AI News Hunter",
                model="gpt-5-mini",
                instructions=f"""
                You are an AI news curator specializing in AI agents and automation.

                TODAY'S DATE: {today}

                Your task:
                1. Use google_search_news to find the latest AI news focusing on:
                   - AI agents and agentic systems
                   - AI automation tools and platforms
                   - New AI agent frameworks or releases
                   - AI workflow automation
                   - Multi-agent systems

                2. From the search results, identify THE ONE most viral-worthy story:
                   - Most recent (within last 24-48 hours from {today})
                   - High engagement potential
                   - Significant impact on AI/tech community
                   - Preferably about AI agents or automation

                3. Create ONE X post (max 280 characters) about this story:
                   - Professional but engaging tone
                   - Tech-focused, not humorous, but not too serious 
                   - Include key insight or takeaway
                   - Keep it concise and impactful
                   - Style and laguage should follow the typical non serious but viral-making X posting style and language
                """,
                mcp_servers=[serper_server],
            )

            result = await Runner.run(
                agent,
                "Find the most viral and recent AI news about AI agents or automation, then create ONE professional X post about it (MUST BE UNDER 280 CHARACTERS). Use google_search_news to search. Return ONLY the X post text, nothing else."
            )

            return result.final_output

    async def run(self):
        """
        Main execution method - search for news and generate a post.

        Returns:
            str: Generated X post
        """
        today = datetime.now().strftime("%B %d, %Y")
        print(f"Searching for viral AI agent/automation news...")
        print(f"Today's date: {today}")
        print(f"Using model: {self.model}\n")

        post = await self.search_and_generate()

        print("\nGenerated Post:")
        print("=" * 50)
        print(post)
        print("=" * 50)
        print(f"\nCharacter count: {len(post)}/280")

        return post


async def main():
    """
    Example usage of the News Hunter agent.

    You can specify a different model:
    - agent = NewsHunterAgent(model="gpt-5")
    - agent = NewsHunterAgent(model="gpt-5-mini")
    - agent = NewsHunterAgent(model="gpt-5-nano")
    """
    agent = NewsHunterAgent()  # Default: gpt-4.1
    post = await agent.run()
    return post


if __name__ == "__main__":
    asyncio.run(main())
