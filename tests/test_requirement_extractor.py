from modules.requirement_extractor import extract_deadline, extract_requirements


def test_deadline_is_extracted_only_from_deadline_context():
    assert extract_deadline("The submission deadline is 30/11/2026.") == "30/11/2026"
    assert extract_deadline("The project starts on 30/11/2026.") == ""


def test_requirement_records_include_deadline_and_review_fields():
    pages = [{
        "page": 1,
        "text": "The bidder must submit the proposal by 30/11/2026.",
    }]

    requirements = extract_requirements(pages)

    assert requirements[0]["Deadline"] == "30/11/2026"
    assert requirements[0]["Review Status"] == "Pending Review"
