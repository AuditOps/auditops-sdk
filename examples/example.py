import boto3, shutil, json, os
from auditops import (AWSCollector, AWSTester, EvidenceReader, EvidenceWriter, Uploader, Audit,
GitHubCollector, GitHubTester)
from dotenv import load_dotenv

def run_audit(collector, tester, report_name, writer):
    """Collect evidence, execute tests, and save the audit report."""
    collector.collect(writer)

    audit = Audit()
    audit.test_results = tester.run_tests()

    os.makedirs("tmp/reports", exist_ok=True)
    with open(f"tmp/reports/{report_name}.json", "w") as f:
        json.dump(audit.to_dict(), f, indent=4, default=str)

def main():
    load_dotenv()
    writer = EvidenceWriter()
    reader = EvidenceReader()

    # Run AWS Audit
    session = boto3.Session()
    run_audit(AWSCollector(session), AWSTester(reader), "aws_audit_report", writer)

    # Run GitHub Audit
    run_audit(
        GitHubCollector(os.getenv("github_token"), os.getenv("github_org_name")),
        GitHubTester(reader, os.getenv("github_org_name")),
        "github_audit_report", writer,
    )

    # Create zip file
    shutil.make_archive("audit_package", "zip", "tmp")

    # Upload evidence to audit portal
    uploader = Uploader("https://upload.auditops.io")
    #uploader.upload("audit_package.zip", "john.doe@client.com", "jane.doe@auditor.com")

if __name__ == "__main__":
    main()