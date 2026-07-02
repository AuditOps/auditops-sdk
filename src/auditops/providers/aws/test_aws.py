import pytest
from unittest.mock import Mock

from auditops.providers.aws import AWSConfig, AWSTester

@pytest.fixture
def config():
    return AWSConfig(
        in_scope_regions=["us-east-1"]
    )

@pytest.fixture
def reader():
    return Mock()

@pytest.fixture
def tester(reader, config):
    return AWSTester(reader, config)


def test_root_access_keys_missing_summary_fails(tester, reader):
    reader.read_json.return_value = None

    result = tester._test_iam_root_access_key()

    assert result.is_passing is False
    assert result.comments == "Unable to retrieve AWS account summary."

    reader.read_json.assert_called_once_with(
        "aws",
        "iam/account_summary.json"
    )


def test_root_access_keys_pass_when_none_exist(tester, reader):
    reader.read_json.return_value = {
        "SummaryMap": {
            "AccountAccessKeysPresent": 0
        }
    }

    result = tester._test_iam_root_access_key()

    assert result.is_passing is True
    assert result.comments == ""


def test_root_access_keys_fail_when_present(tester, reader):
    reader.read_json.return_value = {
        "SummaryMap": {
            "AccountAccessKeysPresent": 2
        }
    }

    result = tester._test_iam_root_access_key()

    assert result.is_passing is False
    assert result.comments == "Root account has 2 active access key(s)."


#
# IAM Password Policy
#

def test_password_policy_missing_fails(tester, reader):
    reader.read_json.return_value = None

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert result.comments == "No password policy configured."


def test_password_policy_passes(tester, reader):
    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 24,
            "ExpirePasswords": False,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is True
    assert result.comments == ""


def test_password_policy_fails_short_password(tester, reader):
    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 8,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 24,
            "ExpirePasswords": False,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert "Minimum password length" in result.comments


def test_password_policy_fails_missing_complexity(tester, reader):
    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 14,
            "RequireSymbols": False,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 24,
            "ExpirePasswords": False,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert "Symbols are not required." in result.comments


def test_password_policy_fails_password_history(tester, reader):
    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 5,
            "ExpirePasswords": False,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert "Password history" in result.comments


def test_password_policy_fails_expiration_disabled_when_required(reader):
    config = AWSConfig(
        in_scope_regions=["us-east-1"],
        iam_max_password_age=90,
    )

    tester = AWSTester(reader, config)

    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 24,
            "ExpirePasswords": False,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert "Password expiration is not enabled." in result.comments


def test_password_policy_fails_password_age(reader):
    config = AWSConfig(
        in_scope_regions=["us-east-1"],
        iam_max_password_age=90,
    )

    tester = AWSTester(reader, config)

    reader.read_json.return_value = {
        "PasswordPolicy": {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "PasswordReusePrevention": 24,
            "ExpirePasswords": True,
            "MaxPasswordAge": 365,
        }
    }

    result = tester._test_iam_password_policy()

    assert result.is_passing is False
    assert "Maximum password age" in result.comments