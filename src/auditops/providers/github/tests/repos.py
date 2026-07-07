from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def run_repo_tests(tester):
    return [
        test_repository_visibility(tester)
    ]


def test_repository_visibility(tester):
    metadata = {
        "test_id": "github-repo-001",
        "test_description": "All repositories in the organization are set to private or restricted.",
        "risk_rating": 0,
        "table_headers": ["Repository Name", "Conclusion", "Comments"],
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{tester.github_org_name}.",
            "Saved the list of GitHub repos: org/all_repos.json.",
            "???"        
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    repos = tester.read("organization/all_repos.json")               

    for repo in repos:
        sample = Sample(sample_id={"repo_name": repo["name"]})
        if repo.get("private", True):
            sample.result = True
        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, tester.provider)

    return test