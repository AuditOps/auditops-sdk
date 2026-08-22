from auditops.providers.aws.tests.s3 import check_s3_public_access
from utils.evidence import load_evidence


def test_fail_missing_bucket_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"s3/buckets.json"},
    )

    result = check_s3_public_access(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (s3/buckets.json)."
    )


def test_pass_bucket_with_public_access_block_enabled(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/public_access_block.json": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_public_access(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == ""


def test_fail_bucket_with_public_access_setting_disabled(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/public_access_block.json": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": True,
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_public_access(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1


    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == (
        "One or more public access settings are disabled."
    )


def test_fail_bucket_with_all_public_access_settings_disabled(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "example-bucket",
                }
            ]
        },
        "s3/buckets/example-bucket/public_access_block.json": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_public_access(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 S3 bucket(s) are not configured to block public access."
    )

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == (
        "One or more public access settings are disabled."
    )


def test_fail_bucket_without_public_access_block_configuration(tester):
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

    result = check_s3_public_access(tester)

    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.sample_id == {"bucket_name": "example-bucket"}
    assert sample.comments == (
        "No Public Access Block configuration found."
    )
    assert sample.is_passing is False


def test_fail_mixed_bucket_population(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "passing-bucket",
                },
                {
                    "Name": "failing-bucket",
                },
                {
                    "Name": "missing-config-bucket",
                },
            ]
        },
        "s3/buckets/passing-bucket/public_access_block.json": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }
        },
        "s3/buckets/failing-bucket/public_access_block.json": {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_public_access(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 S3 bucket(s) are not configured to block public access."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == (
        "One or more public access settings are disabled."
    )

    assert result.samples[2].is_passing is False
    assert result.samples[2].comments == (
        "No Public Access Block configuration found."
    )