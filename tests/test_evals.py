"""Tool-selection evals: check the model picks the right tool for a request.

Tools are not executed, so no wallet or Moralis key is needed, but these call
the OpenAI API and cost a small amount. Run with: pytest -m evals
"""

import os

import pytest
from swarm import Swarm

from based_agent.agent import based_agent

pytestmark = [
    pytest.mark.evals,
    pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"),
                       reason="OPENAI_API_KEY not set"),
]


def first_tool_call(query: str) -> str | None:
    response = Swarm().run(
        agent=based_agent,
        messages=[{"role": "user", "content": query}],
        execute_tools=False,
    )
    tool_calls = response.messages[-1].get("tool_calls")
    return tool_calls[0]["function"]["name"] if tool_calls else None


@pytest.mark.parametrize(
    ("query", "expected_tool"),
    [
        ("What tokens are trending on Base right now?", "get_trending_tokens"),
        ("Which tokens do I hold in my wallet?", "get_wallet_tokens"),
        ("How much profit have I made on my trades?", "get_wallet_pnl"),
        ("Show me the NFTs in my wallet.", "get_wallet_nfts"),
        ("What DEX pairs exist for token 0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed?",
         "get_token_pairs"),
        ("Deploy an ERC-20 token called Based Coin, symbol BASED, supply 1000000.",
         "create_token"),
    ],
)
def test_calls_expected_tool(query, expected_tool):
    assert first_tool_call(query) == expected_tool


def test_does_not_call_tools_for_small_talk():
    assert first_tool_call("Hi! What's your name?") is None
