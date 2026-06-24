from botocore.exceptions import ClientError

class AWSCollector:
    def __init__(self, session):
        self.session = session
        self.iam = session.client("iam")
        self.s3 = session.client("s3")
        self.sts = session.client("sts")

    def collect(self, writer):
        """
        Collect all AWS evidence.
        """
        self._collect_account_identity(writer)
        self._collect_iam_evidence(writer)
        self._collect_s3_evidence(writer)

    def _collect_account_identity(self, writer):
        identity = self.sts.get_caller_identity()
        writer.save_json("aws", "account/account_identity.json", identity)

    def _collect_iam_evidence(self, writer):
        try:
            password_policy = self.iam.get_account_password_policy()
            writer.save_json("aws", "iam/password_policy.json", password_policy)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass
            else:
                raise

    def _collect_s3_evidence(self, writer):
        buckets = self.s3.list_buckets()

        writer.save_json("aws", "s3/buckets.json", buckets)
        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket['Name']
            try:
                bucket_encryption = self.s3.get_bucket_encryption(Bucket=bucket_name)
                writer.save_json("aws", f"s3/buckets/{bucket_name}/encryption.json", bucket_encryption)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    # Encryption is not enabled. This will show as a finding on the report.
                    pass
                elif e.response['Error']['Code'] == 'AccessDenied':
                    # Unable to gather evidence. Will need to be manually investigated.
                    logger.warning(f"AccessDenied when calling get_bucket_encryption(): {bucketName}")
                else:
                    raise e