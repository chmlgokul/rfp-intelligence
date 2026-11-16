from modules.opportunity_storage import list_opportunities, load_opportunity, save_opportunity


def test_opportunity_storage_round_trip(tmp_path):
    db_path = tmp_path / "opportunities.db"
    payload = {
        "file_name": "example.xlsx",
        "opportunity_stage": "Review",
        "human_decision": "Pending human review",
        "requirements": [{"Requirement": "Supplier must provide support"}],
    }

    opportunity_id = save_opportunity(payload, db_path=db_path)
    payload["opportunity_stage"] = "Proposal"
    save_opportunity(payload, opportunity_id, db_path)

    summaries = list_opportunities(db_path)
    loaded = load_opportunity(opportunity_id, db_path)

    assert summaries[0]["file_name"] == "example.xlsx"
    assert summaries[0]["stage"] == "Review" or summaries[0]["stage"] == "Proposal"
    assert loaded["opportunity_stage"] == "Proposal"
    assert loaded["opportunity_id"] == opportunity_id
