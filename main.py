import json
import os
import time
from typing import Dict, Any, List

import requests
from pathlib import Path

from dotenv import load_dotenv

from models import Order

load_dotenv()
ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT")
AUTH_TOKEN = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
PROMPTS_DIR = REPO_ROOT / "prompts"

def load_prompt() -> Dict[str, Any]:
    """
    Loads the Clairic AI prompt from a JSON file
    An email should be assigned to the "state" field before submitting to Clairic
    :return: the prompt as a JSON dictionary
    """
    with open(PROMPTS_DIR / "email-evaluation.json", "r") as f:
        return json.load(f)

def load_email(filename: str) -> str:
    """
    Loads a single email file as a string
    :param filename:
    :return: The contents of the file
    """
    with open(DATA_DIR / filename, "r") as f:
        return f.read()

def find_email_list() -> List[str]:
    """
    Finds all email files in the data directory
    :return: A list of filenames
    """
    return [f.name for f in DATA_DIR.iterdir() if f.is_file() and f.suffix == ".txt"]

def ask_clairic(prompt: Dict[str, Any], email: str):

    prompt["state"] = email

    response = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/cloudflare/clairic",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json=prompt
    )

    answers = response.json()["result"]["answers"]

    order = Order.from_dict(answers)
    return order

def main() -> int:
    prompt = load_prompt()
    count = 0
    email_list = find_email_list()
    total_processing_time = time.perf_counter_ns()
    for email_file in email_list:
        count += 1
        email = load_email(email_file)

        processing_time = time.perf_counter_ns()
        order = ask_clairic(prompt, email)
        print(f"File: {email_file}, Order: {order}")
        if len(order.items) == 0:
            print("- Error: Mismatched item_id, item_price, and item_quantity lists")
        print("Processing time (ms):", (time.perf_counter_ns() - processing_time) / 1000000)
        print("------\n")

    print(f"Total processing time for {count} orders in (ms): {(time.perf_counter_ns() - total_processing_time) / 1000000}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())


