from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test, evaluate_tags


def run_ebs_tests(tester):
    return [
        test_ebs_default_encryption(tester),
        test_ebs_volume_encryption(tester),
        test_ebs_tags(tester),
    ]


def test_ebs_default_encryption(tester):
    metadata = {
        "test_id": "aws-ebs-001",
        "test_description": "EBS volumes must have default encryption enabled in each region.",
        "risk_rating": 2,
        "test_procedures": [
            "For each in-scope region, obtained the EBS default encryption settings by calling get_ebs_encryption_by_default() boto3 command.",
            "For each in-scope region, saved the EBS default encryption settings: ec2/[region_name]/default_ebs_encryption.json.",
            "Inspected the configuration for each region to determine if 'EbsEncryptionByDefault' is set to True."

        ],
        "test_attributes": [],
        "table_headers": ["Region", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        default_encryption = tester.read(f"ec2/{region}/ebs_encryption_by_default.json")

        sample = Sample(sample_id={"region": region})

        sample.is_passing = default_encryption.get("EbsEncryptionByDefault")

        if not sample.is_passing:
            sample.comments = "EBS default encryption is not enabled in this region."

        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} region(s) do not have EBS default encryption enabled."
        )

    return test


def test_ebs_volume_encryption(tester):
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


def test_ebs_tags(tester):
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

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} EBS volume(s) are missing required tags or have empty values."
        )

    return test
