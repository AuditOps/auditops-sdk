from auditops.providers.github.tests.orgs import check_orgs_members_create_public_repos
from utils.evidence import load_evidence


def test_pass_members_cannot_create_public_repos(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "plan": {
                    "name": "enterprise",
                },
                "members_can_create_public_repositories": False,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_passing is True
    assert result.is_excluded is False

def test_fail_members_can_create_public_repos(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "plan": {
                    "name": "enterprise",
                },
                "members_can_create_public_repositories": True,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_passing is False
    assert result.is_excluded is False


def test_fail_missing_org_settings_fails(tester):
    load_evidence(tester, {}, missing_required={"orgs/org_settings.json"})

    result = check_orgs_members_create_public_repos(tester)

    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (orgs/org_settings.json)."
    )
    assert result.is_passing is False
    assert result.is_excluded is False


def test_pass_non_enterprise_plan(tester):
    # NOTE: Test should ignore the plan type unless the setting allows members to create public repos.
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "plan": {
                    "name": "team",
                },
                "members_can_create_public_repositories": False,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_passing is True


def test_exclude_missing_plan_without_protection(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_create_public_repositories": True,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_excluded is True
    assert result.is_passing is False
    assert result.comments == (
        "N/A - This setting is not enforceable on the current GitHub organization plan."
    )

def test_pass_missing_plan_with_protection(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_create_public_repositories": False,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_excluded is False
    assert result.is_passing is True

def test_exclude_non_enterprise_plan(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "plan": {
                    "name": "team",
                },
                "members_can_create_public_repositories": True,
            }
        },
    )

    result = check_orgs_members_create_public_repos(tester)

    assert result.is_excluded is True
    assert result.is_passing is False
    assert result.comments == (
        "N/A - This setting is not enforceable on the current GitHub organization plan."
    )