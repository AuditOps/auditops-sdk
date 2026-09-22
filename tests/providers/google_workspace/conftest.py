import pytest
from auditops.providers.google_workspace import GoogleWorkspaceTester, GoogleWorkspaceConfig

@pytest.fixture
def tester():
    tester = GoogleWorkspaceTester()
    gw_config = GoogleWorkspaceConfig()
    gw_config.required_group_emails = ["required@example.com"]

    tester.config = gw_config

    return tester