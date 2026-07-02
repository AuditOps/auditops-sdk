from botocore.exceptions import ClientError

class AWSCollector:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def collect(self, writer):
        self._collect_account_identity(writer)
        self._collect_iam_evidence(writer)
        self._collect_s3_evidence(writer)
        self._collect_ec2_evidence(writer)

    def _call_api(self, client, method=None, method_kwargs=None, paginator_params=None,
                ignore_codes=None, warn_codes=None):
        try:
            if paginator_params:
                paginator = client.get_paginator(paginator_params["method_name"])
                key = paginator_params["pagination_key"]
                items = []
                for page in paginator.paginate(**(paginator_params.get("params") or {})):
                    items.extend(page.get(key, []))
                return {key: items}

            return getattr(client, method)(**(method_kwargs or {}))

        except ClientError as e:
            code = e.response["Error"]["Code"]
            if warn_codes and code in warn_codes:
                logger.warning(f"{code} calling {method or paginator_params.get('method_name')}")
                return None
            if ignore_codes and code in ignore_codes:
                return None
            raise
        
    def _collect_account_identity(self, writer):
        sts_client = self.session.client("sts")
        identity = sts_client.get_caller_identity()
        writer.save_json("aws", "account/account_identity.json", identity)

    def _collect_iam_evidence(self, writer):
        iam_client = self.session.client("iam")
        writer.save_json("aws", "iam/account_summary.json", iam_client.get_account_summary())
        try:
            password_policy = iam_client.get_account_password_policy()
            writer.save_json("aws", "iam/password_policy.json", password_policy)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass
            else:
                raise

    def _collect_s3_evidence(self, writer):
        s3_client = self.session.client("s3")
        buckets = self._call_api(s3_client, method="list_buckets")
        writer.save_json("aws", "s3/buckets.json", buckets)

        for bucket in buckets.get("Buckets", []):
            name = bucket["Name"]

            encryption = self._call_api(
                s3_client, method="get_bucket_encryption", method_kwargs={"Bucket": name},
                ignore_codes=["ServerSideEncryptionConfigurationNotFoundError"],
                warn_codes=["AccessDenied"],
            )
            writer.save_json("aws", f"s3/buckets/{name}/encryption.json", encryption)

            public_access_block = self._call_api(
                s3_client, method="get_public_access_block", method_kwargs={"Bucket": name},
                ignore_codes=["NoSuchPublicAccessBlockConfiguration"],
            )
            writer.save_json("aws", f"s3/buckets/{name}/public_access_block.json", public_access_block)

    def _collect_ec2_evidence(self, writer):
        for region in self.config.in_scope_regions:
            try:
                ec2_client = self.session.client("ec2", region_name=region)
                instances = ec2_client.describe_instances()
                writer.save_json("aws", f"ec2/{region}/instances.json", instances)
            except ClientError as e:
                raise