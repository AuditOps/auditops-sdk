from pathlib import Path
import json

class EvidenceReader:
    def __init__(self, root_dir="tmp/audit_evidence"):
        self.root_dir = Path(root_dir)

    def _path(self, provider, relative_path):
        return self.root_dir / provider / relative_path

    def read_json(self, provider, relative_path):
        path = self._path(provider, relative_path)

        if not path.exists():
            return None

        with path.open() as f:
            return json.load(f)