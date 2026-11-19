"""Shared contracts and policy constants for Integrix."""
from typing import TypedDict, Optional

CONFIDENCE_THRESHOLD = 0.80

class Issue(TypedDict):
    row: int
    column: str
    issue_type: str
    value: Optional[str]
    suggestion: Optional[str]
    confidence: float
    reason: str

class ChangeRecord(TypedDict):
    row: int
    column: str
    old_value: str
    new_value: str
    reason: str
    confidence: float
    issue_type: str
