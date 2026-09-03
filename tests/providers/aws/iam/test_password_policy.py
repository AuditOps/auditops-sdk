from auditops.providers.aws import AWSConfig
from auditops.providers.aws.tests.iam import check_iam_password_policy
from utils.evidence import load_evidence


def test_metadata(tester):
    load_evidence(tester, {}, missing_required={"iam/password_policy.json"})

    result = check_iam_password_policy(tester)

    assert result.test_id == "aws-iam-005"
    assert result.test_description == "IAM passwords comply with the organization's password policy."
    assert result.risk_rating == 2
    assert result.test_procedures == [
        "Obtained the IAM password policy by calling the get_account_password_policy() boto3 command.",
        "Saved the password policy: iam/password_policy.json.",
        "Inspected the password policy to determine if it complies with the configured requirements."
    ]
    assert result.test_attributes == [
        "Minimum password length >= 14.",
        "Password history >= 24.",
        "Passwords require symbols.",
        "Passwords require numbers.",
        "Passwords require uppercase letters.",
        "Passwords require lowercase letters."
    ]


def test_fail_missing_evidence(tester):
    load_evidence(tester, {}, missing_required={"iam/password_policy.json"})

    result = check_iam_password_policy(tester)

    assert result.is_passing is False
    assert result.comments == "No password policy configured."


def test_pass_password_policy_passes(tester):
    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is True
    assert result.comments == ""


def test_fail_short_password(tester):
    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is False


def test_fail_missing_complexity(tester):
    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is False
    assert (
        "IAM password policy does not meet the complexity requirements."
        in result.comments
    )


def test_fail_insufficient_password_history(tester):
    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is False


def test_fail_expiration_disabled_when_required(tester):
    tester.config = AWSConfig(
        in_scope_regions=["us-east-1"],
        iam_max_password_age=90,
    )

    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is False


def test_fail_insufficient_password_age(tester):
    tester.config = AWSConfig(
        in_scope_regions=["us-east-1"],
        iam_max_password_age=90,
    )

    load_evidence(
        tester,
        {
            "iam/password_policy.json": {
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
        },
    )

    result = check_iam_password_policy(tester)

    assert result.is_passing is False