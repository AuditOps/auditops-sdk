import boto3, shutil
from auditops import AWSCollector, EvidenceWriter, Uploader

session = boto3.Session()
writer = EvidenceWriter()
collector = AWSCollector(session)
collector.collect(writer)

# Create zip file
shutil.make_archive("audit_evidence", "zip", "audit_evidence")

# Upload evidence to audit portal
uploader = Uploader("https://upload.auditops.io")
#uploader.upload("audit_evidence.zip", "john.doe@client.com", "jane.doe@auditor.com")