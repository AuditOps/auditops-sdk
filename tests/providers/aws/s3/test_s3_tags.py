from auditops.providers.aws.tests.s3 import check_s3_tags
from utils.evidence import load_evidence


def test_fail_missing_bucket_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"s3/buckets.json"},
    )

    result = check_s3_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (s3/buckets.json)."
    )


def test_pass_bucket_with_required_tags(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "Production application data",
                },
                {
                    "Key": "Classification",
                    "Value": "Confidential",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == ""


def test_fail_bucket_missing_required_tag(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "Production application data",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 S3 bucket(s) are missing required tags or have empty values."
    )    

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "example-bucket"}


def test_fail_bucket_with_empty_required_tag_value(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "",
                },
                {
                    "Key": "Classification",
                    "Value": "Confidential",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "example-bucket"}


def test_pass_bucket_with_extra_tags(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "Production application data",
                },
                {
                    "Key": "Classification",
                    "Value": "Confidential",
                },
                {
                    "Key": "Environment",
                    "Value": "Production",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == ""


def test_fail_bucket_without_tags_evidence(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == "Tags not found on this bucket."


def test_fail_mixed_bucket_population(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "passing-bucket",
                },
                {
                    "Name": "missing-tag-bucket",
                },
                {
                    "Name": "empty-value-bucket",
                },
            ]
        },
        "s3/buckets/passing-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "Production application data",
                },
                {
                    "Key": "Classification",
                    "Value": "Confidential",
                },
            ]
        },
        "s3/buckets/missing-tag-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "Production application data",
                },
            ]
        },
        "s3/buckets/empty-value-bucket/tags.json": {
            "TagSet": [
                {
                    "Key": "Owner",
                    "Value": "security@example.com",
                },
                {
                    "Key": "Description",
                    "Value": "",
                },
                {
                    "Key": "Classification",
                    "Value": "Confidential",
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 S3 bucket(s) are missing required tags or have empty values."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False

    assert result.samples[2].is_passing is False