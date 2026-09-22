from auditops.providers.aws.tests.iam import check_iam_root_mfa
from utils.evidence import load_evidence


def test_fail_missing_evidence(tester):
    load_evidence(
        tester,
        {},
        missing_required={"iam/account_summary.json"},
    )

    result = check_iam_root_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "ERROR: Unable to retrieve required evidence (iam/account_summary.json)."
    )


def test_not_applicable_root_user_without_password(tester):
    example_evidence = {
        "iam/account_summary.json": {
            "SummaryMap": {
                "AccountPasswordPresent": 0,
                "AccountMFAEnabled": 0,
            }
        }
    }

    load_evidence(tester, example_evidence)

    result = check_iam_root_mfa(tester)

    assert result.is_passing is True
    assert result.comments == (
        "Not applicable. Root account does not have a password."
    )

def test_fail_root_user_without_mfa(tester):
    example_evidence = {
        "iam/account_summary.json": {
            "SummaryMap": {
                "AccountMFAEnabled": 0,
            }
        }
    }

    load_evidence(tester, example_evidence)

    result = check_iam_root_mfa(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exceptions Noted. Root account does not have MFA enabled."
    )


def test_pass_root_user_with_mfa(tester):
    example_evidence = {
        "iam/account_summary.json": {
            "SummaryMap": {
                "AccountMFAEnabled": 1,
            }
        }
    }

    load_evidence(tester, example_evidence)

    result = check_iam_root_mfa(tester)

    assert result.is_passing is True
    assert result.comments == ""