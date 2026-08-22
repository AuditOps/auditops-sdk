from auditops.providers.aws.tests.rds import check_rds_deletion_protection
from utils.evidence import load_evidence


def test_fail_missing_cluster_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"rds/us-east-1/db_clusters.json"},
    )

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(rds/us-east-1/db_clusters.json)."
    )


def test_fail_missing_instance_evidence(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": []
        }
    }

    load_evidence(
        tester,
        example_evidence,
        missing_required={"rds/us-east-1/db_instances.json"},
    )

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(rds/us-east-1/db_instances.json)."
    )


def test_pass_instance_with_instance_level_deletion_protection(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": []
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "DeletionProtection": True,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_pass_cluster_with_cluster_level_deletion_protection(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": [
                {
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": True,
                }
            ]
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": False,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_pass_instance_with_both_instance_and_cluster_protection(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": [
                {
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": True,
                }
            ]
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": True,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_cluster_instance_without_deletion_protection(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": [
                {
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": False,
                }
            ]
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "DBClusterIdentifier": "production-cluster",
                    "DeletionProtection": False,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 RDS instance(s) do not have "
        "deletion protection enabled."
    )    

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == (
        "Deletion protection is not enabled at either the instance or cluster level."
    )


def test_fail_non_clustered_instance_without_deletion_protection(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": []
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "standalone-db",
                    "DeletionProtection": False,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "standalone-db",
    }
    assert sample.comments == (
        "Deletion protection is not enabled at the instance level."
    )


def test_fail_mixed_instance_population(tester):
    example_evidence = {
        "rds/us-east-1/db_clusters.json": {
            "DBClusters": [
                {
                    "DBClusterIdentifier": "protected-cluster",
                    "DeletionProtection": True,
                },
                {
                    "DBClusterIdentifier": "unprotected-cluster",
                    "DeletionProtection": False,
                },
            ]
        },
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "instance-protected",
                    "DBClusterIdentifier": "unprotected-cluster",
                    "DeletionProtection": True,
                },
                {
                    "DBInstanceIdentifier": "cluster-protected",
                    "DBClusterIdentifier": "protected-cluster",
                    "DeletionProtection": False,
                },
                {
                    "DBInstanceIdentifier": "unprotected-db",
                    "DBClusterIdentifier": "unprotected-cluster",
                    "DeletionProtection": False,
                },
                {
                    "DBInstanceIdentifier": "standalone-unprotected",
                    "DeletionProtection": False,
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_rds_deletion_protection(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 4 RDS instance(s) do not have "
        "deletion protection enabled."
    )

    assert len(result.samples) == 4

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "db_instance": "instance-protected",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is True
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "db_instance": "cluster-protected",
    }
    assert result.samples[1].comments == ""

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "db_instance": "unprotected-db",
    }
    assert result.samples[2].comments == (
        "Deletion protection is not enabled at either the instance or cluster level."
    )

    assert result.samples[3].is_passing is False
    assert result.samples[3].sample_id == {
        "region": "us-east-1",
        "db_instance": "standalone-unprotected",
    }
    assert result.samples[3].comments == (
        "Deletion protection is not enabled at the instance level."
    )