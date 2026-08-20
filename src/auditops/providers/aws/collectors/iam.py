def collect_iam_evidence(collector):
    # NOTE: If performance becomes an issue, we could collect this evidence in parrallel.
    iam_client = collector.session.client("iam")

    collect_iam_settings(collector, iam_client)
    collect_iam_users(collector, iam_client)
    collect_iam_groups(collector, iam_client)
    collect_iam_roles(collector, iam_client)
    collect_iam_administrative_access(collector, iam_client)


# ==============================================================================
# General IAM Settings
# ==============================================================================
def collect_iam_settings(collector, iam_client):
    collector.collect(
        evidence_path="iam/account_summary.json",
        client=iam_client,
        method="get_account_summary",
    )

    collector.collect(
        evidence_path="iam/password_policy.json",
        client=iam_client,
        method="get_account_password_policy",
        ignore_codes="NoSuchEntity",
    )


# ==============================================================================
# IAM Users
# ==============================================================================
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
        collect_iam_user(collector, iam_client, user["UserName"])


def collect_iam_user(collector, iam_client, user_name):
    collect_iam_user_login_profile(collector, iam_client, user_name)
    collect_iam_user_mfa_devices(collector, iam_client, user_name)
    collect_iam_user_access_keys(collector, iam_client, user_name)
    collect_iam_user_attached_policies(collector, iam_client, user_name)
    collect_iam_user_inline_policies(collector, iam_client, user_name)
    collect_iam_user_groups(collector, iam_client, user_name)


def collect_iam_user_login_profile(collector, iam_client, user_name):
    collector.collect(
        evidence_path=f"iam/users/{user_name}/login_profile.json",
        client=iam_client,
        method="get_login_profile",
        method_kwargs={
            "UserName": user_name,
        },
        ignore_codes=["NoSuchEntity"],
    )


def collect_iam_user_mfa_devices(collector, iam_client, user_name):
    collector.collect(
        evidence_path=f"iam/users/{user_name}/mfa_devices.json",
        client=iam_client,
        method="list_mfa_devices",
        method_kwargs={
            "UserName": user_name,
        },
    )


def collect_iam_user_access_keys(collector, iam_client, user_name):
    collector.collect(
        evidence_path=f"iam/users/{user_name}/access_keys.json",
        client=iam_client,
        method="list_access_keys",
        method_kwargs={
            "UserName": user_name,
        },
    )


def collect_iam_user_attached_policies(collector, iam_client, user_name):
    collector.collect(
        evidence_path=f"iam/users/{user_name}/attached_managed_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_attached_user_policies",
            "pagination_key": "AttachedPolicies",
            "params": {
                "UserName": user_name,
            },
        },
    )


def collect_iam_user_inline_policies(collector, iam_client, user_name):
    inline_policies = collector.collect(
        evidence_path=f"iam/users/{user_name}/inline_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_user_policies",
            "pagination_key": "PolicyNames",
            "params": {
                "UserName": user_name,
            },
        },
    )

    for policy_name in inline_policies.get("PolicyNames", []):
        collector.collect(
            evidence_path=(
                f"iam/users/{user_name}/inline_policies/{policy_name}.json"
            ),
            client=iam_client,
            method="get_user_policy",
            method_kwargs={
                "UserName": user_name,
                "PolicyName": policy_name,
            },
        )


def collect_iam_user_groups(collector, iam_client, user_name):
    collector.collect(
        evidence_path=f"iam/users/{user_name}/group_membership.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_groups_for_user",
            "pagination_key": "Groups",
            "params": {
                "UserName": user_name,
            },
        },
    )

# ==============================================================================
# IAM Groups
# ==============================================================================
def collect_iam_groups(collector, iam_client):
    groups = collector.collect(
        evidence_path="iam/groups.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_groups",
            "pagination_key": "Groups",
        },
    )

    for group in groups.get("Groups", []):
        collect_iam_group(collector, iam_client, group["GroupName"])

def collect_iam_group(collector, iam_client, group_name):
    collect_iam_group_members(collector, iam_client, group_name)
    collect_iam_group_attached_policies(collector, iam_client, group_name)
    collect_iam_group_inline_policies(collector, iam_client, group_name)


def collect_iam_group_members(collector, iam_client, group_name):
    collector.collect(
        evidence_path=f"iam/groups/{group_name}/group_members.json",
        client=iam_client,
        paginator_params={
            "method_name": "get_group",
            "pagination_key": "Users",
            "params": {
                "GroupName": group_name,
            },
        },
    )


def collect_iam_group_attached_policies(collector, iam_client, group_name):
    collector.collect(
        evidence_path=f"iam/groups/{group_name}/attached_managed_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_attached_group_policies",
            "pagination_key": "AttachedPolicies",
            "params": {
                "GroupName": group_name,
            },
        },
    )


def collect_iam_group_inline_policies(collector, iam_client, group_name):
    inline_policies = collector.collect(
        evidence_path=f"iam/groups/{group_name}/inline_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_group_policies",
            "pagination_key": "PolicyNames",
            "params": {
                "GroupName": group_name,
            },
        },
    )

    for policy_name in inline_policies.get("PolicyNames", []):
        collector.collect(
            evidence_path=(
                f"iam/groups/{group_name}/inline_policies/{policy_name}.json"
            ),
            client=iam_client,
            method="get_group_policy",
            method_kwargs={
                "GroupName": group_name,
                "PolicyName": policy_name,
            },
        )

# ==============================================================================
# IAM Roles
# ==============================================================================
def collect_iam_roles(collector, iam_client):
    roles = collector.collect(
        evidence_path="iam/roles.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_roles",
            "pagination_key": "Roles",
        },
    )

    for role in roles.get("Roles", []):
        collect_iam_role(collector, iam_client, role["RoleName"])


def collect_iam_role(collector, iam_client, role_name):
    # RoleName can contain '/', so normalize it for the evidence path.
    evidence_name = role_name.replace("/", "_")

    collect_iam_role_details(collector, iam_client, role_name, evidence_name)
    collect_iam_role_attached_policies(collector, iam_client, role_name, evidence_name)
    collect_iam_role_inline_policies(collector, iam_client, role_name, evidence_name)


def collect_iam_role_details(collector, iam_client, role_name, evidence_name):
    collector.collect(
        evidence_path=f"iam/roles/{evidence_name}/role_details.json",
        client=iam_client,
        method="get_role",
        method_kwargs={
            "RoleName": role_name,
        },
    )


def collect_iam_role_attached_policies(collector, iam_client, role_name, evidence_name):
    collector.collect(
        evidence_path=f"iam/roles/{evidence_name}/attached_managed_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_attached_role_policies",
            "pagination_key": "AttachedPolicies",
            "params": {
                "RoleName": role_name,
            },
        },
    )


def collect_iam_role_inline_policies(collector, iam_client, role_name, evidence_name):
    inline_policies = collector.collect(
        evidence_path=f"iam/roles/{evidence_name}/inline_policies.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_role_policies",
            "pagination_key": "PolicyNames",
            "params": {
                "RoleName": role_name,
            },
        },
    )

    for policy_name in inline_policies.get("PolicyNames", []):
        collector.collect(
            evidence_path=(
                f"iam/roles/{evidence_name}/inline_policies/{policy_name}.json"
            ),
            client=iam_client,
            method="get_role_policy",
            method_kwargs={
                "RoleName": role_name,
                "PolicyName": policy_name,
            },
        )

# ==============================================================================
# IAM Administrators
# ==============================================================================

def collect_iam_administrative_access(collector, iam_client):
    policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

    collect_iam_administrative_policy_users(collector, iam_client, policy_arn)
    collect_iam_administrative_policy_groups(collector, iam_client, policy_arn)
    collect_iam_administrative_policy_roles(collector, iam_client, policy_arn)


def collect_iam_administrative_policy_users(collector, iam_client, policy_arn):
    collector.collect(
        evidence_path="iam/admin/policy_users.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_entities_for_policy",
            "pagination_key": "PolicyUsers",
            "params": {
                "PolicyArn": policy_arn,
            },
        },
    )


def collect_iam_administrative_policy_groups(collector, iam_client, policy_arn):
    collector.collect(
        evidence_path="iam/admin/policy_groups.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_entities_for_policy",
            "pagination_key": "PolicyGroups",
            "params": {
                "PolicyArn": policy_arn,
            },
        },
    )


def collect_iam_administrative_policy_roles(collector, iam_client, policy_arn):
    collector.collect(
        evidence_path="iam/admin/policy_roles.json",
        client=iam_client,
        paginator_params={
            "method_name": "list_entities_for_policy",
            "pagination_key": "PolicyRoles",
            "params": {
                "PolicyArn": policy_arn,
            },
        },
    )