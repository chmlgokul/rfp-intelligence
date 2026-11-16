from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_starts_without_exception():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "AssistLana - RFP intelligence"
    assert app.info


def test_app_admin_role_switch():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=10).run()
    # Switch role to Admin
    app.selectbox[0].select("Admin").run()
    assert not app.exception
    assert any("Admin Mode" in info.value for info in app.info)


def test_app_decision_centre_renders_with_analysis():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=10).run()
    app.session_state["requirements"] = [
        {"Requirement": "Must have ISO 27001", "Category": "Certification", "Type": "Mandatory", "Source Page": 1, "Review Status": "Pending Review", "Deadline": "", "Evidence": "", "Reviewer Notes": ""}
    ]
    app.session_state["matches"] = [
        {"Requirement": "Must have ISO 27001", "Category": "Certification", "Type": "Mandatory", "Source Page": 1, "Match Status": "Gap", "Match Score": 0, "Capability Evidence": "No matching capability provided", "Shared Terms": "-"}
    ]
    app.session_state["risks"] = [
        {"Risk Level": "High", "Category": "Certification", "Requirement": "Must have ISO 27001", "Reason": "Mandatory gap", "Suggested Action": "Review", "Source Page": 1, "Status": "Open"}
    ]
    app.session_state["recommendation"] = {
        "Signal": "No-Bid signal - mandatory gaps require resolution",
        "Score": 0,
        "Mandatory Requirements": 1,
        "Mandatory Gaps": 1,
        "High Risks": 1,
        "Items to Verify": 0,
        "Disclaimer": "Human review required",
    }
    app.session_state["file_name"] = "sample.pdf"
    app.run()
    assert not app.exception
    assert any("RECOMMENDATION: NO-BID" in err.value for err in app.error)
