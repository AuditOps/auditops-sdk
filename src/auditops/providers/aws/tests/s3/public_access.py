from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_s3_public_access(tester):
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
    
    test.evaluate_samples(
        tester.exclusions,
        tester.provider,
        failure_message="S3 bucket(s) are not configured to block public access."
    )

    return test