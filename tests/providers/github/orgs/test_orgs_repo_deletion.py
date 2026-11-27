from auditops.providers.github.tests.orgs import check_orgs_repo_deletion
from utils.evidence import load_evidence


def test_pass_members_cannot_delete_repos(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_delete_repositories": False,
            }
        },
    )

    result = check_orgs_repo_deletion(tester)

    assert result.is_passing is True
    assert result.is_excluded is False


def test_fail_members_can_delete_repos(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_delete_repositories": True,
            }
        },
    )

    result = check_orgs_repo_deletion(tester)

    assert result.is_passing is False
    assert result.is_excluded is False


def test_fail_missing_org_settings(tester):
    load_evidence(
        tester,
        {},
        missing_required={"orgs/org_settings.json"},
    )

    result = check_orgs_repo_deletion(tester)

    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (orgs/org_settings.json)."
    )
    assert result.is_passing is False
    assert result.is_excluded is False


def test_fail_missing_repo_deletion_setting(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {},
        },
    )

    result = check_orgs_repo_deletion(tester)

    assert result.is_passing is False
    assert result.is_excluded is False