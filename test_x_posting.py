"""
Test X API credentials with a simple text post.
"""

import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

# Load credentials
x_api_key = os.getenv("X_API_KEY")
x_api_secret = os.getenv("X_API_SECRET")
x_access_token = os.getenv("X_ACCESS_TOKEN")
x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
x_bearer_token = os.getenv("X_BEARER_TOKEN")

print("Testing X API credentials...\n")

# Test V2 API (for posting tweets)
try:
    client = tweepy.Client(
        bearer_token=x_bearer_token,
        consumer_key=x_api_key,
        consumer_secret=x_api_secret,
        access_token=x_access_token,
        access_token_secret=x_access_token_secret
    )

    # Try to get authenticated user
    me = client.get_me()
    print(f"✅ Authenticated as: @{me.data.username}")
    print(f"   User ID: {me.data.id}")
    print(f"   Name: {me.data.name}\n")

    # Ask to post a test tweet
    confirm = input("Do you want to post a test tweet? (yes/no): ")
    if confirm.lower() == "yes":
        test_text = "Testing my automated X posting system 🤖"
        response = client.create_tweet(text=test_text)
        tweet_id = response.data["id"]
        print(f"\n✅ Test tweet posted successfully!")
        print(f"   Tweet ID: {tweet_id}")
        print(f"   URL: https://twitter.com/{me.data.username}/status/{tweet_id}")
    else:
        print("\nSkipped posting test tweet.")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check your X API credentials in .env file")
