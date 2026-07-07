from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def run_lambda_tests(tester):
    return [
        test_lambda_tags(tester)
    ]

def test_lambda_tags(tester):
    required_tags = tester.config.required_tags

    metadata = {
        "test_id": "aws-lambda-XXX",
        "test_description": (
            "Lambda functions must have required tags applied and tag values must not be empty."
        ),
        "risk_rating": 1,
        "test_procedures": [
            "For each in-scope region, obtained the list of Lambda functions by calling list_functions() boto3 command.",
            "Saved the list of functions in the audit evidence folder (lambda/[region_name]/functions.json).",
            "For each function, obtained its tags using list_tags() boto3 command.",
            "Saved the tags for each function in the audit evidence folder (lambda/[region_name]/functions/[function_name]/tags.json).",
            f"Inspected each Lambda function to determine if the following tag keys exist and have non-empty values: {required_tags}"
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Function Name", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        functions = tester.read(f"lambda/{region}/functions.json")

        for fn in functions.get("Functions", []):
            function_name = fn["FunctionName"]

            sample = Sample(
                sample_id={
                    "region": region,
                    "function_name": function_name,
                }
            )

            tags_response = tester.read(
                f"lambda/{region}/functions/{function_name}/tags.json"
            )

            lambda_tags = tags_response.get("Tags", {})

            evaluate_tags(sample, required_tags, lambda_tags)

            test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    if not test.is_passing:
        test.comments = (
            f"Exceptions Noted. {test.num_findings} Lambda function(s) are missing required tags or have empty values."
        )

    return test