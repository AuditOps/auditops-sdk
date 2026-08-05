# Resources
- **Example Report**: [Link](/examples/summary_mode/AWS%20Audit%20Report%20(Summary%20Mode).pdf)
- **FAQs**: [Link](/docs/general/faqs.md)

# AWS Setup Guide

This guide walks you through running your first AWS audit with AuditOps.

The setup consists of four steps:

1. Environment Setup (install Python, Pip, and AWS CLI)
2. Configure AWS access
3. Run your first audit
4. Review the generated reports

Once you've run your fist scan, try customizing the audit (adding exclusions, uploading to audit servers, etc)

---

# Prerequisites

Before you begin, you'll need:

- An AWS account
- An IAM user (or an IAM Identity Center user) with the required permissions
    - Feel free to use [training.itauditguy.com](https://training.itauditguy.com). Using this form creates an IAM user in the IT Audit Guy sandbox AWS account.
- Python 3.11 or later

---

# 1. Environment Setup

## Verify Python, Pip, and AWS CLI is installed
If any of the verification steps below fail, please check out the [Prerequisite Instruction](/docs/general/prerequisites.md).

Verify Python is installed:
```bash
python --version
```

Verify Pip is installed:
```bash
pip --version
```

Verify AWS CLI is installed:
```bash
aws --version
```

---

## Install AuditOps

Install the latest AuditOps package from PyPI.

```bash
pip install -U auditops
```

---

# 2. Configure AWS Access

AuditOps uses the AWS credentials configured on your local machine to collect evidence from your AWS account.

## Create an AWS User

Option 1 (Sandbox Environment):


Option 2 (Production Scan): Work with your engineering / DevOps team to create either:
- An IAM User, or
- An IAM Identity Center User

Attach the AWS managed **SecurityAudit** policy to the user.

For more information, see the AWS documentation:

https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SecurityAudit.html

---

## Create Access Keys (IAM Users Only)

If you're using an IAM user, create an access key (IAM > Users > [YOUR USER] > Security Credentials > Create Access Key.

> **Note**
>
> Access keys are only shown once when they are created. Store them securely.

---

## Configure Local Credentials

Configure your credentials using the AWS CLI.

```bash
aws configure
```

You'll be prompted for:

- AWS Access Key ID
- AWS Secret Access Key
- Default Region
- Output Format

If you need help, see:

https://youtu.be/RLx5qVZSTyE?si=7fqyxFzThDaB-mGQ

---

# 3. Run Your First Audit

Create a file named **auditops_example.py**.

```python
from auditops.core.models import Audit, AuditHelpers
from auditops.core.utils import aws_create_session
from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig


def main():

    # Uses the credentials configured with "aws configure"
    session = aws_create_session()

    # Customize your organization's security requirements.
    aws_config = AWSConfig(
        in_scope_regions=["us-east-1"]
    )

    helpers = AuditHelpers.create()

    audit = Audit(
        helpers=helpers,
        title="AWS Audit Report",
        config=aws_config,
        auditor_name="Happy Gilmore",
        audit_folder="aws",
        delete_cached_evidence=True,
        summary_mode=True,
    )

    audit.run(
        collector=AWSCollector(session),
        tester=AWSTester(),
    )


if __name__ == "__main__":
    main()
```

Run the audit:

```bash
python auditops_example.py
```

Most audits complete within a few minutes, depending on the size of your AWS environment.

---

# 4. Review the Results

AuditOps creates a `tmp` directory containing the collected evidence and generated reports.

```
tmp/
├── audit_evidence/
└── reports/
```

The **reports** directory contains:

- PDF audit report
- JSON audit report

The **audit_evidence** directory contains the raw AWS evidence collected during the audit.

---

# 5. Customizing the Audit

The `AWSConfig` object defines your organization's expected security baseline.

Only `in_scope_regions` is required. All other settings use built-in defaults.

For example:

```python
aws_config = AWSConfig(
    in_scope_regions=["us-east-1", "us-east-2"],
    iam_minimum_password_length=12,
)
```

You can customize settings such as:

- Required resource tags
- IAM password policy
- IAM access key age
- RDS backup retention
- CloudTrail log retention

For a complete list of configuration options, see the AWSConfig documentation (**[link](aws-config.md)**).

---

# Optional: Upload Reports to AuditOps

Upload the generated report directly to AuditOps for vendor due diligence or audit requests.

```python
audit.upload(
    destination="auditops",
    package="pdf",
    client_email="john@acme.com",
)
```

---

# Optional: Archive Results in Amazon S3

Store the complete audit package in an Amazon S3 bucket for long-term retention.

```python
from datetime import datetime
import boto3

bucket_save_path = datetime.now().strftime("%Y/%m/%d/aws")

audit.upload(
    destination="s3",
    package="full",
    client=boto3.client("s3"),
    bucket="YOUR_BUCKET_NAME",
    key=bucket_save_path,
)
```

A common folder structure is:

```
2026/
└── 08/
    └── 02/
        └── aws.zip
```

---

# Next Steps

Once you've successfully completed your first audit, you can:

- Customize your AWS security baseline with `AWSConfig`
- Schedule audits using cron, Task Scheduler, or CI/CD pipelines
- Upload reports to AuditOps
- Archive audit packages in Amazon S3
- Review the generated evidence to investigate failed tests
