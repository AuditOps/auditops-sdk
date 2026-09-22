import json
from .collectors import collect_admin_evidence


class GoogleWorkspaceCollector:
    def __init__(self, credentials, admin_email):
        self.credentials = credentials
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
        """
        Return existing evidence if available.
        Otherwise, call the Google Workspace API and save the evidence.
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