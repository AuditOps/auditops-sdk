from botocore.exceptions import ClientError
from .collectors import (collect_account_identity, collect_iam_evidence,
    collect_s3_evidence, collect_lambda_evidence, collect_ec2_ebs_evidence,
    collect_rds_evidence, collect_cloudtrail_evidence, collect_elbv2_evidence,
    collect_wafv2_evidence, collect_apigateway_evidence, collect_guardduty_evidence)
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AWSCollector:
    def __init__(self, session):
        self.session = session
        self.audit_folder = None
        self.config = None
        self.writer = None
        self.reader = None

    def gather_evidence(self, audit):
        self.audit_folder = audit.audit_folder
        self.config = audit.config
        self.writer = audit.writer
        self.reader = audit.reader

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
        evidence = self.reader.read_json(f"{self.audit_folder}/audit_evidence/{evidence_path}", optional=True)

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

        # Save JSON evidence to the requested folder (Ex. tmp/aws/us_prod/audit_evidence/s3/buckets.json).
        self.writer.save_json(f"{self.audit_folder}/audit_evidence/{evidence_path}", evidence)
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