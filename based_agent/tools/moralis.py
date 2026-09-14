"""Market and wallet data tools backed by the Moralis Web3 Data API.

Docs: https://docs.moralis.com/web3-data-api/evm
"""

from typing import Any

import requests

from based_agent import config
from based_agent.tools.common import tool
from based_agent.wallet import wallet_address, wallet_is_mainnet

MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"
REQUEST_TIMEOUT_SECONDS = 30


def moralis_get(path: str, params: dict[str, Any]) -> Any:
    """GET a Moralis endpoint and return the decoded JSON body."""
    if not config.MORALIS_API_KEY:
        raise RuntimeError("MORALIS_API_KEY environment variable is not set")

    response = requests.get(
        f"{MORALIS_BASE_URL}{path}",
        headers={
            "accept": "application/json",
            "X-API-Key": config.MORALIS_API_KEY
        },
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def wallet_chain() -> str:
    """Moralis chain name matching the network the agent's wallet is on."""
    return "base" if wallet_is_mainnet() else "base sepolia"


@tool("fetching token metadata")
def get_token_metadata(token_address: str) -> str:
    """
    Fetch metadata for an ERC-20 token on the network the agent's wallet is on.

    Args:
        token_address (str): The address of the ERC-20 token

    Returns:
        str: The token metadata or an error message if unsuccessful
    """
    metadata = moralis_get("/erc20/metadata", {
        "chain": wallet_chain(),
        "addresses[0]": token_address
    })
    if not metadata:
        return "No metadata found for the provided token address."

    token = metadata[0]
    return (f"Token Name: {token.get('name')}\n"
            f"Symbol: {token.get('symbol')}\n"
            f"Decimals: {token.get('decimals')}\n"
            f"Total Supply: {token.get('total_supply_formatted')}\n"
            f"Contract Address: {token.get('address')}\n"
            f"Verified: {token.get('verified_contract')}\n"
            f"Logo URL: {token.get('logo')}\n")


@tool("fetching wallet tokens")
def get_wallet_tokens() -> str:
    """
    Fetch the tokens (including native ETH) held by the agent's wallet, with balances and USD prices.

    Returns:
        str: The list of tokens and balances or an error message if unsuccessful
    """
    address = wallet_address()
    tokens = moralis_get(f"/wallets/{address}/tokens", {
        "chain": wallet_chain()
    }).get("result", [])
    if not tokens:
        return f"No tokens found for wallet {address}."

    token_list = "\n".join(
        f"Token: {token.get('name')} ({token.get('symbol')})\n"
        f"Balance: {token.get('balance_formatted')} {token.get('symbol')}\n"
        f"Contract Address: {token.get('token_address')}\n"
        f"Verified: {'Yes' if token.get('verified_contract') else 'No'}\n"
        f"Price (USD): {token.get('usd_price') or 'N/A'}\n"
        for token in tokens)
    return f"Tokens held by {address}:\n{token_list}"


@tool("fetching trending tokens")
def get_trending_tokens(security_score: int = 80,
                        min_market_cap: int = 100000,
                        limit: int = 10) -> str:
    """
    Fetch trending tokens on Base Mainnet filtered by security score and market cap.

    Args:
        security_score (int): Minimum security score (0-100) for tokens
        min_market_cap (int): Minimum market cap in USD
        limit (int): Maximum number of tokens to return

    Returns:
        str: Trending token information or an error message
    """
    tokens = moralis_get("/discovery/tokens/trending", {
        "chain": "base",
        "security_score": security_score,
        "min_market_cap": min_market_cap,
    })
    if not tokens:
        return "No trending tokens matched the filters."

    token_info = "\n".join(
        f"Token Name: {token.get('token_name')} ({token.get('token_symbol')})\n"
        f"Contract Address: {token.get('token_address')}\n"
        f"Price (USD): {token.get('price_usd')}\n"
        f"Market Cap: {token.get('market_cap')}\n"
        f"Security Score: {token.get('security_score')}\n"
        for token in tokens[:limit])
    return f"Trending Tokens:\n{token_info}"


@tool("fetching wallet PnL")
def get_wallet_pnl() -> str:
    """
    Retrieve profit and loss (PnL) for each token the agent's wallet has traded on Base Mainnet.

    Returns:
        str: Wallet PnL data or an error message if unsuccessful
    """
    address = wallet_address()
    pnl_data = moralis_get(f"/wallets/{address}/profitability", {
        "chain": "base"
    }).get("result", [])
    if not pnl_data:
        return "No PnL data found for the wallet."

    pnl_info = "\n".join(
        f"Token: {entry.get('name')} ({entry.get('symbol')})\n"
        f"Total Invested: ${entry.get('total_usd_invested')}\n"
        f"Realized Profit: ${entry.get('realized_profit_usd')}\n"
        f"Avg Buy Price: ${entry.get('avg_buy_price_usd')}\n"
        f"Total Tokens Bought: {entry.get('total_tokens_bought')}\n"
        for entry in pnl_data)
    return f"Wallet PnL for {address}:\n{pnl_info}"


@tool("fetching wallet NFTs")
def get_wallet_nfts() -> str:
    """
    Fetch the NFTs held by the agent's wallet on the network the wallet is on.

    Returns:
        str: The list of NFTs or an error message if unsuccessful
    """
    address = wallet_address()
    nfts = moralis_get(f"/{address}/nft", {
        "chain": wallet_chain(),
        "format": "decimal",
        "media_items": "false",
    }).get("result", [])
    if not nfts:
        return f"No NFTs found for wallet {address}."

    nft_list = "\n".join(
        f"- {nft.get('name')} ({nft.get('symbol')}) #{nft.get('token_id')} "
        f"[{nft.get('contract_type')}] at {nft.get('token_address')}, "
        f"amount: {nft.get('amount')}"
        for nft in nfts)
    return f"NFTs held by {address}:\n{nft_list}"


@tool("fetching token pairs")
def get_token_pairs(token_address: str) -> str:
    """
    Fetch DEX trading pairs for an ERC-20 token on the network the agent's wallet is on.

    Args:
        token_address (str): The address of the ERC-20 token

    Returns:
        str: Information about trading pairs or an error message if unsuccessful
    """
    pairs = moralis_get(f"/erc20/{token_address}/pairs", {
        "chain": wallet_chain()
    }).get("pairs", [])
    if not pairs:
        return f"No trading pairs found for token {token_address}."

    def describe(side: dict) -> str:
        return f"{side.get('token_name')} ({side.get('token_symbol')})"

    pairs_info = "\n".join(
        f"Pair: {pair.get('pair_label')}\n"
        f"Price (USD): {pair.get('usd_price')}\n"
        f"24hr Price Change (%): {pair.get('usd_price_24hr_percent_change')}\n"
        f"Liquidity (USD): {pair.get('liquidity_usd')}\n"
        f"Exchange Address: {pair.get('exchange_address')}\n"
        f"Tokens: {' / '.join(describe(side) for side in pair.get('pair', []))}\n"
        for pair in pairs)
    return f"Trading pairs for token {token_address}:\n{pairs_info}"


@tool("fetching token details")
def get_token_details(token_address: str) -> str:
    """
    Fetch market analytics for an ERC-20 token (price, market cap, security score, holder and volume trends).

    Args:
        token_address (str): The address of the ERC-20 token

    Returns:
        str: Information about the token or an error message if unsuccessful
    """
    token = moralis_get("/discovery/token", {
        "chain": wallet_chain(),
        "token_address": token_address
    })
    holders_change = token.get("holders_change") or {}
    volume_change = token.get("volume_change_usd") or {}
    price_change = token.get("price_percent_change_usd") or {}

    return (f"Token Name: {token.get('token_name')}\n"
            f"Symbol: {token.get('token_symbol')}\n"
            f"Price (USD): {token.get('price_usd')}\n"
            f"Market Cap: {token.get('market_cap')}\n"
            f"Security Score: {token.get('security_score')}\n"
            f"Token Age (days): {token.get('token_age_in_days')}\n"
            f"On-Chain Strength Index: {token.get('on_chain_strength_index')}\n"
            f"1-Day Holders Change: {holders_change.get('1d')}\n"
            f"1-Day Volume Change (USD): {volume_change.get('1d')}\n"
            f"1-Month Price Change (%): {price_change.get('1M')}\n")
