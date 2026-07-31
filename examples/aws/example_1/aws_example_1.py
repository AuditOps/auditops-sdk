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
import boto3
from datetime import datetime

def main():
    session = aws_create_session()
    aws_config = AWSConfig(in_scope_regions=['us-east-1'])
    helpers = AuditHelpers.create()

    # NOTE: Setting summary_mode to 'True' will anonymize the sample ID's in the PDF & JSON reports (ex. "Sample 1", "Sample 2", "Sample 3").
    # NOTE: Setting delete_cached_evidence to 'True' will allow you re-run the scan using previously collected evidence.
    audit = Audit(helpers = helpers, title = "AWS Audit Report", config=aws_config, auditor_name = "AJ Dehn",
    audit_folder = "aws/us_prod_2", delete_cached_evidence=False, summary_mode=True, exclusions=None)

    audit.run(collector=AWSCollector(session), tester=AWSTester())

    # Upload to AuditOps (for vendor due diligence and/or audit requests)
    audit.upload(destination="auditops", package="json", client_email="aj@auditops.io")

    # Upload to an auditor's portal. NOTE: Please replace the "upload_url".
    #audit.upload(destination="portal", package="pdf", upload_url="https://upload.auditops.io", client_email="aj@auditops.io")

    # Upload to S3 (for data retention)
    bucket_save_path = datetime.now().strftime("%Y/%m/%d/aws")
    #audit.upload(destination="s3", package="full", client=boto3.client("s3"), bucket="bad-bucket-54321", key=bucket_save_path)

if __name__ == "__main__":
    main()