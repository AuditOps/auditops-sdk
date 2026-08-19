from google.oauth2 import service_account
from googleapiclient.discovery import build


def collect_admin_evidence(collector):
    scopes = [
        "https://www.googleapis.com/auth/admin.directory.user.readonly",
        "https://www.googleapis.com/auth/admin.directory.group.readonly",
        "https://www.googleapis.com/auth/admin.directory.group.member.readonly",
    ]

    # Authenticate using the service account credentials
    creds = service_account.Credentials.from_service_account_file(
        collector.credentials_file, scopes=scopes
    )
    delegated_creds = creds.with_subject(collector.admin_email)

    # Build the Directory API client
    service = build("admin", "directory_v1", credentials=delegated_creds)

    collect_google_users(collector, service)
    collect_google_groups(collector, service)


def collect_google_users(collector, service):
    collector.collect(
        evidence_path="admin/users.json",
        api_call=lambda: service.users().list(
            customer="my_customer"
        ).execute()
    )

def collect_google_groups(collector, service):
    # Check if evidence already exists.
    evidence = collector.reader.read_json(
        f"{collector.audit_folder}/audit_evidence/admin/groups.json",
        optional=True,
    )

    if evidence is not None:
        return evidence

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

    evidence = {
        "groups": groups,
        "nextPageToken": page_token,
    }

    # Save evidence.
    collector.writer.save_json(
        f"{collector.audit_folder}/audit_evidence/admin/groups.json",
        evidence,
    )