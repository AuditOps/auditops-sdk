"""
    Test configuration supporting multiple providers (AWS, GitHub, etc.)
"""

from unittest.mock import Mock
import pytest


@pytest.fixture
def reader():
    return Mock()

@pytest.fixture
def load_evidence():  
    def _load_evidence(tester, evidence, *, missing_required=None):

        missing_required = set(missing_required or [])

        def read(path, optional=False):
            if path in missing_required:
                return None

            if optional:
                return evidence.get(path)

            return evidence[path]

        tester.read = Mock(side_effect=read)

    return _load_evidence