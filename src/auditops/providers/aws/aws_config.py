from dataclasses import dataclass, field

@dataclass
class AWSConfig:
    """
    Configuration options used by AWSCollector and AWSTester.

    Most values represent your organization's desired security baseline.
    Tests compare collected AWS evidence against these values.
    """

    # Required
    in_scope_regions: list[str]

    # Default tagging policy
    required_tags: list[str] = field(default_factory=lambda: ["Owner", "Description", "Classification"])
    ec2_security_group_required_tags: list[str] = field(default_factory=lambda: ["Owner", "Description", "ReviewedBy", "LastReviewedDate"])    

    # Optional service-specific tag overrides
    s3_required_tags: list[str] | None = None
    ec2_required_tags: list[str] | None = None
    ebs_required_tags: list[str] | None = None
    lambda_required_tags: list[str] | None = None
    rds_required_tags: list[str] | None = None

    # IAM Password Policy
    iam_minimum_password_length: int = 14
    iam_require_uppercase: bool = True
    iam_require_lowercase: bool = True
    iam_require_numbers: bool = True
    iam_require_symbols: bool = True
    iam_max_password_age: int = 0               # NOTE: Value of 0 means passwords do not need to be rotated.
    iam_password_reuse_prevention: int = 24

    # IAM Access Keys
    iam_access_key_max_age: int = 90

    # RDS
    rds_backup_retention_days: int = 14

    # CloudTrail
    cloudtrail_logging_lookback_days: int = 365

    def __post_init__(self):
        if not self.in_scope_regions:
            raise ValueError("in_scope_regions must contain at least one AWS region.")

        # Lowercase provided regions and remove duplicates.
        self.in_scope_regions = list(dict.fromkeys(
            region.lower().strip()
            for region in self.in_scope_regions
        ))

    def update(self, **kwargs):
        # Allow end users to update configuration values after construction.
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError(f"Unknown configuration option: {key}")

            setattr(self, key, value)

    def get_required_tags(self, service: str) -> list[str]:
        """
        Returns the required tags for a particular AWS service.
        Falls back to required_tags if no service-specific override exists.
        """

        override = {
            "s3": self.s3_required_tags,
            "ec2": self.ec2_required_tags,
            "ebs": self.ebs_required_tags,
            "lambda": self.lambda_required_tags,
            "rds": self.rds_required_tags,
        }.get(service)

        return override or self.required_tags