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

## Findings
For most fields the Clairic AI did a good job extracting details, but importantly had some confusion with the 
details related to individual items at time.  I tried to get it to extract `item_name` but it almost universally
failed at extracting this field, often extracting more names than actual items.  This seemed to be confusion in
how the AI was splitting the item detail lines generated in the emails, sometimes partially picking up the start of
an item id as part of the name.  Prices, quantities, and item ids tended to be more reliable for extraction.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- An API key for OpenAI or any OpenAI-compatible provider (for email generation)
- An Auth-token for [(Clairic)](https://developers.cloudflare.com/workers-ai/models/clairic/)

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
`OPENAI_API_KEY` is the only required setting for OpenAI. The others fall back to
`gpt-4o-mini`, the default OpenAI endpoint, and a built-in system message.

## Prompt files

There are 2 prompt files:
- `prompts/email-generation.md` — This is used by the Email Generator to create a synthetic dataset for purchase emails.
- `prompts/email-evaluation.json` — This is a [(Clairic)](https://developers.cloudflare.com/workers-ai/models/clairic/) prompt file extracting order-related information from emails.

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

## Using Clairic to extract order details from the emails
The app in `main.py` iterates through the synthetic emails that have been generated over in the `data/` directory 
one at a time and submits them to Clairic for order details extraction.  The data is mapped to the `Order` dataclass.
The app does not include extensive data validation but will report if there is a mismatch in the extracted lengths
of the three arrays that represent the order item details. If the sizes are mismatched, the `items list` will be
empty in the output. These are:

- `item_id`
- `item_quantity`
- `item_price`

There is an argument to be made that if I wasn't working with such variety in the synthetic dataset for `item_id`, 
we might be able to define a better `instruction` for the extraction AI to increase success in this area by 
describing the format of the `item_id` field in the synthetic emails.  I'm leaving this an exercise for the reader.

## Project layout

```
clairic-test/
├── prompts/
│   ├── email-evaluation.json   # Clairic prompt template for 
│   └── email-generation.md     # LLM Prompt to generate synthetic emails
├── scripts/
│   └── generate_emails.py      # the generator (installed as `generate`)
├── models/
│   └── order.py                # Dataclasses for order details
├── data/                       # generated output, gitignored
└── main.py                     # clairic extraction request
```
