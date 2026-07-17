from botocore.exceptions import ClientError
from .collectors import (collect_account_identity, collect_iam_evidence,
    collect_s3_evidence, collect_lambda_evidence, collect_ec2_ebs_evidence,
    collect_rds_evidence, collect_cloudtrail_evidence, collect_elbv2_evidence,
    collect_wafv2_evidence, collect_apigateway_evidence, collect_guardduty_evidence)
from auditops.core.utils import delete_evidence_folder
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class AWSCollector:
    def __init__(self, session, context):
        self.session = session
        self.evidence_folder = context.evidence_folder
        self.config = context.config
        self.writer = context.writer
        self.reader = context.reader
        self.delete_cached_evidence = context.delete_cached_evidence


    def gather_evidence(self):

        evidence_path = self.reader.evidence_dir / self.evidence_folder

        if self.delete_cached_evidence:
            delete_evidence_folder(evidence_path)
        elif evidence_path.exists():
            logger.info(f"Using cached evidence in: {evidence_path}")

        collect_lambda_evidence(self)
        collect_account_identity(self)
        collect_iam_evidence(self)
        collect_s3_evidence(self)
        collect_ec2_ebs_evidence(self)
        collect_rds_evidence(self)
        collect_cloudtrail_evidence(self)
        collect_elbv2_evidence(self)
        collect_apigateway_evidence(self)
        collect_wafv2_evidence(self)
        collect_guardduty_evidence(self)


    def collect(self, evidence_path, client, *, method=None, method_kwargs=None, paginator_params=None,
    ignore_codes=None, warn_codes=None):
        """
            AWS-safe fetch wrapper with optional pagination support.
            Returns requested evidence (will check if evidence already exists)
            NOTE: When paginating evidence, the ResponseMetadata is flattened (from the last page).

            evidence_path: file path describing where evidence should be saved (e.g., s3/buckets.json)
            client: AWS client.
            method: AWS method name (e.g., 'list_buckets', 'get_bucket_encryption')
            method_kwargs: dict (arguments to pass to the AWS method). E.g. {"Bucket": "my-bucket"}
            not_found_codes: list of potential AWS error codes (e.g., ["ServerSideEncryptionConfigurationNotFoundError"]).
            NOTE: not_found_codes is used to avoid errors when 'optional' evidence is not available.
            paginator_params: dict with keys:
            - method_name: str (e.g., 'list_users')
            - pagination_key: str (key in each page to combine, e.g., 'Users')
            - params: dict (parameters to pass to the AWS method)
        """
        # Check if evidence already exists
        evidence = self.reader.read_json(f"{self.evidence_folder}/{evidence_path}", optional=True)

        if evidence is not None:
            # Return cached evidence. 
            return evidence

        evidence = self._call_api(
            client,
            method=method,
            method_kwargs=method_kwargs,
            paginator_params=paginator_params,
            ignore_codes=ignore_codes,
            warn_codes=warn_codes
        )
        """
        Saves JSON evidence to the requested folder (Ex. tmp/audit_evidence/aws/us_prod/s3/buckets.json).

        NOTE: The string below is made up of the following attributes:
            - writer.evidence_dir: "tmp/audit_evidence"
            - self.evidence_folder: "aws/us_prod"
            - evidence_path: "s3/buckets.json"
        """
        self.writer.save_json(f"{self.evidence_folder}/{evidence_path}", evidence)
        return evidence


    def _call_api(self, client, method=None, method_kwargs=None, paginator_params=None,
                ignore_codes=None, warn_codes=None):
        try:
            if paginator_params:
                paginator = client.get_paginator(paginator_params["method_name"])
                key = paginator_params["pagination_key"]
                items = []
                for page in paginator.paginate(**(paginator_params.get("params") or {})):
                    items.extend(page.get(key, []))
                    last_metadata = page.get("ResponseMetadata", {})

                return {
                    key: items,
                    "ResponseMetadata": last_metadata
                }

            return getattr(client, method)(**(method_kwargs or {}))

        except ClientError as e:
            code = e.response["Error"]["Code"]
            if warn_codes and code in warn_codes:
                logger.warning(f"{code} calling {method or paginator_params.get('method_name')}")
                return None
            if ignore_codes and code in ignore_codes:
                return None
            raise