from .iam import collect_iam_evidence
from .s3 import collect_s3_evidence
from .lmbda import collect_lambda_evidence
from .account import collect_account_identity
from .ec2 import collect_ec2_ebs_evidence
from .rds import collect_rds_evidence
from .cloudtrail import collect_cloudtrail_evidence
from .elbv2 import collect_elbv2_evidence
from .wafv2 import collect_wafv2_evidence
from .apigateway import collect_apigateway_evidence
from .guardduty import collect_guardduty_evidence

__all__ = ["collect_iam_evidence", "collect_s3_evidence", "collect_lambda_evidence", "collect_account_identity",
    "collect_ec2_ebs_evidence", "collect_rds_evidence", "collect_cloudtrail_evidence", "collect_elbv2_evidence",
    "collect_wafv2_evidence", "collect_apigateway_evidence", "collect_guardduty_evidence",]