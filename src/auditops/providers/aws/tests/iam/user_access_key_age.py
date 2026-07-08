from datetime import datetime, timezone

from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_iam_user_access_key_age(tester):
    max_age_days = tester.config.iam_access_key_max_age

    metadata = {
        "test_id": "aws-iam-XXX",
        "test_description": f"IAM user access keys are rotated at least every {max_age_days} days.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained a list of IAM users by calling the list_users() boto3 command.",
            "Saved the list of IAM users: iam/users.json.",
            "For each IAM user, obtained access key metadata by calling the list_access_keys() boto3 command.",
            "For each IAM user, saved access key metadata: iam/users/[user_name]/access_keys.json",
            "Inspected the 'AccessKeyMetadata' for each user to determine if they comply with the test attribute(s) below."
        ],
        "test_attributes": [
            f"'CREATE_DATE <= {max_age_days} days ago (for keys with an 'ACTIVE' status)."
        ],
        "table_headers": ["User", "Access Key ID", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    users = tester.read("iam/users.json")

    if not users:
        test.is_passing = False
        test.comments = "Unable to retrieve IAM users."
        return test

    now = datetime.now(timezone.utc)

    for user in users.get("Users", []):
        username = user["UserName"]

        keys = tester.read(
            f"iam/users/{username}/access_keys.json"
        )

        for key in keys.get("AccessKeyMetadata", []):
            sample = Sample(
                sample_id={
                    "user": username,
                    "access_key_id": key["AccessKeyId"],
                }
            )

            if key["Status"] != "Active":
                sample.is_excluded = True
                sample.comments = "N/A - key is inactive."
                test.samples.append(sample)
                continue

            create_date = key["CreateDate"]

            if isinstance(create_date, str):
                create_date = create_date.replace("Z", "+00:00")
                create_date = datetime.fromisoformat(create_date)

            actual_age_days = (now - create_date).days

            if actual_age_days <= max_age_days:
                sample.is_passing = True
            else:
                sample.comments = f"Key is {actual_age_days} days old."

            test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} IAM key(s) are over {max_age_days} days old."
        )

    return test