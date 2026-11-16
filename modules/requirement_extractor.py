"""Deterministic, source-grounded requirement extraction for RFP documents."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping


CATEGORY_KEYWORDS = {
    "Eligibility": ("eligibility", "eligible", "qualification", "qualifications", "registration", "registered", "turnover", "revenue", "financial capacity", "contractor", "entity"),
    "Technical": ("technical", "technology", "software", "hardware", "integration", "infrastructure", "system requirement", "technical specification", "architecture", "api", "security requirement", "performance", "operator", "service", "equipment", "lubricant", "functioning", "treated water", "testing", "cloud", "platform", "telemetry", "iot", "database", "analytics", "dashboard", "microservices"),
    "Certification": ("certification", "certifications", "certificate", "certificates", "iso", "license", "licence", "accreditation", "accredited"),
    "Experience": ("experience", "years of experience", "previous project", "similar project", "track record", "reference project", "client reference"),
    "Submission": ("submission", "submissions", "submit", "submitting", "proposal", "proposals", "bid document", "bidder", "upload", "uploaded", "tender document", "response format", "boq", "template", "portal", "clarification", "clarifications", "late submission"),
    "Timeline": ("deadline", "deadlines", "due date", "closing date", "last date", "submission date", "timeline", "timelines", "milestone", "milestones", "delivery date", "schedule"),
    "Commercial": ("commercial", "payment", "pricing", "financial", "budget", "cost", "penalty", "penalties", "liquidated damages", "invoice", "tax", "price schedule", "damages", "warranty"),
    "Compliance": ("compliance", "regulatory", "applicable law", "comply", "privacy", "data protection", "audit", "audits", "regulation", "standards", "standard"),
    "Risk": ("risk", "risks", "ambiguity", "unclear", "uncertainty", "resource constraint", "assumption", "dependency", "liability"),
}

MANDATORY_PATTERNS = (r"\bmust\b", r"\bshall\b", r"\bis required to\b", r"\bare required to\b", r"\brequired\b", r"\bmandatory\b", r"\bcompulsory\b", r"\bneed(?:s)? to\b")
OPTIONAL_PATTERNS = (r"\boptional\b", r"\bmay\b", r"\bpreferably\b", r"\bdesirable\b", r"\brecommended\b", r"\bshould\b")
ACTION_VERBS = ("provide", "submit", "maintain", "ensure", "identify", "include", "handle", "track", "create", "allow", "support", "demonstrate", "comply", "deliver", "possess", "establish", "prepare", "manage", "implement", "upload", "perform", "attach", "specify", "have", "meet", "complete", "respond")
BACKGROUND_STARTS = ("companies receive", "companies often", "the system should reduce", "you are expected", "the objective of this", "this project aims", "the final expectation", "the completed mvp", "the assignment will")

_PAGE_HEADER = re.compile(r"^(?:adz4needz\s*\|.*|page\s+\d+)\s*$", re.I)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_DATE_PATTERNS = (
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),
    re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4}\b",
        re.I,
    ),
    re.compile(
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|"
        r"Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
        re.I,
    ),
)
_DATE_CONTEXT = re.compile(
    r"\b(?:deadline|due date|closing date|last date|submission date|submit by|due by|"
    r"closes on|by|before)\b",
    re.I,
)


def clean_text(text: object) -> str:
    """Normalize whitespace and common PDF bullet artifacts."""
    if text is None:
        return ""
    value = unicodedata.normalize("NFKC", str(text))
    value = value.replace("\u00a0", " ").replace("\u00ad", "")
    value = re.sub(r"[\u2022\u25cf\u25aa\u25e6\u25b8]\s*", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n-")


def has_pattern(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _contains_keyword(text: str, keyword: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text, re.I) is not None


def classify_categories(text: str) -> list[str]:
    """Return all applicable categories in stable display order."""
    categories = [category for category, keywords in CATEGORY_KEYWORDS.items() if any(_contains_keyword(text, keyword) for keyword in keywords)]
    return categories or ["General"]


def classify_type(text: str) -> str:
    """Classify hard obligations before softer recommendations."""
    if has_pattern(text, MANDATORY_PATTERNS):
        return "Mandatory"
    if has_pattern(text, OPTIONAL_PATTERNS):
        return "Optional"
    return "Needs Verification"


def extract_deadline(text: str) -> str:
    """Return a date when the sentence clearly describes a deadline."""
    if not _DATE_CONTEXT.search(text):
        return ""
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return "Date mentioned - verify"


def is_requirement(text: str) -> bool:
    """Return whether a cleaned segment is actionable RFP content."""
    text = clean_text(text)
    lower = text.lower()
    if not 20 <= len(text) <= 700 or _PAGE_HEADER.match(text):
        return False
    if any(lower.startswith(start) for start in BACKGROUND_STARTS):
        return False
    if text.endswith(":") and not has_pattern(text, MANDATORY_PATTERNS + OPTIONAL_PATTERNS):
        return False
    if has_pattern(text, MANDATORY_PATTERNS + OPTIONAL_PATTERNS):
        return True
    has_action = any(re.search(r"\b" + re.escape(verb) + r"\b", lower) for verb in ACTION_VERBS)
    has_category = any(_contains_keyword(lower, keyword) for keywords in CATEGORY_KEYWORDS.values() for keyword in keywords)
    return has_action and has_category


def _candidate_segments(page_text: str) -> Iterable[str]:
    """Yield sentence-sized candidates while preserving page boundaries."""
    for raw_line in re.split(r"\r?\n", page_text or ""):
        line = clean_text(raw_line)
        if not line or _PAGE_HEADER.match(line):
            continue
        for segment in _SENTENCE_SPLIT.split(line):
            segment = re.sub(r"^(?:[-*]|\(?\d+[.)]|[a-z][.)])\s*", "", segment, flags=re.I)
            segment = clean_text(segment)
            if segment:
                yield segment


def _unique_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def extract_requirements(pages: Iterable[Mapping[str, object]] | None) -> list[dict[str, object]]:
    """Extract deduplicated, source-traceable requirements from page records."""
    requirements: list[dict[str, object]] = []
    seen: set[str] = set()
    for page in pages or []:
        if not isinstance(page, Mapping):
            continue
        page_number = page.get("page")
        for line in _candidate_segments(str(page.get("text", "") or "")):
            if not is_requirement(line):
                continue
            unique_key = _unique_key(line)
            if not unique_key or unique_key in seen:
                continue
            seen.add(unique_key)
            requirements.append({
                "Requirement": line,
                "Category": ", ".join(classify_categories(line)),
                "Type": classify_type(line),
                "Deadline": extract_deadline(line),
                "Evidence": "",
                "Reviewer Notes": "",
                "Source Page": page_number,
                "Review Status": "Pending Review",
            })
    return requirements
