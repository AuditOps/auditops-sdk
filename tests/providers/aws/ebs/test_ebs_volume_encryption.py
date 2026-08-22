from auditops.providers.aws.tests.ebs import check_ebs_volume_encryption
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"ec2/us-east-1/volumes.json"},
    )

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(ec2/us-east-1/volumes.json)."
    )


def test_pass_encrypted_volume(tester):
    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Encrypted": True,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_unencrypted_volume(tester):
    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Encrypted": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert sample.comments == "EBS volume is not encrypted."


def test_pass_multiple_encrypted_volumes(tester):
    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Encrypted": True,
                },
                {
                    "VolumeId": "vol-0123456789abcdef1",
                    "Encrypted": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is True
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef1",
    }
    assert result.samples[1].comments == ""


def test_fail_mixed_volume_population(tester):
    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Encrypted": True,
                },
                {
                    "VolumeId": "vol-0123456789abcdef1",
                    "Encrypted": False,
                },
                {
                    "VolumeId": "vol-0123456789abcdef2",
                    "Encrypted": True,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 3 EBS volume(s) are not encrypted."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef1",
    }
    assert result.samples[1].comments == "EBS volume is not encrypted."

    assert result.samples[2].is_passing is True
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef2",
    }
    assert result.samples[2].comments == ""


def test_pass_multiple_regions(tester):
    tester.config.in_scope_regions = [
        "us-east-1",
        "us-west-2",
    ]

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Encrypted": True,
                }
            ]
        },
        "ec2/us-west-2/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef1",
                    "Encrypted": True,
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 2

    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].sample_id == {
        "region": "us-west-2",
        "volume_id": "vol-0123456789abcdef1",
    }
    assert result.samples[1].is_passing is True
    assert result.samples[1].comments == ""