from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def check_ec2_instance_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-ec2-001",
        "test_description": (
            "EC2 instances must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained the list of EC2 instances by calling describe_instances() boto3 command.",
            "For each in-scope AWS region, saved the list of EC2 instances: ec2/[region_name]/instances.json",
            f"For each EC2 instance, reviewed the 'Tags' to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Instance ID", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"ec2/{region}/instances.json")

        for reservation in instances.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                sample = Sample(
                    sample_id={
                        "region": region,
                        "instance_id": instance["InstanceId"],
                    }
                )

                instance_tags = {
                    tag["Key"]: tag.get("Value", "")
                    for tag in instance.get("Tags", [])
                }

                evaluate_tags(sample, required_tags, instance_tags)

                test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        tester.provider,
        failure_message="EC2 instance(s) are missing required tags or have empty values."
    )

    return test