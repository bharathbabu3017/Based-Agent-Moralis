"""Definition of the Based Agent and the tools it can call.

To add a tool:
  1. Write a function in ``based_agent/tools/`` that returns a string. Use type
     hints and a descriptive docstring - Swarm turns both into the tool schema
     the model sees.
  2. Decorate it with ``@tool("doing something")`` so failures are reported to
     the model instead of crashing the loop.
  3. Add it to ``build_functions()`` below.
"""

from swarm import Agent

from based_agent import config
from based_agent.tools import moralis, onchain

INSTRUCTIONS = """\
You are a specialized investment agent on the Base Layer 2 blockchain, designed \
to optimize an existing portfolio by analyzing and trading trending tokens. Your \
primary goal is to identify profitable tokens in the market, review wallet \
balances, and make calculated swap decisions to enhance the portfolio value.

Follow these steps when making investment decisions:
1. Use trending data to identify promising tokens with potential profit.
2. For each trending token, retrieve detailed information and trading pairs to \
evaluate its market cap, liquidity, and security.
3. Check the wallet balance to understand the available assets and decide on a \
safe percentage to invest.
4. Execute swaps to acquire trending tokens, ensuring the chosen amount aligns \
with profitability goals and balance management.

Make data-driven decisions based on token performance, wallet balance, and \
profitability, while maximizing portfolio value with each trade. Never risk the \
entire balance on a single trade, and always keep enough ETH for gas. If a tool \
returns an error, explain it rather than retrying blindly."""


def build_functions() -> list:
    functions = [
        # Onchain actions (CDP)
        onchain.create_token,
        onchain.request_eth_from_faucet,
        onchain.deploy_nft,
        onchain.mint_nft,
        onchain.swap_assets,
        onchain.register_basename,
        # Market and wallet data (Moralis)
        moralis.get_token_metadata,
        moralis.get_wallet_tokens,
        moralis.get_trending_tokens,
        moralis.get_wallet_pnl,
        moralis.get_wallet_nfts,
        moralis.get_token_pairs,
        moralis.get_token_details,
    ]

    if config.ENABLE_ART_GENERATION:
        functions.append(onchain.generate_art)

    if config.TWITTER_ENABLED:
        from based_agent.tools import twitter

        functions += [
            twitter.post_to_twitter,
            twitter.check_twitter_mentions,
            twitter.reply_to_twitter_mention,
            twitter.search_twitter,
        ]

    return functions


based_agent = Agent(
    name="Based Agent",
    model=config.OPENAI_MODEL,
    instructions=INSTRUCTIONS,
    functions=build_functions(),
)
