

# AWS Setup Instructions
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
        session = aws_create_session()
        aws_config = AWSConfig(in_scope_regions=['us-east-1'])
        helpers = AuditHelpers.create()

        audit = Audit(helpers = helpers, title = "AWS Audit Report", config=aws_config,
        auditor_name = "AJ Dehn", evidence_folder = "aws")

        run_audit(audit, AWSCollector(session, audit), AWSTester(audit))

    if __name__ == "__main__":
        main()
    ```
8. Run the code:
    ```
        python auditops_example.py
    ```
9. The library will create a new 'tmp' folder containing audit_evidence and reports.