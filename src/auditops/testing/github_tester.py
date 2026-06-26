from .models import Test, Sample

class GitHubTester:
    def __init__(self, reader, github_org_name):
        self.reader = reader
        self.github_org_name = github_org_name

    def _read(self, path):
        return self.reader.read_json("github", path)

    def _create_test(self, metadata):
        return Test(test_id=metadata.get("id"), test_description=metadata.get("description"), 
            test_procedures=metadata.get("procedures"), test_attributes=metadata.get("attributes"), 
            table_headers=metadata.get("headers"), risk_rating=metadata.get("risk_rating"))

    def run_tests(self):
        tests = [
            self.test_org_mfa_settings()
        ]
        return tests        

    def test_org_mfa_settings(self):
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