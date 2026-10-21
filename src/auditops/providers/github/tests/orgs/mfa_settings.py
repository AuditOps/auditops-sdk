from auditops.core.utils import create_test


def check_orgs_mfa_settings(tester):
    metadata = {
        "test_id": "github-org-001",
        "test_description": "GitHub organization settings require users to enable MFA.",
        "risk_rating": 3,
        "test_procedures": [
            "Called the [Get an organization](https://docs.github.com/en/rest/orgs/orgs#get-an-organization) endpoint "
            "to obtain information about the GitHub organization.",
            "Saved the API response: orgs/org_settings.json.",
            "Inspected the evidence (orgs/org_settings.json) to determine whether the 'two_factor_requirement_enabled' property was set to 'true'."
        ],
        "test_attributes": [],
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail("ERROR: Unable to retrieve required evidence (orgs/org_settings.json).")

    test.is_passing = org_settings.get("two_factor_requirement_enabled", False)

    return test