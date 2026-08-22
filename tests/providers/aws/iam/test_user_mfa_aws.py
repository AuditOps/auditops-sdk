from auditops.providers.aws.tests.iam import check_iam_user_mfa
from utils.evidence import load_evidence


def test_fail_missing_user_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"iam/users.json"},
    )

    result = check_iam_user_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (iam/users.json)."
    )


def test_pass_user_with_mfa(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/login_profile.json": {
            "LoginProfile": {
                "UserName": "user1",
            }
        },
        "iam/users/user1/mfa_devices.json": {
            "MFADevices": [
                {
                    "SerialNumber": "arn:aws:iam::123456789012:mfa/user1",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"user_name": "user1"}
    assert sample.comments == ""


def test_fail_user_without_mfa(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/login_profile.json": {
            "LoginProfile": {
                "UserName": "user1",
            }
        },
        "iam/users/user1/mfa_devices.json": {
            "MFADevices": []
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_mfa(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"user_name": "user1"}
    assert sample.comments == (
        "Console password enabled but no MFA device assigned."
    )


def test_pass_user_without_console_access(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 0
    assert result.comments == ""


def test_pass_user_with_multiple_mfa_devices(tester):
    example_evidence = {
        "iam/users.json": {
            "Users": [
                {
                    "UserName": "user1",
                }
            ]
        },
        "iam/users/user1/login_profile.json": {
            "LoginProfile": {
                "UserName": "user1",
            }
        },
        "iam/users/user1/mfa_devices.json": {
            "MFADevices": [
                {
                    "SerialNumber": "arn:aws:iam::123456789012:mfa/user1",
                },
                {
                    "SerialNumber": "arn:aws:iam::123456789012:mfa/user1-backup",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"user_name": "user1"}
    assert sample.comments == ""


def test_fail_mixed_user_population(tester):
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
                    "UserName": "no-console-user",
                },
            ]
        },
        "iam/users/passing-user/login_profile.json": {
            "LoginProfile": {
                "UserName": "passing-user",
            }
        },
        "iam/users/passing-user/mfa_devices.json": {
            "MFADevices": [
                {
                    "SerialNumber": (
                        "arn:aws:iam::123456789012:mfa/passing-user"
                    ),
                }
            ]
        },
        "iam/users/failing-user/login_profile.json": {
            "LoginProfile": {
                "UserName": "failing-user",
            }
        },
        "iam/users/failing-user/mfa_devices.json": {
            "MFADevices": []
        },
    }

    load_evidence(tester, example_evidence)

    result = check_iam_user_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 2 IAM user(s) have an active console password but do not have MFA enabled."
    )

    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == (
        "Console password enabled but no MFA device assigned."
    )