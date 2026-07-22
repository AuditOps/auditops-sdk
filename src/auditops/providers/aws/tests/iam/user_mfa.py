from datetime import datetime, timezone
from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_iam_user_mfa(tester):
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

    test.evaluate_samples(
        tester.exclusions,
        failure_message="IAM user(s) have an active console password but do not have MFA enabled."
    )

    return test