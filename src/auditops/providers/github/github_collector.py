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
            return all_data

        else:
            res = requests.get(github_url, headers=headers, params=params)
            if handle_404 and res.status_code == 404:
                return None
            res.raise_for_status()
            self.writer.save_json(f"{self.evidence_folder}/{evidence_path}", res.json())
            return res.json()

    def gather_evidence(self):
        # NOTE: Consider moving this to multiple collector files (similar to AWS) as this gets more complex.
        self._collect_org_settings()
        self._collect_repo_info()

    def _collect_org_settings(self):
        self._call_api("orgs/org_settings.json",
            f"https://api.github.com/orgs/{self.org_name}"
        )
    
    def _collect_repo_info(self):
        repos = self._call_api("orgs/repos.json",
            f"https://api.github.com/orgs/{self.org_name}/repos", paginate=True
        )

        for repo in repos:
            repo_name = repo["name"]
            # TODO: Make dynamic based on the name of the default branch.

            # Gather evidence for each repo's branch protection rules.
            url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/branches/main/protection"
            branch_protection_rules = self._call_api(f"repos/{repo_name}/branch_protection_rules.json", url, handle_404=True)

            # Gather evidence for each repo ruleset.
            url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/rulesets"
            rulesets = self._call_api(f"repos/{repo_name}/rulesets.json", url, handle_404=True)

            for rule in rulesets:
                rule_id = rule["id"]
                settings = self._call_api(
                    f"repos/{repo_name}/rulesets/{rule_id}.json",
                    f"https://api.github.com/repos/{self.org_name}/{repo_name}/rulesets/{rule_id}"
                )