
from auditops.providers.aws.tests.inspector import check_inspector_enabled
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"inspector/us-east-1/account_status.json"},
    )

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (inspector/us-east-1/account_status.json)."
    )


def test_pass_region_with_all_resource_types_enabled(tester):
    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": [
                {
                    "resourceState": {
                        "ec2": {"status": "ENABLED"},
                        "ecr": {"status": "ENABLED"},
                        "lambda": {"status": "ENABLED"},
                    }
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == ""


def test_fail_region_with_disabled_resource_type(tester):
    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": [
                {
                    "resourceState": {
                        "ec2": {"status": "ENABLED"},
                        "ecr": {"status": "DISABLED"},
                        "lambda": {"status": "ENABLED"},
                    }
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == "Inspector not enabled for: ECR."


def test_fail_region_with_all_resource_types_disabled(tester):
    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": [
                {
                    "resourceState": {
                        "ec2": {"status": "DISABLED"},
                        "ecr": {"status": "DISABLED"},
                        "lambda": {"status": "DISABLED"},
                    }
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == (
        "Inspector not enabled for: EC2, ECR, LAMBDA."
    )


def test_fail_region_with_missing_resource_state(tester):
    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": [
                {}
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == (
        "Inspector not enabled for: EC2, ECR, LAMBDA."
    )


def test_fail_region_with_no_account_status(tester):
    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": []
        }
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: No Inspector account status found "
        "for region us-east-1."
    )


def test_fail_multiple_regions_with_mixed_results(tester):
    tester.config.in_scope_regions = ["us-east-1", "us-west-2"]

    example_evidence = {
        "inspector/us-east-1/account_status.json": {
            "accounts": [
                {
                    "resourceState": {
                        "ec2": {"status": "ENABLED"},
                        "ecr": {"status": "ENABLED"},
                        "lambda": {"status": "ENABLED"},
                    }
                }
            ]
        },
        "inspector/us-west-2/account_status.json": {
            "accounts": [
                {
                    "resourceState": {
                        "ec2": {"status": "ENABLED"},
                        "ecr": {"status": "DISABLED"},
                        "lambda": {"status": "ENABLED"},
                    }
                }
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_inspector_enabled(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 2 region(s) do not have "
        "Amazon Inspector enabled."
    )

    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {"region": "us-east-1"}
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {"region": "us-west-2"}
    assert result.samples[1].comments == (
        "Inspector not enabled for: ECR."
    )

    tester.config.in_scope_regions = ["us-east-1"]
