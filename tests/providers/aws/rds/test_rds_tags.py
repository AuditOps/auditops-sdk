from auditops.providers.aws.tests.rds import check_rds_tags
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"rds/us-east-1/db_instances.json"},
    )

    result = check_rds_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(rds/us-east-1/db_instances.json)."
    )


def test_pass_instance_with_required_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "TagList": [
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

    result = check_rds_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }
    assert sample.comments == ""


def test_fail_instance_missing_required_tag(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "TagList": [
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

    result = check_rds_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 RDS instance(s) are missing "
        "required tags or have empty values."
    )    

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }


def test_fail_instance_with_empty_required_tag_value(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "TagList": [
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

    result = check_rds_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
    }


def test_pass_instance_with_extra_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "production-db",
                    "TagList": [
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

    result = check_rds_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "db_instance": "production-db",
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
            "Value": "" if tag == required_tags[0] else f"{tag}-value",
        }
        for tag in required_tags
    ]

    example_evidence = {
        "rds/us-east-1/db_instances.json": {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "passing-db",
                    "TagList": passing_tags,
                },
                {
                    "DBInstanceIdentifier": "missing-tag-db",
                    "TagList": missing_tag_tags,
                },
                {
                    "DBInstanceIdentifier": "empty-value-db",
                    "TagList": empty_value_tags,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_rds_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 RDS instance(s) are missing "
        "required tags or have empty values."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "db_instance": "passing-db",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "db_instance": "missing-tag-db",
    }

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "db_instance": "empty-value-db",
    }