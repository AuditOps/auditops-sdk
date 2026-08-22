from auditops.providers.aws.tests.iam import check_iam_root_access_key

#from conftest import load_evidence
from utils.evidence import load_evidence


def test_fail_missing_evidence(tester):
    load_evidence(tester, {}, missing_required={"iam/account_summary.json"})

    result = check_iam_root_access_key(tester)

    assert result.is_passing is False
    assert result.comments == "ERROR: Unable to retrieve required evidence (iam/account_summary.json)."

def test_fail_access_key_present(tester):
    example_evidence = {
        "iam/account_summary.json": {
            "SummaryMap": {
                "AccountAccessKeysPresent": 2
            }
        }
    }
    
    load_evidence(tester, example_evidence)

    result = check_iam_root_access_key(tester)

    assert result.is_passing is False
    assert result.comments == (
        "Exception Noted. Root account has 2 active access key(s)."
    )

def test_pass_no_access_keys_present(tester):
    example_evidence = {
        "iam/account_summary.json": {
            "SummaryMap": {
                "AccountAccessKeysPresent": 0
            }
        }
    }

    load_evidence(tester, example_evidence)

    result = check_iam_root_access_key(tester)

    assert result.is_passing is True
    assert result.comments == ""