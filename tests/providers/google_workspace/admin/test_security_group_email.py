from auditops.providers.google_workspace.tests.admin import check_security_email
from utils.evidence import load_evidence


def test_fail_missing_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"admin/groups.json"},
    )

    result = check_security_email(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve list of Google Groups."
    )


def test_pass_no_required_group_emails(tester):
    tester.config.required_group_emails = []

    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "security@example.com",
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is True
    assert len(result.samples) == 0
    assert result.comments == ""


def test_fail_required_group_does_not_exist(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "security@example.com",
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == (
        "There is no Google Group associated with: required@example.com."
    )


def test_fail_missing_group_members_evidence(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "required@example.com",
                }
            ]
        }
    }

    load_evidence(
        tester,
        example_evidence,
        missing_required={
            "admin/groups/123456789/members.json"
        },
    )

    result = check_security_email(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == ("Unable to retrieve Google Group members.")


def test_fail_group_below_minimum_members(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "required@example.com",
                }
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user@example.com",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == (
        "Google Group has only 1 member(s). "
        "At least 2 members are required."
    )


def test_fail_missing_group_settings_evidence(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "required@example.com",
                }
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
    }

    load_evidence(
        tester,
        example_evidence,
        missing_required={
            "admin/groups/123456789/settings.json"
        },
    )

    result = check_security_email(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == (
        "Unable to retrieve Google Group settings."
    )


def test_fail_group_does_not_permit_public_posting(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "required@example.com",
                }
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
        "admin/groups/123456789/settings.json": {
            "whoCanPostMessage": "ALL_MANAGERS_CAN_POST",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == (
        "Google Group does not permit public posting. "
        "'whoCanPostMessage' is 'ALL_MANAGERS_CAN_POST'."
    )


def test_pass_required_group(tester):
    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "required@example.com",
                }
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
        "admin/groups/123456789/settings.json": {
            "whoCanPostMessage": "ANYONE_CAN_POST",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "group_email": "required@example.com"
    }
    assert sample.comments == (
        "Google Group exists with 2 members and permits public posting."
    )


def test_pass_required_group_alias(tester):
    tester.config.required_group_emails = [
        "security-alias@other-example.com"
    ]

    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "security@example.com",
                    "aliases": [
                        "security-alias@other-example.com"
                    ],
                }
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
        "admin/groups/123456789/settings.json": {
            "whoCanPostMessage": "ANYONE_CAN_POST",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "group_email": "security-alias@other-example.com"
    }
    assert sample.comments == (
        "Google Group exists with 2 members and permits public posting."
    )


def test_fail_mixed_group_population(tester):
    tester.config.required_group_emails = [
        "security@example.com",
        "compliance@example.com",
        "missing@example.com",
    ]

    example_evidence = {
        "admin/groups.json": {
            "groups": [
                {
                    "id": "123456789",
                    "name": "Security Team",
                    "email": "security@example.com",
                },
                {
                    "id": "987654321",
                    "name": "Compliance Team",
                    "email": "compliance@example.com",
                },
            ]
        },
        "admin/groups/123456789/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
        "admin/groups/123456789/settings.json": {
            "whoCanPostMessage": "ANYONE_CAN_POST",
        },
        "admin/groups/987654321/members.json": {
            "members": [
                {
                    "email": "user1@example.com",
                },
                {
                    "email": "user2@example.com",
                },
            ]
        },
        "admin/groups/987654321/settings.json": {
            "whoCanPostMessage": "ALL_MANAGERS_CAN_POST",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_security_email(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 required Google Groups do not meet "
        "the configuration requirements."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == (
        "Google Group exists with 2 members and permits public posting."
    )

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == (
        "Google Group does not permit public posting. "
        "'whoCanPostMessage' is 'ALL_MANAGERS_CAN_POST'."
    )

    assert result.samples[2].is_passing is False
    assert result.samples[2].comments == (
        "There is no Google Group associated with: missing@example.com."
    )