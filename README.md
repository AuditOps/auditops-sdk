# Project Description
Gathers evidence, performs testing, and creates audit reports in ~25 lines of code per provider (AWS, GitHub, etc).

This project is maintained and published by [AuditOps.io](https://www.auditops.io).

### Use cases:
- Vendor Due Diligence: Evaluate your vendors actual security posture using transparent and timely reports.
- Audits: Automatically collect and share high quality evidence directly to your auditor (no screenshots required).

### Getting Started (AWS Example)
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
    pip install -U <package_name>
    ```
5. Create an IAM user (or Identity Center user) in the AWS management console.
    * The user needs [Security Audit](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SecurityAudit.html) permissions.
6. Create an access key for the IAM user created in the previous step: [AWS Docs](https://docs.aws.amazon.com/keyspaces/latest/devguide/create.keypair.html)
    * NOTE: Configure the access key on your local machine using the 'aws configure' command [Video Tutorial](https://youtu.be/RLx5qVZSTyE?si=7fqyxFzThDaB-mGQ).
    * NOTE: Access keys can only be viewed once, at the time of creation.  They must be stored securely elsewhere for future use.
7. Copy the code below and name the file *auditops_example.py*.
    ```
   from auditops.core.models import Audit, AuditHelpers
   from auditops.providers.aws import AWSCollector, AWSTester, AWSConfig
   from auditops.core.utils import aws_create_session
   import boto3
   from datetime import datetime
   
   def main():
       session = aws_create_session()
       aws_config = AWSConfig(in_scope_regions=['us-east-1'])
       helpers = AuditHelpers.create()
   
       audit = Audit(helpers = helpers, title = "AWS Audit Report", config=aws_config, auditor_name = "AJ Dehn",
       audit_folder = "aws", delete_cached_evidence=True, summary_mode=True, exclusions=None)
   
       audit.run(collector=AWSCollector(session), tester=AWSTester())

       # Upload to AuditOps (for vendor due diligence and/or audit requests)
       audit.upload(destination="auditops", package="pdf", client_email="john@acme.com")    

       # OPTIONAL: Upload to S3 (for data retention). NOTE: Please replace the "BUCKET_NAME".
       bucket_save_path = datetime.now().strftime("%Y/%m/%d/aws")
       audit.upload(destination="s3", package="full", client=boto3.client("s3"), bucket="BUCKET_NAME", key=bucket_save_path)
   
   if __name__ == "__main__":
       main()

    ```
7. Run the code:
    ```
        python auditops_example.py
    ```
8. A new folder will be created for the audit. Within that folder, the library will collect and store the evidence in the 'audit_evidence' folder. Once collected, it will begin performing the testing and the audit reports will be stored in the 'reports' folder.


## Design Philosophy:
1. **Lightweight:** You can setup this library in minutes, and it doesn't require intensive integrations with your cloud providers. This eliminates vendor lock-in and gives you control over how your data is processed.
2. **Repeatability:** Clear instructions explain how evidence was gathered and describes the test procedures that were performed. Share your AuditOps report + supporting evidence, and kindly ask your auditor to re-perform the work that was already done.
3. **Anti-Checkbox:** We all know that compliance has become a check-box exercise. We hope you'll use this library to fight against it and start holding everyone to higher standard.
