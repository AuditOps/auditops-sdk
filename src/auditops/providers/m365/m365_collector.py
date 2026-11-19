
import msal
import requests
from .collectors import collect_admin_evidence


class M365Collector:
    def __init__(self, credentials):
        self.credentials = credentials

        self.audit_folder = None
        self.writer = None
        self.reader = None
        self.service = None

    def gather_evidence(self, audit):
        self.audit_folder = audit.audit_folder
        self.writer = audit.writer
        self.reader = audit.reader

        self.authenticate()
        collect_admin_evidence(self)

    def authenticate(self):
        app = msal.ConfidentialClientApplication(
            self.credentials["client_id"],
            authority=f"https://login.microsoftonline.com/{self.credentials['tenant_id']}",
            client_credential=self.credentials["client_secret"],
        )

        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" not in result:
            raise RuntimeError(
                f"M365 authentication failed: "
                f"{result.get('error')}: {result.get('error_description')}"
            )

        self.service = requests.Session()
        self.service.headers.update({
            "Authorization": f"Bearer {result['access_token']}",
        })

    def collect(self, evidence_path, api_call):
        """
        Return existing evidence if available.
        Otherwise, call the Microsoft Graph API and save the evidence.
        """

        full_path = f"{self.audit_folder}/audit_evidence/{evidence_path}"

        evidence = self.reader.read_json(
            full_path,
            optional=True,
        )

        if evidence is not None:
            return evidence

        evidence = api_call()

        self.writer.save_json(
            full_path,
            evidence,
        )

        return evidence
