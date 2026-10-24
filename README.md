# Email to Order Example with Clairic

Synthetic data experiments for the [Cloudflare - Clairic AI](https://blog.cloudflare.com/clairic-extraction-model/)
Clairic is a System One Extraction Model capable of extracting structured data from unstructured text.

This repo contains two things:

- **`main.py`** — Sends a series of requests (one per generated synthetic email) to the Clairic AI 
  model [(docs)](https://developers.cloudflare.com/workers-ai/models/clairic/) extracting structured data 
  from that email and judging how well it was able to obtain a proper purchase order from the unstructured email.
- **`The email generator`** — a small CLI that asks an OpenAI-compatible chat model
  to write synthetic business emails from a configurable prompt file and saves
  each one as its own timestamped `.txt` file. Use it to build a test corpus for
  the `main.py` application to process.  (See [Generating Emails](#generating-emails))
- 
   - It can be run with `uv run generate --count {number of emails}`

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- An API key for OpenAI or any OpenAI-compatible provider

## Setup

```sh
uv sync
```

Add your credentials to `.env` in the repo root (see examples provided)

```sh
# Cloudflare - Clairic settings
CLOUDFLARE_ACCOUNT={account-num}
CLOUDFLARE_AUTH_TOKEN={auth-token}

# Synthetic email generator settings (scripts/generate_emails.py)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY={your-api-key}
OPENAI_MODEL=gpt-4o-mini

# Optional: override the system message sent with every request
# SYSTEM_PROMPT=You write realistic business emails.
```
`CLOUDFLARE_ACCOUNT` is required for running the `main.py` app and using the [Cloudflare - Clairic](https://docs.astral.sh/clairic/) model
`OPENAI_API_KEY` is the only required setting. The others fall back to
`gpt-4o-mini`, the default OpenAI endpoint, and a built-in system message.

## Writing a prompt

The prompt file holds the user message. **One API call produces one email**, so
ask for a single message and tell the model to return only the email text — no
commentary, no preamble.

The starter prompt lives at `prompts/email-generation.md` and describes a purchase-order email.


> Please accept this email as a formal order for the following items:
>
> Item: Ergonomic Desk Chair (Model #EC-100) — Quantity: 4 — Unit Price: $150.00
>
> Have it delivered to: Acme Corporation, Attn: Jane Doe, Suite 400 ...

Add more prompt files to `prompts/` if you want alternate scenarios; pass
`--prompt <name>` to select one.

## Generating emails

```sh
# 10 emails from prompts/email-generation.md into ./data (the defaults)
uv run generate

# a larger batch
uv run generate --count 25

# a different prompt by name, or by path
uv run generate --count 5 --prompt order-invoice
uv run generate --count 5 --prompt ~/prompts/custom.txt

# more variety, different model, different output folder
uv run generate --temperature 0.9 --model gpt-4o --out /tmp/emails
```

| Flag                   | Default        | Meaning                                              |
| ---------------------- | -------------- | ---------------------------------------------------- |
| `--count`              | `10`           | number of emails to generate                         |
| `--prompt`             | `email`        | name inside `prompts/`, or a path to a prompt file   |
| `--out`                | `data`         | output directory, created if missing                 |
| `--temperature`        | `0.7`          | sampling temperature                                 |
| `--model`              | `OPENAI_MODEL` | model name, overrides the env var                    |
| `--max-output-tokens`  | `2048`         | maximum tokens per response                          |

## Output

Each email is written to its own file:

```
data/2026-10-22_14-30-12-001.txt
data/2026-10-22_14-30-12-002.txt
```

The prefix is the run's start time in local time (`YYYY-MM-DD_HH-MM-SS`) and the
suffix is the zero-padded sequence number, so files sort in generation order.
Every file in a run shares the same timestamp. Responses are cleaned before
writing: markdown code fences are stripped and surrounding blank lines removed.

`data/` is gitignored and files accumulate across runs — nothing is ever
overwritten.

## Behavior on failure

The generator fails immediately. An API error, a missing/empty prompt file, a
missing API key, or an empty response prints an `error:` message to stderr and
exits with status 1. Emails from earlier in the run stay on disk, so a failed
run leaves `001.txt` … `00N.txt` for whatever succeeded before the failure.
There are no automatic retries.

## Project layout

```
clairic-test/
├── prompts/
│   └── email.txt               # user prompt, one email per call
├── scripts/
│   └── generate_emails.py      # the generator (installed as `generate`)
├── data/                       # generated output, gitignored
└── main.py                     # clairic extraction request
```
