from auditops.providers.aws.tests.s3 import check_s3_secure_transport
from utils.evidence import load_evidence


def test_fail_missing_bucket_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"s3/buckets.json"},
    )

    result = check_s3_secure_transport(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (s3/buckets.json)."
    )


def test_pass_bucket_with_secure_transport_policy(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "secure-bucket",
                }
            ]
        },
        "s3/buckets/secure-bucket/policy.json": {
            "Policy": (
                '{"Version":"2012-10-17",'
                '"Statement":[{'
                '"Effect":"Deny",'
                '"Principal":"*",'
                '"Action":"s3:*",'
                '"Resource":"*",'
                '"Condition":{"Bool":{"aws:SecureTransport":"false"}}'
                '}]}'
            )
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "secure-bucket"}
    assert sample.comments == ""


def test_fail_bucket_without_secure_transport_policy(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "insecure-bucket",
                }
            ]
        },
        "s3/buckets/insecure-bucket/policy.json": {
            "Policy": (
                '{"Version":"2012-10-17",'
                '"Statement":[{'
                '"Effect":"Allow",'
                '"Principal":"*",'
                '"Action":"s3:GetObject",'
                '"Resource":"*"'
                '}]}'
            )
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "insecure-bucket"}
    assert sample.comments == (
        "No bucket policy statement enforcing SecureTransport."
    )


def test_fail_bucket_without_policy(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "no-policy-bucket",
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"bucket_name": "no-policy-bucket"}
    assert sample.comments == "No bucket policy found."


def test_fail_unparseable_bucket_policy(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "invalid-policy-bucket",
                }
            ]
        },
        "s3/buckets/invalid-policy-bucket/policy.json": {
            "Policy": "not valid JSON"
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 S3 bucket(s) do not enforce secure transport (HTTPS)."
    )    

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "bucket_name": "invalid-policy-bucket"
    }
    assert sample.comments == "Unable to parse bucket policy."


def test_pass_bucket_with_single_secure_transport_statement(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "secure-bucket",
                }
            ]
        },
        "s3/buckets/secure-bucket/policy.json": {
            "Policy": (
                '{"Version":"2012-10-17",'
                '"Statement":{'
                '"Effect":"Deny",'
                '"Principal":"*",'
                '"Action":"s3:*",'
                '"Resource":"*",'
                '"Condition":{"Bool":{"aws:SecureTransport":"false"}}'
                '}'
                '}'
            )
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"bucket_name": "secure-bucket"}
    assert sample.comments == ""


def test_fail_mixed_bucket_population(tester):
    example_evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {
                    "Name": "secure-bucket",
                },
                {
                    "Name": "insecure-bucket",
                },
                {
                    "Name": "no-policy-bucket",
                },
            ]
        },
        "s3/buckets/secure-bucket/policy.json": {
            "Policy": (
                '{"Version":"2012-10-17",'
                '"Statement":[{'
                '"Effect":"Deny",'
                '"Principal":"*",'
                '"Action":"s3:*",'
                '"Resource":"*",'
                '"Condition":{"Bool":{"aws:SecureTransport":"false"}}'
                '}]}'
            )
        },
        "s3/buckets/insecure-bucket/policy.json": {
            "Policy": (
                '{"Version":"2012-10-17",'
                '"Statement":[{'
                '"Effect":"Allow",'
                '"Principal":"*",'
                '"Action":"s3:GetObject",'
                '"Resource":"*"'
                '}]}'
            )
        },
    }

    load_evidence(tester, example_evidence)

    result = check_s3_secure_transport(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 S3 bucket(s) do not enforce secure transport (HTTPS)."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == (
        "No bucket policy statement enforcing SecureTransport."
    )

    assert result.samples[2].is_passing is False
    assert result.samples[2].comments == "No bucket policy found."