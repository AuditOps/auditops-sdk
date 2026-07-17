from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_rds_public_access(tester):
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

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        for db_instance in instances.get("DBInstances", []):

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

        test.evaluate_samples(
            tester.exclusions,
            tester.provider,
            failure_message="RDS instance(s) are publicly accessible."    
        )

    return test
