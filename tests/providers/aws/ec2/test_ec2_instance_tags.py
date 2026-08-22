from auditops.providers.aws.tests.ec2 import check_ec2_instance_tags
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"ec2/us-east-1/instances.json"},
    )

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(ec2/us-east-1/instances.json)."
    )


def test_pass_instance_with_required_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
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
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_instance_missing_required_tag(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
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
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }


def test_fail_instance_with_empty_required_tag_value(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
                            "Tags": [
                                {
                                    "Key": tag,
                                    "Value": (
                                        ""
                                        if tag == required_tags[0]
                                        else f"{tag}-value"
                                    ),
                                }
                                for tag in required_tags
                            ],
                        }
                    ]
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }


def test_pass_instance_with_extra_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
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
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_mixed_instance_population(tester):
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
            "Value": (
                ""
                if tag == required_tags[0]
                else f"{tag}-value"
            ),
        }
        for tag in required_tags
    ]

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef0",
                            "Tags": passing_tags,
                        },
                        {
                            "InstanceId": "i-0123456789abcdef1",
                            "Tags": missing_tag_tags,
                        },
                    ]
                },
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0123456789abcdef2",
                            "Tags": empty_value_tags,
                        }
                    ]
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 EC2 instance(s) are missing "
        "required tags or have empty values."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef1",
    }

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef2",
    }


def test_pass_instances_across_multiple_reservations(tester):
    required_tags = tester.config.required_tags

    def make_instance(instance_id):
        return {
            "InstanceId": instance_id,
            "Tags": [
                {
                    "Key": tag,
                    "Value": f"{tag}-value",
                }
                for tag in required_tags
            ],
        }

    example_evidence = {
        "ec2/us-east-1/instances.json": {
            "Reservations": [
                {
                    "Instances": [
                        make_instance("i-0123456789abcdef0"),
                    ]
                },
                {
                    "Instances": [
                        make_instance("i-0123456789abcdef1"),
                        make_instance("i-0123456789abcdef2"),
                    ]
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_instance_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 3

    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef0",
    }
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef1",
    }
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "instance_id": "i-0123456789abcdef2",
    }

    assert all(sample.is_passing for sample in result.samples)
    assert all(sample.comments == "" for sample in result.samples)