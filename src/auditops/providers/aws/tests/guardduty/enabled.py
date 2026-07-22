from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_guardduty_enabled(tester):
    metadata = {
        "test_id": "aws-guardduty-001",
        "test_description": "GuardDuty is enabled for all in-scope regions.",
        "risk_rating": 3,
        "test_procedures": [
            "For each in-scope region, obtained a list of GuardDuty detectors by calling the list_detectors() boto3 command.",
            "For each in-scope region, saved the list of detector IDs: guardduty/[region]/detectors.json.",
            "For each detector ID, obtained detector configuration by calling the get_detector() boto3 command.",
            "For each detector ID, saved the detector configuration: guardduty/[region]/[detector_id]/config.json.",
            "For each detector ID, inspected the detector configuration to determine whether 'Status' is set to 'ENABLED'."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    for region in tester.config.in_scope_regions:
        sample = Sample(sample_id={"region": region})

        detectors = tester.read(
            f"guardduty/{region}/detectors.json",
        )

        if not detectors:
            sample.is_passing = False
            sample.comments = "No GuardDuty detectors in region."
            test.samples.append(sample)
            continue

        enabled_detector_found = False

        for detector_id in detectors.get("DetectorIds"):
            config = tester.read(
                f"guardduty/{region}/{detector_id}/detector.json",
            )

            if config.get("Status") == "ENABLED":
                enabled_detector_found = True
                break

        if enabled_detector_found:
            sample.is_passing = True
        else:
            sample.is_passing = False
            sample.comments = "Detector(s) found but none are enabled."

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message="region(s) do not have GuardDuty enabled."
    )

    return test