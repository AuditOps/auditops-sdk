from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def run_ec2_tests(tester):
    return [
        test_ec2_tags(tester),
        test_ec2_security_group_tags(tester)
    ]


def test_ec2_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-ec2-XXX",
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

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} EC2 instance(s) are missing required tags or have empty values."
        )

    return test


def test_ec2_security_group_tags(tester):
    required_tags = tester.config.ec2_security_group_required_tags

    metadata = {
        "test_id": "aws-ec2-XXX",
        "test_description": (
            "EC2 security groups have required tags applied and tag values are not empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained a list of EC2 security groups by calling describe_security_groups() boto3 command.",
            "For each in-scope region, saved the list of security groups: ec2/[region]/security_groups.json",
            f"Inspected each security group's 'Tags' attribute to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Security Group ID", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        security_groups = tester.read(f"ec2/{region}/security_groups.json")

        for sg in security_groups.get("SecurityGroups", []):
            sample = Sample(
                sample_id={
                    "region": region,
                    "security_group_id": sg["GroupId"],
                }
            )

            actual_sg_tags = {
                tag["Key"]: tag.get("Value", "")
                for tag in sg.get("Tags", [])
            }

            evaluate_tags(sample, required_tags, actual_sg_tags)

            test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} security group(s) are missing required tags or have empty values."
        )

    return test