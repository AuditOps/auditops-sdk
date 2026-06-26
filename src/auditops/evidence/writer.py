from pathlib import Path
import json

class EvidenceWriter:
    def __init__(self, root_dir="tmp/audit_evidence"):
        self.root_dir = Path(root_dir)

    def save_json(self, tool_name, relative_path, data):
        file_path = self.root_dir / tool_name / relative_path

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w") as f:
            json.dump(data, f, indent=4, default=str)