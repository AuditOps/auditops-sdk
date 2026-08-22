from auditops.providers.aws.tests.cloudtrail import check_cloudtrail_multi_region
from utils.evidence import load_evidence


def test_fail_missing_trail_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"cloudtrail/trails.json"},
    )

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (cloudtrail/trails.json)."
    )


def test_fail_no_cloudtrail_trails(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": []
        }
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. No multi-region CloudTrail trail with active logging was found."
    )


def test_pass_multi_region_trail_with_logging(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": [
                {
                    "Name": "organization-trail",
                    "IsMultiRegionTrail": True,
                }
            ]
        },
        "cloudtrail/trails/organization-trail/trail_status.json": {
            "IsLogging": True,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is True
    assert result.comments == ""
    assert result.samples == []


def test_fail_multi_region_trail_without_logging(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": [
                {
                    "Name": "organization-trail",
                    "IsMultiRegionTrail": True,
                }
            ]
        },
        "cloudtrail/trails/organization-trail/trail_status.json": {
            "IsLogging": False,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. No multi-region CloudTrail trail "
        "with active logging was found."
    )
    assert result.samples == []


def test_fail_only_single_region_trails(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": [
                {
                    "Name": "regional-trail-1",
                    "IsMultiRegionTrail": False,
                },
                {
                    "Name": "regional-trail-2",
                    "IsMultiRegionTrail": False,
                },
            ]
        },
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. No multi-region CloudTrail trail "
        "with active logging was found."
    )
    assert result.samples == []


def test_pass_when_one_of_multiple_trails_is_valid(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": [
                {
                    "Name": "regional-trail",
                    "IsMultiRegionTrail": False,
                },
                {
                    "Name": "inactive-multi-region-trail",
                    "IsMultiRegionTrail": True,
                },
                {
                    "Name": "active-multi-region-trail",
                    "IsMultiRegionTrail": True,
                },
            ]
        },
        "cloudtrail/trails/inactive-multi-region-trail/trail_status.json": {
            "IsLogging": False,
        },
        "cloudtrail/trails/active-multi-region-trail/trail_status.json": {
            "IsLogging": True,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is True
    assert result.comments == ""
    assert result.samples == []


def test_fail_multiple_multi_region_trails_without_logging(tester):
    example_evidence = {
        "cloudtrail/trails.json": {
            "trailList": [
                {
                    "Name": "trail-one",
                    "IsMultiRegionTrail": True,
                },
                {
                    "Name": "trail-two",
                    "IsMultiRegionTrail": True,
                },
            ]
        },
        "cloudtrail/trails/trail-one/trail_status.json": {
            "IsLogging": False,
        },
        "cloudtrail/trails/trail-two/trail_status.json": {
            "IsLogging": False,
        },
    }

    load_evidence(tester, example_evidence)

    result = check_cloudtrail_multi_region(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. No multi-region CloudTrail trail "
        "with active logging was found."
    )
    assert result.samples == []