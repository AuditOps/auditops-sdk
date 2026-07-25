import requests
from pathlib import Path
from auditops.core.utils import delete_evidence_folder


class GitHubCollector:
    def __init__(self, token, org_name, audit):
        self.token = token
        self.org_name = org_name
        self.evidence_folder = audit.evidence_folder
        self.writer = audit.writer
        self.reader = audit.reader

    def _call_api(self, evidence_path, github_url, params=None, paginate=False, handle_404=False):
        # Check if evidence already exists
        evidence = self.reader.read_json(f"{self.evidence_folder}/{evidence_path}", optional=True)

        if evidence is not None:
            # Return cached evidence. 
            return evidence

        headers = {"Authorization": f"token {self.token}"}

        if paginate:
            all_data = []
            page = 1
            while True:
                page_params = params.copy() if params else {}
                page_params.update({"per_page": 100, "page": page})
                res = requests.get(github_url, headers=headers, params=page_params)
                
                if handle_404 and res.status_code == 404:
                    return None
                res.raise_for_status()

                page_data = res.json()
                if not page_data:
                    break

                all_data.extend(page_data)
                page += 1
            self.writer.save_json(f"{self.evidence_folder}/{evidence_path}", all_data)

        else:
            res = requests.get(github_url, headers=headers, params=params)
            if handle_404 and res.status_code == 404:
                return None
            res.raise_for_status()
            self.writer.save_json(f"{self.evidence_folder}/{evidence_path}", res.json())

    def gather_evidence(self):
        # NOTE: Consider moving this to multiple collector files (similar to AWS) as this gets more complex.
        self._collect_org_settings()
        self._collect_repo_info()

    def _collect_org_settings(self):
        self._call_api("orgs/org_settings.json",
            f"https://api.github.com/orgs/{self.org_name}"
        )
    
    def _collect_repo_info(self):
        self._call_api("orgs/repos.json",
            f"https://api.github.com/orgs/{self.org_name}/repos", paginate=True
        )