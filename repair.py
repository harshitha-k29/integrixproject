"""Confidence-gated repair engine. Ambiguous changes are sent for human review."""
import pandas as pd
from contract import CONFIDENCE_THRESHOLD

AUTO_REPAIR_TYPES = {"Inconsistent label", "Mixed date format", "Phone formatting", "Invalid phone"}

def repair_dataset(df: pd.DataFrame, issues: list):
    cleaned = df.copy(deep=True)
    changes, review = [], []
    for issue in issues:
        row_pos = int(issue["row"]) - 1
        col = issue["column"]
        confidence = float(issue.get("confidence", 0))
        kind = issue["issue_type"]

        if kind == "Duplicate row":
            review.append({**issue, "recommended_action": "Review before removing duplicate"})
            continue
        if kind == "Missing value":
            review.append({**issue, "recommended_action": "Choose a domain-appropriate value"})
            continue
        if kind == "Potential outlier":
            review.append({**issue, "recommended_action": "Verify against domain rules; no automatic change"})
            continue
        if col not in cleaned.columns or row_pos < 0 or row_pos >= len(cleaned):
            continue
        suggestion = issue.get("suggestion")
        if kind not in AUTO_REPAIR_TYPES or suggestion is None or confidence < CONFIDENCE_THRESHOLD:
            review.append({**issue, "recommended_action": "Manual review required"})
            continue

        old = cleaned.iloc[row_pos][col]
        cleaned.iat[row_pos, cleaned.columns.get_loc(col)] = suggestion
        changes.append({
            "row": issue["row"], "column": col, "old_value": str(old),
            "new_value": str(suggestion), "reason": issue.get("reason", ""),
            "confidence": confidence, "issue_type": kind
        })
    return cleaned, changes, review
