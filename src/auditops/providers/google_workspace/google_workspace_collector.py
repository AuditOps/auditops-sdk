import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleWorkspaceCollector:
    def __init__(self, credentials_file_path, admin_email):
        self.credentials_file = credentials_file_path
        self.admin_email = admin_email

        self.audit_folder = None
        self.writer = None
        self.reader = None

    def gather_evidence(self, audit):
        self.audit_folder = audit.audit_folder
        self.writer = audit.writer
        self.reader = audit.reader

        self._collect_org_settings()

    def _collect_org_settings(self):
        scopes = [
            "https://www.googleapis.com/auth/admin.directory.user.readonly",
            "https://www.googleapis.com/auth/admin.directory.group.readonly",
            "https://www.googleapis.com/auth/admin.directory.group.member.readonly",
        ]

        # Authenticate using the service account credentials
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_file, scopes=scopes
        )
        delegated_creds = creds.with_subject(self.admin_email)

        # Build the Directory API client
        service = build("admin", "directory_v1", credentials=delegated_creds)

        self._save_google_users(service)
        self._save_google_groups(service)

    def _save_google_users(self, service):
        # Save Users File
        response = service.users().list(customer="my_customer").execute()
        users_list = response.get("users", [])
        self.writer.save_json(f"{self.audit_folder}/audit_evidence/admin/users.json", users_list)

    def _save_google_groups(self, service):
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
        
        self.writer.save_json(f"{self.audit_folder}/audit_evidence/admin/groups.json", groups)