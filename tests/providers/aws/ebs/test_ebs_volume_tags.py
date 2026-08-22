from auditops.providers.aws.tests.ebs import check_ebs_volume_tags
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"ec2/us-east-1/volumes.json"},
    )

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(ec2/us-east-1/volumes.json)."
    )


def test_pass_volume_with_required_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Tags": [
                        {
                            "Key": tag,
                            "Value": f"{tag}-value",
                        }
                        for tag in required_tags
                    ],
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_volume_missing_required_tag(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Tags": [
                        {
                            "Key": tag,
                            "Value": f"{tag}-value",
                        }
                        for tag in required_tags[:-1]
                    ],
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }


def test_fail_volume_with_empty_required_tag_value(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Tags": [
                        {
                            "Key": tag,
                            "Value": "" if tag == required_tags[0] else f"{tag}-value",
                        }
                        for tag in required_tags
                    ],
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }


def test_pass_volume_with_extra_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Tags": [
                        *[
                            {
                                "Key": tag,
                                "Value": f"{tag}-value",
                            }
                            for tag in required_tags
                        ],
                        {
                            "Key": "Environment",
                            "Value": "Production",
                        },
                    ],
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_mixed_volume_population(tester):
    required_tags = tester.config.required_tags

    passing_tags = [
        {
            "Key": tag,
            "Value": f"{tag}-value",
        }
        for tag in required_tags
    ]

    missing_tag_tags = [
        {
            "Key": tag,
            "Value": f"{tag}-value",
        }
        for tag in required_tags[:-1]
    ]

    empty_value_tags = [
        {
            "Key": tag,
            "Value": "" if tag == required_tags[0] else f"{tag}-value",
        }
        for tag in required_tags
    ]

    example_evidence = {
        "ec2/us-east-1/volumes.json": {
            "Volumes": [
                {
                    "VolumeId": "vol-0123456789abcdef0",
                    "Tags": passing_tags,
                },
                {
                    "VolumeId": "vol-0123456789abcdef1",
                    "Tags": missing_tag_tags,
                },
                {
                    "VolumeId": "vol-0123456789abcdef2",
                    "Tags": empty_value_tags,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_volume_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 EBS volume(s) are missing "
        "required tags or have empty values."
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

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "volume_id": "vol-0123456789abcdef2",
    }