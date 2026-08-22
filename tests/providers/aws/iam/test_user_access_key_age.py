from datetime import datetime, timedelta, timezone

from auditops.providers.aws.tests.iam import check_iam_user_access_key_age
from utils.evidence import load_evidence


def _access_key_date(days_old):
    return (
        datetime.now(timezone.utc) - timedelta(days=days_old)
    ).isoformat().replace("+00:00", "Z")


def test_fail_missing_user_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"iam/users.json"},
    )

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is False
    assert result.comments == "ERROR: Unable to retrieve required evidence (iam/users.json)."


def test_pass_active_key_within_max_age(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIA123456789",
                    "Status": "Active",
                    "CreateDate": _access_key_date(30),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "user_name": "user1",
        "access_key_id": "AKIA123456789",
    }
    assert sample.comments == ""


def test_pass_active_key_at_max_age(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIA123456789",
                    "Status": "Active",
                    "CreateDate": _access_key_date(90),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "user_name": "user1",
        "access_key_id": "AKIA123456789",
    }
    assert sample.comments == ""


def test_fail_active_key_over_max_age(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIA123456789",
                    "Status": "Active",
                    "CreateDate": _access_key_date(91),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "user_name": "user1",
        "access_key_id": "AKIA123456789",
    }
    assert sample.comments == "Key is 91 days old."


def test_pass_inactive_key(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIA123456789",
                    "Status": "Inactive",
                    "CreateDate": _access_key_date(365),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "user_name": "user1",
        "access_key_id": "AKIA123456789",
    }
    assert sample.comments == "N/A - key is inactive."


def test_fail_mixed_key_population(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "passing-user",
                },
                {
                    "UserName": "failing-user",
                },
                {
                    "UserName": "inactive-user",
                },
            ]
        },
        "iam/users/passing-user/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIAPASSING",
                    "Status": "Active",
                    "CreateDate": _access_key_date(30),
                }
            ]
        },
        "iam/users/failing-user/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIAFAILING",
                    "Status": "Active",
                    "CreateDate": _access_key_date(91),
                }
            ]
        },
        "iam/users/inactive-user/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIAINACTIVE",
                    "Status": "Inactive",
                    "CreateDate": _access_key_date(365),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 3 IAM key(s) are active and over 90 days old."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == "Key is 91 days old."

    assert result.samples[2].is_passing is True
    assert result.samples[2].comments == "N/A - key is inactive."


def test_uses_configured_max_age(tester):
    tester.config.iam_access_key_max_age = 30

    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/access_keys.json": {
            "AccessKeyMetadata": [
                {
                    "AccessKeyId": "AKIA123456789",
                    "Status": "Active",
                    "CreateDate": _access_key_date(31),
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_access_key_age(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "user_name": "user1",
        "access_key_id": "AKIA123456789",
    }
    assert sample.comments == "Key is 31 days old."