"""
LangChain + AWS Bedrock client for Claude models.

Two models are used:
  - Response generation: Claude Sonnet 4.6 (anthropic.claude-sonnet-4-6-20250514-v1:0)
  - Judge/evaluator: Claude Opus 4.6 (anthropic.claude-opus-4-6-20250514-v1:0)

Configurable via environment variables (see .env.example):
  - AWS_REGION                      (default: us-east-1)
  - BEDROCK_MODEL_ID                (default: anthropic.claude-sonnet-4-6-20250514-v1:0)
  - BEDROCK_JUDGE_MODEL_ID          (default: anthropic.claude-opus-4-6-20250514-v1:0)
  - BEDROCK_INPUT_PRICE_PER_M       (default: 3.0  — USD per 1M input tokens for Sonnet)
  - BEDROCK_OUTPUT_PRICE_PER_M      (default: 15.0 — USD per 1M output tokens for Sonnet)
  - BEDROCK_JUDGE_INPUT_PRICE_PER_M (default: 15.0 — USD per 1M input tokens for Opus)
  - BEDROCK_JUDGE_OUTPUT_PRICE_PER_M(default: 75.0 — USD per 1M output tokens for Opus)
  - BEDROCK_MAX_TOKENS              (default: 4096)
  - BEDROCK_TEMPERATURE             (default: 0.0)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import boto3
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage


def _get_bedrock_client():
    """Create a Bedrock runtime client using the default profile."""
    from botocore.config import Config

    region = os.getenv("AWS_REGION", "us-east-1")
    profile = os.getenv("AWS_PROFILE_OVERRIDE", "default")

    config = Config(
        read_timeout=300,
        connect_timeout=60,
        retries={"max_attempts": 3}
    )

    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("bedrock-runtime", config=config)


# ---------------------------------------------------------------------------
# Pricing (USD per 1M tokens)
# ---------------------------------------------------------------------------

# Sonnet 4.6 pricing (response generation)
DEFAULT_INPUT_PRICE_PER_M = float(os.getenv("BEDROCK_INPUT_PRICE_PER_M", "3.0"))
DEFAULT_OUTPUT_PRICE_PER_M = float(os.getenv("BEDROCK_OUTPUT_PRICE_PER_M", "15.0"))

# Opus 4.6 pricing (judge/evaluator)
JUDGE_INPUT_PRICE_PER_M = float(os.getenv("BEDROCK_JUDGE_INPUT_PRICE_PER_M", "15.0"))
JUDGE_OUTPUT_PRICE_PER_M = float(os.getenv("BEDROCK_JUDGE_OUTPUT_PRICE_PER_M", "75.0"))


# ---------------------------------------------------------------------------
# Model IDs
# ---------------------------------------------------------------------------

# Response generation model — Claude Sonnet 4.6 (using cross-region inference profile)
DEFAULT_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-sonnet-4-6",
)

# Judge/evaluator model — Claude Opus 4.6 (using cross-region inference profile)
JUDGE_MODEL_ID = os.getenv(
    "BEDROCK_JUDGE_MODEL_ID",
    "us.anthropic.claude-opus-4-6-v1",
)


@dataclass
class LLMCallResult:
    """Everything we need to track from one LLM call."""
    response_text: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    latency_seconds: float
    model_id: str
    stop_reason: str | None = None


def get_chat_model(
    *,
    model_id: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatBedrockConverse:
    """Build a LangChain ChatBedrockConverse instance for response generation.

    Uses the Converse API which has consistent token-usage metadata across
    Anthropic models on Bedrock — easier than parsing per-model response
    schemas from InvokeModel.
    """
    return ChatBedrockConverse(
        model=model_id or DEFAULT_MODEL_ID,
        client=_get_bedrock_client(),
        max_tokens=max_tokens or int(os.getenv("BEDROCK_MAX_TOKENS", "4096")),
        temperature=(
            temperature
            if temperature is not None
            else float(os.getenv("BEDROCK_TEMPERATURE", "0.0"))
        ),
    )


def get_judge_model(
    *,
    model_id: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatBedrockConverse:
    """Build a LangChain ChatBedrockConverse instance for the judge/evaluator.

    Uses Claude Opus 4.6 by default.
    """
    return ChatBedrockConverse(
        model=model_id or JUDGE_MODEL_ID,
        client=_get_bedrock_client(),
        max_tokens=max_tokens or int(os.getenv("BEDROCK_MAX_TOKENS", "4096")),
        temperature=(
            temperature
            if temperature is not None
            else float(os.getenv("BEDROCK_TEMPERATURE", "0.0"))
        ),
    )


def call_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    model: ChatBedrockConverse | None = None,
    input_price_per_m: float = DEFAULT_INPUT_PRICE_PER_M,
    output_price_per_m: float = DEFAULT_OUTPUT_PRICE_PER_M,
) -> LLMCallResult:
    """Invoke the model and capture token usage + latency + cost."""
    if model is None:
        model = get_chat_model()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    start = time.time()
    response = model.invoke(messages)
    latency = time.time() - start

    # ChatBedrockConverse populates `usage_metadata` (LangChain standard).
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)

    # Fallback to response_metadata if usage_metadata is empty
    if input_tokens == 0 and output_tokens == 0:
        meta = getattr(response, "response_metadata", {}) or {}
        usage_alt = meta.get("usage", {})
        input_tokens = int(usage_alt.get("input_tokens", 0) or 0)
        output_tokens = int(usage_alt.get("output_tokens", 0) or 0)

    input_cost = (input_tokens / 1_000_000) * input_price_per_m
    output_cost = (output_tokens / 1_000_000) * output_price_per_m

    # Response content can be a string or a list of content blocks
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif "text" in block:
                    text_parts.append(block["text"])
            elif isinstance(block, str):
                text_parts.append(block)
        response_text = "\n".join(text_parts)
    else:
        response_text = str(content)

    stop_reason = (response.response_metadata or {}).get("stop_reason")

    return LLMCallResult(
        response_text=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=input_cost + output_cost,
        latency_seconds=latency,
        model_id=model.model_id if hasattr(model, "model_id") else str(model.model),
        stop_reason=stop_reason,
    )
