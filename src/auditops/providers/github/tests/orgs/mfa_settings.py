from auditops.core.utils import create_test


def check_orgs_mfa_settings(tester):
    metadata = {
        "test_id": "github-org-001",
        "test_description": "GitHub organization settings require users to enable MFA.",
        "risk_rating": 3,
        "test_attributes": [
            "'two_factor_requirement_enabled' is set to true."
        ],
        "test_procedures": [
            "Called the GitHub API (https://api.github.com/orgs/[ORG_NAME]) to obtain information about the GitHub organization.",
            "Saved the GitHub API response: orgs/org_settings.json.",
            "Inspected the evidence (orgs/org_settings.json) to determine if the GitHub organization is compliant with the test attribute(s) below.",
        ],
        "test_attributes": [
            "'two_factor_requirement_enabled' is set to true.",
        ]
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail("ERROR: Unable to retrieve required evidence (orgs/org_settings.json).")

    test.is_passing = org_settings.get("two_factor_requirement_enabled", False)

    return test