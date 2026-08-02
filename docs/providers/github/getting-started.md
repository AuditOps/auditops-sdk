# GitHub Setup Guide

This guide walks you through running your first GitHub organization audit with AuditOps.

The setup consists of four steps:

1. Install the required software
2. Create a GitHub personal access token
3. Run your first audit
4. Review the generated reports

---

# Prerequisites

Before you begin, you'll need:

- A GitHub organization
- Permission to create a Personal Access Token (PAT)
- Administrator or security permissions to the GitHub organization you want to audit
- Python 3.11 or later

---

# 1. Install the Required Software

## Install Python

If Python is not already installed, follow the tutorial below:

- https://www.youtube.com/watch?v=D2cwvpJSBX4

Verify the installation:

```bash
python --version
```

---

## Install AuditOps

Install the latest version from PyPI.

```bash
pip install auditops
```

---

## Install python-dotenv

This example stores your GitHub credentials in a local `.env` file.

Install the required package:

```bash
pip install python-dotenv
```

---

# 2. Configure GitHub Access

AuditOps uses a GitHub Personal Access Token (PAT) to collect security evidence from your GitHub organization.

## Create a Personal Access Token

Create a **Fine-grained Personal Access Token** or a **Classic Personal Access Token** with read-only permissions required to audit your organization.

For most users, a Fine-grained Personal Access Token is recommended.

GitHub Documentation:

https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

> **Note**
>
> Store your personal access token securely. It provides access to your GitHub organization.

---

## Create a `.env` File

Create a file named `.env` in the same directory as your Python script.

```text
github_token=YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
github_org_name=YOUR_GITHUB_ORGANIZATION
```

For example:

```text
github_token=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxx
github_org_name=acme-corporation
```

---

# 3. Run Your First Audit

Create a file named **auditops_example.py**.

```python
import os

from dotenv import load_dotenv

from auditops.core.models import Audit, AuditHelpers
from auditops.providers.github import GitHubCollector, GitHubTester


def main():

    load_dotenv()

    helpers = AuditHelpers.create()

    audit = Audit(
        helpers=helpers,
        title="GitHub Audit Report",
        auditor_name="Shooter McGavin",
        audit_folder="github",
        summary_mode=False,
        delete_cached_evidence=True,
    )

    audit.run(
        collector=GitHubCollector(
            token=os.getenv("github_token"),
            org_name=os.getenv("github_org_name"),
        ),
        tester=GitHubTester(),
    )


if __name__ == "__main__":
    main()
```

Run the audit:

```bash
python auditops_example.py
```

Most audits complete within a few minutes, depending on the size of your GitHub organization.

---

# 4. Review the Results

After the audit completes, AuditOps creates a `tmp` directory containing the collected evidence and generated reports.

```
tmp/
├── audit_evidence/
└── reports/
```

The **reports** directory contains:

- PDF audit report
- JSON audit report

The **audit_evidence** directory contains the raw GitHub evidence collected during the audit.

---

# Understanding Audit Options

The `Audit` object includes a few optional settings that control how reports are generated.

## Summary Mode

Setting `summary_mode=True` anonymizes sample identifiers in the PDF report.

Instead of displaying repository or resource names, the report will use generic labels such as:

```text
Sample 1
Sample 2
Sample 3
```

This is useful when sharing reports externally while minimizing exposure of sensitive resource names.

The JSON report always contains the original evidence.

---

## Cached Evidence

By default, AuditOps can reuse previously collected evidence to speed up repeated testing.

Setting:

```python
delete_cached_evidence=True
```

forces AuditOps to collect fresh evidence before running the tests.

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

# Next Steps

Once you've successfully completed your first GitHub audit, you can:

- Share the generated PDF report with customers or auditors
- Upload reports to AuditOps
- Schedule recurring audits using cron, Task Scheduler, or CI/CD pipelines
- Review the collected evidence to investigate failed tests
- Incorporate GitHub audits into your third-party risk management process