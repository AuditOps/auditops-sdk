from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_security_email(tester):
    min_group_members = tester.config.min_group_members
    required_group_emails = tester.config.required_group_emails

    if not required_group_emails:
        required_group_emails_str = "N/A - no required group emails."
    else:
        required_group_emails_str = ", ".join(required_group_emails)

    metadata = {
        "test_id": "google-groups-001",
        "test_description": (
            f"Dedicated security & compliance group emails exist, and have "
            f"at least {min_group_members} members."
        ),
        "risk_rating": 3,
        "table_headers": ["Group Name", "Result", "Comments"],
        "test_procedures": [
            "Obtained a list of Google Groups by calling the groups.list method.",
            "Saved the list of groups: admin/groups.json.",
            "For each Google Group, obtained the group members by calling the members.list method.",
            "Saved the group members: admin/groups/[GROUP_ID]/members.json.",
            "Obtained the Google Group settings by calling the Groups Settings API.",
            "Saved the group settings under admin/groups/[GROUP_ID]/settings.json.",
            "For each required Google Group, verified the attributes defined below were in place.",
        ],
        "test_attributes": [
            f"The following email addresses are associated with Google Groups: "
            f"{required_group_emails_str}.",
            f"Each required Google Group has at least {min_group_members} members.",
            "Each required Google Group has 'whoCanPostMessage' set to 'ANYONE_CAN_POST'.",
        ],
    }

    test = create_test(tester, metadata)

    # If no groups are configured as required, there is nothing to test.
    if not required_group_emails:
        return test

    groups = tester.read("admin/groups.json")

    if not groups:
        return test.fail(
            "ERROR: Unable to retrieve list of Google Groups."
        )

    # Create a lookup using the primary email and all group aliases.
    groups_by_email = {}

    for group in groups.get("groups", []):
        group_email = group.get("email")

        if group_email:
            groups_by_email[group_email.lower()] = group

        for alias in group.get("aliases", []):
            groups_by_email[alias.lower()] = group

        for alias in group.get("nonEditableAliases", []):
            groups_by_email[alias.lower()] = group

    for required_email in required_group_emails:
        required_email = required_email.lower()

        sample = Sample(
            sample_id={"group_email": required_email}
        )

        # Verify the required group exists by primary email or alias.
        group = groups_by_email.get(required_email)

        if group is None:
            sample.is_passing = False
            sample.comments = (
                f"There is no Google Group associated with: "
                f"{required_email}."
            )

            test.samples.append(sample)
            continue

        group_id = group.get("id")
        group_name = group.get("name", required_email)

        if not group_id:
            sample.is_passing = False
            sample.comments = (
                f"Google Group {required_email} does not have a group ID."
            )

            test.samples.append(sample)
            continue

        # Get group members using the stable group ID evidence path.
        members = tester.read(
            f"admin/groups/{group_id}/members.json"
        )

        if not members:
            sample.is_passing = False
            sample.comments = ("Unable to retrieve Google Group members.")

            test.samples.append(sample)
            continue

        group_members = members.get("members", [])

        # Verify minimum number of members.
        if len(group_members) < min_group_members:
            sample.is_passing = False
            sample.comments = (
                f"Google Group has only {len(group_members)} member(s). "
                f"At least {min_group_members} members are required."
            )

            test.samples.append(sample)
            continue

        # Get group settings using the stable group ID evidence path.
        settings = tester.read(
            f"admin/groups/{group_id}/settings.json"
        )

        if not settings:
            sample.is_passing = False
            sample.comments = (
                "Unable to retrieve Google Group settings."
            )

            test.samples.append(sample)
            continue

        # Verify public posting is enabled.
        who_can_post = settings.get("whoCanPostMessage")

        if who_can_post != "ANYONE_CAN_POST":
            sample.is_passing = False
            sample.comments = (
                "Google Group does not permit public posting. "
                f"'whoCanPostMessage' is '{who_can_post}'."
            )
        else:
            sample.is_passing = True
            sample.comments = (
                f"Google Group exists with "
                f"{len(group_members)} members and permits public posting."
            )

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "required Google Groups do not meet the configuration requirements."
        ),
    )

    return test