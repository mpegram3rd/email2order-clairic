"""Generate a corpus of synthetic emails from a prompt file.

Each invocation asks an OpenAI-compatible chat model for one email per API
call and writes the cleaned response to its own timestamped .txt file.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PROMPTS_DIR = REPO_ROOT / "prompts"
DEFAULT_PROMPT = "email-generation"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.85 # Juice the creativity a bit

# General guidance on email generation: Plaintext and all dates need to be in the future from the run date
DEFAULT_SYSTEM_PROMPT = (
    "You write realistic, internally consistent business emails. "
    "Return exactly one email as plain text, with no commentary, headings, "
    "or markdown formatting. Do not write HTML or Markdown, only plain text. "
    f"Today's date is {datetime.now().strftime('%Y-%m-%d')} "
    "so it is vitally important that any generated dates occur after that date."
)

# This really shouldn't be needed but can't hurt.  Will clean out any generated markdown style code.
FENCE_RE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)

def load_settings(args: argparse.Namespace) -> dict[str, object]:
    """
    Gather configuration information with some sensible fallback values

    :param args:
    :return:
    """
    """Resolve configuration from the environment and CLI overrides."""
    load_dotenv(REPO_ROOT / ".env")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        fail("OPENAI_API_KEY is not set. Add it to .env or the environment.")

    return {
        "api_key": api_key,
        "base_url": os.environ.get("OPENAI_BASE_URL") or None,
        "model": args.model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL,
        "system_prompt": os.environ.get("SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT,
        "count": args.count,
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
        "out_dir": Path(args.out).expanduser().resolve(),
    }

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command line arguments

    :param argv:
    :return:
    """
    parser = argparse.ArgumentParser(
        prog="generate",
        description="Generate synthetic emails from a prompt file.",
    )
    parser.add_argument(
        "--count",
        type=positive_int,
        default=10,
        help="number of emails to generate (default: 10)",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="prompt filename inside prompts/ or a path to a prompt file "
        f"(default: {DEFAULT_PROMPT})",
    )
    parser.add_argument(
        "--out",
        default="data",
        help="output directory, created if missing (default: data)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.85,
        help="sampling temperature (default: 0.85)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="model name, overrides OPENAI_MODEL",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=positive_int,
        default=2048,
        help="maximum tokens per response (default: 2048)",
    )
    return parser.parse_args(argv)


def load_prompt(argument: str) -> str:
    """Resolve a prompt name or path to the contents of the file if found"""
    candidate = Path(argument).expanduser()
    if not candidate.suffix and os.sep not in argument:
        candidate = PROMPTS_DIR / f"{argument}.md"

    if not candidate.is_file():
        fail(f"Prompt file not found: {candidate}")

    text = candidate.read_text(encoding="utf-8").strip()
    if not text:
        fail(f"Prompt file is empty: {candidate}")
    return text


def build_client(settings: dict[str, object]) -> OpenAI:
    try:
        return OpenAI(
            api_key=settings["api_key"],
            base_url=settings["base_url"],
        )
    except OpenAIError as exc:
        fail(f"Could not create OpenAI client: {exc}")


def generate_one(
    client: OpenAI,
    settings: dict[str, object],
    prompt: str,
) -> str:
    """
    Generates a single email from the given prompt using the provided LLM client.

    :param client:
    :param settings:
    :param prompt:
    :return:
    """
    try:
        response = client.chat.completions.create(
            model=settings["model"],
            messages=[
                {"role": "system", "content": settings["system_prompt"]},
                {"role": "user", "content": prompt},
            ],
            temperature=settings["temperature"],
        )
    except OpenAIError as exc:
        fail(f"API request failed: {exc}")

    choices = response.choices
    if not choices or not choices[0].message.content:
        fail("API returned an empty response.")

    text = clean(choices[0].message.content)
    if not text:
        fail("API returned a response with no usable content.")
    return text


def clean(text: str) -> str:
    """Strip markdown code fences and surrounding blank lines."""
    match = FENCE_RE.match(text)
    if match:
        text = match.group(1)
    return text.strip()


def write_email(out_dir: Path, run_stamp: str, index: int, body: str) -> Path:
    """
    Outputs the generated email to a file in the specified directory.

    :param out_dir: The directory where the email will be saved.
    :param run_stamp: A timestamp or identifier for the current run.
    :param index: The index of the email within the current run.
    :param body: The content of the email.
    :return: The path to the saved email file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_stamp}-{index:03d}.txt"
    path.write_text(body + "\n", encoding="utf-8")
    return path


def fail(message: str) -> None:
    """
    Make app go 💥 with an error message.

    :param message: The error message to display.
    :return: None
    """
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def positive_int(value: str) -> int:
    """
    Validates and converts a string to a positive integer.

    :param value: The string to be converted.
    :return: The positive integer value.
    :raises argparse.ArgumentTypeError: If the input is not a valid positive integer.
    """
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}")
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = load_settings(args)
    prompt = load_prompt(args.prompt)

    client = build_client(settings)

    run_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = settings["out_dir"]
    written = 0

    for index in range(1, int(settings["count"]) + 1):
        timer = time.perf_counter_ns()
        body = generate_one(client, settings, prompt)
        path = write_email(out_dir, run_stamp, index, body)
        written += 1
        print(f"wrote {path} in {(time.perf_counter_ns() - timer) / 1000000} ms")

    print(f"{written} email(s) written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
