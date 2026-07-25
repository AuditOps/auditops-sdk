from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .tests.orgs import (check_orgs_mfa_settings, check_orgs_members_create_public_resources)
from .tests.repos import (check_repos_visibility)


class GitHubTester:
    def __init__(self, github_org_name: str, audit):
        self.reader = audit.reader
        self.github_org_name = github_org_name
        self.exclusions = audit.exclusions
        self.evidence_folder = audit.evidence_folder

    GITHUB_TESTS = [
        # Organization Settings
        check_orgs_mfa_settings,
        check_orgs_members_create_public_resources,

        # Repos
        check_repos_visibility
    ]

    def get_scope(self):
        return [
            f"Organization Name: {self.github_org_name}"
        ]

    def read(self, relative_path, optional=False):
        return self.reader.read_json(f"{self.evidence_folder}/{relative_path}", optional=optional)

    def run_tests(self):
        all_tests = []
        
        for test in self.GITHUB_TESTS:
            all_tests.append(test(self))
        
        return all_tests