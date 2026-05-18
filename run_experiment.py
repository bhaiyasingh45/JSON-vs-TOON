"""
CLI entry point — runs the full TOON vs JSON benchmark and saves artifacts.

Usage:
    python run_experiment.py                       # full run with LLM-judge scoring
    python run_experiment.py --no-score            # skip scoring (cheaper)
    python run_experiment.py --dry-run             # just show encoded sizes, no LLM call
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()  # pick up .env before importing core (which reads env vars)

from encoders import encode_agent_data_json, encode_agent_data_toon  # noqa: E402
from agents import get_full_payload  # noqa: E402

# core.experiment is imported lazily inside main() so that --dry-run works
# without requiring langchain-aws / boto3 to be installed.


def _dry_run() -> None:
    """Just show the encoded payload sizes without any LLM call."""
    payload = get_full_payload()
    agent_results = payload["agent_results"]

    json_pretty = encode_agent_data_json(agent_results, pretty=True)
    json_compact = encode_agent_data_json(agent_results, pretty=False)
    toon = encode_agent_data_toon(agent_results)

    print("Encoded sizes (chars):")
    print(f"  JSON pretty:  {len(json_pretty):>8,}")
    print(f"  JSON compact: {len(json_compact):>8,}")
    print(f"  TOON:         {len(toon):>8,}")
    print()
    print("Rough token estimates (chars/4):")
    print(f"  JSON pretty:  ~{len(json_pretty)//4:>7,}")
    print(f"  JSON compact: ~{len(json_compact)//4:>7,}")
    print(f"  TOON:         ~{len(toon)//4:>7,}")
    print()
    print("TOON savings vs JSON pretty:  "
          f"{100 - len(toon)*100/len(json_pretty):.1f}%")
    print("TOON savings vs JSON compact: "
          f"{100 - len(toon)*100/len(json_compact):.1f}%")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the TOON vs JSON Bedrock benchmark."
    )
    parser.add_argument(
        "--no-score",
        action="store_true",
        help="Skip the LLM-as-judge scoring step (saves cost).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show encoded payload sizes without calling the LLM.",
    )
    args = parser.parse_args()

    if args.dry_run:
        _dry_run()
        return 0

    try:
        # Lazy import — only loaded when we actually need AWS
        from experiment import run_experiment
        run_experiment(score_responses=not args.no_score)
    except Exception as e:
        print(f"\n✗ Experiment failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
