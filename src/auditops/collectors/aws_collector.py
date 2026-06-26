from botocore.exceptions import ClientError

class AWSCollector:
    def __init__(self, session, in_scope_regions=None):
        self.session = session
        self.in_scope_regions = in_scope_regions

    def collect(self, writer):
        """
        Collect all AWS evidence.
        """
        self._collect_account_identity(writer)
        self._collect_iam_evidence(writer)
        self._collect_s3_evidence(writer)

    def _get_service_regions(self, service_name):
        return self.session.get_available_regions(service_name.lower())

    def _collect_account_identity(self, writer):
        sts_client = self.session.client("sts")
        identity = sts_client.get_caller_identity()
        writer.save_json("aws", "account/account_identity.json", identity)

    def _collect_iam_evidence(self, writer):
        iam_client = self.session.client("iam")
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
        buckets = s3_client.list_buckets()

        writer.save_json("aws", "s3/buckets.json", buckets)
        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket['Name']
            try:
                bucket_encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
                writer.save_json("aws", f"s3/buckets/{bucket_name}/encryption.json", bucket_encryption)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    # Encryption is not enabled. This will show as a finding on the report.
                    pass
                elif e.response['Error']['Code'] == 'AccessDenied':
                    # Unable to gather evidence. Will need to be manually investigated.
                    logger.warning(f"AccessDenied when calling get_bucket_encryption(): {bucket_name}")
                else:
                    raise e

    def _collect_ec2_evidence(self, writer):
        regions = self.in_scope_regions or self._get_service_regions("ec2")

        for region in regions:
            try:
                ec2_client = self.session.client("ec2", region_name=region)
                instances = ec2_client.describe_instances()
                writer.save_json("aws", f"ec2/{region}/instances.json", instances)
            except ClientError as e:
                if e.response["Error"]["Code"] == "AuthFailure":
                    continue
                raise