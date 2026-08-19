from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .tests.admin import check_user_mfa


class GoogleWorkpaceTester:
    def __init__(self):
        self.reader = None
        self.exclusions = None
        self.audit_folder = None

    GOOGLE_WORKSPACE_TESTS = [
        # Organization Settings
        check_user_mfa
    ]

    def get_scope(self):
        # NOTE: Identify a clear Google Workspace identifier.
        return []

    def read(self, relative_path, optional=False):
        return self.reader.read_json(f"{self.audit_folder}/audit_evidence/{relative_path}", optional=optional)

    def run_tests(self, audit):
        self.reader = audit.reader
        self.exclusions = audit.exclusions
        self.audit_folder = audit.audit_folder

        all_tests = []
        
        for test in self.GOOGLE_WORKSPACE_TESTS:
            all_tests.append(test(self))

        return all_tests