from auditops.providers.aws.tests.rds import check_rds_backup_retention
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"rds/us-east-1/db_instances.json"},
    )

    result = check_rds_backup_retention(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(rds/us-east-1/db_instances.json)."
    )


def test_pass_instance_with_required_backup_retention(tester):
    required_retention_days = tester.config.rds_backup_retention_days

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "BackupRetentionPeriod": required_retention_days,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_backup_retention(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_instance_below_required_backup_retention(tester):
    required_retention_days = tester.config.rds_backup_retention_days

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "BackupRetentionPeriod": required_retention_days - 1,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_backup_retention(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        f"Exceptions Noted. 1 of 1 RDS instance(s) do not retain "
        f"backups for at least {required_retention_days} days."
    )        

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == (
        f"Retention is {required_retention_days - 1} days"
    )


def test_pass_instance_above_required_backup_retention(tester):
    required_retention_days = tester.config.rds_backup_retention_days

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "BackupRetentionPeriod": required_retention_days + 1,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_backup_retention(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_instance_with_zero_day_backup_retention(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "BackupRetentionPeriod": 0,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_backup_retention(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == "Retention is 0 days"


def test_fail_mixed_instance_population(tester):
    required_retention_days = tester.config.rds_backup_retention_days

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "passing-db",
                    "BackupRetentionPeriod": required_retention_days,
                },
                {
                    "DBInstanceIdentifier": "failing-db",
                    "BackupRetentionPeriod": required_retention_days - 1,
                },
                {
                    "DBInstanceIdentifier": "another-passing-db",
                    "BackupRetentionPeriod": required_retention_days + 5,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_backup_retention(tester)

    assert result.is_passing is False
    assert result.comments == (
        f"Exceptions Noted. 1 of 3 RDS instance(s) do not retain "
        f"backups for at least {required_retention_days} days."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "db_instance": "passing-db",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "db_instance": "failing-db",
    }
    assert result.samples[1].comments == (
        f"Retention is {required_retention_days - 1} days"
    )

    assert result.samples[2].is_passing is True
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "db_instance": "another-passing-db",
    }
    assert result.samples[2].comments == ""