from datetime import datetime, timedelta, timezone

from auditops.providers.google_workspace.tests.admin import check_user_mfa
from utils.evidence import load_evidence


def test_fail_missing_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"admin/users.json"},
    )

    result = check_user_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve list of Google Users."
    )


def test_pass_suspended_user(tester):
    example_evidence = {
        "admin/users.json": {
            "users": [
                {
                    "primaryEmail": "suspended@example.com",
                    "suspended": True,
                    "creationTime": "2026-01-01T00:00:00.000Z",
                    "isEnrolledIn2Sv": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"user_name": "suspended@example.com"}
    assert sample.comments == (
        "User is suspended; MFA is not applicable."
    )


def test_pass_user_within_grace_period(tester):
    creation_time = (
        datetime.now(timezone.utc) - timedelta(days=3)
    ).isoformat().replace("+00:00", "Z")

    example_evidence = {
        "admin/users.json": {
            "users": [
                {
                    "primaryEmail": "newuser@example.com",
                    "suspended": False,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"user_name": "newuser@example.com"}
    assert sample.comments == (
        "User was created less than 7 days ago. Still within the grace period."
    )


def test_fail_user_without_mfa(tester):
    creation_time = (
        datetime.now(timezone.utc) - timedelta(days=30)
    ).isoformat().replace("+00:00", "Z")

    example_evidence = {
        "admin/users.json": {
            "users": [
                {
                    "primaryEmail": "user@example.com",
                    "suspended": False,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": False,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_user_mfa(tester)

    assert result.is_passing is False
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is False
    assert sample.sample_id == {"user_name": "user@example.com"}
    assert sample.comments == (
        "User is not enrolled in Google 2-Step Verification."
    )


def test_pass_user_with_mfa(tester):
    creation_time = (
        datetime.now(timezone.utc) - timedelta(days=30)
    ).isoformat().replace("+00:00", "Z")

    example_evidence = {
        "admin/users.json": {
            "users": [
                {
                    "primaryEmail": "user@example.com",
                    "suspended": False,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": True,
                }
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_user_mfa(tester)

    assert result.is_passing is True
    assert len(result.samples) == 1

    sample = result.samples[0]
    assert sample.is_passing is True
    assert sample.sample_id == {"user_name": "user@example.com"}
    assert sample.comments == ""


def test_fail_mixed_user_population(tester):
    creation_time = (
        datetime.now(timezone.utc) - timedelta(days=30)
    ).isoformat().replace("+00:00", "Z")

    example_evidence = {
        "admin/users.json": {
            "users": [
                {
                    "primaryEmail": "passing@example.com",
                    "suspended": False,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": True,
                },
                {
                    "primaryEmail": "failing@example.com",
                    "suspended": False,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": False,
                },
                {
                    "primaryEmail": "suspended@example.com",
                    "suspended": True,
                    "creationTime": creation_time,
                    "isEnrolledIn2Sv": False,
                },
            ]
        }
    }

    load_evidence(tester, example_evidence)

    result = check_user_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. 1 of 3 Google Workspace user(s) are not enrolled in 2-Step Verification."
    )

    assert len(result.samples) == 3

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == ""

    assert result.samples[1].is_passing is False
    assert result.samples[1].comments == (
        "User is not enrolled in Google 2-Step Verification."
    )

    assert result.samples[2].is_passing is True
    assert result.samples[2].comments == (
        "User is suspended; MFA is not applicable."
    )