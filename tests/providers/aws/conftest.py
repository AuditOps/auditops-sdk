import pytest

from auditops.providers.aws import AWSConfig, AWSTester


@pytest.fixture
def config():
    return AWSConfig(in_scope_regions=["us-east-1"])

@pytest.fixture
def tester(config):
    tester = AWSTester()
    tester.config = AWSConfig(in_scope_regions=['us-east-1'])

    return tester