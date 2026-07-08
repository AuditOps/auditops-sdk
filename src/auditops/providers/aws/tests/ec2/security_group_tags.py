from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def check_ec2_security_group_tags(tester):
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