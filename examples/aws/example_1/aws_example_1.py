"""
    Author: AJ Dehn (Creator of AuditOps)

    Simplest possible AWS example.
    - Use local credentials (through an access key).
    - No exclusions.
    - Scanning a single AWS region (us-east-1).
"""

from auditops.core.models import Audit, AuditHelpers
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
from auditops.core.utils import aws_create_session

def main():
    session = aws_create_session()
    aws_config = AWSConfig(in_scope_regions=['us-east-1'])
    helpers = AuditHelpers.create()

    # NOTE: Setting summary_mode to 'True' will anonymize the sample ID's in the PDF & JSON reports (ex. "Sample 1", "Sample 2", "Sample 3").
    # NOTE: Setting delete_cached_evidence to 'True' will allow you to use previously collected evidence.
    audit = Audit(helpers = helpers, title = "AWS Audit Report", config=aws_config, auditor_name = "AJ Dehn",
    evidence_folder = "aws", delete_cached_evidence=False, summary_mode=True, exclusions=None)

    audit.run(collector=AWSCollector(session), tester=AWSTester())

    """
    audit.collect(collector=AWSCollector(session))
    audit.perform_testing(tester=AWSTester())
    audit.save_reports()
    """

    #run_audit(audit, , AWSTester(audit))

if __name__ == "__main__":
    main()