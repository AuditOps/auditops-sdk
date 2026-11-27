from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_required_status_checks(tester):
    metadata = {
        "test_id": "github-repo-004",
        "test_description": (
            "Active repositories require at least one status check to pass before changes can be merged."
        ),
        "risk_rating": 3,
        "table_headers": [
            "Repository Name",
            "Conclusion",
            "Comments",
        ],
        "test_procedures": [
            "Obtained a list of repositories by calling the "
            "[List organization repositories](https://docs.github.com/en/rest/repos/repos#list-organization-repositories) GitHub endpoint.",
            "Saved the list of repositories: orgs/repos.json.",
            "For each repository, performed the following steps:",
            "- Checked if the repository was archived. Archived repositories were excluded from required status check testing because they are not actively maintained.",
            "- Obtained the branch protection configuration for the repository's default branch by calling the "
            "[Get branch protection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection) GitHub endpoint.",
            "- Saved the branch protection rules: repos/[REPO_NAME]/branch_protection_rules.json",
            "- Obtained the rulesets associated with the repository by calling the "
            "[List repository rulesets](https://docs.github.com/en/rest/repos/rules#list-repository-rulesets) GitHub endpoint.",
            "- Saved the rulesets associated with the repository: repos/[REPO_NAME]/rulesets.json",
            "For each repository ruleset, performed the following steps:",
            "- Obtained the ruleset's configuration by calling the [Get a repository ruleset](https://docs.github.com/en/rest/repos/rules#get-repository-ruleset) GitHub endpoint.",
            "- Saved the ruleset's configuration: repos/[REPO_NAME]/rulesets/[RULE_ID].json",
            "For each active repository, inspected the branch protection configuration and applicable rulesets to determine "
            "whether the default branch required at least one status check to pass before changes could be merged."
        ],
        "test_attributes": [],
        "remediation_url": "https://github.com/ajdehn/AWS-Audit-Playbook/tree/main/test_library/github/github-repo-003#remediation-guidance"
    }

    test = create_test(tester, metadata)

    repos = tester.read("orgs/repos.json")

    for repo in repos:
        repo_name = repo["name"]
        sample = Sample(
            sample_id={
                "repo_name": repo_name,
            }
        )

        if repo["archived"]:
            sample.is_passing = True
            sample.comments = (
                "This repository is archived; status check testing is not applicable."
            )
            test.samples.append(sample)
            continue

        branch_protection = tester.read(
            f"repos/{repo_name}/branch_protection_rules.json",
            optional=True,
        )

        rulesets = tester.read(
            f"repos/{repo_name}/rulesets.json",
            optional=True,
        )

        status_checks_required = False

        # Check classic branch protection rules.
        if branch_protection:
            required_status_checks = branch_protection.get(
                "required_status_checks"
            )

            if required_status_checks:
                contexts = required_status_checks.get("contexts") or []
                checks = required_status_checks.get("checks") or []

                required_checks = contexts + [
                    check.get("context")
                    for check in checks
                    if check.get("context")
                ]

                if required_checks:
                    status_checks_required = True

                    sample.is_passing = True
                    sample.comments = (
                        "Classic branch protection requires at least one "
                        "status check to pass before changes can be merged: "
                        f"{', '.join(required_checks)}."
                    )

        # Check repository rulesets if classic branch protection did not
        # satisfy the requirement.
        if not status_checks_required and rulesets:
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
                    if rule.get("type") != "required_status_checks":
                        continue

                    parameters = rule.get("parameters", {})

                    required_checks = parameters.get(
                        "required_status_checks",
                        [],
                    )

                    if required_checks:
                        status_checks_required = True

                        check_names = [
                            check.get("context")
                            for check in required_checks
                            if check.get("context")
                        ]

                        sample.is_passing = True
                        sample.comments = (
                            "An active repository ruleset requires at least "
                            "one status check to pass before changes can be "
                            "merged: "
                            f"{', '.join(check_names)}."
                        )
                        break

                if status_checks_required:
                    break

        if not status_checks_required:
            sample.is_passing = False

            if not branch_protection and not rulesets:
                sample.comments = (
                    "No branch protection rules or repository rulesets were identified."
                )
            else:
                sample.comments = (
                    "No active branch protection rule or repository "
                    "ruleset requires at least one status check to pass "
                    "before changes can be merged."
                )

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "Repositories did not require at least one status check to pass before changes could be merged."
        ),
    )

    return test