from auditops.core.utils import create_test, fail_test


def check_orgs_mfa_settings(tester):
    metadata = {
        "test_id": "github-org-001",
        "test_description": "GitHub organization settings require users to enable MFA.",
        "risk_rating": 3,
        "test_attributes": [
            "'two_factor_requirement_enabled' is set to true."
        ],
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/[org_name].",
            "Saved the GitHub organization settings: orgs/org_settings.json.",
            "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
        ]
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")
    test.is_passing = org_settings.get("two_factor_requirement_enabled")
    
    return test