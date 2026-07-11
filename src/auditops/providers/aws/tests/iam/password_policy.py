from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_iam_password_policy(tester):
    metadata = {
        "test_id": "aws-iam-006",
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
            "Exception Noted. IAM password policy does not meet the complexity requirements."
        )

    return test