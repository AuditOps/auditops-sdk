from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test

def run_iam_tests(tester):
    return [
        test_iam_root_access_key(tester),
        test_iam_root_mfa(tester),
        test_iam_user_mfa(tester),
        test_iam_password_policy(tester)
    ]
    """
    FUTURE TESTS
    return [
        _test_iam_user_access_key_age(tester),
    ]
    """

def test_iam_root_access_key(tester):
    metadata = {
        "test_id": "aws-iam-001",
        "test_description": "Root account does not have any active access keys.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
            "Saved the account summary: iam/account_summary.json.",
            "Inspected the account summary to determine if 'AccountAccessKeysPresent' is set to 0."
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    summary = tester.read("iam/account_summary.json")

    root_keys = summary.get("SummaryMap", {}).get("AccountAccessKeysPresent", 0)

    if root_keys == 0:
        test.is_passing = True
    else:
        return fail_test(test, f"Exception Noted. Root account has {root_keys} active access key(s).")

    return test

def test_iam_root_mfa(tester):
    metadata = {
        "test_id": "aws-iam-003",
        "test_description": "Root account has MFA enabled.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
            "Saved the account summary: iam/account_summary.json",
            "Inspected the account summary to determine if 'AccountMFAEnabled' is set to 1."
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    summary = tester.read("iam/account_summary.json")

    mfa_enabled = summary.get("SummaryMap", {}).get("AccountMFAEnabled", 0)

    if mfa_enabled != 1:
        return fail_test(test, f"Exceptions Noted. Root account does not have MFA enabled.")

    return test


def test_iam_user_mfa(tester):
    metadata = {
        "test_id": "aws-iam-004",
        "test_description": "IAM users with an active console password have MFA enabled.",
        "risk_rating": 3,
        "table_headers": ["User Name", "Result", "Comments"],
        "test_procedures": [
            "Obtained a list of IAM users by calling the list_users() boto3 command.",
            "Saved the list of users: iam/users.json.",
            "For each user, obtained the login profile by calling the get_login_profile() boto3 command.",
            "For each user with a login profile, obtained MFA devices by calling the list_mfa_devices() boto3 command.",
            "Inspected the MFA device configuration to determine if at least one MFA device is assigned."
        ],
        "test_attributes": [
            "Users with a login profile have at least one MFA device."
        ]
    }

    test = create_test(tester, metadata)

    users = tester.read("iam/users.json")

    for user in users.get("Users", []):
        username = user["UserName"]

        login_profile = tester.read(
            f"iam/users/{username}/login_profile.json",
            optional=True,
        )

        # Skip users without console access.
        if not login_profile:
            continue

        sample = Sample(sample_id={"user_name": username})

        mfa_devices = tester.read(
            f"iam/users/{username}/mfa_devices.json"
        )

        if len(mfa_devices.get("MFADevices", [])) == 0:
            sample.comments = "Console password enabled but no MFA device assigned."

        sample.is_passing = len(mfa_devices.get("MFADevices", [])) > 0

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} IAM user(s) "
            "have an active console password but do not have MFA enabled."
        )

    return test


def test_iam_password_policy(tester):
    metadata = {
        "test_id": "aws-iam-005",
        "test_description": "IAM passwords comply with the organization's password policy.",
        "risk_rating": 2,
        "test_procedures": [
            "Obtained the IAM password policy by calling the get_account_password_policy() boto3 command.",
            "Saved the password policy: iam/password_policy.json.",
            "Inspected the password policy to determine if it complies with the configured requirements."
        ],
        "test_attributes": [
            f"Minimum password length >= {tester.config.iam_minimum_password_length}.",
            f"Password history >= {tester.config.iam_password_reuse_prevention}."
        ],
    }

    # Add additional test attributes based on AWSConfig.
    if tester.config.iam_require_symbols:
        metadata["test_attributes"].append("Passwords require symbols.")
    if tester.config.iam_require_numbers:
        metadata["test_attributes"].append("Passwords require numbers.")
    if tester.config.iam_require_uppercase:
        metadata["test_attributes"].append("Passwords require uppercase letters.")
    if tester.config.iam_require_lowercase:
        metadata["test_attributes"].append("Passwords require lowercase letters.")
    if tester.config.iam_max_password_age > 0:
        metadata["test_attributes"].append(f"Passwords expire within {tester.config.iam_max_password_age} days.")

    test = create_test(tester, metadata)

    policy = tester.read("iam/password_policy.json")

    if not policy:
        return fail_test(test, "No password policy configured.")

    password_policy = policy.get("PasswordPolicy", {})

    # Minimum password length
    actual = password_policy.get("MinimumPasswordLength", 0)
    if actual < tester.config.iam_minimum_password_length:
        test.is_passing = False

    # Password complexity
    if (tester.config.iam_require_symbols and not password_policy.get("RequireSymbols", False)):
        test.is_passing = False
    if (tester.config.iam_require_numbers and not password_policy.get("RequireNumbers", False)):
        test.is_passing = False
    if (tester.config.iam_require_uppercase and not password_policy.get("RequireUppercaseCharacters", False)):
        test.is_passing = False
    if (tester.config.iam_require_lowercase and not password_policy.get("RequireLowercaseCharacters", False)):
        test.is_passing = False
    # Password history
    actual = password_policy.get("PasswordReusePrevention", 0)
    if actual < tester.config.iam_password_reuse_prevention:
        test.is_passing = False

    # Password expiration (optional)
    if tester.config.iam_max_password_age > 0:
        if not password_policy.get("ExpirePasswords", False):
            test.is_passing = False
        else:
            actual = password_policy.get("MaxPasswordAge", 0)

            if actual > tester.config.iam_max_password_age:
                test.is_passing = False
    
    if not test.is_passing:
        test.comments = (
            "The AWS account password policy does not meet the configured requirements."
        )

    return test