from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_repos_visibility(tester):
    metadata = {
        "test_id": "github-repo-001",
        "test_description": "Repositories in the GitHub organization are set to private.",
        "risk_rating": 0,
        "table_headers": ["Repository Name", "Conclusion", "Comments"],
        "test_procedures": [
            "Called the [List organization repositories](https://docs.github.com/en/rest/repos/repos#list-organization-repositories) "
            "endpoint to obtain a list of all repositories.",
            "Saved the API response: orgs/repos.json.",
            "For each repository, inspected the 'private' property to determine whether setting was set to 'true'."
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