from auditops.providers.github.tests.repos import check_branch_protection_rules
from utils.evidence import load_evidence


def test_pass_classic_branch_protection_requires_approval(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                }
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_classic_branch_protection_does_not_require_approval(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_pull_request_reviews": {
                    "required_approving_review_count": 0,
                }
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_pass_active_ruleset_requires_approval(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "rules": [
                    {
                        "type": "pull_request",
                        "parameters": {
                            "required_approving_review_count": 1,
                        },
                    }
                ]
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_inactive_ruleset_does_not_require_approval(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "disabled",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "rules": [
                    {
                        "type": "pull_request",
                        "parameters": {
                            "required_approving_review_count": 1,
                        },
                    }
                ]
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_ruleset_without_required_approval(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "rules": [
                    {
                        "type": "pull_request",
                        "parameters": {
                            "required_approving_review_count": 0,
                        },
                    }
                ]
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_no_branch_protection_or_rulesets(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False
    assert result.samples[0].comments == (
        "No branch protection rules or repository rulesets were identified."
    )


def test_pass_classic_branch_protection_takes_precedence(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_pull_request_reviews": {
                    "required_approving_review_count": 2,
                }
            },
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "rules": [
                    {
                        "type": "pull_request",
                        "parameters": {
                            "required_approving_review_count": 1,
                        },
                    }
                ]
            },
        },
    )

    result = check_branch_protection_rules(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == (
        "Classic branch protection requires at least 2 approved "
        "pull request review before changes can be merged."
    )