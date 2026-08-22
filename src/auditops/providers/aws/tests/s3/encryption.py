from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_s3_encryption(tester):
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

    if not buckets:
        return test.fail("ERROR: Unable to retrieve required evidence (s3/buckets.json).")
    
    for bucket in buckets.get("Buckets"):
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

    test.evaluate_samples(
        tester.exclusions,
        failure_message="S3 bucket(s) do not have encryption enabled."
    )

    return test