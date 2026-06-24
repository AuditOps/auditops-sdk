import boto3

from auditops import AWSCollector, EvidenceWriter

session = boto3.Session()
writer = EvidenceWriter()

collector = AWSCollector(session)
collector.collect(writer)