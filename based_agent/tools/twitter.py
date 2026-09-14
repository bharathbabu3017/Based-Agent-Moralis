"""Optional X (Twitter) tools, enabled when all TWITTER_* env vars are set.

Uses the X API v2 via tweepy. Posting works on the free tier; reading mentions
and searching require a paid (Basic or higher) access level.
"""

from functools import lru_cache

import tweepy

from based_agent import config
from based_agent.tools.common import tool


@lru_cache(maxsize=1)
def get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=config.TWITTER_API_KEY,
        consumer_secret=config.TWITTER_API_SECRET,
        access_token=config.TWITTER_ACCESS_TOKEN,
        access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
    )


def _format_tweets(response: tweepy.Response) -> str:
    users = {u.id: u.username for u in response.includes.get("users", [])}
    return "\n".join(
        f"- [{tweet.id}] @{users.get(tweet.author_id, tweet.author_id)}: {tweet.text}"
        for tweet in response.data)


@tool("posting to Twitter")
def post_to_twitter(content: str) -> str:
    """
    Post a message to Twitter.

    Args:
        content (str): The content to tweet (max 280 characters)

    Returns:
        str: Status message about the tweet
    """
    response = get_client().create_tweet(text=content)
    return f"Successfully posted tweet with ID: {response.data['id']}"


@tool("checking Twitter mentions")
def check_twitter_mentions(count: int = 10) -> str:
    """
    Check recent Twitter mentions of the agent's account.

    Args:
        count (int): Number of recent mentions to retrieve (5-100)

    Returns:
        str: Formatted list of recent mentions, including tweet IDs
    """
    client = get_client()
    me = client.get_me(user_auth=True).data
    response = client.get_users_mentions(
        me.id,
        max_results=max(5, min(count, 100)),
        expansions=["author_id"],
        user_auth=True,
    )
    if not response.data:
        return "No recent mentions found"
    return f"Recent mentions:\n{_format_tweets(response)}"


@tool("replying to tweet")
def reply_to_twitter_mention(tweet_id: str, content: str) -> str:
    """
    Reply to a specific tweet.

    Args:
        tweet_id (str): ID of the tweet to reply to
        content (str): Content of the reply

    Returns:
        str: Status message about the reply
    """
    get_client().create_tweet(text=content, in_reply_to_tweet_id=tweet_id)
    return f"Successfully replied to tweet {tweet_id}"


@tool("searching tweets")
def search_twitter(query: str, count: int = 10) -> str:
    """
    Search recent tweets (last 7 days) matching a query.

    Args:
        query (str): Search query
        count (int): Number of tweets to retrieve (10-100)

    Returns:
        str: Formatted list of matching tweets
    """
    response = get_client().search_recent_tweets(
        query,
        max_results=max(10, min(count, 100)),
        expansions=["author_id"],
        user_auth=True,
    )
    if not response.data:
        return f"No tweets found matching query: {query}"
    return f"Tweets matching '{query}':\n{_format_tweets(response)}"
