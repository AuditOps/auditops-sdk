from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .tests.orgs import (check_orgs_mfa_settings, check_orgs_members_create_public_resources)
from .tests.repos import (check_repos_visibility, check_branch_protection_rules)


class GitHubTester:
    def __init__(self):
        self.reader = None
        self.exclusions = None
        self.audit_folder = None

    GITHUB_TESTS = [
        # Organization Settings
        check_orgs_mfa_settings,
        check_orgs_members_create_public_resources,

        # Repos
        check_repos_visibility,
        check_branch_protection_rules
    ]

    def get_scope(self):
        github_org_name = self.read("orgs/org_settings.json").get("login", "ERROR: Unable to retrieve organization name.")
        return [
            f"Organization Name: {github_org_name}"
        ]

    def read(self, relative_path, optional=False):
        return self.reader.read_json(f"{self.audit_folder}/audit_evidence/{relative_path}", optional=optional)

    def run_tests(self, audit):
        self.reader = audit.reader
        self.exclusions = audit.exclusions
        self.audit_folder = audit.audit_folder

        all_tests = []
        
        for test in self.GITHUB_TESTS:
            all_tests.append(test(self))

        return all_tests