import boto3, shutil, json, os
from auditops.core import (EvidenceReader, EvidenceWriter, Uploader, PDFReportBuilder, ExclusionManager)
from auditops.core.models import AuditContext, AuditHelpers
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
from auditops.core.utils import aws_create_session, run_audit
from dotenv import load_dotenv

"""
    Author: AJ Dehn (Creator of AuditOps)

    Example of a more complex AWS environment.
    - Scans multiple AWS accounts (Ex. US prod & EU prod)
    - Uses IAM roles (assumed through local credentials)
    - Updates configuration (US Prod: Changes minimum password length)
    - Adds exclusions (US Prod: Adds one test exclusion and one sample exclusion)
"""


def main():
    load_dotenv()

    helpers = AuditHelpers.create()

    # Create session using an IAM role.
    us_prod_session = aws_create_session(role_arn=os.getenv("aws_us_prod_role_arn"), external_id=os.getenv("aws_us_prod_external_id"))

    # Create AWS configuration and decrease min. password length from 14 -> 12 characters
    us_prod_aws_config = AWSConfig(in_scope_regions=['us-east-1', 'us-east-2'])
    us_prod_aws_config.update(iam_minimum_password_length=12)
    
    aws_us_prod_context = AuditContext(provider="aws", helpers=helpers, config=us_prod_aws_config, evidence_folder="aws/us_prod", 
        report_name="aws_us_prod", auditor_name="AJ Dehn", delete_cached_evidence = False, summary_mode = True,)

    run_audit(
        AWSCollector(us_prod_session, aws_us_prod_context),
        AWSTester(aws_us_prod_context),
        aws_us_prod_context
    )

    # Audit AWS Account (EU Prod)
    eu_prod_session = aws_create_session(role_arn=os.getenv("aws_eu_prod_role_arn"), external_id=os.getenv("aws_eu_prod_external_id"))
    eu_prod_aws_config = AWSConfig(in_scope_regions=['eu-west-1'])
    aws_eu_prod_context = AuditContext(provider="aws", helpers=helpers, config=us_prod_aws_config, evidence_folder="aws/eu_prod", 
        report_name="aws_eu_prod", auditor_name="AJ Dehn",)

    # Decrease minimum password length requirements from 14 -> 12 characters
    eu_prod_aws_config.update(iam_minimum_password_length=12)

    run_audit(
        AWSCollector(eu_prod_session, aws_eu_prod_context),
        AWSTester(aws_eu_prod_context),
        aws_eu_prod_context
    )

    github_context = AuditContext(provider="github", helpers=helpers, evidence_folder="github",
        report_name="github_audit_report", auditor_name="AJ Dehn", delete_cached_evidence = False,
    )

    # Run GitHub Audit
    run_audit(
        GitHubCollector(os.getenv("github_token"), os.getenv("github_org_name"), github_context),
        GitHubTester(os.getenv("github_org_name"), github_context),
        github_context
    )

    # Create zip file
    shutil.make_archive("audit_package", "zip", "tmp")

    # Upload evidence to audit portal
    # uploader = Uploader("https://upload.auditops.io")
    # uploader.upload("audit_package.zip", "john.doe@client.com", "jane.doe@auditor.com")

if __name__ == "__main__":
    main()