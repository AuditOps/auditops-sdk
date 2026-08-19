import json
from .collectors import collect_admin_evidence


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

        collect_admin_evidence(self)

    def collect(self, evidence_path, api_call):
        # Check if evidence already exists.
        evidence = self.reader.read_json(
            f"{self.audit_folder}/audit_evidence/{evidence_path}",
            optional=True,
        )

        if evidence is not None:
            return evidence

        # Call API.
        evidence = api_call()

        # Save evidence.
        self.writer.save_json(
            f"{self.audit_folder}/audit_evidence/{evidence_path}",
            evidence,
        )

        return evidence