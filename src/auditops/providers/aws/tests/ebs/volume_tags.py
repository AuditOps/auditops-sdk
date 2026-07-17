from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def check_ebs_volume_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-ebs-003",
        "test_description": (
            "EBS volumes must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained the list of EBS volumes by calling describe_volumes() boto3 command.",
            "Saved the list of volumes in the audit evidence folder (ec2/[region_name]/volumes.json).",
            "For each volume, obtained its tags from the 'Tags' attribute.",
            f"Inspected each EBS volume to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Volume ID", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        volumes = tester.read(f"ec2/{region}/volumes.json")

        for volume in volumes.get("Volumes", []):
            sample = Sample(
                sample_id={
                    "region": region,
                    "volume_id": volume["VolumeId"],
                }
            )

            volume_tags = {
                tag["Key"]: tag.get("Value", "")
                for tag in volume.get("Tags", [])
            }

            evaluate_tags(sample, required_tags, volume_tags)

            test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        tester.provider,
        failure_message="EBS volume(s) are missing required tags or have empty values."
    )

    return test
