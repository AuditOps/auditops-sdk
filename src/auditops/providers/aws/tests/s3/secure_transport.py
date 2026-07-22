from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test
import json


def check_s3_secure_transport(tester):
    metadata = {
        "test_id": "aws-s3-003",
        "test_description": "S3 buckets are configured to deny unencrypted data in-transit.",
        "risk_rating": 0,
        "test_procedures": [
            "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
            "Saved the list of buckets: s3/buckets.json.",
            "For each bucket, obtained the bucket policy by calling the get_bucket_policy() boto3 command.",
            "For each bucket, saved the bucket policy: s3/buckets/[bucket_name]/bucket_policy.json.",
            "For each bucket, inspected the bucket policy to determine if a statement exists that denies requests when aws:SecureTransport is false."
        ],
        "test_attributes": [],
        "table_headers": ["Bucket Name", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    buckets = tester.read("s3/buckets.json")

    for bucket in buckets.get("Buckets", []):
        bucket_name = bucket["Name"]

        sample = Sample(
            sample_id={
                "bucket_name": bucket_name,
            }
        )

        policy = tester.read(f"s3/buckets/{bucket_name}/policy.json", optional=True)

        if not policy:
            sample.comments = "No bucket policy found."
            test.samples.append(sample)
            continue

        try:
            policy_doc = json.loads(policy.get("Policy", "{}"))
        except Exception:
            sample.comments = "Unable to parse bucket policy."
            test.samples.append(sample)
            continue

        statements = policy_doc.get("Statement", [])

        if isinstance(statements, dict):
            statements = [statements]

        sample.is_passing = any(
            statement.get("Effect") == "Deny"
            and statement.get("Condition", {}).get("Bool", {}).get("aws:SecureTransport") == "false"
            for statement in statements
        )

        if not sample.is_passing:
            sample.comments = "No bucket policy statement enforcing SecureTransport."

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message="S3 bucket(s) do not enforce secure transport (HTTPS)."
    )

    return test