"""
    Author: AJ Dehn (Creator of AuditOps)

    Simplest possible GitHub example.
    - No exclusions.
"""

import os
from auditops.core.models import Audit, AuditHelpers
from auditops.providers.github import GitHubCollector, GitHubTester
from dotenv import load_dotenv

def main():
    load_dotenv()

    helpers = AuditHelpers.create()

    # NOTE: Setting summary_mode to 'True' will anonymize the sample ID's in the PDF report (ex. "Sample 1", "Sample 2", "Sample 3").
    # NOTE: Setting delete_cached_evidence to 'True' will allow you to use previously collected evidence.
    audit = Audit(helpers = helpers, title = "GitHub Audit Report", auditor_name = "AJ Dehn", evidence_folder = "github",
    summary_mode = False, delete_cached_evidence= True)

    audit.run(
        collector=GitHubCollector(os.getenv("github_token"), os.getenv("github_org_name")),
        tester=GitHubTester()
    )

if __name__ == "__main__":
    main()