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
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/[org_name].",
            "Saved the GitHub organization settings: orgs/org_settings.json.",
            "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
        ],
        "test_attributes": [
            "'members_can_create_public_repositories' is set to false.",
        ]
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