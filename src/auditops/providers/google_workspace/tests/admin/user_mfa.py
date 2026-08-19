from auditops.core.models import Sample
from auditops.core.utils import create_test
from datetime import datetime, timedelta, timezone


def check_user_mfa(tester):
    # NOTE: Update grace period with a config value.
    metadata = {
        "test_id": "google-auth-001",
        "test_description": "Google users with an active console password have MFA enabled.",
        "risk_rating": 3,
        "table_headers": ["User Name", "Result", "Comments"],
        "test_procedures": [
            "Obtained a list of Google users by calling the users.list method.",
            "Saved the list of users: admin/users.json.",
            "For each user, verified the following attributes", 
        ],
        "test_attributes": [
            "The user is at least 7 days old (grace period for enabling MFA). See 'creationTime' in users.json.",
            "User is enrolled in two-step verification ('isEnrolledIn2Sv': true)"
        ]
    }

    test = create_test(tester, metadata)

    users = tester.read("admin/users.json")

    if not users:
        return test.fail("ERROR: Unable to retrieve list of Google Users.")


    # NOTE: Update grace period with a config value.
    grace_period = timedelta(days=7)
    grace_period_cutoff = datetime.now(timezone.utc) - grace_period

    for user in users.get("users", []):
        username = user["primaryEmail"]
        sample = Sample(sample_id={"user_name": username})

        # Suspended users are not applicable for MFA testing.
        if user.get("suspended", False):
            sample.is_passing = True
            sample.comments = "User is suspended; MFA is not applicable."

        else:
            creation_time = datetime.fromisoformat(
                user["creationTime"].replace("Z", "+00:00")
            )

            # Newly created users are within the MFA grace period.
            if creation_time > grace_period_cutoff:
                sample.is_passing = True
                # NOTE: Update grace period with a config value.
                sample.comments = (
                    f"User was created less than 7 days ago. Still within the grace period."
                )

            else:
                mfa_enabled = user.get("isEnrolledIn2Sv", False)

                if not mfa_enabled:
                    sample.comments = (
                        "User is not enrolled in Google 2-Step Verification."
                    )

                sample.is_passing = mfa_enabled

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "Google Workspace user(s) are not enrolled in 2-Step Verification."
        ),
    )

    return test