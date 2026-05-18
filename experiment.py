"""
Experiment orchestration.

Runs the same RCA task twice — once with JSON data, once with TOON — using
Claude Sonnet 4.6 for response generation. Captures token usage, cost, and
latency for the response generation calls only.

Optionally scores responses using Claude Opus 4.6 as the judge (scoring
metrics are tracked separately and not included in the main comparison).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from encoders import encode_agent_data_json, encode_agent_data_toon, encode_json
from llm import (
    LLMCallResult,
    call_llm,
    get_chat_model,
    get_judge_model,
    JUDGE_INPUT_PRICE_PER_M,
    JUDGE_OUTPUT_PRICE_PER_M,
)
from prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_evaluator_prompt,
    build_user_prompt,
)
from agents import CONTEXT, DIAGNOSTIC_QUERY, get_full_payload
from ground_truth import GROUND_TRUTH


ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


@dataclass
class FormatRunResult:
    """Result of one format run (JSON or TOON)."""
    format_name: str
    prompt_chars: int
    agent_data_chars: int
    llm_result: dict
    response_text: str
    scores: dict | None = None


@dataclass
class ExperimentResult:
    """Top-level experiment artifact."""
    timestamp: str
    model_id: str
    diagnostic_query: str
    runs: dict[str, dict]  # {"json": {...}, "toon": {...}}
    comparison: dict


def _format_context_str() -> str:
    """Human-readable context block for the prompt."""
    lines = [f"- {k}: {v}" for k, v in CONTEXT.items()]
    return "\n".join(lines)


def _format_agent_descriptions_str(payload: dict) -> str:
    """Markdown bulleted list of agent descriptions."""
    descriptions = payload["agent_descriptions"]
    return "\n".join(f"- **{name}**: {desc}" for name, desc in descriptions.items())


def _run_one_format(
    *,
    format_name: str,
    agent_data_encoded: str,
    payload: dict,
    model,
) -> FormatRunResult:
    """Run the response generation for one format."""
    user_prompt = build_user_prompt(
        query=DIAGNOSTIC_QUERY,
        context_str=_format_context_str(),
        agent_descriptions_str=_format_agent_descriptions_str(payload),
        agent_data=agent_data_encoded,
        format_label=format_name.upper(),
        include_toon_hint=(format_name == "toon"),
    )

    print(f"\n  → Calling Bedrock for {format_name.upper()} run...")
    print(f"    Prompt chars: {len(user_prompt):,}")
    print(f"    Agent data chars: {len(agent_data_encoded):,}")

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=model,
    )

    print(f"    Input tokens:  {result.input_tokens:,}")
    print(f"    Output tokens: {result.output_tokens:,}")
    print(f"    Cost USD:      ${result.total_cost_usd:.4f}")
    print(f"    Latency:       {result.latency_seconds:.2f}s")

    return FormatRunResult(
        format_name=format_name,
        prompt_chars=len(user_prompt),
        agent_data_chars=len(agent_data_encoded),
        llm_result=asdict(result),
        response_text=result.response_text,
    )


def _score_response(*, response_text: str, judge_model) -> dict | None:
    """Use Claude Opus 4.6 as an LLM-judge to score the response against ground truth."""
    ground_truth_str = json.dumps(GROUND_TRUTH, indent=2, ensure_ascii=False)
    eval_user = build_evaluator_prompt(
        query=DIAGNOSTIC_QUERY,
        ground_truth_str=ground_truth_str,
        response=response_text,
    )

    print(f"    → Scoring against ground truth (using Opus judge)...")
    result = call_llm(
        system_prompt=EVALUATOR_SYSTEM_PROMPT,
        user_prompt=eval_user,
        model=judge_model,
        input_price_per_m=JUDGE_INPUT_PRICE_PER_M,
        output_price_per_m=JUDGE_OUTPUT_PRICE_PER_M,
    )

    # Parse the JSON. Strip markdown fences if any.
    text = result.response_text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("`").strip()

    try:
        scores = json.loads(text)
    except json.JSONDecodeError:
        print(f"    ⚠ Could not parse evaluator JSON. Raw: {text[:200]}")
        scores = {"parse_error": True, "raw": result.response_text}

    scores["_evaluator_model"] = judge_model.model if hasattr(judge_model, "model") else str(judge_model)
    scores["_evaluator_input_tokens"] = result.input_tokens
    scores["_evaluator_output_tokens"] = result.output_tokens
    scores["_evaluator_cost_usd"] = result.total_cost_usd
    return scores


def _build_comparison(json_run: FormatRunResult, toon_run: FormatRunResult) -> dict:
    """Compute side-by-side delta metrics."""
    j = json_run.llm_result
    t = toon_run.llm_result

    def _pct_change(new: float, old: float) -> float:
        if old == 0:
            return 0.0
        return round((new - old) / old * 100, 2)

    return {
        "prompt_chars": {
            "json": json_run.prompt_chars,
            "toon": toon_run.prompt_chars,
            "delta": toon_run.prompt_chars - json_run.prompt_chars,
            "pct_change": _pct_change(toon_run.prompt_chars, json_run.prompt_chars),
        },
        "input_tokens": {
            "json": j["input_tokens"],
            "toon": t["input_tokens"],
            "delta": t["input_tokens"] - j["input_tokens"],
            "pct_change": _pct_change(t["input_tokens"], j["input_tokens"]),
        },
        "output_tokens": {
            "json": j["output_tokens"],
            "toon": t["output_tokens"],
            "delta": t["output_tokens"] - j["output_tokens"],
            "pct_change": _pct_change(t["output_tokens"], j["output_tokens"]),
        },
        "total_cost_usd": {
            "json": round(j["total_cost_usd"], 5),
            "toon": round(t["total_cost_usd"], 5),
            "delta": round(t["total_cost_usd"] - j["total_cost_usd"], 5),
            "pct_change": _pct_change(t["total_cost_usd"], j["total_cost_usd"]),
        },
        "latency_seconds": {
            "json": round(j["latency_seconds"], 2),
            "toon": round(t["latency_seconds"], 2),
            "delta": round(t["latency_seconds"] - j["latency_seconds"], 2),
            "pct_change": _pct_change(t["latency_seconds"], j["latency_seconds"]),
        },
    }


def run_experiment(
    *,
    score_responses: bool = True,
    save_artifact: bool = True,
) -> ExperimentResult:
    """Run the full JSON vs TOON benchmark and save an artifact JSON."""
    print("=" * 60)
    print("  TOON vs JSON — L'Oréal Vietnam Q3 RCA Benchmark")
    print("=" * 60)

    payload = get_full_payload()
    agent_results = payload["agent_results"]

    # Encode the agent data in both formats
    json_encoded = encode_agent_data_json(agent_results, pretty=True)
    toon_encoded = encode_agent_data_toon(agent_results)

    # Response generation model: Claude Sonnet 4.6
    response_model = get_chat_model()
    response_model_name = response_model.model if hasattr(response_model, 'model') else 'default'

    print(f"\nResponse Model: {response_model_name} (Sonnet 4.6)")
    print(f"Agents: {len(agent_results)}")
    print(f"Total rows: {sum(len(rows) for rows in agent_results.values())}")
    print(f"JSON encoded: {len(json_encoded):,} chars")
    print(f"TOON encoded: {len(toon_encoded):,} chars")

    # Run both formats with Sonnet 4.6
    print("\n[1/2] JSON format run (Sonnet 4.6)")
    json_run = _run_one_format(
        format_name="json",
        agent_data_encoded=json_encoded,
        payload=payload,
        model=response_model,
    )

    print("\n[2/2] TOON format run (Sonnet 4.6)")
    toon_run = _run_one_format(
        format_name="toon",
        agent_data_encoded=toon_encoded,
        payload=payload,
        model=response_model,
    )

    # Score each using Opus 4.6 as judge
    if score_responses:
        judge_model = get_judge_model()
        judge_model_name = judge_model.model if hasattr(judge_model, 'model') else 'default'
        print(f"\n[Scoring] Evaluating responses with judge model: {judge_model_name} (Opus 4.6)")
        json_run.scores = _score_response(response_text=json_run.response_text, judge_model=judge_model)
        toon_run.scores = _score_response(response_text=toon_run.response_text, judge_model=judge_model)

    # Build comparison
    comparison = _build_comparison(json_run, toon_run)

    # Add accuracy comparison if scored
    if score_responses and json_run.scores and toon_run.scores:
        if "total_score" in json_run.scores and "total_score" in toon_run.scores:
            comparison["total_score"] = {
                "json": json_run.scores["total_score"],
                "toon": toon_run.scores["total_score"],
                "delta": toon_run.scores["total_score"] - json_run.scores["total_score"],
                "max": 50,
            }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment = ExperimentResult(
        timestamp=timestamp,
        model_id=json_run.llm_result["model_id"],
        diagnostic_query=DIAGNOSTIC_QUERY,
        runs={
            "json": {
                "format_name": json_run.format_name,
                "prompt_chars": json_run.prompt_chars,
                "agent_data_chars": json_run.agent_data_chars,
                "llm_result": json_run.llm_result,
                "response_text": json_run.response_text,
                "scores": json_run.scores,
                "agent_data_encoded": json_encoded,
            },
            "toon": {
                "format_name": toon_run.format_name,
                "prompt_chars": toon_run.prompt_chars,
                "agent_data_chars": toon_run.agent_data_chars,
                "llm_result": toon_run.llm_result,
                "response_text": toon_run.response_text,
                "scores": toon_run.scores,
                "agent_data_encoded": toon_encoded,
            },
        },
        comparison=comparison,
    )

    if save_artifact:
        out_path = ARTIFACTS_DIR / f"experiment_{timestamp}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(asdict(experiment), f, indent=2, ensure_ascii=False)
        # Also write a "latest" symlink-like copy for the Streamlit app
        latest_path = ARTIFACTS_DIR / "latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(asdict(experiment), f, indent=2, ensure_ascii=False)
        print(f"\n✓ Artifact saved: {out_path}")
        print(f"✓ Latest pointer: {latest_path}")

    _print_summary(experiment)
    return experiment


def _print_summary(exp: ExperimentResult) -> None:
    """Pretty-print the summary table to stdout."""
    c = exp.comparison
    print("\n" + "=" * 60)
    print("  SUMMARY — JSON vs TOON")
    print("=" * 60)
    print(f"{'Metric':<22} {'JSON':>14} {'TOON':>14} {'Δ':>12}")
    print("-" * 64)
    for metric in ("prompt_chars", "input_tokens", "output_tokens",
                   "total_cost_usd", "latency_seconds"):
        m = c[metric]
        delta_str = f"{m['pct_change']:+.1f}%"
        if isinstance(m["json"], float):
            j_str = f"${m['json']:.4f}" if "cost" in metric else f"{m['json']:.2f}"
            t_str = f"${m['toon']:.4f}" if "cost" in metric else f"{m['toon']:.2f}"
        else:
            j_str = f"{m['json']:,}"
            t_str = f"{m['toon']:,}"
        print(f"{metric:<22} {j_str:>14} {t_str:>14} {delta_str:>12}")

    if "total_score" in c:
        s = c["total_score"]
        print(f"{'accuracy_score/50':<22} {s['json']:>14} {s['toon']:>14} {s['delta']:>+12}")

    print("-" * 64)
    print(f"Artifact ID: experiment_{exp.timestamp}")
