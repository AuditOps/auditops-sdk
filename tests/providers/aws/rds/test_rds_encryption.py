from auditops.providers.aws.tests.rds import check_rds_encryption
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"rds/us-east-1/db_instances.json"},
    )

    result = check_rds_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(rds/us-east-1/db_instances.json)."
    )


def test_pass_encrypted_instance(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "StorageEncrypted": True,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_unencrypted_instance(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "StorageEncrypted": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_encryption(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 RDS instance(s) are not encrypted."
    )

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == "RDS instance is not encrypted."


def test_pass_multiple_encrypted_instances(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "StorageEncrypted": True,
                },
                {
                    "DBInstanceIdentifier": "reporting-db",
                    "StorageEncrypted": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is True
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "db_instance": "reporting-db",
    }
    assert result.samples[1].comments == ""


def test_fail_mixed_instance_population(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "encrypted-db",
                    "StorageEncrypted": True,
                },
                {
                    "DBInstanceIdentifier": "unencrypted-db",
                    "StorageEncrypted": False,
                },
                {
                    "DBInstanceIdentifier": "another-encrypted-db",
                    "StorageEncrypted": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 3 RDS instance(s) are not encrypted."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "db_instance": "encrypted-db",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "db_instance": "unencrypted-db",
    }
    assert result.samples[1].comments == "RDS instance is not encrypted."

    assert result.samples[2].is_passing is True
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "db_instance": "another-encrypted-db",
    }
    assert result.samples[2].comments == ""