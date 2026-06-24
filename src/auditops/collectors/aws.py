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
        self._collect_password_policy(writer)
        self._collect_s3_buckets(writer)

    def _collect_account_identity(self, writer):
        identity = self.sts.get_caller_identity()

        writer.save_json(
            "aws",
            "account/account_identity.json",
            identity
        )

    def _collect_password_policy(self, writer):
        try:
            password_policy = self.iam.get_account_password_policy()

            writer.save_json(
                "aws",
                "iam/password_policy.json",
                password_policy
            )

        except self.iam.exceptions.NoSuchEntityException:
            writer.save_json(
                "aws",
                "iam/password_policy.json",
                {
                    "exists": False,
                    "message": "No password policy configured"
                }
            )

    def _collect_s3_buckets(self, writer):
        buckets = self.s3.list_buckets()

        writer.save_json(
            "aws",
            "s3/buckets.json",
            buckets
        )