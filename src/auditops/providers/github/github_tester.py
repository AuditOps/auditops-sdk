from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .tests.org import run_org_tests
from .tests.repos import run_repo_tests


class GitHubTester:
    def __init__(self, reader, github_org_name: str, exclusions: ExclusionManager | None = None):
        self.provider = "github"
        self.report_title = "GitHub Audit Report"
        self.reader = reader
        self.github_org_name = github_org_name
        self.exclusions = exclusions or ExclusionManager()
        self.scope = [
            f"Organization Name: {github_org_name}"
        ]


    def read(self, path):
        return self.reader.read_json("github", path)


    def run_tests(self):
        tests = []

        tests.extend(run_org_tests(self))
        tests.extend(run_repo_tests(self))

        return tests