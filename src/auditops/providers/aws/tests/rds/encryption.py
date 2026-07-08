from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_rds_encryption(tester):
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

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db_instance in instances.get("DBInstances", []):
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