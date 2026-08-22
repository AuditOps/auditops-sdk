from auditops.providers.aws.tests.lmbda import check_lambda_tags
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"lambda/us-east-1/functions.json"},
    )

    result = check_lambda_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(lambda/us-east-1/functions.json)."
    )


def test_pass_function_with_required_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "lambda/us-east-1/functions.json": {
            "Functions": [
                {
                    "FunctionName": "my-function",
                }
            ]
        },
        "lambda/us-east-1/functions/my-function/tags.json": {
            "Tags": {
                tag: f"{tag}-value"
                for tag in required_tags
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_lambda_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "function_name": "my-function",
    }
    assert sample.comments == ""


def test_fail_function_missing_required_tag(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "lambda/us-east-1/functions.json": {
            "Functions": [
                {
                    "FunctionName": "my-function",
                }
            ]
        },
        "lambda/us-east-1/functions/my-function/tags.json": {
            "Tags": {
                tag: f"{tag}-value"
                for tag in required_tags[:-1]
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_lambda_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "function_name": "my-function",
    }


def test_fail_function_with_empty_required_tag_value(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "lambda/us-east-1/functions.json": {
            "Functions": [
                {
                    "FunctionName": "my-function",
                }
            ]
        },
        "lambda/us-east-1/functions/my-function/tags.json": {
            "Tags": {
                tag: (
                    ""
                    if tag == required_tags[0]
                    else f"{tag}-value"
                )
                for tag in required_tags
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_lambda_tags(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {
        "region": "us-east-1",
        "function_name": "my-function",
    }


def test_pass_function_with_extra_tags(tester):
    required_tags = tester.config.required_tags

    example_evidence = {
        "lambda/us-east-1/functions.json": {
            "Functions": [
                {
                    "FunctionName": "my-function",
                }
            ]
        },
        "lambda/us-east-1/functions/my-function/tags.json": {
            "Tags": {
                **{
                    tag: f"{tag}-value"
                    for tag in required_tags
                },
                "Environment": "Production",
            }
        },
    }

    load_evidence(tester, example_evidence)

    result = check_lambda_tags(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {
        "region": "us-east-1",
        "function_name": "my-function",
    }
    assert sample.comments == ""


def test_fail_mixed_function_population(tester):
    required_tags = tester.config.required_tags

    passing_tags = {
        tag: f"{tag}-value"
        for tag in required_tags
    }

    missing_tag_tags = {
        tag: f"{tag}-value"
        for tag in required_tags[:-1]
    }

    empty_value_tags = {
        tag: (
            ""
            if tag == required_tags[0]
            else f"{tag}-value"
        )
        for tag in required_tags
    }

    example_evidence = {
        "lambda/us-east-1/functions.json": {
            "Functions": [
                {
                    "FunctionName": "passing-function",
                },
                {
                    "FunctionName": "missing-tag-function",
                },
                {
                    "FunctionName": "empty-value-function",
                },
            ]
        },
        "lambda/us-east-1/functions/passing-function/tags.json": {
            "Tags": passing_tags,
        },
        "lambda/us-east-1/functions/missing-tag-function/tags.json": {
            "Tags": missing_tag_tags,
        },
        "lambda/us-east-1/functions/empty-value-function/tags.json": {
            "Tags": empty_value_tags,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_lambda_tags(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 2 of 3 Lambda function(s) are missing "
        "required tags or have empty values."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {
        "region": "us-east-1",
        "function_name": "passing-function",
    }
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {
        "region": "us-east-1",
        "function_name": "missing-tag-function",
    }

    assert result.samples[2].is_passing is False
    assert result.samples[2].sample_id == {
        "region": "us-east-1",
        "function_name": "empty-value-function",
    }