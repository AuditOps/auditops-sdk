from datetime import datetime, timezone
from auditops.core.models import Test, Sample
from auditops.core.exclusions import ExclusionManager
from .aws_config import AWSConfig
from .tests.iam import run_iam_tests
from .tests.s3 import run_s3_tests
from .tests.rds import run_rds_tests
from .tests.ec2 import run_ec2_tests
from .tests.ebs import run_ebs_tests
from .tests.cloudtrail import run_cloudtrail_tests
from .tests.guardduty import run_guardduty_tests
#from .tests.lambda import run_lambda_tests

class AWSTester:
    def __init__(self, reader, config: AWSConfig, exclusions: ExclusionManager | None = None):
        self.provider = "aws"
        self.report_title = "AWS Audit Report"
        self.reader = reader
        self.config = config
        self.exclusions = exclusions or ExclusionManager()


    def run_tests(self):
        tests = []

        tests.extend(run_iam_tests(self))
        tests.extend(run_s3_tests(self))
        tests.extend(run_rds_tests(self))
        tests.extend(run_ec2_tests(self))
        tests.extend(run_ebs_tests(self))
        tests.extend(run_cloudtrail_tests(self))
        tests.extend(run_guardduty_tests(self))

        return tests
        
        """

        # Lambda
        self._test_lambda_function_tags(),

        # CloudTrail
        self._test_cloudtrail_multi_region(),
        self._test_cloudtrail_log_file_validation(),
        self._test_cloudtrail_logging(),
        self._test_cloudtrail_bucket_protection(),

        # WAF
        self._test_waf_enabled(),

        # GuardDuty
        self._test_guardduty_enabled(),
        """

    ####################################################################
    #
    # Helpers
    #
    ####################################################################

    def _fail_test(self, test, message):
        test.is_passing = False
        test.comments = message
        return test

    def read(self, path, optional=False):
        return self.reader.read_json("aws", path, optional=optional)

    def _create_test(self, metadata):
        test = Test(**metadata)

        exclusion = self.exclusions.get_test_exclusion(self.provider, test.test_id)
        if exclusion:
            test.is_excluded = True
            test.comments = exclusion.rationale

        return test

    def _get_required_tags(self, service):
        return self.config.get_required_tags(service)

    @staticmethod
    def _find_tag(tags, key):
        if not tags:
            return None

        for tag in tags:
            if tag["Key"] == key:
                return tag["Value"]

        return None

    def _test_ec2_security_group_tags(self):
        metadata = {
            "test_id": "aws-ec2-001",
            "test_description": (
                "EC2 security groups have required tags applied and tag values are not empty."
            ),
            "risk_rating": 0,
            "table_headers": ["Region", "Security Group ID", "Result", "Comments"],
            "test_procedures": [
                "For each in-scope region, obtained a list of EC2 security groups by calling describe_security_groups() boto3 command.",
                "Saved the list of security groups: ec2/[region]/security_groups.json.",
                "Inspected each security group's tags to determine whether the required tags exist and have non-empty values.",
            ],
            "test_attributes": [],            
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