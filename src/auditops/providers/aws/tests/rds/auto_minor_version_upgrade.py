from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_rds_auto_minor_version_upgrade(tester):
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

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db_instance in instances.get("DBInstances", []):
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

    test.evaluate_samples(
        tester.exclusions,
        failure_message = "RDS instance(s) do not have automatic minor version upgrades enabled."
    )

    return test