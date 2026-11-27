from auditops.core.utils import create_test


def check_orgs_repo_deletion(tester):
    metadata = {
        "test_id": "github-org-004",
        "test_description": (
            "Organization members cannot delete or transfer repositories."
        ),
        "risk_rating": 3,
        "test_procedures": [
            "Obtained the GitHub organization metadata by calling the [Get an organization](https://docs.github.com/en/rest/orgs/orgs#get-an-organization) "
            "GitHub endpoint.",
            "Saved the GitHub organization metadata: orgs/org_settings.json.",
            "Inspected the GitHub organization metadata to determine whether the 'members_can_delete_repositories' property was set to 'false'.",
        ],
        "test_attributes": [],
        "remediation_url": "",
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("orgs/org_settings.json")

    if not org_settings:
        return test.fail(
            "ERROR: Unable to retrieve required evidence (orgs/org_settings.json)."
        )

    test.is_passing = not org_settings.get(
        "members_can_delete_repositories",
        True,
    )

    return test