from pathlib import Path
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
# Disables unnecessary AWS logs (ex. "New session created using local Boto3 credentials.""). 
logging.getLogger('botocore.credentials').setLevel(logging.WARNING)


class EvidenceWriter:
    def __init__(self, root_dir="tmp"):
        self.root_dir = Path(root_dir)

    def save_json(self, relative_path, data):
        if data:
            file_path = self.root_dir / relative_path

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("w") as f:
                json.dump(data, f, indent=4, default=str)