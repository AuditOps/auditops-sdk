from auditops.providers.github.tests.repos import check_required_status_checks
from utils.evidence import load_evidence


def test_pass_classic_branch_protection_requires_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_status_checks": {
                    "contexts": ["ci/test"],
                    "checks": [],
                }
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_classic_branch_protection_without_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_status_checks": {
                    "contexts": [],
                    "checks": [],
                }
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_pass_classic_branch_protection_with_multiple_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_status_checks": {
                    "contexts": [
                        "ci/test",
                        "security/scan",
                    ],
                    "checks": [
                        {
                            "context": "build",
                        }
                    ],
                }
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_pass_active_ruleset_requires_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
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
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {
                                    "context": "ci/test",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_inactive_ruleset_requires_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
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
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {
                                    "context": "ci/test",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_active_ruleset_without_required_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
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
                        "parameters": {},
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_fail_active_ruleset_with_empty_required_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
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
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [],
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


def test_pass_one_of_multiple_active_rulesets_requires_status_checks(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                },
                {
                    "id": 456,
                    "enforcement": "active",
                },
            ],
            "repos/test-repo/rulesets/123.json": {
                "rules": [
                    {
                        "type": "pull_request",
                        "parameters": {},
                    }
                ]
            },
            "repos/test-repo/rulesets/456.json": {
                "rules": [
                    {
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {
                                    "context": "ci/test",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_pass_classic_branch_protection_takes_precedence(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_status_checks": {
                    "contexts": ["ci/test"],
                    "checks": [],
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
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {
                                    "context": "security/scan",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_pass_active_ruleset_when_classic_branch_protection_has_no_checks(
    tester,
):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/branch_protection_rules.json": {
                "required_status_checks": {
                    "contexts": [],
                    "checks": [],
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
                        "type": "required_status_checks",
                        "parameters": {
                            "required_status_checks": [
                                {
                                    "context": "ci/test",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True


def test_fail_no_branch_protection_or_rulesets(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False
    assert result.samples[0].comments == (
        "No branch protection rules or repository rulesets were identified."
    )


def test_fail_active_ruleset_missing_configuration(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": False,
                }
            ],
            "repos/test-repo/rulesets.json": [
                {
                    "id": 123,
                    "enforcement": "active",
                }
            ],
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert result.samples[0].is_passing is False


# Archived repository tests

def test_pass_archived_repository(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "test-repo",
                    "archived": True,
                }
            ],
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is True
    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == (
        "This repository is archived; status check testing is not applicable."
    )


def test_archived_repository_excluded_from_testing(tester):
    load_evidence(
        tester,
        {
            "orgs/repos.json": [
                {
                    "name": "archived-repo",
                    "archived": True,
                },
                {
                    "name": "active-repo",
                    "archived": False,
                },
            ],
        },
    )

    result = check_required_status_checks(tester)

    assert result.is_passing is False
    assert len(result.samples) == 2

    assert result.samples[0].is_passing is True
    assert result.samples[0].comments == (
        "This repository is archived; status check testing is not applicable."
    )

    assert result.samples[1].is_passing is False