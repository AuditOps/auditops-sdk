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
            "Called the [GitHub API](https://docs.github.com/en/rest/orgs/orgs#get-an-organization) to obtain information about the GitHub organization.",
            "Saved the API response: orgs/org_settings.json.",
            "Inspected the evidence (orgs/org_settings.json) to determine whether the 'members_can_create_public_pages' property was set to 'false'."
        ],
        "test_attributes": [],  
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail("ERROR: Unable to retrieve required evidence (orgs/org_settings.json).")

    test.is_passing = not org_settings.get(
        "members_can_create_public_pages", True
    )
    
    return test