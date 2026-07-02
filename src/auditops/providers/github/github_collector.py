import requests

class GitHubCollector:
    def __init__(self, token, org_name, writer):
        self.token = token
        self.org_name = org_name
        self.writer = writer

    def _call_api(self, relative_path, github_url, params=None, paginate=False, handle_404=False):
        # Return cached evidence if it exists
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
            self.writer.save_json("github", relative_path, all_data)

        else:
            res = requests.get(github_url, headers=headers, params=params)
            if handle_404 and res.status_code == 404:
                return None
            res.raise_for_status()
            self.writer.save_json("github", relative_path, res.json())

    def collect(self):
        self._collect_org_settings()
        self._collect_repo_info()

    def _collect_org_settings(self):
        self._call_api("organization/settings.json",
            f"https://api.github.com/orgs/{self.org_name}"
        )
    
    def _collect_repo_info(self):
        self._call_api("organization/all_repos.json",
            f"https://api.github.com/orgs/{self.org_name}/repos", paginate=True
        )