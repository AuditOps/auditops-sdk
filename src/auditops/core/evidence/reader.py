from pathlib import Path
import json


class EvidenceReader:
    def __init__(self, root_dir="tmp"):
        self.root_dir = Path(root_dir)
        self.evidence_dir = self.root_dir / "audit_evidence"

    def _path(self, relative_path):
        return self.evidence_dir / relative_path

    def read_json(self, relative_path, optional=False):
        """
        Read a JSON evidence file.

        Args:
            relative_path: Path relative from the audit's evidence folder.
            optional: Return None instead of raising if the file is missing.
        """
        path = self._path(relative_path)

        if not path.exists():
            if optional:
                return None
            
            raise FileNotFoundError(f"Missing required evidence: {relative_path}")

        with path.open() as f:
            return json.load(f)