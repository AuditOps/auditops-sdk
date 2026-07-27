from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def check_branch_protection_rules(tester):
    metadata = {
        "test_id": "github-repo-002",
        "test_description": "Repositories are configured to require an approval before the change is merged.",
        "risk_rating": 3,
        "table_headers": ["Repository Name", "Conclusion", "Comments"],
        "test_procedures": [
            f"Obtained a list of all repositories by calling: https://api.github.com/orgs/[org_name]/repos.",
            "Saved the list of all repositories: orgs/repos.json.",
            "Obtained the branch protection rules from each repository by calling: https://api.github.com/repos/[org_name]/[repo_name]/branches/main/protection",
            "Saved the branch protection rules: repos/[repo_name]/branch_protection_rules.json.",
            "Obtained the rulesets from each repository by calling: https://api.github.com/repos/[org_name]/[repo_name]/rulesets",
            "Saved the rulesets: repos/[repo_name]/rulesets.json.",
            "Inspected each repository to determine if it was compliant with the test attributes below."
            "Obtained the settings for each repository ruleset by calling: https://api.github.com/repos/[org_name]/[repo_name]/rulesets/[rule_id]",
            "Saved the settings from each ruleset: repos/[repo_name]/rulesets/[rule_id].json.",       
        ],
        "test_attributes": [
            "An active branch protection rule or repository ruleset is enforced.",
            "Pull requests require at least one approval before merging.",
            "No unauthorized users, teams, roles, or applications may bypass pull request requirements.",
            "Administrators are subject to branch protection requirements.",
            "Direct pushes to protected branches are prevented."
        ]        
    }

    test = create_test(tester, metadata)

    repos = tester.read("orgs/repos.json")
    for repo in repos:
        repo_name = repo["name"]
        # TODO: Make dynamic based on the name of the default branch.
        branch_protection = tester.read(
            f"repos/{repo_name}/branch_protection_rules.json",
            optional=True,
        )

        repo_rulesets = tester.read(f"repos/{repo_name}/rulesets.json", optional=True) or []

        detailed_rulesets = []

        for rule in repo_rulesets:
            ruleset_settings = tester.read(f"repos/{repo_name}/rulesets/{rule["id"]}.json")
            if ruleset_settings:
                detailed_rulesets.append(ruleset_settings)

        sample = Sample(
            sample_id={"repo_name": repo_name}
        )

        sample = evaluate_branch_protection_rules(sample, branch_protection, detailed_rulesets)

        test.samples.append(sample)
    
    test.evaluate_samples(tester.exclusions, failure_message="repositories did not have branch protection enabled.")
    
    return test

def evaluate_branch_protection_rules(sample, branch_protection, detailed_rulesets):
    has_any_protection = False
    requires_approval = False
    admins_protected = False
    allows_direct_push = False
    bypass_actors = []

    # ---------------------------
    # 1. Evaluate classic branch protection
    # ---------------------------
    if branch_protection:
        has_any_protection = True

        # PR approval requirements
        required_reviews = branch_protection.get(
            "required_pull_request_reviews"
        )

        if required_reviews:
            if required_reviews.get(
                "required_approving_review_count", 0
            ) >= 1:
                requires_approval = True

        # Admin enforcement
        admins = branch_protection.get("enforce_admins", {})
        admins_protected = admins.get("enabled", False)

        # Direct push restrictions
        restrictions = branch_protection.get("restrictions")

        # If restrictions are None, users with push permissions may push
        if restrictions is None:
            allows_direct_push = True

    # ---------------------------
    # 2. Evaluate repository rulesets
    # ---------------------------
    for ruleset in detailed_rulesets or []:

        if ruleset.get("enforcement") != "active":
            continue

        has_any_protection = True

        # Repository rulesets protect admins by default
        admins_protected = True

        for rule in ruleset.get("rules", []):
            rule_type = rule.get("type")
            params = rule.get("parameters", {})

            if rule_type == "pull_request":
                if params.get(
                    "required_approving_review_count", 0
                ) >= 1:
                    requires_approval = True

            if rule_type == "update":
                allows_direct_push = True


        # ---------------------------
        # Evaluate ruleset bypass actors
        # ---------------------------
        for actor in ruleset.get("bypass_actors", []):

            mode = actor.get("bypass_mode")

            if mode and mode != "never":

                actor_type = actor.get("actor_type")
                actor_id = actor.get("actor_id")

                bypass_actors.append(
                    f"{actor_type}:{actor_id} ({mode})"
                )

                # Repository admins bypassing protections
                if (
                    actor_type == "RepositoryRole"
                    and actor_id in [1, 2, 5]
                ):
                    admins_protected = False


    # ---------------------------
    # 2. Evaluate repository rulesets (new GitHub model)
    # ---------------------------
    for ruleset in detailed_rulesets or []:

        if ruleset.get("enforcement") != "active":
            continue

        has_any_protection = True

        # ---------------------------
        # PR approval requirements
        # ---------------------------
        for rule in ruleset.get("rules", []):

            rule_type = rule.get("type")
            params = rule.get("parameters", {})

            if rule_type == "pull_request":

                if params.get(
                    "required_approving_review_count", 0
                ) >= 1:
                    requires_approval = True


            # Direct push protection
            if rule_type == "update":
                allows_direct_push = True

        # ---------------------------
        # Ruleset bypass actors
        # ---------------------------
        for actor in ruleset.get("bypass_actors", []):

            mode = actor.get("bypass_mode")

            # "never" means no bypass allowed
            if mode and mode != "never":

                actor_type = actor.get("actor_type")
                actor_id = actor.get("actor_id")

                bypass_actors.append(
                    f"{actor_type}:{actor_id} ({mode})"
                )


    # ---------------------------
    # 3. Evaluate compliance
    # ---------------------------
    issues = []

    if not has_any_protection:
        issues.append(
            "No branch protection rules or active rulesets configured"
        )

    if not requires_approval:
        issues.append(
            "Pull request approvals are not required"
        )

    if not admins_protected:
        issues.append(
            "Administrators may bypass branch protection"
        )

    if allows_direct_push:
        issues.append(
            "Direct pushes may be permitted"
        )

    if bypass_actors:
        issues.append(
            "Bypass actors configured: "
            + ", ".join(bypass_actors)
        )


    # ---------------------------
    # 4. Set final result
    # ---------------------------
    if issues:
        sample.is_passing = False
        sample.comments = ". ".join(issues)

    else:
        sample.is_passing = True
        sample.comments = (
            "Branch protection requires PR approval "
            "and no bypass exceptions were identified"
        )

    return sample