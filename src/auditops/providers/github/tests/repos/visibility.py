from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_repos_visibility(tester):
    metadata = {
        "test_id": "github-repo-001",
        "test_description": "Repositories in the GitHub organization are set to private.",
        "risk_rating": 0,
        "table_headers": ["Repository Name", "Conclusion", "Comments"],
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{tester.github_org_name}.",
            "Saved the list of GitHub repos: orgs/repos.json.",
            "For each repo, inspected the repositories acccess settings to determine if it is set to 'private'"        
        ],
        "test_attributes": []
    }

    test = create_test(tester, metadata)

    repos = tester.read("orgs/repos.json")

    for repo in repos:
        sample = Sample(sample_id={"repo_name": repo["name"]})
        if repo.get("private", True):
            sample.is_passing = True
        test.samples.append(sample)

    test.evaluate_samples(tester.exclusions, failure_message="repositories were not set to private.")

    return test