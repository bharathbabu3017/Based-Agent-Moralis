"""Offline unit tests: no API keys or network access required."""

from unittest.mock import MagicMock, patch

import pytest
from swarm.util import function_to_json

from based_agent import config
from based_agent.abis import L2_RESOLVER_ADDRESS_TESTNET
from based_agent.agent import based_agent
from based_agent.tools import moralis, onchain
from based_agent.tools.common import tool

ADDRESS = "0x0000000000000000000000000000000000000001"


def test_tool_decorator_returns_error_string():

    @tool("doing a thing")
    def boom() -> str:
        """Docstring."""
        raise ValueError("bad input")

    assert boom() == "Error doing a thing: bad input"
    assert boom.__name__ == "boom"
    assert boom.__doc__ == "Docstring."


def test_agent_tool_schemas_keep_names_and_types():
    schemas = {
        s["function"]["name"]: s["function"]
        for s in map(function_to_json, based_agent.functions)
    }

    assert "get_trending_tokens" in schemas
    swap = schemas["swap_assets"]["parameters"]
    assert swap["properties"]["amount"]["type"] == "number"
    assert swap["required"] == ["amount", "from_asset_id", "to_asset_id"]
    assert schemas["swap_assets"]["description"].strip()


def test_register_args_strip_suffix_and_use_testnet_resolver():
    args = onchain.create_register_contract_method_args(
        "myagent.basetest.eth", ADDRESS, is_mainnet=False)

    name, owner, duration, resolver, data, reverse = args["request"]
    assert name == "myagent"
    assert owner == ADDRESS
    assert duration == onchain.BASENAME_REGISTRATION_SECONDS
    assert resolver == L2_RESOLVER_ADDRESS_TESTNET
    assert len(data) == 2 and all(d.startswith("0x") for d in data)
    assert reverse is True


@pytest.fixture
def moralis_response(monkeypatch):
    """Patch requests.get and return the mock so tests can set a JSON body."""
    monkeypatch.setattr(config, "MORALIS_API_KEY", "test-key")
    response = MagicMock()
    with patch("based_agent.tools.moralis.requests.get",
               return_value=response) as get:
        yield response, get


def test_moralis_tools_require_api_key(monkeypatch):
    monkeypatch.setattr(config, "MORALIS_API_KEY", None)
    assert "MORALIS_API_KEY" in moralis.get_trending_tokens()


def test_trending_tokens_respects_limit(moralis_response):
    response, get = moralis_response
    response.json.return_value = [{
        "token_name": f"Token{i}",
        "token_symbol": f"T{i}",
        "token_address": ADDRESS,
    } for i in range(5)]

    result = moralis.get_trending_tokens(limit=2)

    assert "Token1" in result and "Token2" not in result
    assert get.call_args.kwargs["headers"]["X-API-Key"] == "test-key"
    assert get.call_args.kwargs["timeout"] == moralis.REQUEST_TIMEOUT_SECONDS


def test_token_details_tolerates_missing_nested_fields(moralis_response):
    response, _ = moralis_response
    response.json.return_value = {"token_name": "Degen", "token_symbol": "DEGEN"}

    with patch.object(moralis, "wallet_is_mainnet", return_value=True):
        result = moralis.get_token_details(ADDRESS)

    assert result.startswith("Token Name: Degen")
    assert "1-Day Holders Change: None" in result


def test_wallet_tokens_uses_wallet_network(moralis_response):
    response, get = moralis_response
    response.json.return_value = {"result": []}

    with patch.object(moralis, "wallet_address", return_value=ADDRESS), \
         patch.object(moralis, "wallet_is_mainnet", return_value=False):
        result = moralis.get_wallet_tokens()

    assert result == f"No tokens found for wallet {ADDRESS}."
    assert get.call_args.kwargs["params"] == {"chain": "base sepolia"}


def test_swap_refuses_on_testnet():
    with patch.object(onchain, "wallet_is_mainnet", return_value=False):
        assert onchain.swap_assets(1, "eth", "usdc").startswith("Error")
