"""Deterministic data-quality detection for Integrix."""
import re
import pandas as pd
import numpy as np

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{7,17}$")
GENDER_MAP = {
    "m": "Male", "male": "Male", "man": "Male",
    "f": "Female", "female": "Female", "woman": "Female",
    "nonbinary": "Non-binary", "non-binary": "Non-binary",
}

def _missing(value):
    if pd.isna(value):
        return True
    return isinstance(value, str) and not value.strip()

def _add(items, position, col, issue_type, value, suggestion=None, confidence=0.0, reason=""):
    try:
        missing = pd.isna(value)
        if not isinstance(missing, (bool, np.bool_)):
            missing = False
    except (TypeError, ValueError):
        missing = False
    items.append({
        "row": int(position) + 1, "column": str(col), "issue_type": issue_type,
        "value": None if missing else str(value), "suggestion": suggestion,
        "confidence": round(float(confidence), 2), "reason": reason
    })

def _phone_suggestion(value):
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 10:
        return digits
    return None

def detect_issues(df: pd.DataFrame):
    """Return issues with 1-based positional row numbers (not index labels)."""
    issues = []
    if df is None or df.empty:
        return issues

    # Missing values, including whitespace-only strings.
    for col in df.columns:
        for pos, value in enumerate(df[col].tolist()):
            if _missing(value):
                _add(issues, pos, col, "Missing value", value, None, .99,
                     "Cell is null, empty, or whitespace-only; choose a value based on domain context.")

    # Exact duplicate rows, keeping the first occurrence.
    duplicate_mask = df.duplicated(keep="first").to_numpy()
    for pos in np.flatnonzero(duplicate_mask):
        _add(issues, int(pos), "*", "Duplicate row",
             " / ".join(map(str, df.iloc[int(pos)].tolist())), None, .99,
             "This complete row matches an earlier row. Confirm it is not a legitimate repeated transaction.")

    for col in df.columns:
        low = str(col).lower()
        series = df[col]

        if "email" in low:
            for pos, value in enumerate(series.tolist()):
                if not _missing(value) and not EMAIL_RE.fullmatch(str(value).strip()):
                    _add(issues, pos, col, "Invalid email", value, None, .45,
                         "Email does not match a basic address format; the missing or incorrect address cannot be safely guessed.")

        if any(k in low for k in ("phone", "mobile", "contact")):
            for pos, value in enumerate(series.tolist()):
                if _missing(value):
                    continue
                raw = str(value).strip()
                if not PHONE_RE.fullmatch(raw):
                    suggestion = _phone_suggestion(raw)
                    _add(issues, pos, col, "Invalid phone", value, suggestion,
                         .86 if suggestion else .40,
                         "Phone contains unexpected characters. A repair is suggested only when exactly 10 digits (or +91 plus 10 digits) can be recovered.")
                else:
                    suggestion = _phone_suggestion(raw)
                    if suggestion and raw != suggestion:
                        _add(issues, pos, col, "Phone formatting", value, suggestion, .90,
                             "A 10-digit phone number was normalized to digits only.")

        # Canonicalize known gender abbreviations and case-only variants.
        if "gender" in low or "sex" == low:
            for pos, value in enumerate(series.tolist()):
                if _missing(value):
                    continue
                key = re.sub(r"[\s_]+", "-", str(value).strip().lower())
                if key in GENDER_MAP and str(value) != GENDER_MAP[key]:
                    _add(issues, pos, col, "Inconsistent label", value, GENDER_MAP[key], .95,
                         "Recognized gender abbreviation or capitalization variant mapped to a standard label.")

        # Case/whitespace-only variants for low-cardinality categorical columns.
        elif series.dtype == "object":
            values = [str(v) for v in series.tolist() if not _missing(v)]
            if 1 < len(set(v.strip().lower() for v in values)) <= min(30, max(5, len(values)//2)):
                groups = {}
                for value in values:
                    groups.setdefault(value.strip().lower(), []).append(value)
                for variants in groups.values():
                    canonical = max(set(variants), key=lambda x: (variants.count(x), -len(x), x))
                    for pos, value in enumerate(series.tolist()):
                        if not _missing(value) and str(value) in variants and str(value) != canonical:
                            _add(issues, pos, col, "Inconsistent label", value, canonical, .90,
                                 "Values differ only by capitalization or surrounding whitespace; the most frequent spelling was selected.")

        # Mixed date formats; only date-named columns are considered.
        if any(k in low for k in ("date", "dob", "created", "updated")):
            valid_values = []
            for pos, value in enumerate(series.tolist()):
                if _missing(value):
                    continue
                raw_date = str(value).strip()
                # ISO/year-first dates must not be reinterpreted as day-first.
                year_first = bool(re.match(r"^\d{4}[-/.]", raw_date))
                parsed = pd.to_datetime(value, errors="coerce", dayfirst=not year_first)
                if pd.notna(parsed):
                    valid_values.append((pos, value, parsed))
            styles = set()
            for _, value, _ in valid_values:
                s = str(value)
                if "/" in s: styles.add("slash")
                if "-" in s: styles.add("hyphen")
                if "." in s: styles.add("dot")
            if len(styles) > 1:
                for pos, value, parsed in valid_values:
                    normalized = parsed.strftime("%Y-%m-%d")
                    if str(value) != normalized:
                        _add(issues, pos, col, "Mixed date format", value, normalized, .88,
                             "Date column contains multiple separators/formats; parsed value is normalized to YYYY-MM-DD. Review ambiguous dates.")

        # Numeric outliers are flagged only; never auto-modified.
        numeric = pd.to_numeric(series, errors="coerce")
        vals = numeric.dropna()
        if len(vals) >= 5 and vals.nunique() > 3:
            q1, q3 = vals.quantile(.25), vals.quantile(.75)
            iqr = q3 - q1
            if iqr > 0:
                lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                for pos, value in enumerate(numeric.tolist()):
                    if pd.notna(value) and (value < lo or value > hi):
                        _add(issues, pos, col, "Potential outlier", value, None, .70,
                             f"Value is outside IQR bounds [{lo:.2f}, {hi:.2f}]. This is a review flag, not proof of an error.")
    return issues
