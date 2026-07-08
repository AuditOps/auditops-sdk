from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_ebs_volume_encryption(tester):
    metadata = {
        "test_id": "aws-ebs-002",
        "test_description": "EBS volumes are encrypted at rest.",
        "risk_rating": 2,
        "test_procedures": [
            "For each in-scope region, obtained a list of EBS volumes by calling describe_volumes() boto3 command.",
            "For each in-scope region, saved the list of EBS volumes: ec2/[region_name]/volumes.json.",
            "For each EBS volume, inspected the 'Encrypted' attribute to determine it is set to 'true'."
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

            sample.is_passing = volume.get("Encrypted", False)

            if not sample.is_passing:
                sample.comments = "EBS volume is not encrypted."

            test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} EBS volume(s) are not encrypted."
        )

    return test
