# TOON vs JSON — Token Efficiency Benchmark for Agentic RCA Pipelines

> **TL;DR** — A reproducible benchmark that compares **TOON** (Token-Oriented
> Object Notation) against **JSON** when passing structured data from 35
> specialized analytics agents to a final Response Generation Agent. Runs on
> AWS Bedrock via LangChain with:
> - **Claude Sonnet 4.6** for response generation (metrics tracked)
> - **Claude Opus 4.6** for LLM-as-judge scoring
>
> Tracks input/output tokens, cost, and latency for the response generation
> calls, plus accuracy scores from the Opus judge. Ships with a Streamlit UI
> for side-by-side comparison.
> 
<img width="1358" height="732" alt="Screenshot 2026-05-18 at 7 42 16 PM" src="https://github.com/user-attachments/assets/be55570c-1412-433e-a228-e1119135e044" />

## Why this benchmark exists

Modern agentic systems for enterprise analytics typically follow this pattern:

```
User question
     │
     ▼
┌──────────────────┐
│   Orchestrator   │
└──────────────────┘
     │  dispatches in parallel
     ▼
┌──────┐  ┌──────┐  ┌──────┐        ┌──────┐
│Agent │  │Agent │  │Agent │  ...   │Agent │   ← 30–50 specialized agents
│  1   │  │  2   │  │  3   │        │  N   │      each returns a small DataFrame
└──────┘  └──────┘  └──────┘        └──────┘
     │        │        │                │
     └────────┴────┬───┴────────────────┘
                   ▼
        ┌────────────────────────┐
        │ Response Generation    │   ← THE prompt where token waste happens
        │ Agent (single LLM call)│      because N agents × M rows × verbose JSON
        └────────────────────────┘      = thousands of repeated keys
                   │
                   ▼
            Final answer
```

The Response Generation Agent receives the **concatenated output of all
agents**, which can be tens of thousands of tokens of structured data. In
JSON, every row repeats every key. In **TOON**, fields are declared once
per table, like a CSV with a schema header. For uniform tabular data —
exactly what SQL-style agents produce — TOON can cut tokens by 40–70%
losslessly.

This repo measures the actual savings on a realistic scenario.

## The scenario

**Use case:** L'Oréal Vietnam Q3 2025 revenue dropped 18.4% vs Q2. Why?

**Setup:** 35 simulated analytics agents have queried the data warehouse,
each returning a small structured table. Topics include:

- Revenue decomposition (by brand / division / region / channel)
- Top declining SKUs and stores
- Warehouse stock-out events and OOS days
- Logistics on-time delivery & customs lead times
- Demand forecast accuracy by division
- Distributor performance, inventory days, margin changes
- Sales force coverage
- Competitor pricing actions & new launches
- Market share & category growth
- E-commerce traffic & conversion rates
- Marketing spend & promo campaigns
- Customer returns & complaint volume
- Loyalty program engagement
- FX impact, weather, holidays, store openings/closures, product launches

**Ground truth** (baked into the dummy data — three root causes the
Response Generation Agent should identify):

1. **Hanoi DC customs clearance delay** → stock-outs of DPD products in
   North Vietnam (La Roche-Posay, CeraVe). ~7B VND impact.
2. **Beauty Republic competitive offensive** on TikTok Shop (LUXE tier).
   ~4.7B VND impact.
3. **Saigon Distribution Co. inventory crisis** → Modern Trade coverage
   collapse in HCMC and Mekong. ~4B VND impact.

The dataset also contains **red herrings** (FX moves, raw material costs,
customer returns) so the synthesis isn't trivially keyword-matchable.

## What the benchmark measures

For each format (JSON, TOON), one Bedrock call is made using **Claude Sonnet
4.6** for the Response Generation Agent with the **same** system prompt,
**same** task, and the **same** 35 agent outputs — only the serialization
differs.

Captured per run (Sonnet 4.6 only — these are the comparison metrics):
- Full prompt character count
- Input tokens (from Bedrock usage metadata)
- Output tokens
- Cost (USD) using Sonnet pricing ($3/$15 per M tokens)
- Latency (wall-clock seconds)

Separately, **Claude Opus 4.6** is used as the **Evaluator / LLM-as-Judge**
to score each response against the ground truth on five dimensions (0–10
each). Judge costs are tracked but not included in the main comparison:

| Dimension | What it measures |
|---|---|
| `root_cause_coverage` | Did it find all 3 root causes? |
| `quantification` | Did it cite specific numbers? |
| `evidence_linking` | Did it reference specific agent outputs? |
| `red_herring_avoidance` | Did it correctly de-prioritize noise? |
| `action_quality` | Are the recommended actions concrete? |

Total score is out of 50.

## Project layout

```
JSON-vs-TOON/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── __init__.py              # Package exports
├── run_experiment.py        # CLI entry: runs both formats + scoring
├── app.py                   # Streamlit UI for side-by-side comparison
├── agents.py                # 35 simulated agents + their dataframes
├── ground_truth.py          # Expected answer (for the evaluator)
├── encoders.py              # JSON & TOON encoders
├── prompts.py               # Response-gen + evaluator prompt templates
├── llm.py                   # LangChain + Bedrock wrapper, token accounting
├── experiment.py            # Orchestration & artifact saving
└── artifacts/               # Output JSON files (one per run)
```

## Setup

### 1. Prerequisites

- Python 3.10+
- AWS account with **Bedrock model access** for:
  - Claude Sonnet 4.6 (`anthropic.claude-sonnet-4-6-20250514-v1:0`) — response generation
  - Claude Opus 4.6 (`anthropic.claude-opus-4-6-20250514-v1:0`) — judge/evaluator
- AWS credentials configured locally (`aws configure sso` or `aws configure`)

### 2. Install

```bash
git clone <your-repo-url>
cd toon-vs-json

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env — at minimum set AWS_REGION; optionally pick a different
# BEDROCK_MODEL_ID if your account has access to a different Sonnet variant.
```

If you use AWS SSO with a named profile, either uncomment `AWS_PROFILE`
in `.env` or run `export AWS_PROFILE=your-profile-name` before invoking
the experiment.

### 4. Sanity check (no cost)

```bash
python run_experiment.py --dry-run
```

This just encodes the agent payload in both formats and prints sizes — no
Bedrock call. Confirms the project is wired correctly before you spend money.

Expected output (approximately):
```
Encoded sizes (chars):
  JSON pretty:    ~24,000
  JSON compact:   ~16,500
  TOON:           ~ 8,700

TOON savings vs JSON pretty:  ~64%
TOON savings vs JSON compact: ~47%
```

## Run

### Full benchmark

```bash
python run_experiment.py
```

This will:
1. Encode the 35-agent payload as JSON (pretty) and as TOON.
2. Call Claude Sonnet 4.6 on Bedrock once per format (response generation).
3. Call Claude Opus 4.6 to score each response against ground truth (judge).
4. Save the artifact to `artifacts/experiment_<timestamp>.json`.
5. Save a copy to `artifacts/latest.json` for the UI.
6. Print a summary table.

**Estimated cost per run:** ~$0.15–$0.30
- Response generation (Sonnet 4.6): ~$0.05–$0.10 (two calls at $3/$15 per M tokens)
- Judge/evaluator (Opus 4.6): ~$0.10–$0.20 (two calls at $15/$75 per M tokens)

### Skip scoring (cheaper, faster)

```bash
python run_experiment.py --no-score
```

Drops the two evaluator calls. Useful when iterating on the prompt or
encoder. Cost drops to ~$0.05 per run.

### Open the comparison UI

```bash
streamlit run app.py
```

The UI shows:
- **Top-line metrics** — tokens, cost, latency, accuracy (with TOON-vs-JSON deltas)
- **Responses side-by-side** — the two RCA reports with their judge scores
- **Prompts & encoded data** — see exactly what was sent to the model
- **Detailed metrics** — full numerical breakdown
- **35 Agents data** — browse each agent's dataframe
- **Ground truth** — the expected root causes and red herrings
- **Raw artifact** — the full JSON output, downloadable

You can switch between past runs from the sidebar dropdown.

## What I observe (and what to look for)

Even before running, the headline numbers are predictable:

- **Input tokens:** TOON typically uses **40–55% fewer** input tokens than
  pretty-printed JSON. This is the main cost lever, since input tokens
  dominate by volume in agentic RCA pipelines.
- **Output tokens:** Roughly the same — the model's response doesn't depend
  on input format.
- **Cost:** Drops in proportion to input tokens × input price (≈40–55%).
- **Latency:** Modest improvement (Bedrock processes fewer tokens, but
  output dominates time-to-completion).
- **Accuracy:** Within ±2 points of 50. Public benchmarks suggest TOON ≥
  JSON for uniform tabular data; the gap on this scenario is small but
  real. The interesting failure modes show up in *non-uniform* sections
  of the data, which is why this benchmark deliberately includes them.

The **right way to read this benchmark** is per-row: for uniform
dataframes (which is most of what comes out of a SQL agent), TOON is a
clear win. For deeply nested or sparse data, JSON or hybrid is better.
Don't blanket-convert.

## Customizing the experiment

### Add or modify agents

Edit `data/agents.py`. The `AGENTS` list is just Python — each entry needs
`name`, `description`, and `data` (list of dicts with identical keys). The
encoders and prompt builders pick up new agents automatically.

### Use different models

In `.env`, you can override the model IDs:
- `BEDROCK_MODEL_ID` — response generation model (default: Sonnet 4.6)
- `BEDROCK_JUDGE_MODEL_ID` — judge/evaluator model (default: Opus 4.6)

When changing models, update the pricing env vars to match:
- `BEDROCK_INPUT_PRICE_PER_M` / `BEDROCK_OUTPUT_PRICE_PER_M` — for response model
- `BEDROCK_JUDGE_INPUT_PRICE_PER_M` / `BEDROCK_JUDGE_OUTPUT_PRICE_PER_M` — for judge model

Example for Haiku 4.5 as response model:
```
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_INPUT_PRICE_PER_M=0.8
BEDROCK_OUTPUT_PRICE_PER_M=4.0
```

### Try different TOON variations

`encoders.py` is intentionally simple. Things you might experiment
with:
- Use `;` or `|` as the delimiter (TOON spec allows it; useful if your
  data contains many commas).
- Drop the `[N]` row count to test if the model still parses correctly.
- Inline a short one-shot example in the system prompt and compare.

### Run multiple trials for variance

Edit `experiment.py` to loop the response-generation call N times
per format and aggregate. Token counts will be ~deterministic;
output/score may vary at temperature > 0.

## Limitations & honest caveats

- **Single-shot benchmark.** One scenario, one model, one prompt. Results
  may not generalize to your specific data shape or task. Always A/B test
  on your own pipeline before swapping formats in production.
- **TOON wasn't in training data.** Comprehension is via in-context
  pattern matching from the schema header. Generation of TOON by the
  model is less reliable — keep generation as structured-output JSON.
- **LLM-as-judge has its own biases.** While we use Opus 4.6 (a different
  model) to evaluate Sonnet 4.6 outputs, both are from the same model family,
  which can introduce subtle bias. For a more rigorous comparison, swap in a
  different judge model (e.g. a non-Anthropic one) via `BEDROCK_JUDGE_MODEL_ID`.
- **Bedrock token counting** is the Anthropic tokenizer; results will
  differ slightly on other providers.

## License

MIT.

## Acknowledgements

- **TOON spec:** [toon-format/toon](https://github.com/toon-format/toon)
- The L'Oréal Vietnam scenario is a synthetic illustration; numbers are
  invented for pedagogical purposes and do not reflect any real company data.
