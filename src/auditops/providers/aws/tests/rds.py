from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def run_rds_tests(tester):
    return [
        test_rds_encryption(tester),
        test_rds_public_access(tester),
        test_rds_backup_retention(tester),
        test_rds_auto_minor_version_upgrade(tester),
        test_rds_deletion_protection(tester),
        test_rds_tags(tester),
    ]


def _iter_db_instances(tester):
    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db_instance in instances.get("DBInstances", []):
            yield region, db_instance


def test_rds_encryption(tester):
    metadata = {
        "test_id": "aws-rds-001",
        "test_description": "RDS instances are encrypted at rest.",
        "risk_rating": 2,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances by calling the describe_db_instances() boto3 command.",
            "For each in-scope region, saved the list of RDS instances: rds/[region_name]/db_instances.json.",
            "For each RDS instance, inspected the `StorageEncrypted` setting to determine if it was set to `true`."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region, db_instance in _iter_db_instances(tester):
        sample = Sample(
            sample_id={
                "region": region,
                "db_instance": db_instance["DBInstanceIdentifier"],
            }
        )

        sample.is_passing = db_instance.get("StorageEncrypted", False)

        if not sample.is_passing:
            sample.comments = "RDS instance is not encrypted."

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) are not encrypted."
        )

    return test


def test_rds_public_access(tester):
    metadata = {
        "test_id": "aws-rds-002",
        "test_description": "RDS instances are configured to block public access.",
        "risk_rating": 3,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances by calling the describe_db_instances() boto3 command.",
            "For each in-scope region, saved the list of RDS instances: rds/[region_name]/db_instances.json.",
            "For each RDS instance, inspected the 'PubliclyAccessible' setting to determine if it was set to 'false'."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region, db_instance in _iter_db_instances(tester):
        sample = Sample(
            sample_id={
                "region": region,
                "db_instance": db_instance["DBInstanceIdentifier"],
            }
        )

        sample.is_passing = not db_instance.get("PubliclyAccessible", False)

        if not sample.is_passing:
            sample.comments = "Instance is publicly accessible."

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) are publicly accessible."
        )

    return test

def test_rds_backup_retention(tester):
    required_retention_days = tester.config.rds_backup_retention_days

    metadata = {
        "test_id": "aws-rds-003",
        "test_description": f"RDS backups are retained for at least {required_retention_days} days.",
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances by calling the describe_db_instances() boto3 command.",
            "For each in-scope region, saved the list of RDS instances: rds/[region_name]/db_instances.json.",
            f"For each RDS instance, inspected the `BackupRetentionPeriod` to determine if it is greater than or equal to {required_retention_days} days."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region, db_instance in _iter_db_instances(tester):
        sample = Sample(
            sample_id={
                "region": region,
                "db_instance": db_instance["DBInstanceIdentifier"],
            }
        )

        actual_retention = db_instance.get("BackupRetentionPeriod", 0)
        sample.is_passing = actual_retention >= required_retention_days

        if not sample.is_passing:
            sample.comments = f"Retention is {actual_retention} days"

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) do not retain backups for at least {required_retention_days} days."
        )

    return test


def test_rds_auto_minor_version_upgrade(tester):
    metadata = {
        "test_id": "aws-rds-004",
        "test_description": "RDS instances have automatic minor version upgrades enabled.",
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained a list of DB instances by calling the describe_db_instances() boto3 command.",
            "For each in-scope region, saved the list of RDS instances: rds/[region_name]/db_instances.json.",
            "For each RDS instance, inspected the 'AutoMinorVersionUpgrade' setting to determine if it was set to 'true'."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region, db_instance in _iter_db_instances(tester):
        sample = Sample(
            sample_id={
                "region": region,
                "db_instance": db_instance["DBInstanceIdentifier"],
            }
        )

        sample.is_passing = db_instance.get("AutoMinorVersionUpgrade", False)

        if not sample.is_passing:
            sample.comments = "Automatic minor version upgrades are not enabled."

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) do not have automatic minor version upgrades enabled."
        )

    return test


def test_rds_deletion_protection(tester):
    metadata = {
        "test_id": "aws-rds-005",
        "test_description": "RDS instances have deletion protection enabled at the cluster or instance level.",
        "risk_rating": 2,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances and RDS clusters using describe_db_instances() and describe_db_clusters() boto3 commands.",
            "Saved the list of RDS instances: rds/[region_name]/db_instances.json and DB clusters: rds/[region_name]/db_clusters.json.",
            "Inspected each RDS instance to determine if 'DeletionProtection' was set to 'true' at the instance or cluster level."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    cluster_maps = {}

    for region in tester.config.in_scope_regions:
        clusters = tester.read(f"rds/{region}/db_clusters.json")

        cluster_maps[region] = {
            cluster["DBClusterIdentifier"]: cluster.get("DeletionProtection", False)
            for cluster in clusters.get("DBClusters", [])
        }

    for region, db_instance in _iter_db_instances(tester):
        sample = Sample(
            sample_id={
                "region": region,
                "db_instance": db_instance["DBInstanceIdentifier"],
            }
        )

        instance_protection = db_instance.get("DeletionProtection", False)
        cluster_id = db_instance.get("DBClusterIdentifier")
        cluster_protection = cluster_maps[region].get(cluster_id, False) if cluster_id else False

        sample.is_passing = instance_protection or cluster_protection

        if not sample.is_passing:
            if cluster_id:
                sample.comments = (
                    "Deletion protection is not enabled at either the instance or cluster level."
                )
            else:
                sample.comments = (
                    "Deletion protection is not enabled at the instance level."
                )

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) do not have deletion protection enabled."
        )

    return test


def test_rds_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-rds-XXX",
        "test_description": (
            "RDS instances must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances by calling describe_db_instances() boto3 command.",
            "For each in-scope region, saved the list of RDS instances: rds/[region_name]/db_instances.json.",
            f"For each RDS instance, reviewed the `TagList` to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db in instances.get("DBInstances", []):
            sample = Sample(
                sample_id={
                    "region": region,
                    "db_instance": db["DBInstanceIdentifier"],
                }
            )

            actual_db_tags = {
                tag["Key"]: tag.get("Value", "")
                for tag in db.get("TagList", [])
            }

            evaluate_tags(sample, required_tags, actual_db_tags)

            test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} RDS instance(s) are missing required tags or have empty values."
        )

    return test