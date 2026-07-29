"""
    Author: AJ Dehn (Creator of AuditOps)

    Example of a more complex AWS environment.
    - Updates configuration (US Prod: Changes minimum password length)
    - Adds exclusions (Adds one test exclusion and one sample exclusion)
"""

from auditops.core import ExclusionManager, Audit, AuditHelpers
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
from auditops.core.utils import aws_create_session
from dotenv import load_dotenv


def main():
    load_dotenv()
    helpers = AuditHelpers.create()

    # Create session using an IAM role.
    # us_prod_session = aws_create_session(role_arn=os.getenv("aws_us_prod_role_arn"), external_id=os.getenv("aws_us_prod_external_id"))
    us_prod_session = aws_create_session()

    # Create AWS configuration. Set minimum password length to 12 characters.
    us_prod_aws_config = AWSConfig(in_scope_regions=['us-east-1', 'us-east-2'], iam_minimum_password_length=12)
    
    # Load exclusions from 'aws_exclusions.json'
    aws_exclusions = ExclusionManager.load_exclusions("aws_exclusions.json")

    audit = Audit(helpers = helpers, title = "AWS Audit Report (US Prod)", auditor_name = "AJ Dehn", config = us_prod_aws_config,
    evidence_folder = "aws/us_prod", exclusions = aws_exclusions, delete_cached_evidence = False, summary_mode = True)

    audit.run(collector=AWSCollector(us_prod_session), tester=AWSTester())

if __name__ == "__main__":
    main()