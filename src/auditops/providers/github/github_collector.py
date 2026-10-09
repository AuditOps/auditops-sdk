import requests
from datetime import datetime, timedelta, timezone

class GitHubCollector:
    def __init__(self, token, org_name):
        if not token or not org_name:
            raise ValueError("Token and org_name are required.")
        
        if not isinstance(token, str) or not isinstance(org_name, str):
            raise TypeError("Token and org_name must be strings.")

        self.token = token
        self.org_name = org_name

        self.audit_folder = None
        self.writer = None
        self.reader = None

    def gather_evidence(self, audit):
        self.audit_folder = audit.audit_folder
        self.writer = audit.writer
        self.reader = audit.reader

        # NOTE: Consider moving this to multiple collector files (similar to AWS) as this gets more complex.
        self._collect_org_settings()
        self._collect_repo_info()
        self._collect_access_info()
        self._collect_branch_protection_bypasses()

    def _call_api(self, evidence_path, github_url, params=None, paginate=False, handle_404=False):
        # Check if evidence already exists
        evidence = self.reader.read_json(f"{self.audit_folder}/audit_evidence/{evidence_path}", optional=True)

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
            self.writer.save_json(f"{self.audit_folder}/audit_evidence/{evidence_path}", all_data)
            return all_data

        else:
            res = requests.get(github_url, headers=headers, params=params)
            if handle_404 and res.status_code == 404:
                return None
            res.raise_for_status()
            self.writer.save_json(f"{self.audit_folder}/audit_evidence/{evidence_path}", res.json())
            return res.json()

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
            default_branch = repo["default_branch"]

            # Gather evidence for each repo's branch protection rules.
            url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/branches/{default_branch}/protection"
            branch_protection_rules = self._call_api(f"repos/{repo_name}/branch_protection_rules.json", url, handle_404=True)

            url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/branches/{default_branch}/protection/restrictions"
            branch_protection_rules = self._call_api(f"repos/{repo_name}/bp_restrictions.json", url, handle_404=True)

            # Gather evidence for each repo ruleset.
            url = f"https://api.github.com/repos/{self.org_name}/{repo_name}/rulesets"
            rulesets = self._call_api(f"repos/{repo_name}/rulesets.json", url, handle_404=True)

            for rule in rulesets:
                rule_id = rule["id"]
                settings = self._call_api(
                    f"repos/{repo_name}/rulesets/{rule_id}.json",
                    f"https://api.github.com/repos/{self.org_name}/{repo_name}/rulesets/{rule_id}"
                )

    def _collect_branch_protection_bypasses(self, look_back_days = 90):
        """
        Collect GitHub organization audit-log events related to
        branch protection and ruleset bypasses from the last 90 days.

        NOTE: These logs are only available for clients on the "Enterprise" plan. 
        """

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=90)

        # GitHub audit-log search syntax.
        events = self._call_api(
            "audit/branch_protection_bypasses.json",
            f"https://api.github.com/orgs/{self.org_name}/audit-log",
            params = {
                "phrase": "action:protected_branch.policy_override",
                "per_page": 10,
            },
            paginate=False,
            handle_404=True,
        )

        return events

    def _collect_access_info(self):
        """
        Collect GitHub organization users, administrators, teams,
        outside collaborators, and repository access.
        """

        # ---------------------------------------------------------
        # Organization members
        # ---------------------------------------------------------

        members = self._call_api(
            "orgs/members.json",
            f"https://api.github.com/orgs/{self.org_name}/members",
            params={"role": "all"},
            paginate=True,
        )

        # Organization owners/admins
        admins = self._call_api(
            "orgs/admins.json",
            f"https://api.github.com/orgs/{self.org_name}/members",
            params={"role": "admin"},
            paginate=True,
        )

        # ---------------------------------------------------------
        # Outside collaborators
        # ---------------------------------------------------------

        outside_collaborators = self._call_api(
            "orgs/outside_collaborators.json",
            f"https://api.github.com/orgs/{self.org_name}/outside_collaborators",
            paginate=True,
        )

        # ---------------------------------------------------------
        # Teams
        # ---------------------------------------------------------

        teams = self._call_api(
            "orgs/teams.json",
            f"https://api.github.com/orgs/{self.org_name}/teams",
            paginate=True,
        )

        for team in teams:
            team_slug = team["slug"]

            # Team members
            self._call_api(
                f"orgs/teams/{team_slug}/members.json",
                f"https://api.github.com/orgs/{self.org_name}/teams/{team_slug}/members",
                paginate=True,
            )

            # Repositories assigned to team
            self._call_api(
                f"teams/{team_slug}/repositories.json",
                f"https://api.github.com/orgs/{self.org_name}/teams/{team_slug}/repos",
                paginate=True,
            )

        # ---------------------------------------------------------
        # Repository access
        # ---------------------------------------------------------

        repos = self._call_api(
            "orgs/repos.json",
            f"https://api.github.com/orgs/{self.org_name}/repos",
            paginate=True,
        )

        for repo in repos:
            repo_name = repo["name"]

            # This is extremely useful for auditing because GitHub
            # calculates the effective permission from all sources:
            # direct repo access, teams, organization permissions,
            # and enterprise permissions.
            self._call_api(
                f"repos/{repo_name}/collaborators.json",
                f"https://api.github.com/repos/"
                f"{self.org_name}/{repo_name}/collaborators",
                paginate=True,
            )