from auditops.providers.aws.tests.guardduty import check_guardduty_enabled
from utils.evidence import load_evidence


def test_fail_missing_region_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"guardduty/us-east-1/detectors.json"},
    )

    result = check_guardduty_enabled(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence "
        "(guardduty/us-east-1/detectors.json)."
    )


def test_pass_region_with_enabled_detector(tester):
    example_evidence = {
        "guardduty/us-east-1/detectors.json": {
            "DetectorIds": [
                "12abc3456789def0",
            ]
        },
        "guardduty/us-east-1/12abc3456789def0/detector.json": {
            "Status": "ENABLED",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_guardduty_enabled(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == ""


def test_fail_region_with_disabled_detector(tester):
    example_evidence = {
        "guardduty/us-east-1/detectors.json": {
            "DetectorIds": [
                "12abc3456789def0",
            ]
        },
        "guardduty/us-east-1/12abc3456789def0/detector.json": {
            "Status": "DISABLED",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_guardduty_enabled(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == "Detector(s) found but none are enabled."


def test_fail_region_with_no_detector_ids(tester):
    example_evidence = {
        "guardduty/us-east-1/detectors.json": {
            "DetectorIds": []
        }
    }

    load_evidence(tester, example_evidence)

    result = check_guardduty_enabled(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1
    assert result.comments == (
        "Exceptions Noted. 1 of 1 region(s) do not have GuardDuty enabled."
    )

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == "No GuardDuty detectors in region."


def test_pass_region_with_one_of_multiple_detectors_enabled(tester):
    example_evidence = {
        "guardduty/us-east-1/detectors.json": {
            "DetectorIds": [
                "12abc3456789def0",
                "23bcd4567890ef01",
            ]
        },
        "guardduty/us-east-1/12abc3456789def0/detector.json": {
            "Status": "DISABLED",
        },
        "guardduty/us-east-1/23bcd4567890ef01/detector.json": {
            "Status": "ENABLED",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_guardduty_enabled(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"region": "us-east-1"}
    assert sample.comments == ""


def test_fail_multiple_regions_with_mixed_results(tester):
    tester.config.in_scope_regions =['us-east-1', 'us-west-2']

    example_evidence = {
        "guardduty/us-east-1/detectors.json": {
            "DetectorIds": [
                "12abc3456789def0",
            ]
        },
        "guardduty/us-east-1/12abc3456789def0/detector.json": {
            "Status": "ENABLED",
        },
        "guardduty/us-west-2/detectors.json": {
            "DetectorIds": [
                "23bcd4567890ef01",
            ]
        },
        "guardduty/us-west-2/23bcd4567890ef01/detector.json": {
            "Status": "DISABLED",
        },
    }

    load_evidence(tester, example_evidence)

    result = check_guardduty_enabled(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 2 region(s) do not have GuardDuty enabled."
    )

    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].sample_id == {"region": "us-east-1"}
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].sample_id == {"region": "us-west-2"}
    assert result.samples[1].comments == (
        "Detector(s) found but none are enabled."
    )

    tester.config.in_scope_regions =['us-east-1']