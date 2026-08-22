from auditops.core.utils import create_test


def check_iam_root_access_key(tester):
    metadata = {
        "test_id": "aws-iam-001",
        "test_description": "Root account does not have any active access keys.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
            "Saved the account summary: iam/account_summary.json.",
            "Inspected the account summary to determine if 'AccountAccessKeysPresent' is set to 0."
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    summary = tester.read("iam/account_summary.json")

    if not summary:
        return test.fail("ERROR: Unable to retrieve required evidence (iam/account_summary.json).")

    root_keys = summary.get("SummaryMap", {}).get("AccountAccessKeysPresent", 0)

    if root_keys == 0:
        test.is_passing = True
    else:
        return test.fail(f"Exception Noted. Root account has {root_keys} active access key(s).")

    return test