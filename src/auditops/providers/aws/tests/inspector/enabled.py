
from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_inspector_enabled(tester):
    metadata = {
        "test_id": "aws-inspector-001",
        "test_description": "Amazon Inspector is enabled for all in-scope regions.",
        "risk_rating": 3,
        "test_procedures": [
            "Performed the following steps for each in-scope region:",
            "- Ran the [batch_get_account_status](https://docs.aws.amazon.com/boto3/latest/reference/services/inspector2/client/batch_get_account_status.html) "
            "boto3 command to obtain the AWS Inspector status.",
            "- Saved the API response: inspector/[REGION]/account_status.json.",
            "- Inspected the account status for EC2, ECR, and Lambda to determine whether each resource type is enabled."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Result", "Comments"]
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        sample = Sample(sample_id={"region": region})

        account_status = tester.read(
            f"inspector/{region}/account_status.json",
        )

        if not account_status:
            return test.fail(
                f"ERROR: Unable to retrieve required evidence "
                f"(inspector/{region}/account_status.json)."
            )

        accounts = account_status.get("accounts", [])

        if not accounts:
            return test.fail(
                f"ERROR: No Inspector account status found "
                f"for region {region}."
            )

        resource_states = accounts[0].get("resourceState", {})

        disabled_resources = []

        for resource_type in ["ec2", "ecr", "lambda"]:
            status = resource_states.get(resource_type, {})

            if status.get("status") != "ENABLED":
                disabled_resources.append(resource_type.upper())

        if disabled_resources:
            sample.is_passing = False
            sample.comments = (
                f"Inspector not enabled for: {', '.join(disabled_resources)}."
            )
        else:
            sample.is_passing = True

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message="region(s) do not have Amazon Inspector enabled."
    )

    return test