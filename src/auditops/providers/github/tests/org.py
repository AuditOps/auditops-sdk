from auditops.core.models import Sample
from auditops.core.utils import create_test, fail_test


def run_org_tests(tester):
    return [
        test_org_mfa_settings(tester),
        test_org_members_create_public_resources(tester)
    ]


def test_org_mfa_settings(tester):
    metadata = {
        "test_id": "github-org-001",
        "test_description": "The GitHub organization settings require users to enable MFA.",
        "risk_rating": 2,
        "test_attributes": [
            "'two_factor_requirement_enabled' is set to true."
        ],
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{tester.github_org_name}.",
            "Saved the GitHub organization settings: org_settings.json.",
            "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
        ]
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("organization/settings.json")
    test.is_passing = org_settings.get("two_factor_requirement_enabled")
    
    return test


def test_org_members_create_public_resources(tester):
    metadata = {
        "test_id": "github-org-002",
        "test_description": "The GitHub organization settings prevent members from creating public resources.",
        "risk_rating": 0,
        "test_procedures": [
            f"Obtained the GitHub organization settings by calling: https://api.github.com/orgs/{tester.github_org_name}.",
            "Saved the GitHub organization settings: org_settings.json.",
            "Inspected the organization settings to determine if they comply with the test attribute(s) defined below."        
        ],          
        "test_attributes": [
            "'members_can_create_public_repositories' in org_settings.json is set to false.",
            "'members_can_create_public_pages' in org_settings.json is set to false."
        ]
    }

    test = create_test(tester, metadata)
    org_settings = tester.read("organization/settings.json")
    test.is_passing = (
        not org_settings.get("members_can_create_public_repositories", True)
        and not org_settings.get("members_can_create_public_pages", True)
    )        
    
    return test