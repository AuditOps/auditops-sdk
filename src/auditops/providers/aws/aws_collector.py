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
        self._collect_lambda_evidence()
        self._collect_rds_evidence()
        self._collect_cloudtrail_evidence()
        self._collect_elbv2_evidence()
        self._collect_apigateway_evidence()
        self._collect_wafv2_evidence()
        self._collect_guardduty_evidence()

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

    ####################################################################
    #
    # IAM
    #
    ####################################################################

    def _collect_iam_evidence(self):
        iam_client = self.session.client("iam")
        self._write("iam/account_summary.json", iam_client.get_account_summary())

        try:
            self._write(
                "iam/password_policy.json",
                iam_client.get_account_password_policy(),
            )

        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                raise

        self._collect_iam_users(iam_client)
        self._collect_iam_roles(iam_client)
        self._collect_iam_groups(iam_client)

    def _collect_iam_users(self, iam_client):
        users = self._call_api(iam_client,
            paginator_params={"method_name": "list_users", "pagination_key": "Users"},
        )
        self._write("iam/users.json", users)

        for user in users.get("Users", []):
            user_name = user["UserName"]

            self._write(
                f"iam/users/{user_name}/login_profile.json",
                self._call_api(
                    iam_client,
                    method="get_login_profile",
                    method_kwargs={
                        "UserName": user_name,
                    },
                    ignore_codes=["NoSuchEntity"],
                ),
            )

            self._write(
                f"iam/users/{user_name}/mfa_devices.json",
                self._call_api(
                    iam_client,
                    method="list_mfa_devices",
                    method_kwargs={
                        "UserName": user_name,
                    },
                ),
            )

            self._write(
                f"iam/users/{user_name}/access_keys.json",
                self._call_api(
                    iam_client,
                    method="list_access_keys",
                    method_kwargs={
                        "UserName": user_name,
                    },
                ),
            )

    def _collect_iam_roles(self, iam_client):
        self._write(
            "iam/roles.json",
            self._call_api(
                iam_client,
                paginator_params={
                    "method_name": "list_roles",
                    "pagination_key": "Roles",
                },
            ),
        )

    def _collect_iam_groups(self, iam_client):
        self._write(
            "iam/groups.json",
            self._call_api(
                iam_client,
                paginator_params={
                    "method_name": "list_groups",
                    "pagination_key": "Groups",
                },
            ),
        )

    ####################################################################
    #
    # S3
    #
    ####################################################################

    def _collect_s3_evidence(self):
        s3_client = self.session.client("s3")

        buckets = self._call_api(s3_client, method="list_buckets")
        self._write("s3/buckets.json", buckets)

        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket["Name"]
            # Encryption
            self._write(
                f"s3/buckets/{bucket_name}/encryption.json",
                self._call_api(
                    s3_client,
                    method="get_bucket_encryption",
                    method_kwargs={"Bucket": bucket_name},
                    ignore_codes=["ServerSideEncryptionConfigurationNotFoundError"],
                    warn_codes=["AccessDenied"],
                )
            )
            # Public access block
            self._write(
                f"s3/buckets/{bucket_name}/public_access_block.json",
                self._call_api(
                    s3_client,
                    method="get_public_access_block",
                    method_kwargs={"Bucket": bucket_name},
                    ignore_codes=["NoSuchPublicAccessBlockConfiguration"],
                ),
            )
            # Bucket policy
            self._write(
                f"s3/buckets/{bucket_name}/policy.json",
                self._call_api(
                    s3_client,
                    method="get_bucket_policy",
                    method_kwargs={"Bucket": bucket_name},
                    ignore_codes=["NoSuchBucketPolicy"],
                    warn_codes=["AccessDenied"],
                ),
            )
            # Bucket tags
            self._write(
                f"s3/buckets/{bucket_name}/tags.json",
                self._call_api(
                    s3_client,
                    method="get_bucket_tagging",
                    method_kwargs={"Bucket": bucket_name},
                    ignore_codes=["NoSuchTagSet"],
                    warn_codes=["AccessDenied"],
                ),
            )

    ####################################################################
    #
    # EC2 / EBS
    #
    ####################################################################

    def _collect_ec2_evidence(self):
        for region in self.config.in_scope_regions:
            ec2_client = self.session.client(
                "ec2",
                region_name=region,
            )
            self._collect_ec2_instances(ec2_client,region)
            self._collect_ec2_security_groups(ec2_client,region)
            self._collect_ebs_volumes(ec2_client,region)
            self._collect_ebs_default_encryption(ec2_client,region)

    def _collect_ec2_instances(self, ec2_client, region):
        self._write(
            f"ec2/{region}/instances.json",
            self._call_api(
                ec2_client,
                method="describe_instances",
            ),
        )

    def _collect_ec2_security_groups(self, ec2_client, region):
        self._write(
            f"ec2/{region}/security_groups.json",
            self._call_api(
                ec2_client,
                method="describe_security_groups",
            ),
        )

    def _collect_ebs_volumes(self, ec2_client, region):
        self._write(
            f"ec2/{region}/volumes.json",
            self._call_api(
                ec2_client,
                method="describe_volumes",
            ),
        )

    def _collect_ebs_default_encryption(self, ec2_client, region):
        self._write(
            f"ec2/{region}/ebs_encryption_by_default.json",
            self._call_api(
                ec2_client,
                method="get_ebs_encryption_by_default",
            ),
        )
    ####################################################################
    #
    # Lambda
    #
    ####################################################################

    def _collect_lambda_evidence(self):
        for region in self.config.in_scope_regions:
            lambda_client = self.session.client("lambda", region_name=region)

            functions = self._call_api(lambda_client, method="list_functions")
            self._write(f"lambda/{region}/functions.json", functions)

            for function in functions.get("Functions", []):
                function_name = function["FunctionName"]
                self._write(
                    f"lambda/{region}/functions/{function_name}/tags.json",
                    self._call_api(
                        lambda_client,
                        method="list_tags",
                        method_kwargs={
                            "Resource": function["FunctionArn"],
                        },
                    ),
                )

    ####################################################################
    #
    # RDS
    #
    ####################################################################

    def _collect_rds_evidence(self):
        for region in self.config.in_scope_regions:
            rds_client = self.session.client("rds", region_name=region)

            self._write(
                (f"rds/{region}/db_instances.json"),
                self._call_api(
                    rds_client,
                    method="describe_db_instances",
                ),
            )

            self._write(
                (f"rds/{region}/db_instances.json"),
                self._call_api(
                    rds_client,
                    method="describe_db_clusters",
                ),
            )

    ####################################################################
    #
    # CloudTrail
    #
    ####################################################################

    def _collect_cloudtrail_evidence(self):
        cloudtrail_client = self.session.client("cloudtrail")

        trails = self._call_api(
            cloudtrail_client,
            method="describe_trails",
        )

        self._write(
            "cloudtrail/trails.json", 
            trails)

        for trail in trails.get("trailList", []):
            trail_name = trail["Name"]

            self._write(
                f"cloudtrail/trails/{trail_name}/trail_status.json",
                self._call_api(
                    cloudtrail_client,
                    method="get_trail_status",
                    method_kwargs={
                        "Name": trail_name,
                    },
                ),
            )
    ####################################################################
    #
    # ELBv2
    #
    ####################################################################

    def _collect_elbv2_evidence(self):
        for region in self.config.in_scope_regions:
            elbv2_client = self.session.client(
                "elbv2",
                region_name=region,
            )

            self._write(
                f"elbv2/{region}/load_balancers.json",
                self._call_api(
                    elbv2_client,
                    method="describe_load_balancers",
                ),
            )

    ####################################################################
    #
    # API Gateway
    #
    ####################################################################

    def _collect_apigateway_evidence(self):
        for region in self.config.in_scope_regions:
            apigateway_client = self.session.client(
                "apigateway",
                region_name=region,
            )

            self._write(
                f"apigateway/{region}/rest_apis.json",
                self._call_api(
                    apigateway_client,
                    method="get_rest_apis",
                ),
            )

    ####################################################################
    #
    # WAFv2
    #
    ####################################################################

    def _collect_wafv2_evidence(self):
        for region in self.config.in_scope_regions:
            wafv2_client = self.session.client(
                "wafv2",
                region_name=region,
            )

            web_acls = self._call_api(
                wafv2_client,
                method="list_web_acls",
                method_kwargs={
                    "Scope": "REGIONAL",
                },
            )

            self._write(
                f"wafv2/{region}/web_acls.json",
                web_acls,
            )

            for web_acl in web_acls.get("WebACLs", []):
                self._write(
                    f"wafv2/{region}/{web_acl['Name']}_{web_acl['Id']}/resources.json",
                    self._call_api(
                        wafv2_client,
                        method="list_resources_for_web_acl",
                        method_kwargs={
                            "WebACLArn": web_acl["ARN"],
                        },
                    ),
                )

    ####################################################################
    #
    # GuardDuty
    #
    ####################################################################

    def _collect_guardduty_evidence(self):
        for region in self.config.in_scope_regions:
            guardduty_client = self.session.client(
                "guardduty",
                region_name=region,
            )

            detectors = self._call_api(
                guardduty_client,
                method="list_detectors",
            )

            self._write(
                f"guardduty/{region}/detectors.json",
                detectors,
            )

            for detector_id in detectors.get("DetectorIds", []):
                self._write(
                    f"guardduty/{region}/{detector_id}/detector.json",
                    self._call_api(
                        guardduty_client,
                        method="get_detector",
                        method_kwargs={
                            "DetectorId": detector_id,
                        },
                    ),
                )