from dataclasses import dataclass, field

@dataclass
class AWSConfig:
    # Required Field
    in_scope_regions: list[str]

    # Tagging
    required_tags: list[str] = field(
        default_factory=lambda: ["Owner", "Description", "Classification"]
    )

    # IAM Password Policy
    iam_minimum_password_length: int = 14
    iam_require_uppercase: bool = True
    iam_require_lowercase: bool = True
    iam_require_numbers: bool = True
    iam_require_symbols: bool = True
    iam_max_password_age: int = 0               # NOTE: Value of 0 means passwords do not need to be rotated.
    iam_password_reuse_prevention: int = 24

    def __post_init__(self):
        if not self.in_scope_regions:
            raise ValueError("in_scope_regions must contain at least one AWS region.")

        # Lowercase provided regions and remove duplicates.
        self.in_scope_regions = list(dict.fromkeys(
            region.lower().strip()
            for region in self.in_scope_regions
        ))        

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError(f"Unknown configuration option: {key}")

            setattr(self, key, value)