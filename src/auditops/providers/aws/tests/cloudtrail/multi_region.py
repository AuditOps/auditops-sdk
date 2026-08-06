from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_cloudtrail_multi_region(tester):
    metadata = {
        "test_id": "aws-cloudtrail-001",
        "test_description": "At least one multi-region CloudTrail trail has logging enabled.",
        "risk_rating": 3,
        "test_procedures": [
            "Obtained a list of CloudTrail trails by calling the describe_trails() boto3 command.",
            "Saved the list of CloudTrail trails: cloudtrail/trails.json.",
            "For each CloudTrail trail, inspected the trail configuration to determine whether 'IsMultiRegionTrail' is set to 'true'.",
            "For each multi-region trail, obtained the trail status by calling the get_trail_status() boto3 command.",
            "For each multi-region trail, saved the trail status: cloudtrail/trails/[trail_name]/trail_status.json.",
            "Inspected the trail configuration and status to determine if at least one trail complies with the test attribute(s) defined below."
        ],
        "test_attributes": [
            "At least one trail must have IsMultiRegionTrail = true and IsLogging = true."
        ],             
    }
    test = create_test(tester, metadata)

    trails = tester.read("cloudtrail/trails.json").get("trailList", [])

    if not trails:
        return test.fail("Exceptions Noted. No CloudTrail trail was found.")

    found_valid_trail = False
    for trail in trails:
        if not trail.get("IsMultiRegionTrail", False):
            continue
        status = tester.read(f"cloudtrail/trails/{trail['Name']}/trail_status.json")
        if status.get("IsLogging", False):
            found_valid_trail = True
            break

    if found_valid_trail:
        test.is_passing = True
    else:
        return test.fail("Exceptions Noted. No multi-region CloudTrail trail with active logging was found.")

    return test