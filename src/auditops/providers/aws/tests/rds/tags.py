from auditops.core.models import Sample
from auditops.core.utils import create_test, evaluate_tags


def check_rds_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-rds-006",
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

    test.evaluate_samples(
        tester.exclusions,
        failure_message="RDS instance(s) are missing required tags or have empty values."
    )

    return test