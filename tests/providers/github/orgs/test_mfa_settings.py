from auditops.providers.github.tests.orgs import check_orgs_mfa_settings
from utils.evidence import load_evidence


def test_fail_mfa_requirement_missing(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {}
        },
    )

    result = check_orgs_mfa_settings(tester)

    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (orgs/org_settings.json)."
    )    
    assert result.is_passing is False


def test_fail_missing_org_settings_fails(tester):
    load_evidence(tester, {}, missing_required={"orgs/org_settings.json"})

    result = check_orgs_mfa_settings(tester)

    assert result.is_passing is False

def test_pass_mfa_required(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "two_factor_requirement_enabled": True,
            }
        },
    )

    result = check_orgs_mfa_settings(tester)

    assert result.is_passing is True


def test_fail_mfa_not_required(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "two_factor_requirement_enabled": False,
            }
        },
    )

    result = check_orgs_mfa_settings(tester)

    assert result.is_passing is False