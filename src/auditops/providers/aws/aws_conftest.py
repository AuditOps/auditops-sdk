import pytest
from unittest.mock import Mock

from auditops.testing.aws.config import AWSConfig

@pytest.fixture
def config():
    return AWSConfig(
        in_scope_regions=["us-east-1"]
    )

@pytest.fixture
def reader():
    return Mock()