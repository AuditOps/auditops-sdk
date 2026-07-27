from auditops.core.utils import create_test, fail_test


def check_iam_root_mfa(tester):
    metadata = {
        "test_id": "aws-iam-003",
        "test_description": "Root account has MFA enabled.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
            "Saved the account summary: iam/account_summary.json",
            "Inspected the account summary to determine if 'AccountMFAEnabled' is set to 1."
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    summary = tester.read("iam/account_summary.json")
    
    if not summary:
        return fail_test(test, "Missing required evidence: iam/account_summary.json.")

    mfa_enabled = summary.get("SummaryMap", {}).get("AccountMFAEnabled", 0)

    if mfa_enabled != 1:
        return fail_test(test, f"Exceptions Noted. Root account does not have MFA enabled.")

    return test