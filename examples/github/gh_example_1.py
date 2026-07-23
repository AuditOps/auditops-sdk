"""
    Author: AJ Dehn (Creator of AuditOps)

    Simplest possible GitHub example.
    - No exclusions.
"""

import os
from auditops.core.models import Audit, AuditHelpers
from auditops.providers.github import GitHubCollector, GitHubTester
from auditops.core.utils import run_audit
from dotenv import load_dotenv

def main():
    load_dotenv()

    helpers = AuditHelpers.create()

    audit = Audit(helpers = helpers, title = "GitHub Audit Report", auditor_name = "AJ Dehn", evidence_folder = "github")

    run_audit(
        audit,
        GitHubCollector(os.getenv("github_token"), os.getenv("github_org_name"), audit),
        GitHubTester(os.getenv("github_org_name"), audit)
    )


if __name__ == "__main__":
    main()