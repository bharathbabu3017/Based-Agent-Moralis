"""Tools that act onchain through the agent's CDP wallet."""

from openai import OpenAI
from web3 import Web3

from based_agent.abis import (
    BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET,
    BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET,
    L2_RESOLVER_ABI,
    L2_RESOLVER_ADDRESS_MAINNET,
    L2_RESOLVER_ADDRESS_TESTNET,
    REGISTRAR_ABI,
)
from based_agent.tools.common import tool
from based_agent.wallet import get_wallet, wallet_address, wallet_is_mainnet

BASENAME_REGISTRATION_SECONDS = "31557600"  # 1 year


@tool("creating token")
def create_token(name: str, symbol: str, initial_supply: int) -> str:
    """
    Create a new ERC-20 token.

    Args:
        name (str): The name of the token
        symbol (str): The symbol of the token
        initial_supply (int): The initial supply of tokens

    Returns:
        str: A message confirming the token creation with details
    """
    deployed_contract = get_wallet().deploy_token(name, symbol, initial_supply)
    deployed_contract.wait()
    return (f"Token {name} ({symbol}) created with initial supply of "
            f"{initial_supply} and contract address "
            f"{deployed_contract.contract_address}")


@tool("requesting ETH from faucet")
def request_eth_from_faucet() -> str:
    """
    Request ETH from the Base Sepolia testnet faucet.

    Returns:
        str: Status message about the faucet request
    """
    if wallet_is_mainnet():
        return "Error: The faucet is only available on Base Sepolia testnet."

    faucet_tx = get_wallet().faucet()
    return f"Requested ETH from faucet. Transaction: {faucet_tx}"


@tool("generating artwork")
def generate_art(prompt: str) -> str:
    """
    Generate art using DALL-E based on a text prompt.

    Args:
        prompt (str): Text description of the desired artwork

    Returns:
        str: Status message about the art generation, including the image URL if successful
    """
    response = OpenAI().images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return f"Generated artwork available at: {response.data[0].url}"


@tool("deploying NFT contract")
def deploy_nft(name: str, symbol: str, base_uri: str) -> str:
    """
    Deploy an ERC-721 NFT contract.

    Args:
        name (str): Name of the NFT collection
        symbol (str): Symbol of the NFT collection
        base_uri (str): Base URI for token metadata

    Returns:
        str: Status message about the NFT deployment, including the contract address
    """
    deployed_nft = get_wallet().deploy_nft(name, symbol, base_uri)
    deployed_nft.wait()
    return (f"Successfully deployed NFT contract '{name}' ({symbol}) at address "
            f"{deployed_nft.contract_address} with base URI: {base_uri}")


@tool("minting NFT")
def mint_nft(contract_address: str, mint_to: str) -> str:
    """
    Mint an NFT to a specified address.

    Args:
        contract_address (str): Address of the NFT contract
        mint_to (str): Address to mint NFT to

    Returns:
        str: Status message about the NFT minting
    """
    mint_invocation = get_wallet().invoke_contract(
        contract_address=contract_address,
        method="mint",
        args={"to": mint_to, "quantity": "1"},
    )
    mint_invocation.wait()
    return f"Successfully minted NFT to {mint_to}"


@tool("swapping assets")
def swap_assets(amount: float, from_asset_id: str, to_asset_id: str) -> str:
    """
    Swap one asset for another using the trade function.
    This function only works on Base Mainnet.

    Args:
        amount (float): Amount of the source asset to swap
        from_asset_id (str): Source asset identifier (e.g. "eth", "usdc", or a token contract address)
        to_asset_id (str): Destination asset identifier

    Returns:
        str: Status message about the swap
    """
    if not wallet_is_mainnet():
        return "Error: Asset swaps are only available on Base Mainnet."

    trade = get_wallet().trade(amount, from_asset_id, to_asset_id)
    trade.wait()
    return f"Successfully swapped {amount} {from_asset_id} for {to_asset_id}"


def create_register_contract_method_args(base_name: str, address_id: str,
                                         is_mainnet: bool) -> dict:
    """
    Build the arguments for the Basenames registrar ``register`` method.

    Args:
        base_name (str): The full Basename (e.g. "example.base.eth" or "example.basetest.eth")
        address_id (str): The address the name should resolve to
        is_mainnet (bool): True if on mainnet, False if on testnet

    Returns:
        dict: Formatted arguments for the register contract method
    """
    w3 = Web3()
    resolver_contract = w3.eth.contract(abi=L2_RESOLVER_ABI)
    name_hash = w3.ens.namehash(base_name)

    address_data = resolver_contract.encode_abi("setAddr",
                                                args=[name_hash, address_id])
    name_data = resolver_contract.encode_abi("setName",
                                             args=[name_hash, base_name])

    suffix = ".base.eth" if is_mainnet else ".basetest.eth"
    resolver = L2_RESOLVER_ADDRESS_MAINNET if is_mainnet else L2_RESOLVER_ADDRESS_TESTNET

    return {
        "request": [
            base_name.removesuffix(suffix),
            address_id,
            BASENAME_REGISTRATION_SECONDS,
            resolver,
            [address_data, name_data],
            True,
        ]
    }


@tool("registering basename")
def register_basename(basename: str, amount: float = 0.002) -> str:
    """
    Register a basename for the agent's wallet.

    Args:
        basename (str): The basename to register (e.g. "myname.base.eth" or "myname.basetest.eth")
        amount (float): Amount of ETH to pay for registration (default 0.002)

    Returns:
        str: Status message about the basename registration
    """
    address_id = wallet_address()
    is_mainnet = wallet_is_mainnet()

    suffix = ".base.eth" if is_mainnet else ".basetest.eth"
    if not basename.endswith(suffix):
        basename += suffix

    contract_address = (BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET
                        if is_mainnet else
                        BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET)

    invocation = get_wallet().invoke_contract(
        contract_address=contract_address,
        method="register",
        args=create_register_contract_method_args(basename, address_id,
                                                  is_mainnet),
        abi=REGISTRAR_ABI,
        amount=amount,
        asset_id="eth",
    )
    invocation.wait()
    return f"Successfully registered basename {basename} for address {address_id}"
