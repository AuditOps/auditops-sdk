from unittest.mock import Mock
from auditops.providers.aws import AWSConfig, AWSTester
from auditops.providers.aws.tests.s3 import check_s3_encryption
import pytest

#from conftest import load_evidence
from utils.evidence import load_evidence

def test_pass(tester):
    evidence = {
        "s3/buckets.json": {
            "Buckets": [
                {"Name": "bucket1"},
                {"Name": "bucket2"},
            ]
        },
        "s3/buckets/bucket1/encryption.json": {
            "ServerSideEncryptionConfiguration": {
                "Rules": []
            }
        },
        "s3/buckets/bucket2/encryption.json": {
            "ServerSideEncryptionConfiguration": {
                "Rules": []
            }
        },
    }

    load_evidence(tester, evidence)

    result = check_s3_encryption(tester)

    assert result.is_passing
    assert result.num_findings == 0
    assert result.total_population == 2


"""
def test_s3_encryption_fails_when_encryption_configuration_missing(tester, reader):
    evidence = {
        "aws/s3/buckets.json": {
            "Buckets": [
                {"Name": "missing-encryption-bucket"},
                {"Name": "bucket2"}
            ]
        },
        "aws/s3/buckets/missing-encryption-bucket/encryption.json": None,
        "aws/s3/buckets/bucket2/encryption.json": {
            "ServerSideEncryptionConfiguration": {
                "Rules": []
            }
        },
    }

    def read_json(provider, path, optional=False):
        return evidence.get(path)

    reader.read_json.side_effect = read_json

    result = check_s3_encryption(tester)

    assert result.is_passing is False
    assert result.num_findings == 1
    assert result.total_population == 2
    assert result.samples[0].comments == "No encryption configuration found."

"""