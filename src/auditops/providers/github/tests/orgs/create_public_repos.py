"""
    NOTE: Test logic is separate for the creation public pages and repositories.
    This decision was made because the ability to create public repos 
    is only available on the GitHub Enterprise plan.
"""

from auditops.core.utils import create_test


def check_orgs_members_create_public_repos(tester):
    metadata = {
        "test_id": "github-org-002",
        "test_description": "GitHub organization settings prevent members from creating public repositories.",
        "risk_rating": 0,
        "test_procedures": [
            "Called the [Get an organization](https://docs.github.com/en/rest/orgs/orgs#get-an-organization) endpoint "
            "to obtain information about the GitHub organization.",
            "Saved the API response: orgs/org_settings.json.",
            "Inspected the evidence (orgs/org_settings.json) to determine whether the 'members_can_create_public_repositories' property was set to 'false'."
        ],
        "test_attributes": [],
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail("ERROR: Unable to retrieve required evidence (orgs/org_settings.json).")

    test.is_passing = not org_settings.get(
        "members_can_create_public_repositories", True
    )

    github_plan_type = org_settings.get("plan", {}).get("name", "").lower()

    if not test.is_passing and github_plan_type != "enterprise":
        test.is_excluded = True
        test.comments = "N/A - This setting is not enforceable on the current GitHub organization plan."
        return test
    
    return test