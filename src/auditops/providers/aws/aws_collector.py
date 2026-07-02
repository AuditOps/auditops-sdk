from botocore.exceptions import ClientError

class AWSCollector:
    def __init__(self, session, writer, config):
        self.provider = "aws"
        self.session = session
        self.config = config
        self.writer = writer

    def collect(self):
        self._collect_account_identity()
        self._collect_iam_evidence()
        self._collect_s3_evidence()
        self._collect_ec2_evidence()

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
    
    def _write(self, path, data):
        return self.writer.save_json("aws", path, data)

    def _collect_account_identity(self):
        sts_client = self.session.client("sts")
        identity = sts_client.get_caller_identity()
        self._write("account/account_identity.json", identity)

    def _collect_iam_evidence(self):
        iam_client = self.session.client("iam")
        self._write("iam/account_summary.json", iam_client.get_account_summary())
        try:
            password_policy = iam_client.get_account_password_policy()
            self._write("iam/password_policy.json", password_policy)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pass
            else:
                raise

        # Users
        users = self._call_api(iam_client,
            paginator_params={"method_name": "list_users", "pagination_key": "Users"},
        )
        self._write("iam/users.json", users)

        for user in users.get("Users"):
            user_name = user["UserName"]

            login_profile = self._call_api(iam_client, method="get_login_profile", method_kwargs={"UserName": user_name},
            ignore_codes=["NoSuchEntity"])
            self._write(f"iam/users/{user_name}/login_profile.json", login_profile)

            mfa_devices = self._call_api(iam_client, method="list_mfa_devices", method_kwargs={"UserName": user_name})
            self._write(f"iam/users/{user_name}/mfa_devices.json", mfa_devices)

        # Roles
        roles = self._call_api(iam_client,
            paginator_params={"method_name": "list_roles", "pagination_key": "Roles"},
        )
        self._write("iam/roles.json", roles)

        # Groups
        groups = self._call_api(
            iam_client,
            paginator_params={"method_name": "list_groups", "pagination_key": "Groups"}
        )
        self._write("iam/groups.json", groups)
        

    def _collect_s3_evidence(self):
        s3_client = self.session.client("s3")
        buckets = self._call_api(s3_client, method="list_buckets")
        self._write("s3/buckets.json", buckets)

        for bucket in buckets.get("Buckets", []):
            name = bucket["Name"]

            encryption = self._call_api(
                s3_client, method="get_bucket_encryption", method_kwargs={"Bucket": name},
                ignore_codes=["ServerSideEncryptionConfigurationNotFoundError"],
                warn_codes=["AccessDenied"],
            )
            self._write(f"s3/buckets/{name}/encryption.json", encryption)

            public_access_block = self._call_api(
                s3_client, method="get_public_access_block", method_kwargs={"Bucket": name},
                ignore_codes=["NoSuchPublicAccessBlockConfiguration"],
            )
            self._write(f"s3/buckets/{name}/public_access_block.json", public_access_block)

    def _collect_ec2_evidence(self):
        for region in self.config.in_scope_regions:
            try:
                ec2_client = self.session.client("ec2", region_name=region)
                instances = ec2_client.describe_instances()
                self._write(f"ec2/{region}/instances.json", instances)
            except ClientError as e:
                raise