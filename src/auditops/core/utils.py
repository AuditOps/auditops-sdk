from auditops.core.models import Test, Audit
import boto3, os, shutil, json, logging

logger = logging.getLogger(__name__)


def delete_evidence_folder(path):
    # Delete underlying folder structure
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except OSError as e:
        logger.error("Error: %s : %s" % (path, e.strerror))

def fail_test(test, message):
    test.is_passing = False
    test.comments = message
    return test

def create_test(tester, metadata):
    test = Test(**metadata)

    exclusion = tester.exclusions.get_test_exclusion(test.test_id)
    if exclusion:
        test.is_excluded = True
        test.comments = exclusion.rationale

    return test

def evaluate_tags(sample, required_tags, actual_resource_tags):
    """
    Evaluates required tags against resource tags (S3, RDS, EC2, etc).

    Args:
        sample (Sample): The sample object to update with results.
        required_tags (list): List of required tag keys.
        resource_tags (dict): Dictionary of tag key/value pairs from the resource.

    Returns:
        None. Updates sample.is_passing and sample.comments in-place.
    """    
    # Normalize keys to lowercase for comparison
    actual_resource_tags_lower = {k.lower(): v for k, v in actual_resource_tags.items()}

    missing_tags = []
    empty_tags = []

    for key in required_tags:
        key_lower = key.lower()
        if key_lower not in actual_resource_tags_lower:
            missing_tags.append(key)
        elif actual_resource_tags_lower[key_lower].strip() == "":
            empty_tags.append(key)

    if not missing_tags and not empty_tags:
        sample.is_passing = True
    else:
        if missing_tags:
            sample.comments += f"Missing tags: {missing_tags}. "
        if empty_tags:
            sample.comments += f"Empty tag values: {empty_tags}."

def aws_create_session(session_name="auditops-assume-role", role_arn=None, external_id=None):
    # No role provided, use local credentials.
    if not role_arn and not external_id:
        logger.info(f"New session created using local Boto3 credentials.")
        return boto3.Session()

    # TODO: Fail hard if role_arn doesn't work....

    # Check if role_arn and external_id are set.
    if not (role_arn and external_id):
        raise ValueError("Both 'role_arn' and 'external_id' must be set in the environment to assume a role.")
    
    creds = aws_assume_role(role_arn, external_id, session_name)
    logger.info(f"New session created using IAM role.")

    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"]
    )

def aws_assume_role(role_arn, external_id, session_name):
    sts = boto3.client("sts")
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            ExternalId=external_id,
            RoleSessionName=session_name
        )
    except ClientError as e:
        raise RuntimeError(
            f"Failed to assume role {role_arn}: "
            f"{e.response['Error']['Message']}"
        ) from e

    return response["Credentials"]

def run_audit(audit, collector, tester):
    """Collect evidence, execute tests, and save the audit reports."""

    evidence_path = audit.reader.evidence_dir / audit.evidence_folder

    if audit.delete_cached_evidence:
        logger.info(f"Deleting evidence in: {evidence_path}.")
        delete_evidence_folder(evidence_path)
    elif evidence_path.exists():
        logger.info(f"Using cached evidence in: {evidence_path}")

    collector.gather_evidence()

    audit.test_results = tester.run_tests()
    audit.scope = tester.get_scope()
    audit.report_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    with audit.json_report_path.open("w", encoding="utf-8") as f:
        json.dump(audit.to_dict(), f, indent=4, default=str)

    # Save PDF report
    audit.report_builder.build(audit, str(audit.pdf_report_path), summary_mode=audit.summary_mode)