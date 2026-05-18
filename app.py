"""
Streamlit UI: TOON vs JSON benchmark comparator.

Loads the latest experiment artifact and shows side-by-side:
  - Token usage, cost, latency, accuracy
  - The two model responses
  - The prompts and encoded data
  - The 35 agent dataframes (browsable)
  - The ground truth

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from agents import AGENTS, CONTEXT, DIAGNOSTIC_QUERY
from ground_truth import GROUND_TRUTH

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TOON vs JSON · Token Efficiency Benchmark",
    page_icon="🎒",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def list_artifacts() -> list[Path]:
    if not ARTIFACTS_DIR.exists():
        return []
    files = sorted(
        ARTIFACTS_DIR.glob("experiment_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files


def load_artifact(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("🎒 TOON vs JSON")
st.sidebar.caption("Token efficiency benchmark for passing structured data to LLMs")

st.sidebar.divider()
st.sidebar.subheader("Experiment")

artifacts = list_artifacts()
if not artifacts:
    st.sidebar.warning("No experiment artifacts found.")
    st.error(
        "**No experiment artifacts yet.**\n\n"
        "Run the benchmark first:\n\n"
        "```bash\npython run_experiment.py\n```"
    )
    st.stop()

artifact_names = [p.name for p in artifacts]
selected_name = st.sidebar.selectbox(
    "Select artifact",
    artifact_names,
    index=0,
)
selected_path = ARTIFACTS_DIR / selected_name
experiment = load_artifact(selected_path)

st.sidebar.caption(f"**Model:** `{experiment['model_id']}`")
st.sidebar.caption(f"**Timestamp:** {experiment['timestamp']}")

st.sidebar.divider()
st.sidebar.subheader("Scenario")
for k, v in CONTEXT.items():
    st.sidebar.caption(f"**{k}**: {v}")


# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------

st.title("TOON vs JSON")
st.markdown(
    "Comparing **Token-Oriented Object Notation** against **JSON** for passing "
    "agent dataframes to a final Response Generation Agent in a "
    "real-world retail RCA pipeline (L'Oréal Vietnam, 35 specialized agents)."
)


# ---------------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------------

c = experiment["comparison"]
json_run = experiment["runs"]["json"]
toon_run = experiment["runs"]["toon"]


def _delta(metric: str, *, lower_is_better: bool = True) -> tuple[str, str]:
    """Return (delta_str, delta_color) for st.metric."""
    pct = c[metric]["pct_change"]
    delta_str = f"{pct:+.1f}%"
    if lower_is_better:
        # Lower TOON = good = "inverse" coloring (green for negative)
        return delta_str, "inverse"
    return delta_str, "normal"


st.subheader("📊 Top-line comparison (TOON vs JSON)")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    d, dc = _delta("input_tokens")
    st.metric(
        "Input tokens",
        f"{c['input_tokens']['toon']:,}",
        d,
        delta_color=dc,
        help=f"JSON: {c['input_tokens']['json']:,}",
    )
with col2:
    d, dc = _delta("output_tokens")
    st.metric(
        "Output tokens",
        f"{c['output_tokens']['toon']:,}",
        d,
        delta_color=dc,
        help=f"JSON: {c['output_tokens']['json']:,}",
    )
with col3:
    d, dc = _delta("total_cost_usd")
    st.metric(
        "Total cost (USD)",
        f"${c['total_cost_usd']['toon']:.4f}",
        d,
        delta_color=dc,
        help=f"JSON: ${c['total_cost_usd']['json']:.4f}",
    )
with col4:
    d, dc = _delta("latency_seconds")
    st.metric(
        "Latency (s)",
        f"{c['latency_seconds']['toon']:.2f}",
        d,
        delta_color=dc,
        help=f"JSON: {c['latency_seconds']['json']:.2f}s",
    )
with col5:
    if "total_score" in c:
        ts = c["total_score"]
        st.metric(
            f"Accuracy (/{ts['max']})",
            f"{ts['toon']}",
            f"{ts['delta']:+d}",
            delta_color="normal",
            help=f"JSON: {ts['json']}/{ts['max']}",
        )
    else:
        st.metric("Accuracy", "N/A", help="Scoring was skipped")


# Bar chart of token counts
fig = go.Figure()
fig.add_trace(go.Bar(
    name="JSON",
    x=["Prompt chars", "Input tokens", "Output tokens"],
    y=[c["prompt_chars"]["json"], c["input_tokens"]["json"], c["output_tokens"]["json"]],
    marker_color="#1f77b4",
    text=[
        f"{c['prompt_chars']['json']:,}",
        f"{c['input_tokens']['json']:,}",
        f"{c['output_tokens']['json']:,}",
    ],
    textposition="auto",
))
fig.add_trace(go.Bar(
    name="TOON",
    x=["Prompt chars", "Input tokens", "Output tokens"],
    y=[c["prompt_chars"]["toon"], c["input_tokens"]["toon"], c["output_tokens"]["toon"]],
    marker_color="#47D7AC",
    text=[
        f"{c['prompt_chars']['toon']:,}",
        f"{c['input_tokens']['toon']:,}",
        f"{c['output_tokens']['toon']:,}",
    ],
    textposition="auto",
))
fig.update_layout(
    barmode="group",
    title="Token & character counts: JSON vs TOON",
    height=380,
    margin=dict(l=20, r=20, t=50, b=20),
)
st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_responses, tab_prompts, tab_data, tab_agents, tab_truth, tab_raw = st.tabs(
    [
        "🔄 Responses side-by-side",
        "📝 Prompts & encoded data",
        "📈 Detailed metrics",
        "🤖 35 Agents data",
        "✅ Ground truth",
        "🗄️ Raw artifact",
    ]
)


# ---------------- Responses ----------------
with tab_responses:
    st.subheader("Diagnostic query")
    st.info(experiment["diagnostic_query"])

    col_json, col_toon = st.columns(2)

    with col_json:
        st.markdown("### 🔵 JSON response")
        sj = json_run.get("scores") or {}
        if "total_score" in sj:
            st.caption(
                f"Score: **{sj['total_score']}/{sj.get('max_score', 50)}**  ·  "
                f"Coverage: {sj.get('root_cause_coverage', '?')}/10  ·  "
                f"Quantification: {sj.get('quantification', '?')}/10  ·  "
                f"Evidence: {sj.get('evidence_linking', '?')}/10"
            )
        st.markdown(json_run["response_text"])

    with col_toon:
        st.markdown("### 🟢 TOON response")
        st_ = toon_run.get("scores") or {}
        if "total_score" in st_:
            st.caption(
                f"Score: **{st_['total_score']}/{st_.get('max_score', 50)}**  ·  "
                f"Coverage: {st_.get('root_cause_coverage', '?')}/10  ·  "
                f"Quantification: {st_.get('quantification', '?')}/10  ·  "
                f"Evidence: {st_.get('evidence_linking', '?')}/10"
            )
        st.markdown(toon_run["response_text"])

    if "total_score" in (json_run.get("scores") or {}) and "total_score" in (toon_run.get("scores") or {}):
        st.divider()
        st.subheader("Evaluator notes")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**JSON judge notes:**")
            st.caption(json_run["scores"].get("notes", "—"))
        with col2:
            st.markdown("**TOON judge notes:**")
            st.caption(toon_run["scores"].get("notes", "—"))


# ---------------- Prompts ----------------
with tab_prompts:
    st.subheader("Encoded agent data (sent to the LLM)")

    col_json, col_toon = st.columns(2)
    with col_json:
        st.markdown(f"**JSON** · {json_run['agent_data_chars']:,} chars")
        with st.expander("Show JSON-encoded agent data", expanded=False):
            st.code(json_run["agent_data_encoded"], language="json")

    with col_toon:
        st.markdown(f"**TOON** · {toon_run['agent_data_chars']:,} chars")
        with st.expander("Show TOON-encoded agent data", expanded=True):
            st.code(toon_run["agent_data_encoded"], language="yaml")

    st.divider()
    st.subheader("Full user-prompt character counts")
    st.caption("This includes system prompt context, agent descriptions, output instructions, etc.")
    df = pd.DataFrame({
        "Format": ["JSON", "TOON"],
        "Full prompt chars": [c["prompt_chars"]["json"], c["prompt_chars"]["toon"]],
        "Input tokens": [c["input_tokens"]["json"], c["input_tokens"]["toon"]],
        "Output tokens": [c["output_tokens"]["json"], c["output_tokens"]["toon"]],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------- Detailed metrics ----------------
with tab_data:
    st.subheader("Detailed comparison table")

    rows = []
    for metric in ("prompt_chars", "input_tokens", "output_tokens",
                   "total_cost_usd", "latency_seconds"):
        m = c[metric]
        rows.append({
            "Metric": metric,
            "JSON": m["json"],
            "TOON": m["toon"],
            "Δ (absolute)": m["delta"],
            "Δ (%)": f"{m['pct_change']:+.2f}%",
        })
    if "total_score" in c:
        s = c["total_score"]
        rows.append({
            "Metric": "accuracy_score (/50)",
            "JSON": s["json"],
            "TOON": s["toon"],
            "Δ (absolute)": s["delta"],
            "Δ (%)": "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Per-run details")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**JSON run**")
        st.json(json_run["llm_result"])
    with col2:
        st.markdown("**TOON run**")
        st.json(toon_run["llm_result"])


# ---------------- 35 Agents ----------------
with tab_agents:
    st.subheader(f"The {len(AGENTS)} agent dataframes")
    st.caption(
        "Each agent specializes in one slice of the business. The Response "
        "Generation Agent receives all of these as context."
    )

    agent_names = [a["name"] for a in AGENTS]
    selected_agent = st.selectbox("Pick an agent", agent_names)
    agent = next(a for a in AGENTS if a["name"] == selected_agent)

    st.markdown(f"**Description:** {agent['description']}")
    st.dataframe(pd.DataFrame(agent["data"]), use_container_width=True, hide_index=True)


# ---------------- Ground truth ----------------
with tab_truth:
    st.subheader("Ground truth — actual root causes")
    st.caption(
        "These are the 'right answers' baked into the dummy data. "
        "The Response Generation Agent should converge on these."
    )

    st.info(GROUND_TRUTH["summary"])

    for rc in GROUND_TRUTH["root_causes"]:
        with st.expander(f"#{rc['rank']} — {rc['cause']}", expanded=True):
            st.markdown(f"**Estimated impact:** {rc['estimated_impact_pct_of_decline']} "
                        f"({rc['estimated_impact_vnd_b']} VND B)")
            st.markdown("**Key evidence keywords:**")
            st.code(", ".join(rc["key_evidence_keywords"]))

    st.markdown("### ⚠️ Red herrings (data to NOT promote to root causes)")
    for rh in GROUND_TRUTH["red_herrings_to_avoid"]:
        st.markdown(f"- {rh}")

    st.markdown("### ✅ Expected recommended actions")
    for i, a in enumerate(GROUND_TRUTH["expected_recommended_actions"], 1):
        st.markdown(f"{i}. {a}")


# ---------------- Raw artifact ----------------
with tab_raw:
    st.subheader("Raw experiment artifact")
    st.caption(f"Path: `{selected_path}`")
    st.json(experiment)
    st.download_button(
        "Download artifact JSON",
        json.dumps(experiment, indent=2, ensure_ascii=False),
        file_name=selected_name,
        mime="application/json",
    )
