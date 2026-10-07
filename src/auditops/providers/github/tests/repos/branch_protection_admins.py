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
            "Administrators are subject to branch protection requirements.",
        ],
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
                    if (
                        actor.get("actor_type") == "RepositoryRole"
                        and actor.get("actor_id") == 5
                        and actor.get("bypass_mode") != "never"
                    ):
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