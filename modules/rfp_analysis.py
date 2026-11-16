
"""Explainable RFP analysis helpers used by the Streamlit MVP.

These functions intentionally use transparent heuristics instead of making
unsupported AI claims.  They produce review queues and evidence for a human
decision-maker; they never accept or reject an opportunity automatically.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping


DEFAULT_CAPABILITIES = (
    "Web and mobile application development",
    "Cloud deployment and infrastructure",
    "API integration and data engineering",
    "Cybersecurity and data protection",
    "Project management and technical support",
    "Quality assurance and testing",
)

_STOPWORDS = {
    "about", "after", "also", "and", "are", "business", "company", "from",
    "have", "into", "must", "need", "provide", "required", "shall", "should",
    "that", "the", "their", "this", "with", "will", "you", "your",
}


def _tokens(value: object) -> set[str]:
    words = re.findall(r"[a-z0-9]{3,}", str(value or "").casefold())
    return {word for word in words if word not in _STOPWORDS}


def parse_capabilities(value: str | Iterable[str] | None) -> list[str]:
    """Convert a textarea or iterable into unique, non-empty capabilities."""
    if value is None:
        return []
    values = value.splitlines() if isinstance(value, str) else value
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        cleaned = str(item).strip(" \t-*\r\n")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


def match_requirements(
    requirements: Iterable[Mapping[str, object]],
    capabilities: str | Iterable[str] | None,
) -> list[dict[str, object]]:
    """Match requirements to capabilities using token overlap and evidence."""
    capability_list = parse_capabilities(capabilities)
    capability_tokens = [(capability, _tokens(capability)) for capability in capability_list]
    matches: list[dict[str, object]] = []

    for requirement in requirements:
        text = str(requirement.get("Requirement", ""))
        requirement_tokens = _tokens(text)
        ranked = []
        for capability, tokens in capability_tokens:
            overlap = requirement_tokens & tokens
            ranked.append((len(overlap), capability, sorted(overlap)))
        ranked.sort(key=lambda item: item[0], reverse=True)
        score, evidence, shared = ranked[0] if ranked else (0, "", [])
        if score == 0:
            evidence = ""
            shared = []
        requirement_type = str(requirement.get("Type", "Needs Verification"))

        categories = {part.strip() for part in str(requirement.get("Category", "")).split(",")}

        if score >= 2:
            status = "Match"
        elif score == 1:
            status = "Partial Match"
        elif requirement_type == "Mandatory" and not ({"Submission", "Timeline"} & categories):
            status = "Gap"
        else:
            status = "Needs Verification"

        matches.append({
            **dict(requirement),
            "Match Status": status,
            "Match Score": round(min(score / 3, 1.0) * 100),
            "Capability Evidence": evidence or "No matching capability provided",
            "Shared Terms": ", ".join(shared) or "-",
        })
    return matches


def identify_risks(matches: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Create a reviewable risk register from requirement evidence."""
    risks: list[dict[str, object]] = []
    for item in matches:
        status = str(item.get("Match Status", ""))
        category = str(item.get("Category", "General"))
        requirement_type = str(item.get("Type", "Needs Verification"))
        requirement = str(item.get("Requirement", ""))
        if status == "Match" and category != "Risk":
            continue

        categories = {part.strip() for part in category.split(",")}
        if status == "Gap" and requirement_type == "Mandatory":
            level = "High"
            reason = "Mandatory requirement has no supporting capability evidence."
        elif "Timeline" in categories:
            level = "High" if requirement_type == "Mandatory" else "Medium"
            reason = "Deadline or delivery commitment needs owner and feasibility confirmation."
        elif "Compliance" in categories or "Eligibility" in categories:
            level = "High" if requirement_type == "Mandatory" else "Medium"
            reason = "Compliance or eligibility evidence must be verified before bidding."
        elif status == "Partial Match":
            level = "Medium"
            reason = "Only partial capability evidence was found."
        else:
            level = "Medium"
            reason = "Requirement needs manual verification or clarification."

        risks.append({
            "Risk Level": level,
            "Category": category,
            "Requirement": requirement,
            "Reason": reason,
            "Suggested Action": "Assign an owner, attach evidence, and record a reviewer decision.",
            "Source Page": item.get("Source Page"),
            "Status": "Open",
        })
    return risks


def clarification_questions(matches: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Generate human-review questions for ambiguous or unsupported items."""
    questions: list[dict[str, object]] = []
    for item in matches:
        if item.get("Match Status") not in {"Needs Verification", "Partial Match", "Gap"}:
            continue
        requirement = str(item.get("Requirement", ""))
        questions.append({
            "Question": f"What evidence or acceptance criteria will confirm: {requirement}",
            "Reason": "The current capability profile does not provide a complete match.",
            "Source Page": item.get("Source Page"),
            "Status": "Draft - review before sending",
        })
    return questions


def bid_recommendation(matches: Iterable[Mapping[str, object]], risks: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Return an explainable signal, never an automatic business decision."""
    match_list = list(matches)
    risk_list = list(risks)
    mandatory = [item for item in match_list if item.get("Type") == "Mandatory"]
    mandatory_gaps = [item for item in mandatory if item.get("Match Status") == "Gap"]
    high_risks = [item for item in risk_list if item.get("Risk Level") == "High"]
    verification = [item for item in match_list if item.get("Match Status") in {"Needs Verification", "Partial Match"}]
    score = 100
    score -= len(mandatory_gaps) * 30
    score -= len(high_risks) * 10
    score -= len(verification) * 3
    score = max(0, min(100, score))

    if mandatory_gaps:
        signal = "No-Bid signal - mandatory gaps require resolution"
    elif score >= 70:
        signal = "Bid signal - capability evidence is broadly aligned"
    else:
        signal = "Review before decision - evidence is incomplete"

    return {
        "Signal": signal,
        "Score": score,
        "Mandatory Requirements": len(mandatory),
        "Mandatory Gaps": len(mandatory_gaps),
        "High Risks": len(high_risks),
        "Items to Verify": len(verification),
        "Disclaimer": "This is decision support only. A human business user must approve the final Bid / No-Bid decision.",
    }


def proposal_mapping(matches: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Create a requirement-to-response work queue for proposal preparation."""
    def draft_response(item: Mapping[str, object]) -> str:
        status = str(item.get("Match Status", "Needs Verification"))
        evidence = str(item.get("Capability Evidence", "No matching capability provided"))
        if status == "Match":
            return f"Draft: We can address this requirement based on {evidence}. Confirm scope and attach supporting evidence before submission."
        if status == "Partial Match":
            return f"Draft: We can partially address this requirement through {evidence}. Confirm the remaining scope and required evidence."
        if status == "Gap":
            return "Draft: This requirement has an open capability gap. Confirm a partner, subcontractor, or mitigation before responding."
        return "Draft: Clarification is required before committing to this requirement."

    return [
        {
            "Requirement": item.get("Requirement"),
            "Response Owner": "Unassigned",
            "Response Status": "Not Started",
            "Evidence / Notes": item.get("Capability Evidence"),
            "Draft Response": draft_response(item),
            "Human Approval": "Not Reviewed",
            "Source Page": item.get("Source Page"),
        }
        for item in matches
    ]
