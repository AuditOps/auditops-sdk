import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleWorkspaceCollector:
    def __init__(self, credentials_file_path, admin_email):
        self.credentials_file = credentials_file_path
        self.admin_email = admin_email

    def collect(self, writer):
        self._collect_org_settings(writer)

    def _collect_org_settings(self, writer):
        scopes = ["https://www.googleapis.com/auth/admin.directory.user.readonly"]

        # Authenticate using the service account credentials
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_file, scopes=scopes
        )
        delegated_creds = creds.with_subject(self.admin_email)

        # Build the Directory API client
        service = build("admin", "directory_v1", credentials=delegated_creds)

        # Save Users File
        response = service.users().list(customer="my_customer").execute()
        users_list = response.get("users", [])
        writer.save_json("google_workspace", "admin/users.json", users_list)