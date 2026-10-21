from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_branch_protection_rules(tester):
    metadata = {
        "test_id": "github-repo-002",
        "test_description": (
            "Repositories are configured to require an approval before a pull request is merged."
        ),
        "risk_rating": 3,
        "table_headers": [
            "Repository Name",
            "Conclusion",
            "Comments",
        ],
        "test_procedures":[
            "Called the [List organization repositories](https://docs.github.com/en/rest/repos/repos#list-organization-repositories) "
            "endpoint to obtain a list of all repositories.",
            "Saved the API response: orgs/repos.json.",
            "For each repository, performed the following steps:",
            "- Called the [Get branch protection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection) "
            "endpoint to obtain the classic branch protection configuration for the repository's default branch.",
            "- Saved the API response: repos/[REPO_NAME]/branch_protection_rules.json.",
            "- Called the [List repository rulesets](https://docs.github.com/en/rest/repos/rules#list-repository-rulesets) endpoint "
            "to obtain the rulesets for each repository.",
            "- Saved the API response: repos/[REPO_NAME]/rulesets.json.",
            "For each repository ruleset, performed the following steps:",
            "- Called the [Get repository ruleset](https://docs.github.com/en/rest/repos/rules#get-repository-ruleset) endpoint "
            "to obtain the ruleset's settings.",
            "- Saved the API response: repos/[REPO_NAME]/rulesets/[RULE_ID].json.",
            "For each repository, inspected the classic branch protection configuration and applicable rulesets to determine "
            "whether the default branch required changes to be approved before the pull request can be merged."
        ],
        "test_attributes": [],
    }

    test = create_test(tester, metadata)

    repos = tester.read("orgs/repos.json")

    for repo in repos:
        repo_name = repo["name"]

        branch_protection = tester.read(
            f"repos/{repo_name}/branch_protection_rules.json",
            optional=True,
        )

        rulesets = tester.read(
            f"repos/{repo_name}/rulesets.json",
            optional=True,
        )

        sample = Sample(
            sample_id={
                "repo_name": repo_name,
            }
        )

        pull_request_required = False

        # Check classic branch protection rules.
        if branch_protection:
            required_pull_request_reviews = branch_protection.get(
                "required_pull_request_reviews"
            )

            if required_pull_request_reviews:
                required_approving_review_count = (
                    required_pull_request_reviews.get(
                        "required_approving_review_count",
                        0,
                    )
                )

                if required_approving_review_count >= 1:
                    pull_request_required = True

                    sample.is_passing = True
                    sample.comments = (
                        "Classic branch protection requires at least "
                        f"{required_approving_review_count} approved "
                        "pull request review before changes can be merged."
                    )

        # Check repository rulesets if classic branch protection did not
        # satisfy the requirement.
        if not pull_request_required and rulesets:
            for ruleset in rulesets:
                if ruleset.get("enforcement") != "active":
                    continue

                ruleset_id = ruleset.get("id")

                if not ruleset_id:
                    continue

                ruleset_settings = tester.read(
                    f"repos/{repo_name}/rulesets/{ruleset_id}.json",
                    optional=True,
                )

                if not ruleset_settings:
                    continue

                for rule in ruleset_settings.get("rules", []):
                    if rule.get("type") != "pull_request":
                        continue

                    parameters = rule.get("parameters", {})

                    required_approving_review_count = parameters.get(
                        "required_approving_review_count",
                        0,
                    )

                    if required_approving_review_count >= 1:
                        pull_request_required = True

                        sample.is_passing = True
                        sample.comments = (
                            "An active repository ruleset requires at least "
                            f"{required_approving_review_count} approved "
                            "pull request review before changes can be "
                            "merged."
                        )
                        break

                if pull_request_required:
                    break

        if not pull_request_required:
            sample.is_passing = False

            if not branch_protection and not rulesets:
                sample.comments = (
                    "No branch protection rules or repository rulesets were identified."
                )
            else:
                sample.comments = (
                    "No active branch protection rule or repository "
                    "ruleset requires at least one approved pull request "
                    "review before changes can be merged."
                )

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "Repositories did not require at least one approved pull request review before changes could be merged."
        ),
    )

    return test