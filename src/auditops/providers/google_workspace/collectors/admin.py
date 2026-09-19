from google.oauth2 import service_account
from googleapiclient.discovery import build


def collect_admin_evidence(collector):
    scopes = [
        "https://www.googleapis.com/auth/admin.directory.user.readonly",
        "https://www.googleapis.com/auth/admin.directory.group.readonly",
        "https://www.googleapis.com/auth/admin.directory.group.member.readonly",
        "https://www.googleapis.com/auth/admin.directory.rolemanagement.readonly",
        "https://www.googleapis.com/auth/apps.groups.settings",
    ]

    # Authenticate using the service account credentials
    creds = service_account.Credentials.from_service_account_file(
        collector.credentials_file, scopes=scopes
    )

    delegated_creds = creds.with_subject(collector.admin_email)

    # Build the API clients
    directory_service = build("admin", "directory_v1", credentials=delegated_creds)
    groups_settings_service = build("groupssettings", "v1", credentials=delegated_creds)

    # Collect Google User Evidence
    collector.collect(
        evidence_path="admin/users.json",
        api_call=lambda: {
            "users": get_users(directory_service),
        }
    )

    # Collect Google Role Evidence
    collector.collect(
        evidence_path="admin/roles.json",
        api_call=lambda: {
            "roles": get_roles(directory_service),
        },
    )

    collect_google_groups(collector, directory_service, groups_settings_service)
    collect_google_role_assignments(collector, directory_service)

# ==============================================================================
# USERS
# ==============================================================================

def get_users(service):
    users = []
    page_token = None

    while True:
        response = (
            service.users().list(
                customer="my_customer",
                maxResults=200,
                pageToken=page_token,
            ).execute()
        )

        users.extend(response.get("users", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return users

# ==============================================================================
# GROUPS
# ==============================================================================

def collect_google_groups(collector, service, groups_settings_service):
    groups = collector.collect(
        evidence_path="admin/groups.json",
        api_call=lambda: {
            "groups": get_groups(service),
        },
    )

    for group in groups["groups"]:
        group_id = group["id"]

        collector.collect(
            evidence_path=f"admin/groups/{group_id}/members.json",
            api_call=lambda group_id=group_id: get_group_members(
                service,
                group_id,
            ),
        )

        collector.collect(
            evidence_path=f"admin/groups/{group_id}/settings.json",
            api_call=lambda group_id=group_id: get_group_settings(
                groups_settings_service,
                group_id,
            ),
        )

    return groups

def get_groups(service):
    groups = []
    page_token = None

    while True:
        response = (
            service.groups()
            .list(
                customer="my_customer",
                maxResults=200,
                pageToken=page_token,
            )
            .execute()
        )

        groups.extend(response.get("groups", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return groups

def get_group_members(service, group_id):
    members = []
    page_token = None

    while True:
        response = (
            service.members()
            .list(
                groupKey=group_id,
                maxResults=200,
                pageToken=page_token,
                includeDerivedMembership=True,
            )
            .execute()
        )

        members.extend(response.get("members", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return {
        "members": members,
    }

def get_group_settings(groups_settings_service, group_id):
    return (
        groups_settings_service.groups()
        .get(
            groupUniqueId=group_id,
        )
        .execute()
    )

# ==============================================================================
# ROLES
# ==============================================================================

def get_roles(service):
    roles = []
    page_token = None

    while True:
        response = (
            service.roles()
            .list(
                customer="my_customer",
                maxResults=200,
                pageToken=page_token,
            )
            .execute()
        )

        roles.extend(response.get("items", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return roles

def collect_google_role_assignments(collector, service):
    return collector.collect(
        evidence_path="admin/role_assignments.json",
        api_call=lambda: {
            "role_assignments": get_role_assignments(service),
        },
    )

def get_role_assignments(service):
    role_assignments = []
    page_token = None

    while True:
        response = (
            service.roleAssignments()
            .list(
                customer="my_customer",
                maxResults=200,
                pageToken=page_token,
            )
            .execute()
        )

        role_assignments.extend(response.get("items", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return role_assignments