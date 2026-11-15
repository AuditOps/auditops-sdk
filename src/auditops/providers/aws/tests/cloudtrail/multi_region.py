from auditops.core.utils import create_test


def check_cloudtrail_multi_region(tester):
    metadata = {
        "test_id": "aws-cloudtrail-001",
        "test_description": "At least one multi-region CloudTrail trail has logging enabled.",
        "risk_rating": 3,
        "test_procedures": [
            "Called the [describe_trails()](https://docs.aws.amazon.com/boto3/latest/reference/services/cloudtrail/client/describe_trails.html) "
            "boto3 command to obtain a list of CloudTrail trails.",            
            "Saved the API response: cloudtrail/trails.json.",
            "For each CloudTrail trail, inspected the trail configuration to determine whether 'IsMultiRegionTrail' is set to 'true'.",
            "For each multi-region trail, performed the following steps:",
            "- Called the [get_trail_status(https://docs.aws.amazon.com/boto3/latest/reference/services/cloudtrail/client/get_trail_status.html)] "
            "boto3 command to obtain information about the trail.",
            "- Saved the API response: cloudtrail/trails/[TRAIL_NAME]/trail_status.json.",
            "Inspected the trail configuration and status for each multi-region CloudTrail to determine "
            "if at least one trail complied with the test attribute(s) defined below."
        ],
        "test_attributes": [
            "At least one trail must have IsMultiRegionTrail = true and IsLogging = true."
        ],             
    }
    test = create_test(tester, metadata)

    trails = tester.read("cloudtrail/trails.json")

    if not trails:
        return test.fail("ERROR: Unable to retrieve required evidence (cloudtrail/trails.json).")        
  
    for trail in trails.get("trailList", []):
        if not trail.get("IsMultiRegionTrail", False):
            continue
        status = tester.read(f"cloudtrail/trails/{trail['Name']}/trail_status.json", optional=True)
        if not status:
            return test.fail("ERROR: Unable to retrieve required evidence (cloudtrail/TRAIL_NAME/trails.json).")

        if status.get("IsLogging", False):
            test.is_passing = True
            return test

    return test.fail("Exceptions Noted. No multi-region CloudTrail trail with active logging was found.")