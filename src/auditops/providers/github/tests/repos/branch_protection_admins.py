from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_branch_protection_admins(tester):
    metadata = {
        "test_id": "github-repo-003",
        "test_description": (
            "Repositories are configured so that administrators are subject to branch protection requirements."
        ),
        "risk_rating": 3,
        "table_headers": [
            "Repository Name",
            "Conclusion",
            "Comments",
        ],
        "test_procedures": [
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
            "For each repository, inspected the branch protection rules and ruleset(s) to determine whether Administrators were subject to branch protection rules / ruleset requirements.",
        ],
        "test_attributes": [],
    }

    test = create_test(tester, metadata)

    repos = tester.read("orgs/repos.json")

    for repo in repos:
        repo_name = repo["name"]
        default_branch = repo["default_branch"]

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

        admins_protected = False

        # Check classic branch protection rules.
        if branch_protection:
            enforce_admins = branch_protection.get(
                "enforce_admins",
                {},
            )

            if enforce_admins.get("enabled", False):
                admins_protected = True

                sample.is_passing = True
                sample.comments = (
                    "Classic branch protection rules for the repository's "
                    f"default branch ({default_branch}) are enforced "
                    "for administrators."
                )

        # Check repository rulesets if classic branch protection did not
        # satisfy the requirement.
        if not admins_protected and rulesets:
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

                conditions = ruleset_settings.get(
                    "conditions",
                    {},
                )

                ref_name = conditions.get(
                    "ref_name",
                    {},
                )

                include_branches = ref_name.get(
                    "include",
                    [],
                )

                exclude_branches = ref_name.get(
                    "exclude",
                    [],
                )

                # Determine whether this ruleset applies to the
                # repository's default branch.
                applies_to_default_branch = False

                if not include_branches:
                    applies_to_default_branch = True

                if "~DEFAULT_BRANCH" in include_branches:
                    applies_to_default_branch = True

                if default_branch in include_branches:
                    applies_to_default_branch = True

                if default_branch in exclude_branches:
                    applies_to_default_branch = False

                if not applies_to_default_branch:
                    continue

                bypass_actors = ruleset_settings.get(
                    "bypass_actors",
                    [],
                )

                admin_bypass = False

                for actor in bypass_actors:
                    if actor.get("bypass_mode") not in ("always", "pull_request", "exempt"):
                        continue

                    admin_bypass = True
                    break

                if not admin_bypass:
                    admins_protected = True

                    sample.is_passing = True
                    sample.comments = (
                        "An active repository ruleset applies to the "
                        f"repository's default branch ({default_branch}) "
                        "and does not grant the repository administrator "
                        "role a bypass."
                    )
                    break

        if not admins_protected:
            sample.is_passing = False

            if not branch_protection and not rulesets:
                sample.comments = (
                    "No branch protection rules or repository rulesets "
                    "were identified."
                )
            else:
                sample.comments = (
                    "Administrators are not subject to the applicable "
                    f"branch protection requirements for the repository's "
                    f"default branch ({default_branch})."
                )

        test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message=(
            "Repositories did not require administrators to comply "
            "with branch protection requirements."
        ),
    )

    return test