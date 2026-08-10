from auditops.core.models import Sample
from auditops.core.utils import create_test, evaluate_tags


def check_s3_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-s3-004",
        "test_description": (
            "S3 buckets must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 0,
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

    test.evaluate_samples(
        tester.exclusions, 
        failure_message="S3 bucket(s) are missing required tags or have empty values."
    )

    return test