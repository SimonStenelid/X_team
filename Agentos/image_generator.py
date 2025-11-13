"""
Image Generator Agent - Creates viral-worthy AI-themed images using Midjourney via WaveSpeed AI.

This agent uses:
1. OpenAI Agents SDK to enhance/generate Midjourney prompts
2. WaveSpeed AI API to generate images with Midjourney
3. Optimized parameters for viral, aesthetic, AI-themed visuals
"""

import os
import asyncio
import requests
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner


class ImageGeneratorAgent:
    """Agent that generates viral-worthy AI-themed images using Midjourney."""

    def __init__(self, model: str = "gpt-5-mini", images_dir: str = None):
        """
        Initialize the Image Generator agent with API keys and configuration.

        Args:
            model: AI model to use for prompt enhancement (default: gpt-5-mini)
            images_dir: Directory to save generated images (default: Agentos/images)
        """
        load_dotenv()

        self.wavespeed_api_key = os.getenv("WAVESPEED_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model

        # Use relative path from script location (works everywhere)
        if images_dir is None:
            script_dir = Path(__file__).parent
            images_dir = script_dir / "images"
        self.images_dir = Path(images_dir)

        if not self.wavespeed_api_key:
            raise ValueError("WAVESPEED_API_KEY not found in environment")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Create images directory if it doesn't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)

    async def enhance_prompt(self, input_text: str = None):
        """
        Use LLM to create/enhance a Midjourney prompt for viral AI imagery.

        Args:
            input_text: Optional X post text or theme to base the image on

        Returns:
            str: Enhanced Midjourney prompt
        """
        agent = Agent(
            name="Prompt Enhancer",
            model=self.model,
            instructions="""
            You are a Midjourney prompt expert specializing in creating viral-worthy AI-themed imagery.

            Your task is to create a stunning Midjourney v7 prompt that:
            - Creates aesthetic, cinematic, viral-potential visuals
            - Relates to AI, technology, automation, or futuristic themes
            - Goes beyond just "robots" - think abstract AI concepts, digital aesthetics, cyber scenes, futuristic landscapes
            - Uses effective Midjourney keywords for quality and style

            PROMPT STYLE GUIDELINES:
            - Start with the main subject/scene
            - Add style keywords: ultra-realistic, cinematic, aesthetic, ethereal, dreamlike, surreal
            - Include lighting: soft lighting, dramatic lighting, neon glow, volumetric lighting
            - Add composition details: centered composition, rule of thirds, symmetrical
            - Include quality boosters: masterpiece, 8k, highly detailed, professional photography
            - Keep it focused and under 300 characters for best results

            AI-THEMED VISUAL IDEAS (not just robots):
            - Abstract neural networks as glowing pathways
            - Digital consciousness visualized as light particles
            - Futuristic server rooms with ethereal glow
            - AI "thoughts" as flowing data streams
            - Cyberpunk cityscapes with AI integration
            - Holographic interfaces and virtual spaces
            - Abstract representations of machine learning
            - Neon-lit technology landscapes
            - Minimalist geometric AI concepts
            - Dreamy, surreal tech aesthetics

            EXAMPLES OF GOOD PROMPTS:
            - "neural network pathways visualized as glowing golden threads in deep space, ethereal, cinematic lighting, ultra-detailed, 8k, dreamlike atmosphere"
            - "minimalist AI consciousness sphere floating in void, soft neon glow, aesthetic composition, surreal, professional render, clean and beautiful"
            - "cyberpunk server room with holographic data streams, volumetric lighting, cinematic, ultra-realistic, dramatic atmosphere, masterpiece"
            - "abstract digital mind represented by flowing light particles, soft focus, aesthetic, ethereal glow, centered composition, 8k"

            Return ONLY the Midjourney prompt text, nothing else. Keep it under 300 characters.
            """,
        )

        task = f"Create a Midjourney prompt for a viral AI-themed image"
        if input_text:
            task += f" based on this concept: {input_text}"
        task += ". Return ONLY the prompt text."

        result = await Runner.run(agent, task)
        return result.final_output.strip()

    def download_images(self, image_urls: list, request_id: str):
        """
        Download all generated images to the local images directory.

        Args:
            image_urls: List of image URLs to download
            request_id: The request ID from WaveSpeed API

        Returns:
            list: Paths to the downloaded images
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_paths = []

        print(f"\nDownloading {len(image_urls)} images...")

        for idx, url in enumerate(image_urls, 1):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    # Create filename: timestamp_requestid_imageX.png
                    filename = f"{timestamp}_{request_id}_{idx}.png"
                    filepath = self.images_dir / filename

                    # Save the image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    saved_paths.append(str(filepath))
                    print(f"  Saved image {idx}: {filename}")
                else:
                    print(f"  Failed to download image {idx}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  Error downloading image {idx}: {e}")

        print(f"Successfully saved {len(saved_paths)}/{len(image_urls)} images to {self.images_dir}")
        return saved_paths

    def generate_image_sync(self, prompt: str):
        """
        Generate an image using WaveSpeed AI (Midjourney) - synchronous version.

        Args:
            prompt: The Midjourney prompt

        Returns:
            dict: Result containing 'url' and 'status'
        """
        url = "https://api.wavespeed.ai/api/v3/midjourney/text-to-image"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.wavespeed_api_key}",
        }

        # Optimized parameters for viral AI imagery
        payload = {
            "aspect_ratio": "1:1",  # Perfect for X/Twitter
            "chaos": 20,  # Low-medium chaos for controlled creativity
            "enable_base64_output": False,
            "niji": "close",  # Not using anime style
            "prompt": prompt,
            "quality": 1,  # High quality
            "seed": -1,  # Random seed
            "stylize": 500,  # Medium-high stylization for artistic appeal
            "version": "7",  # Latest Midjourney version
            "weird": 0  # No weirdness
        }

        print(f"\nSubmitting image generation request...")
        print(f"Prompt: {prompt}")

        begin = time.time()
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()["data"]
            request_id = result["id"]
            print(f"Task submitted successfully. Request ID: {request_id}")
        else:
            return {
                "status": "failed",
                "error": f"API Error: {response.status_code}, {response.text}"
            }

        # Poll for results
        result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
        headers = {"Authorization": f"Bearer {self.wavespeed_api_key}"}

        max_attempts = 600  # 60 seconds timeout (600 * 0.1s)
        attempt = 0

        while attempt < max_attempts:
            response = requests.get(result_url, headers=headers)

            if response.status_code == 200:
                result = response.json()["data"]
                status = result["status"]

                if status == "completed":
                    end = time.time()
                    image_urls = result["outputs"]  # Get all 4 images
                    print(f"Task completed in {end - begin:.2f} seconds.")
                    print(f"Generated {len(image_urls)} images")
                    return {
                        "status": "completed",
                        "urls": image_urls,
                        "duration": end - begin,
                        "request_id": request_id
                    }
                elif status == "failed":
                    error_msg = result.get("error", "Unknown error")
                    print(f"Task failed: {error_msg}")
                    return {
                        "status": "failed",
                        "error": error_msg
                    }
                else:
                    if attempt % 10 == 0:  # Print every second
                        print(f"Processing... Status: {status}")
            else:
                return {
                    "status": "failed",
                    "error": f"Polling Error: {response.status_code}, {response.text}"
                }

            time.sleep(0.1)
            attempt += 1

        return {
            "status": "failed",
            "error": "Timeout: Image generation took too long"
        }

    async def generate_image(self, input_text: str = None):
        """
        Generate an AI-themed image (async wrapper).

        Args:
            input_text: Optional X post text or theme to base the image on

        Returns:
            dict: Result containing 'urls', 'local_paths', and 'status'
        """
        # Enhance the prompt using LLM
        enhanced_prompt = await self.enhance_prompt(input_text)

        # Generate image synchronously (WaveSpeed API uses requests, not async)
        result = self.generate_image_sync(enhanced_prompt)

        # Download images if generation was successful
        if result["status"] == "completed":
            local_paths = self.download_images(result["urls"], result["request_id"])
            result["local_paths"] = local_paths

        return result

    async def run(self, input_text: str = None):
        """
        Main execution method - generate an AI-themed image.

        Args:
            input_text: Optional X post text or theme to base the image on

        Returns:
            dict: Result containing 'urls', 'local_paths', and 'status'
        """
        print(f"Image Generator Agent initializing...")
        print(f"Using model: {self.model}")
        print(f"Midjourney version: 7")
        print(f"Images directory: {self.images_dir}\n")

        result = await self.generate_image(input_text)

        print("\n" + "=" * 50)
        if result["status"] == "completed":
            print("SUCCESS: Images generated!")
            print(f"Generated {len(result['urls'])} images")
            print(f"Duration: {result['duration']:.2f}s")
            print(f"\nImage URLs:")
            for idx, url in enumerate(result['urls'], 1):
                print(f"  {idx}. {url}")
            print(f"\nLocal paths:")
            for idx, path in enumerate(result['local_paths'], 1):
                print(f"  {idx}. {path}")
        else:
            print("FAILED: Image generation failed")
            print(f"Error: {result['error']}")
        print("=" * 50)

        return result


async def main():
    """
    Example usage of the Image Generator agent.

    You can specify a different model for prompt enhancement:
    - agent = ImageGeneratorAgent(model="gpt-5")
    - agent = ImageGeneratorAgent(model="gpt-5-mini")
    - agent = ImageGeneratorAgent(model="gpt-5-nano")
    """
    agent = ImageGeneratorAgent()  # Default: gpt-5-mini

    # Example 1: Generate without input (random AI theme)
    # result = await agent.run()

    # Example 2: Generate based on a concept/post
    result = await agent.run("AI agents becoming self-aware and taking over automation")

    return result


if __name__ == "__main__":
    asyncio.run(main())
