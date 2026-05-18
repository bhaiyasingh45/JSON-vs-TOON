"""
Needle-in-Haystack Benchmark: 50 factual questions testing data retrieval accuracy.

Each question has a specific answer that can be found in the agent data.
We test both JSON and TOON formats to see if the model can find the "needle"
(specific fact) in the "haystack" (all 35 agents' data).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from agents import AGENTS, get_full_payload
from encoders import encode_agent_data_json, encode_agent_data_toon
from llm import get_chat_model, _get_bedrock_client

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

# 50 factual questions with expected answers extracted from agents.py
NEEDLE_QUESTIONS = [
    # Revenue questions (1-10)
    {"q": "What was La Roche-Posay's Q3 revenue in VND billions?", "a": "8.5", "agent": "revenue_by_brand_qoq"},
    {"q": "Which brand had the highest percentage decline Q2 to Q3?", "a": "L'Oréal Professionnel", "agent": "revenue_by_brand_qoq"},
    {"q": "What was the DPD division's Q3 revenue in VND billions?", "a": "20.2", "agent": "revenue_by_division_qoq"},
    {"q": "Which region had a positive revenue change in Q3?", "a": "Central", "agent": "revenue_by_region_qoq"},
    {"q": "What was the Modern Trade channel's Q3 revenue?", "a": "25.4", "agent": "revenue_by_channel_qoq"},
    {"q": "What was CeraVe's percentage decline from Q2 to Q3?", "a": "-28.0", "agent": "revenue_by_brand_qoq"},
    {"q": "What was the E-commerce channel revenue in Q3?", "a": "19.5", "agent": "revenue_by_channel_qoq"},
    {"q": "What was Lancôme's Q2 revenue in VND billions?", "a": "12.0", "agent": "revenue_by_brand_qoq"},
    {"q": "What was the South region's decline percentage?", "a": "-19.0", "agent": "revenue_by_region_qoq"},
    {"q": "What was the LUXE division's Q2 revenue?", "a": "25.0", "agent": "revenue_by_division_qoq"},

    # SKU and Store questions (11-18)
    {"q": "What was the decline in VND millions for the La Roche-Posay Effaclar Duo 400ml?", "a": "1850.0", "agent": "top_declining_skus"},
    {"q": "Which store had the highest decline in VND millions?", "a": "Vinhomes Times City", "agent": "top_declining_stores"},
    {"q": "What was the decline percentage for CeraVe Moisturizing Cream 454g?", "a": "-38.0", "agent": "top_declining_skus"},
    {"q": "What city is the Crescent Mall D7 store in?", "a": "HCMC", "agent": "top_declining_stores"},
    {"q": "What was Lotte Mall West Lake's decline in VND millions?", "a": "740.0", "agent": "top_declining_stores"},
    {"q": "What is the SKU ID for the Kiehl's Midnight Recovery Serum?", "a": "KHL-MIDN-30", "agent": "top_declining_skus"},
    {"q": "What was the decline percentage at Vincom Plaza Can Tho?", "a": "-27.0", "agent": "top_declining_stores"},
    {"q": "What was the SkinCeuticals C E Ferulic decline in VND millions?", "a": "610.0", "agent": "top_declining_skus"},

    # Supply chain questions (19-28)
    {"q": "How many out-of-stock days did Hanoi DC have in Q3?", "a": "21.4", "agent": "warehouse_oos_days"},
    {"q": "How many stock-out incidents did La Roche-Posay have in Q3?", "a": "47", "agent": "stockout_events_by_brand"},
    {"q": "What was the longest OOS days for CeraVe?", "a": "12", "agent": "stockout_events_by_brand"},
    {"q": "What was the on-time delivery percentage for Port HCMC to Hanoi DC in Q3?", "a": "71.0", "agent": "logistics_on_time_delivery"},
    {"q": "What was the average customs clearance days in September 2025?", "a": "18.2", "agent": "customs_clearance_lead_times"},
    {"q": "What was the max clearance days in August 2025?", "a": "22", "agent": "customs_clearance_lead_times"},
    {"q": "What was the DPD forecast accuracy in Q3?", "a": "62.0", "agent": "forecast_accuracy_by_division"},
    {"q": "What was the inventory turnover at Hanoi DC in Q3?", "a": "8.9", "agent": "inventory_turnover"},
    {"q": "What was the Glycerin cost index in Q3?", "a": "102.4", "agent": "raw_material_cost_trends"},
    {"q": "How many shipments were there in September 2025?", "a": "24", "agent": "customs_clearance_lead_times"},

    # Distributor questions (29-34)
    {"q": "What was Saigon Distribution Co.'s score in Q3?", "a": "4.1", "agent": "distributor_performance_scores"},
    {"q": "How many inventory days did Saigon Distribution Co. have in Q3?", "a": "11.0", "agent": "distributor_inventory_days"},
    {"q": "What region does Mekong Beauty Partners operate in?", "a": "South", "agent": "distributor_performance_scores"},
    {"q": "What was Hanoi Trading Group's margin in Q3?", "a": "17.5", "agent": "distributor_margin_changes"},
    {"q": "How many sales reps were in HCMC in Q3?", "a": "39", "agent": "sales_force_coverage"},
    {"q": "How many sales reps did Da Nang have?", "a": "12", "agent": "sales_force_coverage"},

    # Competitor questions (35-40)
    {"q": "What discount percentage did Beauty Republic offer on TikTok Shop?", "a": "-28.0", "agent": "competitor_price_changes"},
    {"q": "How many weeks did the Beauty Republic TikTok Shop discount run?", "a": "8", "agent": "competitor_price_changes"},
    {"q": "What was the target segment for BR Aurora Serum?", "a": "LUXE Anti-aging", "agent": "competitor_new_launches"},
    {"q": "What was L'Oréal's LUXE market share in Q3?", "a": "28.1", "agent": "market_share_by_division"},
    {"q": "What was the TikTok Shop traffic change for LUXE division?", "a": "-35.0", "agent": "ecom_traffic_trends"},
    {"q": "What was The Ordinary's discount percentage?", "a": "0.0", "agent": "competitor_price_changes"},

    # Marketing and customer questions (41-46)
    {"q": "What was the TikTok Ads spend in Q3 in VND millions?", "a": "1900", "agent": "marketing_spend_by_channel"},
    {"q": "What was the ROI index for the Maybelline TikTok Live campaign?", "a": "2.1", "agent": "promo_campaigns_active"},
    {"q": "How many delivery delay complaints were there in Q3?", "a": "312", "agent": "customer_complaint_volume"},
    {"q": "How many stock unavailable complaints were there in Q3?", "a": "287", "agent": "customer_complaint_volume"},
    {"q": "What was the TikTok Shop conversion rate in Q3?", "a": "3.0", "agent": "ecom_conversion_rates"},
    {"q": "How many Diamond tier loyalty members were active in Q3?", "a": "4150", "agent": "loyalty_program_engagement"},

    # Macro/environmental questions (47-50)
    {"q": "What was the VND per USD exchange rate in Q3 2025?", "a": "25150.0", "agent": "fx_impact_vnd_usd"},
    {"q": "What was the traffic impact percentage from Typhoon Yagi remnants?", "a": "-8.0", "agent": "weather_anomalies"},
    {"q": "What was the expected Q3 revenue for Vincom Mega Mall Smart City?", "a": "320.0", "agent": "new_store_openings"},
    {"q": "What was the actual Q3 revenue for Lancôme Idôle L'Intense EDP?", "a": "310.0", "agent": "product_launches"},
]


SYSTEM_PROMPT = """You are a data analyst assistant. You will be given structured data from multiple analytics agents and a specific question.

Your task is to find the exact answer in the data and respond with ONLY the numerical value or short text answer.

Rules:
- Give ONLY the answer, no explanation
- Use the exact value from the data
- If the answer is a number, give just the number (e.g., "21.4" not "21.4 days")
- If the answer is a name, give just the name (e.g., "Central" not "Central region")
- If you cannot find the answer, respond with "NOT FOUND"
"""


@dataclass
class QuestionResult:
    question: str
    expected: str
    got_json: str
    got_toon: str
    correct_json: bool
    correct_toon: bool


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    answer = answer.strip().lower()
    # Remove common suffixes
    for suffix in ['%', ' days', ' vnd', ' vnd b', ' vnd m', 'b vnd', 'm vnd', ' billion', ' million']:
        answer = answer.replace(suffix, '')
    # Remove quotes
    answer = answer.strip('"\'')
    return answer.strip()


def check_answer(expected: str, got: str) -> bool:
    """Check if the answer matches (with some flexibility)."""
    exp_norm = normalize_answer(expected)
    got_norm = normalize_answer(got)

    # Exact match
    if exp_norm == got_norm:
        return True

    # Check if expected is contained in got (for partial matches)
    if exp_norm in got_norm:
        return True

    # Try numeric comparison
    try:
        exp_num = float(exp_norm.replace(',', ''))
        got_num = float(got_norm.replace(',', ''))
        return abs(exp_num - got_num) < 0.01
    except:
        pass

    return False


def ask_question(question: str, agent_data_encoded: str, format_name: str, model) -> str:
    """Ask a single question and get the answer."""
    from langchain_core.messages import HumanMessage, SystemMessage

    user_prompt = f"""Here is the data from 35 analytics agents in {format_name.upper()} format:

{agent_data_encoded}

Question: {question}

Answer (give ONLY the value, nothing else):"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = model.invoke(messages)

    content = response.content
    if isinstance(content, list):
        content = " ".join(str(c) for c in content)

    return content.strip()


def run_needle_benchmark(num_questions: int = 50) -> dict:
    """Run the needle-in-haystack benchmark."""
    print("=" * 60)
    print("  Needle-in-Haystack Benchmark")
    print("=" * 60)

    payload = get_full_payload()
    agent_results = payload["agent_results"]

    json_encoded = encode_agent_data_json(agent_results, pretty=True)
    toon_encoded = encode_agent_data_toon(agent_results)

    print(f"\nJSON encoded: {len(json_encoded):,} chars")
    print(f"TOON encoded: {len(toon_encoded):,} chars")
    print(f"Questions to ask: {num_questions}")

    model = get_chat_model()

    questions = NEEDLE_QUESTIONS[:num_questions]
    results = []

    json_correct = 0
    toon_correct = 0

    print(f"\nRunning {num_questions} questions...")
    print("-" * 60)

    for i, q_data in enumerate(questions):
        question = q_data["q"]
        expected = q_data["a"]

        print(f"[{i+1}/{num_questions}] {question[:50]}...")

        # Ask with JSON
        try:
            json_answer = ask_question(question, json_encoded, "json", model)
        except Exception as e:
            json_answer = f"ERROR: {e}"

        # Ask with TOON
        try:
            toon_answer = ask_question(question, toon_encoded, "toon", model)
        except Exception as e:
            toon_answer = f"ERROR: {e}"

        json_ok = check_answer(expected, json_answer)
        toon_ok = check_answer(expected, toon_answer)

        if json_ok:
            json_correct += 1
        if toon_ok:
            toon_correct += 1

        results.append(QuestionResult(
            question=question,
            expected=expected,
            got_json=json_answer,
            got_toon=toon_answer,
            correct_json=json_ok,
            correct_toon=toon_ok,
        ))

        status_json = "OK" if json_ok else "MISS"
        status_toon = "OK" if toon_ok else "MISS"
        print(f"    Expected: {expected}")
        print(f"    JSON: {json_answer[:50]} [{status_json}]")
        print(f"    TOON: {toon_answer[:50]} [{status_toon}]")

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"JSON correct: {json_correct}/{num_questions} ({100*json_correct/num_questions:.1f}%)")
    print(f"TOON correct: {toon_correct}/{num_questions} ({100*toon_correct/num_questions:.1f}%)")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "num_questions": num_questions,
        "json_correct": json_correct,
        "toon_correct": toon_correct,
        "json_accuracy_pct": round(100 * json_correct / num_questions, 1),
        "toon_accuracy_pct": round(100 * toon_correct / num_questions, 1),
        "results": [
            {
                "question": r.question,
                "expected": r.expected,
                "json_answer": r.got_json,
                "toon_answer": r.got_toon,
                "json_correct": r.correct_json,
                "toon_correct": r.correct_toon,
            }
            for r in results
        ],
    }

    out_path = ARTIFACTS_DIR / f"needle_benchmark_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved: {out_path}")

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", "-n", type=int, default=50, help="Number of questions to ask")
    args = parser.parse_args()

    run_needle_benchmark(args.questions)
