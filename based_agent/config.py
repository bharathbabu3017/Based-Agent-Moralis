"""Environment-driven configuration for Based Agent."""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional; plain env vars work too
    pass

MAINNET_NETWORK_IDS = ("base", "base-mainnet")


def env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable, treating empty strings as unset."""
    value = os.environ.get(name, "").strip()
    return value or default


def env_flag(name: str) -> bool:
    return (env(name) or "").lower() in ("1", "true", "yes", "on")


# Coinbase Developer Platform
CDP_API_KEY_NAME = env("CDP_API_KEY_NAME")
CDP_PRIVATE_KEY = (env("CDP_PRIVATE_KEY") or "").replace("\\n", "\n")

# Wallet: set CDP_WALLET_ID to reuse a wallet, otherwise one is created on NETWORK_ID
NETWORK_ID = env("NETWORK_ID", "base-sepolia")
CDP_WALLET_ID = env("CDP_WALLET_ID")
WALLET_SEED_FILE = env("WALLET_SEED_FILE", "wallet_seed.json")

# Moralis Web3 Data API
MORALIS_API_KEY = env("MORALIS_API_KEY")

# OpenAI
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-4o")
OPENAI_GUIDE_MODEL = env("OPENAI_GUIDE_MODEL", "gpt-4o-mini")

# Optional features
ENABLE_ART_GENERATION = env_flag("ENABLE_ART_GENERATION")
TWITTER_API_KEY = env("TWITTER_API_KEY")
TWITTER_API_SECRET = env("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = env("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = env("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_ENABLED = all((
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
))


def is_mainnet(network_id: str) -> bool:
    return network_id in MAINNET_NETWORK_IDS


def missing_required_env() -> list[str]:
    """Names of required environment variables that are not set."""
    required = {
        "CDP_API_KEY_NAME": CDP_API_KEY_NAME,
        "CDP_PRIVATE_KEY": CDP_PRIVATE_KEY,
        "OPENAI_API_KEY": env("OPENAI_API_KEY"),
        "MORALIS_API_KEY": MORALIS_API_KEY,
    }
    return [name for name, value in required.items() if not value]
