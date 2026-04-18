import os
import google.generativeai as genai
from dotenv import load_dotenv

def get_gemini_model():
    load_dotenv()  # works locally, ignored on HF Spaces

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("⚠️ GEMINI_API_KEY not found. Running without AI.")
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")  # stable + fast

# initialize once
model = get_gemini_model()


def explain_bias_report(metrics: dict, intersectional: dict = None) -> dict:
    if model is None:
        return {
            "raw": "AI explanation unavailable — API key not configured.",
            "sections": {}
        }
    fairness_scores = metrics.get("fairness_scores", {})
    group_metrics = metrics.get("group_metrics", {})

    prompt = f"""
You are a responsible AI auditor explaining bias findings to a non-technical compliance team.

AUDIT RESULTS:
- Protected attribute analyzed: {metrics.get("protected_column")}
- Target/decision column: {metrics.get("target_column")}
- Overall bias verdict: {fairness_scores.get("bias_verdict")}
- Demographic parity gap: {fairness_scores.get("demographic_parity_gap")} (ideal = 0)
- Disparate impact ratio: {fairness_scores.get("disparate_impact_ratio")} (ideal = 1.0, below 0.8 = biased)
- Equalized odds TPR gap: {fairness_scores.get("equalized_odds_tpr_gap")}
- Group-level positive rates: {group_metrics}

{f'''INTERSECTIONAL FINDINGS:
- Worst combination: {intersectional["summary"]["worst_combination"]}
- Worst gap: {intersectional["summary"]["worst_gap"]}
- Most disadvantaged group: {_get_disadvantaged(intersectional)}
''' if intersectional else ''}

Write a clear explanation with these exact sections:
1. SUMMARY (2 sentences max — what is happening in plain English)
2. WHO IS AFFECTED (which groups, how severely)
3. REAL WORLD IMPACT (what this means if deployed)
4. ROOT CAUSE (likely reason bias exists in data)
5. RECOMMENDED FIXES (top 2 specific actions)

Be direct, factual, and avoid jargon. Write for a business audience.
"""

    if not model:
        return {
            "raw": "Gemini explanation skipped because GEMINI_API_KEY is not configured.",
            "sections": {}
        }

    try:
        response = model.generate_content(prompt)
        text = response.text
    except Exception as e:
        return {
            "raw": f"Gemini explanation failed: {str(e)}",
            "sections": {}
        }

    sections = {}
    current = None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for key in ["SUMMARY", "WHO IS AFFECTED", "REAL WORLD IMPACT", "ROOT CAUSE", "RECOMMENDED FIXES"]:
            if key in line.upper():
                current = key
                sections[current] = ""
                break
        else:
            if current:
                sections[current] += line + " "

    return {
        "raw": text,
        "sections": {k: v.strip() for k, v in sections.items()}
    }

def explain_remediation(before: dict, after: dict) -> str:
    if model is None:
        return "AI explanation unavailable — API key not configured."
    prompt = f"""
Explain in 3 sentences what changed after bias remediation.
Before: demographic parity gap = {before.get("fairness_scores", {}).get("demographic_parity_gap")}, verdict = {before.get("fairness_scores", {}).get("bias_verdict")}
After: demographic parity gap = {after.get("fairness_scores", {}).get("demographic_parity_gap")}, verdict = {after.get("fairness_scores", {}).get("bias_verdict")}
Write for a non-technical audience. Be specific about improvement.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def _get_disadvantaged(intersectional: dict) -> str:
    worst_key = intersectional["summary"].get("worst_combination", "")
    worst = intersectional["intersectional_analysis"].get(worst_key, {})
    return worst.get("most_disadvantaged", "unknown")