from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .tests.org import run_org_tests
from .tests.repos import run_repo_tests


class GitHubTester:
    def __init__(self, github_org_name: str, context):
        self.provider = "github"
        self.report_title = "GitHub Audit Report"
        self.reader = context.reader
        self.github_org_name = github_org_name
        self.exclusions = context.exclusions or ExclusionManager()
        self.evidence_folder = context.evidence_folder


    def get_scope(self):
        return [
            f"Organization Name: {self.github_org_name}"
        ]


    def read(self, relative_path, optional=False):
        return self.reader.read_json(f"{self.evidence_folder}/{relative_path}", optional=optional)


    def run_tests(self):
        tests = []

        tests.extend(run_org_tests(self))
        tests.extend(run_repo_tests(self))

        return tests