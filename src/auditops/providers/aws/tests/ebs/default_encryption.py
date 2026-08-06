from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_ebs_default_encryption(tester):
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

    test.evaluate_samples(
        tester.exclusions,
        failure_message="region(s) do not have EBS default encryption enabled."
    )

    return test