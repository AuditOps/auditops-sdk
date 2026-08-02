# AWSConfig

`AWSConfig` defines your organization's expected AWS security baseline.

The AWS collector gathers evidence from your AWS account, and the AWS tests compare that evidence against the values defined in this configuration.

Most organizations only need to customize a few settings, such as:

- AWS regions to audit
- Required resource tags
- Password policy requirements
- Backup retention requirements

Any values you do not specify use the built-in defaults.

---

# Creating a Configuration

The only required setting is the list of AWS regions that should be included in the audit.

```python
from auditops.aws import AWSConfig

config = AWSConfig(
    in_scope_regions=[
        "us-east-1",
        "us-east-2",
    ]
)
```

---

# Changing Security Requirements

Pass additional keyword arguments to override the defaults.

For example, if your organization requires a minimum password length of 12 characters:

```python
config = AWSConfig(
    in_scope_regions=["us-east-1", "us-east-2"],
    iam_minimum_password_length=12,
)
```

You can customize as many settings as needed.

```python
config = AWSConfig(
    in_scope_regions=["us-east-1"],

    iam_minimum_password_length=16,
    iam_max_password_age=90,
    iam_access_key_max_age=45,

    rds_backup_retention_days=30,
)
```

---

# Required Tags

By default, the following tags are required on supported resources:

```text
Owner
Description
Classification
```

You can replace these with your own organization-wide tagging policy.

```python
config = AWSConfig(
    in_scope_regions=["us-east-1"],

    required_tags=[
        "Owner",
        "Environment",
        "Application",
        "CostCenter",
    ]
)
```

---

# Service-Specific Tag Requirements

If a particular AWS service uses different tagging requirements, specify an override.

For example, S3 buckets may require different tags than EC2 instances.

```python
config = AWSConfig(
    in_scope_regions=["us-east-1"],

    required_tags=[
        "Owner",
        "Environment",
    ],

    s3_required_tags=[
        "Owner",
        "Environment",
        "DataClassification",
    ]
)
```

Supported service-specific overrides include:

- `s3_required_tags`
- `ec2_required_tags`
- `ebs_required_tags`
- `lambda_required_tags`
- `rds_required_tags`

If an override is not provided, the global `required_tags` list is used.

---

# Updating an Existing Configuration

Configuration values can also be modified after creation.

```python
config = AWSConfig(
    in_scope_regions=["us-east-1"]
)

config.update(
    iam_minimum_password_length=16,
    rds_backup_retention_days=30,
)
```

Attempting to update an unknown configuration option raises a `ValueError`.

---

# Available Configuration Options

| Option | Default |
|---------|---------|
| `in_scope_regions` | **Required** |
| `required_tags` | `["Owner", "Description", "Classification"]` |
| `ec2_security_group_required_tags` | `["Owner", "Description", "ReviewedBy", "LastReviewedDate"]` |
| `s3_required_tags` | `None` |
| `ec2_required_tags` | `None` |
| `ebs_required_tags` | `None` |
| `lambda_required_tags` | `None` |
| `rds_required_tags` | `None` |
| `iam_minimum_password_length` | `14` |
| `iam_require_uppercase` | `True` |
| `iam_require_lowercase` | `True` |
| `iam_require_numbers` | `True` |
| `iam_require_symbols` | `True` |
| `iam_max_password_age` | `0` (password rotation disabled) |
| `iam_password_reuse_prevention` | `24` |
| `iam_access_key_max_age` | `90` |
| `rds_backup_retention_days` | `14` |
| `cloudtrail_logging_lookback_days` | `365` |

---

# Notes

- Region names are automatically converted to lowercase.
- Duplicate regions are automatically removed.
- At least one AWS region must be specified.
- Unspecified options automatically use the built-in defaults.