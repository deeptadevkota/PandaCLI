import os
import subprocess
import time
import requests
from config import MODEL_PATH, SERVER_PORT, SERVER_URL, TEMPERATURE, TOP_P, TOP_K


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


# TODO: Use streaming here
# TODO: Apply system prompt
# TODO: Refine prompt format for gemma 4
def ask_llm(prompt: str) -> str:
    payload = {
        "prompt": prompt,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
    }

    r = requests.post(f"{SERVER_URL}/completion", json=payload)
    return r.json()["content"]


if __name__ == "__main__":
    print("Starting LLM server...")
    server = start_server()

    # TODO: Instead of a predefined wait, keeping pinging the server to know if it is alive
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