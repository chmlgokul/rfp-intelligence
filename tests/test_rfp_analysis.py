from modules.rfp_analysis import (
    bid_recommendation,
    clarification_questions,
    identify_risks,
    match_requirements,
    parse_capabilities,
    proposal_mapping,
)


def _requirements():
    return [
        {
            "Requirement": "Supplier must provide API integration and technical support.",
            "Category": "Technical",
            "Type": "Mandatory",
            "Source Page": 2,
            "Review Status": "Pending Review",
        },
        {
            "Requirement": "The bidder shall hold ISO certification.",
            "Category": "Certification",
            "Type": "Mandatory",
            "Source Page": 3,
            "Review Status": "Pending Review",
        },
    ]


def test_capability_matching_and_risk_register_are_explainable():
    capabilities = parse_capabilities("API integration and technical support\nQuality assurance")
    matches = match_requirements(_requirements(), capabilities)

    assert matches[0]["Match Status"] == "Match"
    assert matches[0]["Capability Evidence"] == "API integration and technical support"
    assert matches[1]["Match Status"] == "Gap"
    assert matches[1]["Capability Evidence"] == "No matching capability provided"
    assert matches[0]["Match Score"] > matches[1]["Match Score"]

    risks = identify_risks(matches)
    assert len(risks) == 1
    assert risks[0]["Risk Level"] == "High"


def test_recommendation_and_review_queues_keep_human_in_control():
    matches = match_requirements(_requirements(), ["API integration and technical support"])
    risks = identify_risks(matches)
    recommendation = bid_recommendation(matches, risks)

    assert recommendation["Mandatory Gaps"] == 1
    assert "human" in recommendation["Disclaimer"].lower()
    assert len(clarification_questions(matches)) == 1
    proposal = proposal_mapping(matches)
    assert proposal[0]["Response Status"] == "Not Started"
    assert proposal[0]["Human Approval"] == "Not Reviewed"
    assert "Draft:" in proposal[0]["Draft Response"]


def test_submission_instruction_is_not_counted_as_capability_gap():
    requirements = [{
        "Requirement": "The BOQ template must not be modified.",
        "Category": "Submission",
        "Type": "Mandatory",
        "Source Page": 1,
    }]

    match = match_requirements(requirements, ["STP operation and maintenance"])[0]

    assert match["Match Status"] == "Needs Verification"
