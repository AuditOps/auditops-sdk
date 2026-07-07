from auditops.core.models import Test


def fail_test(test, message):
    test.is_passing = False
    test.comments = message
    return test


def create_test(tester, metadata):
    test = Test(**metadata)

    exclusion = tester.exclusions.get_test_exclusion(tester.provider, test.test_id)
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