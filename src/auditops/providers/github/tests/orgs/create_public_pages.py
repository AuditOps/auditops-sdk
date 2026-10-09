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
            "Called the GitHub API (https://api.github.com/orgs/[ORG_NAME]) to retrieve information about the GitHub organization.",
            "Saved the GitHub API response: orgs/org_settings.json.",
            "Inspected the evidence (orgs/org_settings.json) to determine if the GitHub organization is compliant with the test attribute(s) below.",
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