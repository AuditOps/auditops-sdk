import boto3, shutil, json, os
from auditops.core import (EvidenceReader, EvidenceWriter, Uploader, Audit, PDFReportBuilder, ExclusionManager)
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
from auditops.providers.github import GitHubCollector, GitHubTester
#from auditops.providers.google_workspace import GoogleWorkspaceCollector
from dotenv import load_dotenv

def run_audit(collector, tester, report_name, writer, report_builder, tool_name=None):
    """Collect evidence, execute tests, and save the audit report."""
    collector.collect(writer)

    audit = Audit(title=tool_name)
    audit.test_results = tester.run_tests()

    os.makedirs("tmp/reports", exist_ok=True)
    with open(f"tmp/reports/{report_name}.json", "w") as f:
        json.dump(audit.to_dict(), f, indent=4, default=str)
    # Build pdf report
    report_builder.build(audit,f"tmp/reports/{report_name}.pdf")

def main():
    load_dotenv()
    writer = EvidenceWriter()
    reader = EvidenceReader()
    exclusions = ExclusionManager.load_exclusions("exclusions.json")
    
    report_builder = PDFReportBuilder()

    # Run AWS Audit
    session = boto3.Session()
    aws_config = AWSConfig(in_scope_regions=['us-east-1', 'us-east-2'])
    # Update default settings
    aws_config.update(iam_minimum_password_length=12)
    """
    aws_audit = Audit(
        config=aws_config, reader=reader, writer=writer,
        exclusions=audit_exclusions
    )
    """
    """
    run_audit(
        AWSCollector(session, aws_config),
        AWSTester(reader, aws_config, exclusions),
        "aws_audit_report",
        writer,
        report_builder,
        tool_name = "AWS"
    )
    """

    # Run GitHub Audit
    run_audit(
        GitHubCollector(os.getenv("github_token"), os.getenv("github_org_name")),
        GitHubTester(reader, os.getenv("github_org_name"), exclusions),
        "github_audit_report", writer, report_builder, tool_name="GitHub"
    )

    """
    # Run Google Workspace Audit
    gw_admin_email = os.getenv("google_workspace_admin_email")
    GoogleWorkspaceCollector("credentials/google_credentials.json", gw_admin_email).collect(writer)
    """

    # Create zip file
    shutil.make_archive("audit_package", "zip", "tmp")

    # Upload evidence to audit portal
    uploader = Uploader("https://upload.auditops.io")
    #uploader.upload("audit_package.zip", "john.doe@client.com", "jane.doe@auditor.com")

if __name__ == "__main__":
    main()