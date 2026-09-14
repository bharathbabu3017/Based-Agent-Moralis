"""Entry point: run the Based Agent in chat, autonomous, or two-agent mode.

Usage:
    python run.py                    # pick a mode interactively
    python run.py --mode auto --interval 30
"""

import argparse
import sys
import time

from openai import OpenAI
from swarm import Swarm
from swarm.repl import run_demo_loop

from based_agent import config
from based_agent.agent import based_agent
from based_agent.wallet import ConfigError, get_wallet

MODES = {
    "1": "chat",
    "2": "auto",
    "3": "two-agent",
}

AUTONOMOUS_THOUGHT = (
    "Be creative and do something interesting on the Base blockchain. "
    "Don't take any more input from me. Choose an action and execute it now. "
    "Choose those that highlight your identity and abilities best.")

GUIDE_SYSTEM_PROMPT = (
    "You are a user guiding a blockchain agent through various tasks on the Base "
    "blockchain. Engage in a conversation, suggesting actions and responding to the "
    "agent's outputs. Be creative and explore different blockchain capabilities. "
    "Options include analyzing trending tokens, checking wallet balances and PnL, "
    "creating tokens, minting NFTs, and swapping assets. You're not simulating a "
    "conversation, but you will be in one yourself. Make sure you follow the rules "
    "of improv and always ask for some sort of function to occur. Be unique and "
    "interesting.")


def run_autonomous_loop(agent, interval: int = 10) -> None:
    """Prompt the agent to take an action every ``interval`` seconds."""
    client = Swarm()
    messages = []

    print("Starting autonomous Based Agent loop...")

    while True:
        messages.append({"role": "user", "content": AUTONOMOUS_THOUGHT})
        print(f"\n\033[90mAgent's Thought:\033[0m {AUTONOMOUS_THOUGHT}")

        response = client.run(agent=agent, messages=messages, stream=True)
        response_obj = process_and_print_streaming_response(response)
        messages.extend(response_obj.messages)

        time.sleep(interval)


def run_openai_conversation_loop(agent) -> None:
    """Let a second OpenAI model play the user and guide the Based Agent."""
    client = Swarm()
    openai_client = OpenAI()
    messages = []

    print("Starting OpenAI-Based Agent conversation loop...")

    openai_messages = [
        {"role": "system", "content": GUIDE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Start a conversation with the Based Agent and guide it "
                       "through some blockchain tasks.",
        },
    ]

    while True:
        openai_response = openai_client.chat.completions.create(
            model=config.OPENAI_GUIDE_MODEL, messages=openai_messages)
        openai_message = openai_response.choices[0].message.content
        openai_messages.append({"role": "assistant", "content": openai_message})
        print(f"\n\033[92mOpenAI Guide:\033[0m {openai_message}")

        messages.append({"role": "user", "content": openai_message})
        response = client.run(agent=agent, messages=messages, stream=True)
        response_obj = process_and_print_streaming_response(response)
        messages.extend(response_obj.messages)

        based_agent_response = (response_obj.messages[-1]["content"]
                                if response_obj.messages else
                                "No response from Based Agent.")
        openai_messages.append({
            "role": "user",
            "content": f"Based Agent response: {based_agent_response}",
        })

        user_input = input(
            "\nPress Enter to continue the conversation, or type 'exit' to end: ")
        if user_input.strip().lower() == "exit":
            break


def choose_mode() -> str:
    while True:
        print("\nAvailable modes:")
        print("1. chat      - Interactive chat mode")
        print("2. auto      - Autonomous action mode")
        print("3. two-agent - AI-to-agent conversation mode")

        choice = input("\nChoose a mode (enter number or name): ").lower().strip()
        mode = MODES.get(choice, choice)
        if mode in MODES.values():
            return mode
        print("Invalid choice. Please try again.")


def process_and_print_streaming_response(response):
    """Print a Swarm streaming response as it arrives and return the final Response."""
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if chunk.get("content") is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if chunk.get("tool_calls") is not None:
            for tool_call in chunk["tool_calls"]:
                name = tool_call["function"]["name"]
                if name:
                    print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if chunk.get("delim") == "end" and content:
            print()
            content = ""

        if "response" in chunk:
            return chunk["response"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Based Agent.")
    parser.add_argument("--mode",
                        choices=sorted(MODES.values()),
                        help="Mode to run in (prompted if omitted)")
    parser.add_argument("--interval",
                        type=int,
                        default=10,
                        help="Seconds between actions in auto mode (default: 10)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    missing = config.missing_required_env()
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}\n"
              "See .env.example for the full list.")
        return 1

    print("Starting Based Agent...")
    try:
        wallet = get_wallet()
    except ConfigError as e:
        print(f"Configuration error: {e}")
        return 1
    print(f"Agent wallet address: {wallet.default_address.address_id} "
          f"({wallet.network_id})")

    mode = args.mode or choose_mode()
    print(f"\nStarting {mode} mode...")

    try:
        if mode == "chat":
            run_demo_loop(based_agent, stream=True)
        elif mode == "auto":
            run_autonomous_loop(based_agent, interval=args.interval)
        else:
            run_openai_conversation_loop(based_agent)
    except KeyboardInterrupt:
        print("\nStopping Based Agent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
