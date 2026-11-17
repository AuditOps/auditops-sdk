# Project Description
The AuditOps-SDK is an open-source Python library that gathers audit evidence, performs testing, and creates actionable reports in ~25 lines of code per cloud provider (AWS, GitHub, Google Workspace, etc).

This project is maintained and published by [AuditOps.io](https://www.auditops.io).

### Use cases:
- External Audit: Obtain high quality, consistent audit evidence without requesting screenshots.
- Internal Audit: Continuously monitor your organization's cloud configurations.
- Vendor Due Diligence: Evaluate a vendor's actual security posture with transparent and timely reports.

### Resources:
- **Example Report**: [Link](https://github.com/AuditOps/auditops-sdk/blob/main/examples/summary_mode/AWS%20Audit%20Report%20(Summary%20Mode).pdf)
- **FAQs**: [Link](https://github.com/AuditOps/auditops-sdk/blob/main/docs/general/faqs.md)
- **Documentation**:
   - [AWS](https://github.com/AuditOps/auditops-sdk/blob/main/docs/providers/aws/getting-started.md)
   - [GitHub](https://github.com/AuditOps/auditops-sdk/blob/main/docs/providers/aws/github/getting-started.md)

### Getting Started (Simple AWS Example)
1. Install pre-requisites:
    * Python [Tutorial](https://www.youtube.com/watch?v=D2cwvpJSBX4)
    * AWS CLI
        * [Windows Tutorial](https://www.youtube.com/watch?v=jCHOsMPbcV0)
        * [Mac Tutorial](https://www.youtube.com/watch?v=U0AmeqL4DfE)
3. Run these commands to check if everything is installed correctly. If you receive an error, go back to the videos in Step 1.
    ```
    python --version
    aws --version
    ```
4. Install the latest version of the AuditOps-SDK python library.
    ```
    pip install -U auditops
    ```
5. Create an IAM user (or Identity Center user) in the AWS management console.
    * The user needs [Security Audit](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SecurityAudit.html) permissions.
6. Create an access key for the IAM user created in the previous step: [AWS Docs](https://docs.aws.amazon.com/keyspaces/latest/devguide/create.keypair.html)
    * NOTE: Configure the access key on your local machine using the 'aws configure' command [Video Tutorial](https://youtu.be/RLx5qVZSTyE?si=7fqyxFzThDaB-mGQ).
    * NOTE: Access keys can only be viewed once, at the time of creation.  They must be stored securely elsewhere for future use.
7. Copy the code below and name the file *auditops_example.py*.
    ```
   from auditops.core.models import Audit, AuditHelpers, ExclusionManager
   from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
   from auditops.core.utils import aws_create_session
   
   def main():
      session = aws_create_session()
      aws_config = AWSConfig(in_scope_regions=['us-east-1'])
      helpers = AuditHelpers.create()
   
      audit = Audit(
         helpers = helpers,
         title = "AWS Audit Report",
         config=aws_config,
         auditor_name = "Peter Gibbons",
         audit_folder = "aws",
         delete_cached_evidence=True,
         summary_mode=False,
         exclusions=None
      )
   
      audit.run(collector=AWSCollector(session), tester=AWSTester(), min_risk_rating=0)
   
   if __name__ == "__main__":
      main()
    ```
7. Run the code:
    ```
        python auditops_example.py
    ```
8. A new folder will be created for the audit. Within that folder, the library will collect and store the evidence in the 'audit_evidence' folder. Once collected, it will begin performing the testing and the audit reports will be stored in the 'reports' folder.