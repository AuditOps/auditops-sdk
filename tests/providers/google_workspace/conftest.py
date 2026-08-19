import pytest
from auditops.providers.google_workspace import GoogleWorkpaceTester


@pytest.fixture
def tester():
    return GoogleWorkpaceTester()