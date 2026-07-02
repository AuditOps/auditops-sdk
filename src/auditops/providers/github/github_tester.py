from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager

class GitHubTester:
    def __init__(self, reader, github_org_name: str, exclusions: ExclusionManager | None = None):
        self.provider = "github"
        self.reader = reader
        self.github_org_name = github_org_name
        self.exclusions = exclusions or ExclusionManager()
        self.scope = [
            f"Organization Name: {github_org_name}"
        ]

    def _read(self, path):
        return self.reader.read_json("github", path)

    def _create_test(self, metadata):
        return Test(test_id=metadata.get("id"), test_description=metadata.get("description"), 
            test_procedures=metadata.get("procedures"), test_attributes=metadata.get("attributes"), 
            table_headers=metadata.get("headers"), risk_rating=metadata.get("risk_rating"))

    def run_tests(self):
        return [
            self._test_org_mfa_settings(),
            self._test_org_members_create_public_resources(),
            self._test_repository_visibility()
        ] 

    def _test_org_mfa_settings(self):
        metadata = {
            "id": "github-org-001",
            "description": "The GitHub organization settings require users to enable MFA.",
            "risk_rating": 2,
            "attributes": [
                "'two_factor_requirement_enabled' is set to true."
            ],
            "procedures": [
                f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{self.github_org_name}.",
                "Saved the GitHub organization settings: org_settings.json.",
                "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
            ]
        }

        test = self._create_test(metadata)
        org_settings = self._read("organization/settings.json")
        test.result = org_settings.get("two_factor_requirement_enabled")
        
        return test

    def _test_org_members_create_public_resources(self):
        metadata = {
            "id": "github-org-002",
            "description": "The GitHub organization settings prevent members from creating public resources.",
            "risk_rating": 0,
            "procedures": [
                f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{self.github_org_name}.",
                "Saved the GitHub organization settings: org_settings.json.",
                "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
            ],          
            "attributes": [
                "'members_can_create_public_repositories' in org_settings.json is set to false.",
                "'members_can_create_public_pages' in org_settings.json is set to false."
            ]
        }

        test = self._create_test(metadata)
        org_settings = self._read("organization/settings.json")
        test.result = (
            not org_settings.get("members_can_create_public_repositories", True)
            and not org_settings.get("members_can_create_public_pages", True)
        )        
        
        return test

    def _test_repository_visibility(self):
        metadata = {
            "id": "github-repo-001",
            "description": "All repositories in the organization set set to private or restricted.",
            "risk_rating": 0,
            "headers": ["Repository Name", "Conclusion", "Comments"],
            "procedures": [
                f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{self.github_org_name}.",
                "Saved the list of GitHub repos: org/all_repos.json.",
                "???"        
            ],
        }

        test = self._create_test(metadata)

        repos = self._read("organization/all_repos.json")               

        for repo in repos:
            sample = Sample(sample_id={"repo_name": repo["name"]})
            if repo.get("private", True):
                sample.result = True
            test.samples.append(sample)

        test.evaluate_samples(self.exclusions, self.provider)

        return test