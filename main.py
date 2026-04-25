import argparse
import hashlib
import os
import random
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# ---------- Defaults (designed to conserve quota) ----------

DEFAULT_MODELS = ["gemini-2.5-flash", "gemini-3-flash-preview"]

DEFAULT_SYSTEM = (
    "Design minimal API endpoints and JSON schemas for the MVP.\n"
    "Prefer structured output. Provide request/response examples.\n"
    "Return:\n"
    "1) Endpoints table (method, path, purpose)\n"
    "2) JSON Schema for each request/response\n"
    "3) Example requests/responses\n"
    "4) Error codes and example error payloads\n"
)

CACHE_DIR = Path(".cache")
OUT_DIR = Path("outputs")


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def jitter_sleep(seconds: float):
    time.sleep(seconds * random.uniform(0.8, 1.2))


def parse_args():
    p = argparse.ArgumentParser("Gemini quota-friendly runner")
    p.add_argument("--prompt", help="Prompt text")
    p.add_argument("--prompt-file", help="Path to prompt file")
    p.add_argument("--system-file", help="Path to system instruction file")
    p.add_argument("--models", help="Comma-separated models (fallback order)")
    p.add_argument("--max-output-tokens", type=int, default=900)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--attempts", type=int, default=5, help="Attempts per model")
    p.add_argument("--initial-backoff", type=float, default=2.0)
    p.add_argument("--max-backoff", type=float, default=45.0)
    p.add_argument("--no-cache", action="store_true")
    return p.parse_args()


def main():
    # SDK can read GEMINI_API_KEY from env; this is the recommended setup in docs. 
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        eprint('ERROR: Set $env:GEMINI_API_KEY="YOUR_KEY" in this terminal.')
        sys.exit(2)

    args = parse_args()

    # Prompt loading
    prompt = args.prompt
    if not prompt and args.prompt_file:
        prompt = read_text(Path(args.prompt_file))
    if not prompt:
        eprint("ERROR: Provide --prompt or --prompt-file")
        sys.exit(2)

    # System instruction loading
    system_text = DEFAULT_SYSTEM
    if args.system_file:
        system_text = read_text(Path(args.system_file))

    # Models
    models = DEFAULT_MODELS
    if args.models:
        models = [m.strip() for m in args.models.split(",") if m.strip()]

    # Prepare dirs
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cache key
    cache_key = sha("|".join(models) + "|" + system_text + "|" + prompt + f"|{args.max_output_tokens}|{args.temperature}")
    cache_file = CACHE_DIR / f"{cache_key}.txt"

    if not args.no_cache and cache_file.exists():
        eprint(f"[cache] hit: {cache_file}")
        print(cache_file.read_text(encoding="utf-8"))
        return

    client = genai.Client()  # picks env key automatically 

    config = types.GenerateContentConfig(
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        system_instruction=[types.Part.from_text(text=system_text)],
        # Tools and "thinking" intentionally not enabled to reduce quota usage
    )

    last_err = None

    for model in models:
        backoff = args.initial_backoff
        eprint(f"\n==> Trying model: {model}")

        for attempt in range(1, args.attempts + 1):
            try:
                eprint(f"[{model}] attempt {attempt}/{args.attempts}")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                text = response.text or ""
                if not text.strip():
                    raise RuntimeError("Empty response text")

                # Save output
                out_path = OUT_DIR / f"result_{cache_key[:10]}_{model.replace(':','_')}.txt"
                out_path.write_text(text, encoding="utf-8")
                eprint(f"[out] wrote: {out_path}")

                # Save cache
                if not args.no_cache:
                    cache_file.write_text(text, encoding="utf-8")
                    eprint(f"[cache] saved: {cache_file}")

                print(text)
                return

            except genai_errors.ClientError as ce:
                last_err = ce
                msg = str(ce)
                eprint(f"[{model}] ClientError: {msg}")

                # If 429 or transient, backoff+retry
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    eprint(f"[{model}] rate limit/quota hit -> backing off {backoff:.1f}s")
                    jitter_sleep(backoff)
                    backoff = min(backoff * 2, args.max_backoff)
                    continue

                # non-retryable client error
                break

            except Exception as ex:
                last_err = ex
                eprint(f"[{model}] Exception: {ex} -> backing off {backoff:.1f}s")
                jitter_sleep(backoff)
                backoff = min(backoff * 2, args.max_backoff)

        eprint(f"[{model}] exhausted attempts, moving to next model...")

    eprint("\nFAILED ❌")
    eprint(f"Last error: {last_err}")
    eprint(
        "\nIf this is 429 RESOURCE_EXHAUSTED, you’re out of quota or hitting limits.\n"
        "Rate limits are enforced across RPM/TPM/RPD and daily quotas reset at midnight Pacific time. \n"
        "Check https://ai.dev/rate-limit or enable billing/tier to increase quota. "
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
