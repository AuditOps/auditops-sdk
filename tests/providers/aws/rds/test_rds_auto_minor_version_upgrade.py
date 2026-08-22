from auditops.providers.aws.tests.rds import check_rds_auto_minor_version_upgrade
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"rds/us-east-1/db_instances.json"},
    )

    result = check_rds_auto_minor_version_upgrade(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (rds/us-east-1/db_instances.json)."
    )


def test_pass_instance_with_auto_minor_version_upgrade(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "AutoMinorVersionUpgrade": True,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_auto_minor_version_upgrade(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_instance_without_auto_minor_version_upgrade(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "AutoMinorVersionUpgrade": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_auto_minor_version_upgrade(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 1 RDS instance(s) do not have "
        "automatic minor version upgrades enabled."
    )    
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == (
        "Automatic minor version upgrades are not enabled."
    )


def test_pass_multiple_instances_with_auto_minor_version_upgrade(tester):
    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "AutoMinorVersionUpgrade": True,
                },
                {
                    "DBInstanceIdentifier": "reporting-db",
                    "AutoMinorVersionUpgrade": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_auto_minor_version_upgrade(tester)

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
                    "DBInstanceIdentifier": "passing-db",
                    "AutoMinorVersionUpgrade": True,
                },
                {
                    "DBInstanceIdentifier": "failing-db",
                    "AutoMinorVersionUpgrade": False,
                },
                {
                    "DBInstanceIdentifier": "another-passing-db",
                    "AutoMinorVersionUpgrade": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_auto_minor_version_upgrade(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 3 RDS instance(s) do not have "
        "automatic minor version upgrades enabled."
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
        "Automatic minor version upgrades are not enabled."
    )

    assert result.samples[2].is_passing is True
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "db_instance": "another-passing-db",
    }
    assert result.samples[2].comments == ""