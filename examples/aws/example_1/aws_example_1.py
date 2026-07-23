"""
    Author: AJ Dehn (Creator of AuditOps)

    Simplest possible AWS example.
    - Use local credentials (through an access key).
    - No exclusions.
    - Scanning a single AWS region (us-east-1).
"""

from auditops.core.models import Audit, AuditHelpers
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
from auditops.core.utils import aws_create_session, run_audit

def main():
    session = aws_create_session()
    aws_config = AWSConfig(in_scope_regions=['us-east-1'])
    helpers = AuditHelpers.create()

    audit = Audit(helpers = helpers, title = "AWS Audit Report", config=aws_config,
    auditor_name = "AJ Dehn", evidence_folder = "aws")

    run_audit(audit, AWSCollector(session, audit), AWSTester(audit))

if __name__ == "__main__":
    main()