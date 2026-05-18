"""
Prompt templates for:
  1. The Response Generation Agent (synthesizes 35 agent outputs into an RCA)
  2. The Evaluator (scores a generated response against ground truth)

Both prompts are *format-agnostic* — the only thing that changes between
JSON and TOON runs is the encoded `agent_data` block. This is the whole
point of the benchmark: same task, same model, same prompt structure;
only the data serialization changes.
"""

SYSTEM_PROMPT = """\
You are the Response Generation Agent in an enterprise retail-analytics platform.

A senior business stakeholder has raised a diagnostic question. To answer it,
the orchestrator has dispatched 35 specialized analytics agents in parallel.
Each agent has queried the data warehouse for one specific slice of the
business (revenue by brand, warehouse stock-out events, distributor performance,
competitor activity, e-commerce traffic, customer complaints, etc.) and
returned a small structured table of findings.

Your job is to:
  1. Read across ALL 35 agent results.
  2. Identify converging signals that point to the actual root causes.
  3. Ignore red-herring data that looks anomalous but doesn't connect to the outcome.
  4. Quantify your conclusions with specific numbers from the agent data.
  5. Recommend concrete, prioritized next actions.

You will receive the agent results in a structured data format. Each agent's
output is labeled by its name. Treat all 35 as authoritative; do not invent data.

Be rigorous. Be specific. Cite the agent name and concrete numbers when stating
evidence (e.g. "warehouse_oos_days shows Hanoi DC OOS jumped from 3.2 to 21.4 days").
"""


# The TOON-specific hint is intentionally minimal. We want to test how well
# the model handles the format itself, with only the level of documentation
# you would realistically put in a production prompt.
TOON_FORMAT_HINT = """\
NOTE ON DATA FORMAT — The agent results below are in TOON (Token-Oriented
Object Notation). Each block is a table in the form:

    table_name[N]{field1,field2,field3}:
      value1,value2,value3
      value1,value2,value3
      ...

Where [N] is the row count and {field1,...} is the schema header.
Empty fields mean null. This is a compact, lossless representation of JSON.
"""


USER_PROMPT_TEMPLATE = """\
DIAGNOSTIC QUERY
================
{query}

CONTEXT
=======
{context}

AGENT DESCRIPTIONS
==================
{agent_descriptions}

AGENT RESULTS ({format_label})
================================{format_hint}
{agent_data}

REQUIRED OUTPUT STRUCTURE
=========================
Return your response in exactly this Markdown structure:

## Executive Summary
(2–3 sentences stating the headline conclusion.)

## Top 3 Root Causes (ranked by impact)

### 1. <cause title>
- **Estimated impact:** <% of total decline> / <~VND billions>
- **Evidence:** <bullet list of specific agent findings with numbers>
- **Confidence:** <High | Medium | Low>

### 2. <cause title>
(same structure)

### 3. <cause title>
(same structure)

## Recommended Actions
(Numbered list of 5 concrete actions, each with a suggested owner: Supply Chain, Commercial, Marketing, Sales Ops, or Distribution.)

## Data Quality Notes
(Any agent results that were inconsistent, missing, or ambiguous. If none, write "No issues.")
"""


def build_user_prompt(
    *,
    query: str,
    context_str: str,
    agent_descriptions_str: str,
    agent_data: str,
    format_label: str,
    include_toon_hint: bool,
) -> str:
    """Assemble the user prompt for either JSON or TOON format."""
    return USER_PROMPT_TEMPLATE.format(
        query=query,
        context=context_str,
        agent_descriptions=agent_descriptions_str,
        agent_data=agent_data,
        format_label=format_label,
        format_hint=("\n" + TOON_FORMAT_HINT) if include_toon_hint else "",
    )


# ---------------------------------------------------------------------------
# Evaluator prompt — LLM-as-judge scoring of the generated response
# ---------------------------------------------------------------------------

EVALUATOR_SYSTEM_PROMPT = """\
You are an impartial evaluator scoring a root-cause-analysis report.

You will be given:
  - The original diagnostic query
  - The ground-truth root causes (provided as reference)
  - A candidate response from a Response Generation Agent

Score the candidate on five dimensions, each 0–10:

  1. ROOT_CAUSE_COVERAGE — Did it identify all three ground-truth root causes?
     (10 = all three identified; 6 = two of three; 3 = one of three; 0 = none)
  2. QUANTIFICATION — Did it cite specific numbers (e.g. "Hanoi DC OOS 3.2 → 21.4 days")
     rather than vague statements? (10 = consistently quantified, 0 = no numbers)
  3. EVIDENCE_LINKING — Did it cite specific agent names / data points correctly?
     (10 = clear traceability, 0 = unsupported claims)
  4. RED_HERRING_AVOIDANCE — Did it correctly de-prioritize the red-herring data
     (FX, returns, raw materials, tariffs, weather)? (10 = none promoted to root causes, 0 = several)
  5. ACTION_QUALITY — Are the recommended actions concrete and aligned with the
     identified root causes? (10 = sharp and aligned, 0 = generic platitudes)

Output STRICT JSON only — no markdown fences, no commentary:

{
  "root_cause_coverage": <0-10>,
  "quantification": <0-10>,
  "evidence_linking": <0-10>,
  "red_herring_avoidance": <0-10>,
  "action_quality": <0-10>,
  "total_score": <sum of the five>,
  "max_score": 50,
  "notes": "<1-2 sentence justification>"
}
"""


EVALUATOR_USER_TEMPLATE = """\
DIAGNOSTIC QUERY
================
{query}

GROUND-TRUTH ROOT CAUSES (reference)
====================================
{ground_truth}

CANDIDATE RESPONSE
==================
{response}

Score the candidate response. Return JSON only.
"""


def build_evaluator_prompt(
    *,
    query: str,
    ground_truth_str: str,
    response: str,
) -> str:
    return EVALUATOR_USER_TEMPLATE.format(
        query=query,
        ground_truth=ground_truth_str,
        response=response,
    )
