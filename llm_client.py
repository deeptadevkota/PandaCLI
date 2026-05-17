import os
import subprocess
import time
import requests
from config import MODEL_PATH, SERVER_PORT, SERVER_URL, TEMPERATURE, TOP_P, TOP_K, SYSTEM_PROMPT


def start_server():
    cmd = [
        "llama-server",
        "-m", os.path.expanduser(MODEL_PATH),
        "--port", str(SERVER_PORT),
        "--temp", str(TEMPERATURE),
        "--top-p", str(TOP_P),
        "--top-k", str(TOP_K),
    ]

    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_server(timeout: int = 100):
    """Poll until the server is ready or timeout is reached."""
    print("Waiting for server to be ready", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"{SERVER_URL}/health", timeout=1)
            print(" ready!")
            return
        except requests.exceptions.ConnectionError:
            print(".", end="", flush=True)
            time.sleep(1)
    raise TimeoutError(f"LLM server did not become ready within {timeout}s")


def format_prompt(user_message: str) -> str:
    """Wrap the user message in the Gemma 3 IT chat template."""
    return (
        f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
        f"<start_of_turn>user\n{user_message}<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )


# TODO: Use streaming here
def ask_llm(prompt: str) -> str:
    payload = {
        "prompt": format_prompt(prompt),
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
    }

    r = requests.post(f"{SERVER_URL}/completion", json=payload)
    r.raise_for_status()
    data = r.json()
    if "content" not in data:
        raise RuntimeError(f"Unexpected response from server: {data}")
    return data["content"]


if __name__ == "__main__":
    print("Starting LLM server...")
    server = start_server()

    wait_for_server()

    print("LLM server has started...")

    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            response = ask_llm(user_input)
            print("\nLLM:", response)

    finally:
        server.terminate()