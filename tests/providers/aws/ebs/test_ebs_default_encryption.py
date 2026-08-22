from auditops.providers.aws.tests.ebs import check_ebs_default_encryption
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"ec2/us-east-1/ebs_encryption_by_default.json"},
    )

    result = check_ebs_default_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(ec2/us-east-1/ebs_encryption_by_default.json)."
    )


def test_pass_region_with_default_encryption_enabled(tester):
    example_evidence = {
        "ec2/us-east-1/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": True,
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_default_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
    }
    assert sample.comments == ""


def test_fail_region_without_default_encryption(tester):
    example_evidence = {
        "ec2/us-east-1/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": False,
        }
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_default_encryption(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
    }
    assert sample.comments == (
        "EBS default encryption is not enabled in this region."
    )


def test_pass_multiple_regions_with_default_encryption(tester):
    tester.config.in_scope_regions = [
        "us-east-1",
        "us-west-2",
    ]

    example_evidence = {
        "ec2/us-east-1/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": True,
        },
        "ec2/us-west-2/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": True,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_default_encryption(tester)

    assert result.is_passing is True
    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is True
    assert result.samples[1].sample_id == {
        "region": "us-west-2",
    }
    assert result.samples[1].comments == ""


def test_fail_mixed_region_population(tester):
    tester.config.in_scope_regions = [
        "us-east-1",
        "us-west-2",
    ]

    example_evidence = {
        "ec2/us-east-1/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": True,
        },
        "ec2/us-west-2/ebs_encryption_by_default.json": {
            "EbsEncryptionByDefault": False,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_ebs_default_encryption(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 2 region(s) do not have "
        "EBS default encryption enabled."
    )

    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-west-2",
    }
    assert result.samples[1].comments == (
        "EBS default encryption is not enabled in this region."
    )