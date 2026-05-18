"""
Ground truth answer for the L'Oréal Vietnam Q3 2025 RCA scenario.
Used by the evaluator to score Response Generation Agent outputs.
"""

GROUND_TRUTH = {
    "summary": (
        "Q3 revenue declined 18.4% (15.7B VND) due to three converging operational "
        "issues: (1) a Hanoi DC customs delay that caused multi-week stock-outs of "
        "DPD products in North Vietnam, (2) Beauty Republic's aggressive LUXE "
        "campaign on TikTok Shop that captured share from Lancôme/Kiehl's/YSL, "
        "and (3) Saigon Distribution Co.'s working-capital crisis that cut "
        "inventory holdings and broke Modern Trade coverage in HCMC/Mekong."
    ),
    "root_causes": [
        {
            "rank": 1,
            "cause": "North Vietnam stock-outs from Hanoi DC customs clearance delay",
            "estimated_impact_pct_of_decline": "~45%",
            "estimated_impact_vnd_b": -7.0,
            "key_evidence_keywords": [
                "Hanoi DC", "OOS", "out-of-stock", "21.4", "customs",
                "11.8", "18.2", "OTD", "71%", "DPD", "La Roche-Posay",
                "CeraVe", "North", "-28", "lead time",
            ],
        },
        {
            "rank": 2,
            "cause": "Beauty Republic competitive offensive on TikTok Shop (LUXE tier)",
            "estimated_impact_pct_of_decline": "~30%",
            "estimated_impact_vnd_b": -4.7,
            "key_evidence_keywords": [
                "Beauty Republic", "TikTok", "-28", "-22", "LUXE",
                "Lancôme", "Kiehl", "YSL", "traffic", "-35",
                "market share", "competitor", "new SKU", "Aurora",
                "Crystal", "Velvet",
            ],
        },
        {
            "rank": 3,
            "cause": "Saigon Distribution Co. inventory crisis impacting Modern Trade in South",
            "estimated_impact_pct_of_decline": "~25%",
            "estimated_impact_vnd_b": -4.0,
            "key_evidence_keywords": [
                "Saigon Distribution", "distributor", "8.2", "4.1",
                "inventory days", "28", "11", "Modern Trade",
                "HCMC", "South", "-21", "-19",
            ],
        },
    ],
    "red_herrings_to_avoid": [
        # Things that look interesting but aren't actually root causes
        "FX impact (only -0.3B VND — minimal)",
        "Customer returns / quality (flat)",
        "Raw material costs (flat)",
        "Tariff changes (none)",
        "Holiday calendar (comparable to Q2)",
        "Marketing spend (modest TikTok cut, not primary driver)",
        "Weather (typhoon was minor impact)",
    ],
    "expected_recommended_actions": [
        "Escalate Hanoi DC customs clearance with logistics partner; expedite backlog",
        "Replenish North Vietnam stock; consider air freight for top SKUs",
        "Counter Beauty Republic on TikTok Shop with targeted LUXE campaign",
        "Audit Saigon Distribution Co. financial health; evaluate backup distributor",
        "Increase safety stock on top declining SKUs",
    ],
}
