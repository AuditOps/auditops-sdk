from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def run_s3_tests(tester):
    return [
        test_s3_encryption(tester),
        test_s3_public_access(tester),
        test_s3_secure_transport(tester),
        test_s3_tags(tester)
    ]

def test_s3_encryption(tester):
    metadata = {
        "test_id": "aws-s3-001",
        "test_description": "S3 buckets are encrypted at rest.",
        "risk_rating": 2,
        "table_headers": ["Bucket Name", "Result", "Comments"],
        "test_procedures": [
            "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
            "Saved the list of buckets: s3/buckets.json.",
            "For each S3 bucket, obtained the encryption settings by calling the get_bucket_encryption() boto3 command.",
            "For each S3 bucket, saved the encryption settings: s3/buckets/[bucket_name]/encryption.json.",
            "For each S3 bucket, inspected the encryption settings to determine if they comply with the test attribute(s) below."
        ],
        "test_attributes": [
            "ServerSideEncryptionConfiguration is present."
        ],               
    }

    test = create_test(tester, metadata)

    buckets = tester.read("s3/buckets.json")

    for bucket in buckets.get("Buckets", []):
        bucket_name = bucket["Name"]
        sample = Sample(sample_id={"bucket_name": bucket_name})

        encryption = tester.read(f"s3/buckets/{bucket_name}/encryption.json", optional=True)

        if not encryption:
            sample.comments = "No encryption configuration found."
            test.samples.append(sample)
            continue
        
        sample.is_passing = bool(encryption.get("ServerSideEncryptionConfiguration"))

        if not sample.is_passing:
            sample.comments = "No encryption configuration found"

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    return test


def test_s3_public_access(tester):
    metadata = {
        "test_id": "aws-s3-002",
        "test_description": "S3 buckets are configured to block public access.",
        "risk_rating": 2,
        "table_headers": ["Bucket Name", "Result", "Comments"],
        "test_procedures": [
            "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
            "Saved the list of buckets: s3/buckets.json.",
            "For each bucket, obtained the public access block settings by calling the get_public_access_block() boto3 command.",
            "For each bucket, saved the public access block settings: s3/buckets/[bucket_name]/public_access_block.json.",
            "For each bucket, inspected the public access block settings to determine if they comply with the test attribute(s) below."
        ],
        "test_attributes": [
            "BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, and RestrictPublicBuckets are set to true."
        ]          
    }
    test = create_test(tester, metadata)

    buckets = tester.read("s3/buckets.json")

    for bucket in buckets.get("Buckets", []):
        bucket_name = bucket["Name"]
        sample = Sample(sample_id={"bucket_name": bucket_name})

        public_access_block = tester.read(f"s3/buckets/{bucket_name}/public_access_block.json", optional=True)
        
        if not public_access_block:
            sample.comments = "No Public Access Block configuration found."
            test.samples.append(sample)
            continue

        config = public_access_block.get("PublicAccessBlockConfiguration", {})
        sample.is_passing = all([config.get("BlockPublicAcls", False), config.get("IgnorePublicAcls", False),
        config.get("BlockPublicPolicy", False), config.get("RestrictPublicBuckets", False)])

        if not sample.is_passing:
            sample.comments = "One or more public access settings are disabled."

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    return test


import json


def test_s3_secure_transport(tester):
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

        policy = tester.read(f"s3/buckets/{bucket_name}/policy.json")

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

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} S3 bucket(s) do not enforce secure transport (HTTPS)."
        )

    return test


def test_s3_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-s3-004",
        "test_description": (
            "S3 buckets must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
            "Saved the list of buckets: s3/buckets.json.",
            "For each bucket, obtained its tags by calling the get_bucket_tagging() boto3 command.",
            "For each bucket, saved the tags: s3/buckets/[bucket_name]/tags.json.",
            f"For each bucket, inspected the tags to determine if the following tag keys exist and have non-empty values: {required_tags}"
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

        tags = tester.read(f"s3/buckets/{bucket_name}/tags.json", optional=True)

        if not tags:
            sample.comments = "Tags not found on this bucket."
            test.samples.append(sample)
            continue

        actual_bucket_tags = {
            tag["Key"]: tag.get("Value", "")
            for tag in tags.get("TagSet", [])
        }

        evaluate_tags(sample, required_tags, actual_bucket_tags)

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} S3 bucket(s) are missing required tags or have empty values."
        )        

    return test