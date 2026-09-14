"""Lazy loading, creation, and persistence of the agent's CDP wallet.

The wallet is only initialised the first time a tool needs it, so importing the
agent (e.g. for evals) does not require CDP credentials or network access.
"""

import json
import os
from functools import lru_cache

from cdp import Cdp, Wallet

from based_agent import config


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _seed_file_wallet_ids(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(json.load(f).keys())


@lru_cache(maxsize=1)
def get_wallet() -> Wallet:
    """Return the agent's wallet, loading or creating it on first use.

    Resolution order:
      1. ``CDP_WALLET_ID`` + seed from ``WALLET_SEED_FILE``
      2. The single wallet stored in ``WALLET_SEED_FILE``
      3. A brand-new wallet on ``NETWORK_ID``, whose seed is saved (encrypted)
         to ``WALLET_SEED_FILE`` so it survives restarts
    """
    if not config.CDP_API_KEY_NAME or not config.CDP_PRIVATE_KEY:
        raise ConfigError("CDP_API_KEY_NAME and CDP_PRIVATE_KEY must be set.")

    Cdp.configure(config.CDP_API_KEY_NAME, config.CDP_PRIVATE_KEY)

    seed_file = config.WALLET_SEED_FILE
    wallet_id = config.CDP_WALLET_ID
    if not wallet_id:
        stored_ids = _seed_file_wallet_ids(seed_file)
        if len(stored_ids) > 1:
            raise ConfigError(
                f"{seed_file} contains {len(stored_ids)} wallets; "
                "set CDP_WALLET_ID to choose one.")
        wallet_id = stored_ids[0] if stored_ids else None

    if wallet_id:
        wallet = Wallet.fetch(wallet_id)
        wallet.load_seed_from_file(seed_file)
        print(f"Loaded wallet {wallet.id} on {wallet.network_id}")
    else:
        wallet = Wallet.create(network_id=config.NETWORK_ID)
        # WARNING: file-based seed storage is for development only.
        wallet.save_seed_to_file(seed_file, encrypt=True)
        print(f"Created wallet {wallet.id} on {wallet.network_id}; "
              f"seed saved to {seed_file}")

    return wallet


def wallet_address() -> str:
    return get_wallet().default_address.address_id


def wallet_is_mainnet() -> bool:
    return config.is_mainnet(get_wallet().network_id)
