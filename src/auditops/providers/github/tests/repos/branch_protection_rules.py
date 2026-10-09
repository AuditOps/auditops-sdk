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
        "test_procedures": [
            f"Obtained a list of all repositories by calling: https://api.github.com/orgs/[org_name]/repos.",
            "Saved the list of all repositories: orgs/repos.json.",
            "Obtained the branch protection rules from each repository by calling: https://api.github.com/repos/[org_name]/[repo_name]/branches/[default_branch]/protection",
            "Saved the branch protection rules: repos/[repo_name]/branch_protection_rules.json.",
            "Obtained the rulesets from each repository by calling: https://api.github.com/repos/[org_name]/[repo_name]/rulesets",
            "Saved the rulesets: repos/[repo_name]/rulesets.json.",
            "Obtained the settings for each repository ruleset by calling: https://api.github.com/repos/[org_name]/[repo_name]/rulesets/[rule_id]",
            "Saved the settings from each ruleset: repos/[repo_name]/rulesets/[rule_id].json.",       
            "Inspected each repository to determine if it was compliant with the test attributes below."
        ],
        "test_attributes": [
            "Pull requests require at least one approval before merging.",
        ],
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