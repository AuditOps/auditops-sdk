from auditops.providers.aws.tests.s3 import check_s3_encryption
from utils.evidence import load_evidence


def test_fail_missing_bucket_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"s3/buckets.json"},
    )

    result = check_s3_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (s3/buckets.json)."
    )


def test_pass_bucket_with_encryption(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "encrypted-bucket",
                }
            ]
        },
        "s3/buckets/encrypted-bucket/encryption.json": {
            "ServerSideEncryptionConfiguration": {
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256",
                        }
                    }
                ]
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "encrypted-bucket"}
    assert sample.comments == ""


def test_fail_bucket_without_encryption_evidence(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "unencrypted-bucket",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_encryption(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "unencrypted-bucket"}
    assert sample.comments == "No encryption configuration found."


def test_fail_bucket_with_empty_encryption_configuration(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "unencrypted-bucket",
                }
            ]
        },
        "s3/buckets/unencrypted-bucket/encryption.json": {
            "ServerSideEncryptionConfiguration": {}
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_encryption(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 S3 bucket(s) do not have encryption enabled."
    )    

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "unencrypted-bucket"}
    assert sample.comments == "No encryption configuration found"


def test_fail_mixed_bucket_population(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "encrypted-bucket",
                },
                {
                    "Name": "unencrypted-bucket",
                },
                {
                    "Name": "missing-config-bucket",
                },
            ]
        },
        "s3/buckets/encrypted-bucket/encryption.json": {
            "ServerSideEncryptionConfiguration": {
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256",
                        }
                    }
                ]
            }
        },
        "s3/buckets/unencrypted-bucket/encryption.json": {
            "ServerSideEncryptionConfiguration": {}
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 S3 bucket(s) do not have encryption enabled."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == "No encryption configuration found"

    assert result.samples[2].is_passing is False
    assert result.samples[2].comments == "No encryption configuration found."