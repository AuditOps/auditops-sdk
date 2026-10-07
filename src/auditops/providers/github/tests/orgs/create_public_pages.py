"""
    NOTE: Test logic is separate for the creation public pages and repositories.
    See full comment in create_public_repos for the rationale behind the decision.
"""

from auditops.core.utils import create_test


def check_orgs_members_create_public_pages(tester):
    metadata = {
        "test_id": "github-org-003",
        "test_description": "GitHub organization settings prevent members from creating public pages.",
        "risk_rating": 0,
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/[org_name].",
            "Saved the GitHub organization settings: orgs/org_settings.json.",
            "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
        ],
        "test_attributes": [
            "'members_can_create_public_pages' is set to false."
        ]
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail("ERROR: Unable to retrieve required evidence (orgs/org_settings.json).")

    test.is_passing = not org_settings.get(
        "members_can_create_public_pages", True
    )
    
    return test