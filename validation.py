"""Quality scoring and export helpers."""
import pandas as pd
from detect import detect_issues

def _missing_mask(df):
    mask = df.isna().copy()
    for col in df.columns:
        if df[col].dtype == "object" or pd.api.types.is_string_dtype(df[col]):
            mask[col] = mask[col] | df[col].astype("string").str.strip().eq("").fillna(False)
    return mask

def quality_report(df):
    total_cells = max(1, df.shape[0] * df.shape[1])
    missing_cells = int(_missing_mask(df).sum().sum())
    completeness = 100 * (1 - missing_cells / total_cells)
    uniqueness = 100 * (1 - int(df.duplicated().sum()) / max(1, len(df)))
    issues = detect_issues(df)
    validity_types = {"Invalid email", "Invalid phone", "Inconsistent label", "Mixed date format", "Phone formatting"}
    validity_issues = sum(1 for item in issues if item["issue_type"] in validity_types)
    validity = max(0, 100 * (1 - validity_issues / total_cells))
    score = .4 * completeness + .2 * uniqueness + .4 * validity
    return {
        "score": round(score, 1), "completeness": round(completeness, 1),
        "uniqueness": round(uniqueness, 1), "validity": round(validity, 1),
        "rows": int(df.shape[0]), "columns": int(df.shape[1]),
        "missing_cells": missing_cells, "duplicate_rows": int(df.duplicated().sum())
    }

def build_change_log(changes):
    return pd.DataFrame(changes, columns=["row", "column", "old_value", "new_value", "reason", "confidence", "issue_type"])
