from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .aws_config import AWSConfig

class AWSTester:
    def __init__(self, reader, config: AWSConfig, exclusions: ExclusionManager | None = None):
        self.provider = "aws"
        self.reader = reader
        self.config = config
        self.exclusions = exclusions or ExclusionManager()

    def _read(self, path, optional=False):
        return self.reader.read_json("aws", path, optional=optional)

    def _create_test(self, metadata):
        return Test(test_id=metadata.get("id"), test_description=metadata.get("description"), 
            test_procedures=metadata.get("procedures"), test_attributes=metadata.get("attributes"), 
            table_headers=metadata.get("headers"), risk_rating=metadata.get("risk_rating"))
    
    def _fail_test(self, test, message):
        test.is_passing = False
        test.comments = message
        return test

    def run_tests(self):
        return [
            self._run_test(self._test_iam_root_access_key),
            self._run_test(self._test_iam_root_mfa),
            self._run_test(self._test_iam_user_console_password_mfa),
            self._run_test(self._test_iam_password_policy),
            self._run_test(self._test_s3_encryption),
            self._run_test(self._test_s3_public_access),
            #self._test_ec2_security_group_tags()
        ]

    def _run_test(self, test_func):
        test = test_func()

        exclusion = self.exclusions.get_test_exclusion(self.provider, test.test_id)
        if exclusion:
            test.is_excluded = True
            test.comments = exclusion.rationale

        return test

    def _test_iam_root_access_key(self):
        metadata = {
            "id": "AWS-IAM-002",
            "description": "Root account does not have any active access keys.",
            "risk_rating": 3,
            "procedures": [
                "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
                "Saved the account summary: iam/account_summary.json.",
                "Inspected the account summary to determine if 'AccountAccessKeysPresent' is set to 0."
            ]
        }

        test = self._create_test(metadata)

        summary = self._read("iam/account_summary.json")

        if not summary:
            return self._fail_test(test, "Unable to retrieve AWS account summary.")

        root_keys = summary.get("SummaryMap", {}).get("AccountAccessKeysPresent", 0)

        if root_keys > 0:
            return self._fail_test(test, f"Exception Noted. Root account has {root_keys} active access key(s).")

        return test

    def _test_iam_root_mfa(self):
        metadata = {
            "id": "AWS-IAM-003",
            "description": "Root account has MFA enabled.",
            "risk_rating": 3,
            "procedures": [
                "Obtained the AWS account summary by calling the get_account_summary() boto3 command.",
                "Saved the account summary: iam/account_summary.json",
                "Inspected the account summary to determine if 'AccountMFAEnabled' is set to 1."
            ],
            "attributes": []
        }

        test = self._create_test(metadata)

        summary = self._read("iam/account_summary.json")

        mfa_enabled = summary.get("SummaryMap", {}).get("AccountMFAEnabled", 0)

        if mfa_enabled != 1:
            return self._fail_test(test, f"Exceptions Noted. Root account does not have MFA enabled.")

        return test

    def _test_iam_user_console_password_mfa(self):
        metadata = {
            "id": "AWS-IAM-004",
            "description": "IAM users with an active console password have MFA enabled.",
            "risk_rating": 3,
            "headers": ["User Name", "Result", "Comments"],
            "attributes": [
                "Users with a login profile have at least one MFA device."
            ],
            "procedures": [
                "Obtained a list of IAM users by calling the list_users() boto3 command.",
                "Saved the list of users: iam/users.json.",
                "For each user, obtained the login profile by calling the get_login_profile() boto3 command.",
                "For each user with a login profile, obtained MFA devices by calling the list_mfa_devices() boto3 command.",
                "Inspected the MFA device configuration to determine if at least one MFA device is assigned."
            ]
        }

        test = self._create_test(metadata)

        users = self._read("iam/users.json")

        for user in users.get("Users", []):
            username = user["UserName"]

            login_profile = self._read(
                f"iam/users/{username}/login_profile.json",
                optional=True,
            )

            # Skip users without console access.
            if not login_profile:
                continue

            sample = Sample(sample_id={"user_name": username})

            mfa_devices = self._read(
                f"iam/users/{username}/mfa_devices.json"
            )

            if len(mfa_devices.get("MFADevices", [])) == 0:
                sample.comments = "Console password enabled but no MFA device assigned."

            sample.is_passing = len(mfa_devices.get("MFADevices", [])) > 0

            test.samples.append(sample)

        test.evaluate_samples(self.exclusions, self.provider)

        if not test.is_passing:
            test.comments = (
                f"Exceptions Noted. {test.num_findings} IAM user(s) "
                "have an active console password but do not have MFA enabled."
            )

        return test

    def _test_iam_password_policy(self):
        metadata = {
            "id": "AWS-IAM-001",
            "description": (
                "IAM passwords comply with the organization's password policy."
            ),
            "risk_rating": 2,
            "procedures": [
                "Obtained the IAM password policy by calling the get_account_password_policy() boto3 command.",
                "Saved the password policy: iam/password_policy.json.",
                "Inspected the password policy to determine if it complies with the configured requirements."
            ],
            "attributes": [
                f"Minimum password length is at least {self.config.iam_minimum_password_length}.",
                f"Password history is at least {self.config.iam_password_reuse_prevention}."
            ],
        }

        # Add additional test attributes based on AWSConfig.
        if self.config.iam_require_symbols:
            metadata["attributes"].append("Passwords require symbols.")
        if self.config.iam_require_numbers:
            metadata["attributes"].append("Passwords require numbers.")
        if self.config.iam_require_uppercase:
            metadata["attributes"].append("Passwords require uppercase letters.")
        if self.config.iam_require_lowercase:
            metadata["attributes"].append("Passwords require lowercase letters.")
        if self.config.iam_max_password_age > 0:
            metadata["attributes"].append(f"Passwords expire within {self.config.iam_max_password_age} days.")

        test = self._create_test(metadata)

        policy = self._read("iam/password_policy.json", optional=True)

        if not policy:
            return self._fail_test(test, "No password policy configured.")

        password_policy = policy.get("PasswordPolicy", {})
        failures = []

        # Minimum password length
        actual = password_policy.get("MinimumPasswordLength", 0)
        if actual < self.config.iam_minimum_password_length:
            failures.append(
                f"Minimum password length is {actual} "
                f"(required: {self.config.iam_minimum_password_length} characters)."
            )

        # Password complexity
        if (self.config.iam_require_symbols and not password_policy.get("RequireSymbols", False)):
            failures.append("Symbols are not required.")

        if (self.config.iam_require_numbers and not password_policy.get("RequireNumbers", False)):
            failures.append("Numbers are not required.")

        if (self.config.iam_require_uppercase and not password_policy.get("RequireUppercaseCharacters", False)):
            failures.append("Uppercase letters are not required.")

        if (self.config.iam_require_lowercase and not password_policy.get("RequireLowercaseCharacters", False)):
            failures.append("Lowercase letters are not required.")

        # Password history
        actual = password_policy.get("PasswordReusePrevention", 0)
        if actual < self.config.iam_password_reuse_prevention:
            failures.append(f"Password history is {actual}. (Required: {self.config.iam_password_reuse_prevention}).")

        # Password expiration (optional)
        if self.config.iam_max_password_age > 0:
            if not password_policy.get("ExpirePasswords", False):
                failures.append("Password expiration is not enabled.")
            else:
                actual = password_policy.get("MaxPasswordAge", 0)

                if actual > self.config.iam_max_password_age:
                    failures.append(
                        f"Maximum password age is {actual} days. (Required: {self.config.iam_max_password_age} days or less)."
                    )
        
        test.is_passing = len(failures) == 0

        if failures:
            test.comments = " ".join(failures)

        return test

    def _test_s3_public_access(self):
        metadata = {
            "id": "AWS-S3-002",
            "description": "S3 buckets are configured to block public access.",
            "risk_rating": 2,
            "headers": ["Bucket Name", "Result", "Comments"],
            "attributes": [
                "BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, and RestrictPublicBuckets are set to true."
            ],
            "procedures": [
                "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
                "Saved the list of buckets: s3/buckets.json.",
                "For each bucket, obtained the public access block settings by calling the get_public_access_block() boto3 command.",
                "For each bucket, saved the public access block settings: s3/buckets/[bucket_name]/public_access_block.json.",
                "For each bucket, inspected the public access block settings to determine if they comply with the test attribute(s) below."
            ]      
        }
        test = self._create_test(metadata)

        buckets = self._read("s3/buckets.json")

        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket["Name"]
            sample = Sample(sample_id={"bucket_name": bucket_name})

            public_access_block = self._read(f"s3/buckets/{bucket_name}/public_access_block.json", optional=True)
            
            if not public_access_block:
                sample.comments = "No Public Access Block configuration found."
                test.samples.append(sample)
                continue

            config = public_access_block.get("PublicAccessBlockConfiguration", {})
            sample.is_passing = all([config.get("BlockPublicAcls", False), config.get("IgnorePublicAcls", False),
            config.get("BlockPublicPolicy", False), config.get("RestrictPublicBuckets", False)])

            if not sample.is_passing:
                sample.comments = "One or more public access settings are disabled."

            test.samples.append(sample)

        test.evaluate_samples(self.exclusions, self.provider)

        return test

    def _test_s3_encryption(self):
        metadata = {
            "id": "AWS-S3-001",
            "description": "S3 buckets are encrypted at rest.",
            "risk_rating": 2,
            "headers": ["Bucket Name", "Result", "Comments"],
            "attributes": [
                "ServerSideEncryptionConfiguration is present."
            ],
            "procedures": [
                "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
                "Saved the list of buckets: s3/buckets.json.",
                "For each S3 bucket, obtained the encryption settings by calling the get_bucket_encryption() boto3 command.",
                "For each S3 bucket, saved the encryption settings: s3/buckets/[bucket_name]/encryption.json.",
                "For each S3 bucket, inspected the encryption settings to determine if they comply with the test attribute(s) below."
            ],      
        }
        test = self._create_test(metadata)

        buckets = self._read("s3/buckets.json")

        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket["Name"]
            sample = Sample(sample_id={"bucket_name": bucket_name})

            encryption = self._read(f"s3/buckets/{bucket_name}/encryption.json", optional=True)

            if not encryption:
                sample.comments = "No encryption configuration found."
                test.samples.append(sample)
                continue
            
            sample.is_passing = bool(encryption.get("ServerSideEncryptionConfiguration"))

            if not sample.is_passing:
                sample.comments = "No encryption configuration found"

            test.samples.append(sample)

        test.evaluate_samples()

        return test

    def _test_ec2_security_group_tags(self):
        metadata = {
            "id": "AWS-EC2-001",
            "description": (
                "EC2 security groups have required tags applied and tag values are not empty."
            ),
            "risk_rating": 0,
            "headers": ["Region", "Security Group ID", "Result", "Comments"],
            "attributes": [],
            "procedures": [
                "For each in-scope region, obtained a list of EC2 security groups by calling describe_security_groups() boto3 command.",
                "Saved the list of security groups: ec2/[region]/security_groups.json.",
                "Inspected each security group's tags to determine whether the required tags exist and have non-empty values.",
            ],
        }

        test = self._create_test(metadata)

        required_tags = (self.config.get("ec2_sg_required_tags") or ["Owner", "Description", "ReviewedBy", "LastReviewedDate"])

        for region in self.config.in_scope_regions:
            security_groups = self._read(f"ec2/{region}/security_groups.json")

            for sg in security_groups.get("SecurityGroups", []):
                sample = Sample(
                    sample_id={"region": region, "security_group_id": sg["GroupId"]}
                )

                actual_tags = {
                    tag["Key"]: tag.get("Value", "")
                    for tag in sg.get("Tags", [])
                }

                evaluate_tags(sample, required_tags, actual_tags)

                test.samples.append(sample)

        test.evaluate_samples()

        if not test.is_passing:
            test.comments = (
                f"{test.num_findings} security group(s) are missing "
                "required tags or have empty values."
            )

        return test