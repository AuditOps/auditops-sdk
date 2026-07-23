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
4. Install the auditops library
    ```
    pip install auditops
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
    from auditops.core.utils import aws_create_session, run_audit
    
    def main():
        prod_session = aws_create_session()
        us_prod_aws_config = AWSConfig(in_scope_regions=['us-east-1'])
        helpers = AuditHelpers.create()
    
        audit = Audit(helpers = helpers, title = "AWS Audit Report", auditor_name = "AJ Dehn",
        config = us_prod_aws_config, evidence_folder = "aws")
    
        run_audit(audit, AWSCollector(prod_session, audit), AWSTester(audit))
    
    if __name__ == "__main__":
        main()
    ```
8. Run the code:
    ```
        python auditops_example.py
    ```
9. The library will create a new 'tmp' folder containing audit_evidence and reports.


## Design Philosophy:
1. **Lightweight:** You can setup this library in minutes, and it doesn't require intensive integrations with your cloud providers. This eliminates vendor lock-in and gives you control over how your data is processed.
2. **Repeatability:** Clear instructions explain how evidence was gathered and describes the test procedures that were performed. Share your AuditOps report + supporting evidence, and kindly ask your auditor to re-perform the work that was already done.
3. **Anti-Checkbox:** We all know that compliance has become a check-box exercise. We hope you'll use this library to fight against it and start holding everyone to higher standard.
