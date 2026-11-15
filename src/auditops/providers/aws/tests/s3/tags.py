from auditops.core.models import Sample
from auditops.core.utils import create_test, evaluate_tags


def check_s3_tags(tester):
    if tester.config.s3_required_tags is None:
        required_tags = tester.config.required_tags
    else:
        required_tags = tester.config.s3_required_tags

    metadata = {
        "test_id": "aws-s3-004",
        "test_description": (
            "S3 buckets must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 0,
        "test_procedures": [
            "Called the [list_buckets()](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/list_buckets.html#) "
            "boto3 command to obtain a list of all S3 buckets.",
            "Saved the API response: s3/buckets.json.",
            "For each bucket, performed the following steps:",
            "- Called the [get_bucket_tagging()](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/get_bucket_tagging.html#) "
            " boto3 command to obtain the bucket's tags",
            "- Saved the API response: s3/buckets/[bucket_name]/tags.json.",
            f"- Inspected the tags to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Bucket Name", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    buckets = tester.read("s3/buckets.json")

    if not buckets:
        return test.fail("ERROR: Unable to retrieve required evidence (s3/buckets.json).")    

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