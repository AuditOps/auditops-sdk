from datetime import datetime, timezone
from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .aws_config import AWSConfig

# Import test logic
from .tests.iam import (check_iam_root_access_key, check_iam_root_mfa, 
    check_iam_user_mfa, check_iam_user_access_key_age, check_iam_password_policy)
from .tests.rds import (check_rds_encryption, check_rds_auto_minor_version_upgrade, check_rds_backup_retention, 
    check_rds_deletion_protection, check_rds_encryption, check_rds_public_access, check_rds_tags)
from .tests.cloudtrail import (check_cloudtrail_multi_region)
from .tests.guardduty import (check_guardduty_enabled)
from .tests.ebs import (check_ebs_default_encryption, check_ebs_volume_encryption, check_ebs_volume_tags)
from .tests.ec2 import (check_ec2_instance_tags, check_ec2_security_group_tags)
from .tests.s3 import (check_s3_encryption, check_s3_public_access, check_s3_secure_transport, check_s3_tags)
# NOTE: Named this 'lmbda' to avoid conflicts with python 'lambda' functionality.
from .tests.lmbda import (check_lambda_tags)


class AWSTester:
    def __init__(self, context):
        self.report_title = "AWS Audit Report"          # Used when building the PDF.
        self.provider = context.provider                # Used when searching for exclusions.
        self.reader = context.reader
        self.config = context.config
        self.exclusions = context.exclusions
        self.evidence_folder = context.evidence_folder


    AWS_TESTS = [
        # IAM
        check_iam_root_access_key,
        check_iam_root_mfa,
        check_iam_user_mfa,
        check_iam_user_access_key_age,
        check_iam_password_policy,

        # S3
        check_s3_encryption,
        check_s3_public_access,
        check_s3_secure_transport,
        check_s3_tags,

        # EC2
        check_ec2_instance_tags,
        check_ec2_security_group_tags,

        # EBS
        check_ebs_default_encryption,
        check_ebs_volume_encryption,
        check_ebs_volume_tags,

        # RDS
        check_rds_encryption,
        check_rds_auto_minor_version_upgrade,
        check_rds_backup_retention,
        check_rds_deletion_protection,
        check_rds_public_access,
        check_rds_tags,

        # CloudTrail
        check_cloudtrail_multi_region,

        # GuardDuty
        check_guardduty_enabled,

        # Lambda
        check_lambda_tags,
    ]

    def get_scope(self):
        aws_account_id = self.read("account/account_identity.json")["Account"]
        return [
            f"AWS Account ID: {aws_account_id}",
            f"In-Scope Regions: {self.config.in_scope_regions}",
        ]


    def run_tests(self):
        all_tests = []
        
        for test in self.AWS_TESTS:
            all_tests.append(test(self))
        
        return all_tests


    def read(self, relative_path, optional=False):
        return self.reader.read_json(f"{self.evidence_folder}/{relative_path}", optional=optional)