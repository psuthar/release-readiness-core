from release_readiness_core.engine import ValidationMergeConfig, merge_validations


def test_merge_validations_uses_configured_evidence_keys():
    config = ValidationMergeConfig(
        evidence_boolean_keys=("auth_session", "upload_extraction"),
        risk_category_to_required_validation={"migrations": "migrations_validated"},
    )
    evidence = {
        "validations": {"qa_rag": True, "viewer_materials": False},
        "auth_session": True,
        "upload_extraction": False,
    }

    merged = merge_validations(evidence=evidence, risk_categories=("migrations",), config=config)

    assert merged["qa_rag"] is True
    assert merged["viewer_materials"] is False
    assert merged["auth_session"] is True
    assert merged["migrations_validated"] is False
    assert "upload_extraction" not in merged


def test_merge_validations_handles_empty_special_keys():
    config = ValidationMergeConfig(
        evidence_boolean_keys=(),
        risk_category_to_required_validation={"migrations": "migrations_validated"},
    )
    evidence = {"validations": {"qa_rag": True}, "auth_session": True}

    merged = merge_validations(evidence=evidence, risk_categories=("migrations",), config=config)

    assert merged == {"qa_rag": True, "migrations_validated": False}
