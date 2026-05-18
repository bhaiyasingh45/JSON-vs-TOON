"""
The core package re-exports only AWS-free modules at the top level.

LLM / experiment modules (which depend on langchain-aws and boto3) should
be imported directly via `from core.experiment import run_experiment` or
`from core.llm import call_llm` so that the format-only utilities (encoders,
prompts) can be used standalone — e.g. for the `--dry-run` check or in unit
tests — without requiring AWS dependencies to be installed.
"""

from .encoders import (
    encode_agent_data_json,
    encode_agent_data_toon,
    encode_json,
    encode_toon,
)
from .prompts import SYSTEM_PROMPT, TOON_FORMAT_HINT, build_user_prompt

__all__ = [
    "encode_agent_data_json",
    "encode_agent_data_toon",
    "encode_json",
    "encode_toon",
    "SYSTEM_PROMPT",
    "TOON_FORMAT_HINT",
    "build_user_prompt",
]
