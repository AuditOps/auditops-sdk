import pytest
from auditops.providers.github import GitHubTester


@pytest.fixture
def tester():
    return GitHubTester()