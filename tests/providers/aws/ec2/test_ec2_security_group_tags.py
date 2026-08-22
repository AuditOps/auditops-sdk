from auditops.providers.aws.tests.ec2 import check_ec2_security_group_tags
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"ec2/us-east-1/security_groups.json"},
    )

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(ec2/us-east-1/security_groups.json)."
    )


def test_pass_security_group_with_required_tags(tester):
    required_tags = tester.config.ec2_security_group_required_tags

    example_evidence = {
        "ec2/us-east-1/security_groups.json": {
            "SecurityGroups": [
                {
                    "GroupId": "sg-0123456789abcdef0",
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

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_security_group_missing_required_tag(tester):
    required_tags = tester.config.ec2_security_group_required_tags

    example_evidence = {
        "ec2/us-east-1/security_groups.json": {
            "SecurityGroups": [
                {
                    "GroupId": "sg-0123456789abcdef0",
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

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef0",
    }


def test_fail_security_group_with_empty_required_tag_value(tester):
    required_tags = tester.config.ec2_security_group_required_tags

    example_evidence = {
        "ec2/us-east-1/security_groups.json": {
            "SecurityGroups": [
                {
                    "GroupId": "sg-0123456789abcdef0",
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
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef0",
    }


def test_pass_security_group_with_extra_tags(tester):
    required_tags = tester.config.ec2_security_group_required_tags

    example_evidence = {
        "ec2/us-east-1/security_groups.json": {
            "SecurityGroups": [
                {
                    "GroupId": "sg-0123456789abcdef0",
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

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef0",
    }
    assert sample.comments == ""


def test_fail_mixed_security_group_population(tester):
    required_tags = tester.config.ec2_security_group_required_tags

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
        "ec2/us-east-1/security_groups.json": {
            "SecurityGroups": [
                {
                    "GroupId": "sg-0123456789abcdef0",
                    "Tags": passing_tags,
                },
                {
                    "GroupId": "sg-0123456789abcdef1",
                    "Tags": missing_tag_tags,
                },
                {
                    "GroupId": "sg-0123456789abcdef2",
                    "Tags": empty_value_tags,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ec2_security_group_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 security group(s) are missing "
        "required tags or have empty values."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef0",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef1",
    }

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "security_group_id": "sg-0123456789abcdef2",
    }