from unittest.mock import Mock


def load_evidence(tester, evidence, *, missing_required=None):

    missing_required = set(missing_required or [])

    def read(path, optional=False):
        if path in missing_required:
            return None

        if optional:
            return evidence.get(path)

        return evidence[path]

    tester.read = Mock(side_effect=read)