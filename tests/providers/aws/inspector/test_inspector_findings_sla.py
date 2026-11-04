from auditops.providers.aws.tests.inspector import check_inspector_findings
from utils.evidence import load_evidence


def test_inspector_critical_findings_passing(tester):
    """Test that no overdue critical Inspector findings exist."""

    region = "us-east-1"
    tester.config.in_scope_regions = [region]

    load_evidence(tester, {
        f"inspector/{region}/critical_overdue.json": {
            "findings": [],
        },
    })

    result = check_inspector_findings(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1
    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {"region": region}


def test_inspector_critical_findings_failing(tester):
    """Test that overdue critical Inspector findings cause a failure."""

    region = "us-east-1"
    tester.config.in_scope_regions = [region]

    load_evidence(tester, {
        f"inspector/{region}/critical_overdue.json": {
            "findings": [
                {"finding_id": "finding-001"},
                {"finding_id": "finding-002"},
            ],
        },
    })

    result = check_inspector_findings(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.samples[0].is_passing is False
    assert result.samples[0].sample_id == {"region": region}
    assert result.samples[0].comments == "Overdue findings: 2 critical."


def test_inspector_critical_findings_multiple_regions(tester):
    """Test critical findings across multiple in-scope regions."""

    regions = ["us-east-1", "us-west-2"]
    tester.config.in_scope_regions = regions

    load_evidence(tester, {
        f"inspector/{regions[0]}/critical_overdue.json": {
            "findings": [],
        },
        f"inspector/{regions[1]}/critical_overdue.json": {
            "findings": [
                {"finding_id": "finding-001"},
            ],
        },
    })

    result = check_inspector_findings(tester)

    assert result.is_passing is False
    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {"region": regions[0]}

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {"region": regions[1]}
    assert result.samples[1].comments == "Overdue findings: 1 critical."


def test_inspector_critical_findings_missing_evidence(tester):
    """Test that missing critical findings evidence fails the test."""

    region = "us-east-1"
    tester.config.in_scope_regions = [region]

    critical_path = f"inspector/{region}/critical_overdue.json"

    load_evidence(
        tester,
        {},
        missing_required={critical_path},
    )

    result = check_inspector_findings(tester)

    assert result.is_passing is False
    assert result.comments == (
        f"ERROR: Unable to retrieve required evidence ({critical_path})."
    )