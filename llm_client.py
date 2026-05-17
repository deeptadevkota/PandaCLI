import json
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


def wait_for_server():
    """Poll until the server can complete a trivial prompt."""
    print("Waiting for server to be ready", end="", flush=True)
    while True:
        try:
            resp = requests.post(
                f"{SERVER_URL}/completion",
                json={"prompt": "Hi", "n_predict": 1},
                timeout=10,
            )
            resp.raise_for_status()
            print(" ready!")
            return
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.HTTPError):
            print(".", end="", flush=True)
            time.sleep(10)


def format_prompt(user_message: str) -> str:
    """Wrap the user message in the Gemma 3 IT chat template."""
    return (
        f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
        f"<start_of_turn>user\n{user_message}<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )


def ask_llm(prompt: str) -> str:
    """Stream the completion and print tokens as they arrive."""
    payload = {
        "prompt": format_prompt(prompt),
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
        "stream": True,
    }

    full_response = []
    with requests.post(f"{SERVER_URL}/completion", json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            chunk = json.loads(line[len("data: "):])
            token = chunk.get("content", "")
            print(token, end="", flush=True)
            full_response.append(token)
            if chunk.get("stop"):
                break

    return "".join(full_response)


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

            print("\nLLM: ", end="", flush=True)
            ask_llm(user_input)
            print()  # newline after streamed response

    finally:
        server.terminate()