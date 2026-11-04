from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_inspector_findings(tester):
    metadata = {
        "test_id": "aws-inspector-002",
        "test_description": (
            "Amazon Inspector critical findings are remediated within the required SLAs."
        ),
        "risk_rating": 3,
        "test_procedures": [
            "Obtained overdue critical Amazon Inspector findings for each in-scope region.",
            "Reviewed critical findings to determine whether remediation SLAs were exceeded.",
        ],
        "test_attributes": [],
        "table_headers": [
            "Region",
            "Critical Overdue",
            "Comments",
        ],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        sample = Sample(sample_id={"region": region})

        critical_path = f"inspector/{region}/critical_overdue.json"

        critical_findings = tester.read(critical_path)

        if not critical_findings:
            return test.fail(
                f"ERROR: Unable to retrieve required evidence "
                f"({critical_path})."
            )

        critical_count = len(critical_findings.get("findings", []))

        sample.is_passing = critical_count == 0

        if not sample.is_passing:
            sample.comments = (
                f"Overdue findings: {critical_count} critical."
            )

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "region(s) have Inspector findings exceeding remediation SLAs."
        ),
    )

    return test