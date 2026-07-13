def collect_iam_evidence(collector):
    iam_client = collector.session.client("iam")

    collector.collect(
        evidence_path = "iam/account_summary.json",
        client = iam_client,
        method = "get_account_summary",
    )

    collector.collect(
        evidence_path = "iam/password_policy.json",
        client = iam_client,
        method = "get_account_password_policy",
        ignore_codes="NoSuchEntity"
    )

    collect_iam_users(collector, iam_client)
    collect_iam_roles(collector, iam_client)
    collect_iam_groups(collector, iam_client)


def collect_iam_users(collector, iam_client):
    users = collector.collect(
        evidence_path="iam/users.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_users",
            "pagination_key": "Users",
        },
    )

    for user in users.get("Users", []):
        user_name = user["UserName"]

        collector.collect(
            evidence_path=f"iam/users/{user_name}/login_profile.json",
            client=iam_client,
            method="get_login_profile",
            method_kwargs={
                "UserName": user_name,
            },
            ignore_codes=["NoSuchEntity"],
        )

        collector.collect(
            evidence_path=f"iam/users/{user_name}/mfa_devices.json",
            client=iam_client,
            method="list_mfa_devices",
            method_kwargs={
                "UserName": user_name,
            },
        )

        collector.collect(
            evidence_path=f"iam/users/{user_name}/access_keys.json",
            client=iam_client,
            method="list_access_keys",
            method_kwargs={
                "UserName": user_name,
            },
        )


def collect_iam_roles(collector, iam_client):
    collector.collect(
        evidence_path="iam/roles.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_roles",
            "pagination_key": "Roles",
        },
    )


def collect_iam_groups(collector, iam_client):
    collector.collect(
        evidence_path="iam/groups.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_groups",
            "pagination_key": "Groups",
        },
    )