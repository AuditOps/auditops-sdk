from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_rds_backup_retention(tester):
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

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db_instance in instances.get("DBInstances", []):
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

    test.evaluate_samples(
        tester.exclusions,
        tester.provider,
        failure_message=f"RDS instance(s) do not retain backups for at least {required_retention_days} days."
    )

    return test