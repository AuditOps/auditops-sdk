from pathlib import Path
import json

class EvidenceReader:
    def __init__(self, root_dir="tmp/audit_evidence"):
        self.root_dir = Path(root_dir)

    def _path(self, provider, relative_path):
        return self.root_dir / provider / relative_path

    def read_json(self, provider, relative_path, optional_file=False):
        """
        Read a JSON evidence file.

        Args:
            provider: Evidence provider (aws, github, google_workspace).
            relative_path: Path relative to the provider directory.
            optional_file: Return None instead of raising if the file is missing.
        """
        path = self._path(provider, relative_path)

        if not path.exists():
            if optional_file:
                return None
            
            raise FileNotFoundError(f"Missing required evidence: {provider}/{relative_path}")

        with path.open() as f:
            return json.load(f)