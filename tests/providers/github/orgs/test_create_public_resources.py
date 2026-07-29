from auditops.providers.github.tests.orgs import check_orgs_members_create_public_resources
from utils.evidence import load_evidence


def test_pass_members_cannot_create_public_resources(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_create_public_repositories": False,
                "members_can_create_public_pages": False,
            }
        },
    )

    result = check_orgs_members_create_public_resources(tester)

    assert result.is_passing is True


def test_pass_members_can_create_public_repositories(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_create_public_repositories": True,
                "members_can_create_public_pages": False,
            }
        },
    )

    result = check_orgs_members_create_public_resources(tester)

    assert result.is_passing is False


def test_fail_members_can_create_public_pages(tester):
    load_evidence(
        tester,
        {
            "orgs/org_settings.json": {
                "members_can_create_public_repositories": False,
                "members_can_create_public_pages": True,
            }
        },
    )

    result = check_orgs_members_create_public_resources(tester)

    assert result.is_passing is False


def test_fail_missing_org_settings_fails(tester):
    load_evidence(tester, {}, missing_required={"orgs/org_settings.json"})

    result = check_orgs_members_create_public_resources(tester)

    assert result.is_passing is False