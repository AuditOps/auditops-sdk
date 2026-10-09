from auditops.providers.github.tests.repos import check_branch_protection_admins
from utils.evidence import load_evidence


def test_pass_classic_branch_protection_enforces_admins(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "enforce_admins": {
                    "enabled": True,
                }
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_classic_branch_protection_does_not_enforce_admins(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "enforce_admins": {
                    "enabled": False,
                }
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_pass_active_ruleset_protects_admins(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "conditions": {
                    "ref_name": {
                        "include": [
                            "~DEFAULT_BRANCH",
                        ],
                        "exclude": [],
                    }
                },
                "bypass_actors": [],
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_active_ruleset_allows_admin_bypass(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "conditions": {
                    "ref_name": {
                        "include": [
                            "~DEFAULT_BRANCH",
                        ],
                        "exclude": [],
                    }
                },
                "bypass_actors": [
                    {
                        "actor_type": "RepositoryRole",
                        "actor_id": 5,
                        "bypass_mode": "always",
                    }
                ],
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_ruleset_does_not_apply_to_default_branch(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "conditions": {
                    "ref_name": {
                        "include": [
                            "develop",
                        ],
                        "exclude": [],
                    }
                },
                "bypass_actors": [],
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_ruleset_excludes_default_branch(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "conditions": {
                    "ref_name": {
                        "include": [
                            "~DEFAULT_BRANCH",
                        ],
                        "exclude": [
                            "main",
                        ],
                    }
                },
                "bypass_actors": [],
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_no_branch_protection_or_rulesets(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False
    assert result.samples[0].comments == (
        "No branch protection rules or repository rulesets were identified."
    )

def test_pass_ruleset_admin_bypass_mode_never(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "default_branch": "main",
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
            "repos/test-repo/rulesets/123.json": {
                "conditions": {
                    "ref_name": {
                        "include": [
                            "~DEFAULT_BRANCH",
                        ],
                        "exclude": [],
                    }
                },
                "bypass_actors": [
                    {
                        "actor_type": "RepositoryRole",
                        "actor_id": 5,
                        "bypass_mode": "never",
                    }
                ],
            },
        },
    )

    result = check_branch_protection_admins(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True