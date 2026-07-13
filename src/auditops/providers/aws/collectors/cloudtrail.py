
def collect_cloudtrail_evidence(collector):
    cloudtrail_client = collector.session.client("cloudtrail")

    trails = collector.collect(
        evidence_path="cloudtrail/trails.json",
        client=cloudtrail_client,
        method="describe_trails",
    )

    for trail in trails.get("trailList", []):
        trail_name = trail["Name"]

        collector.collect(
            evidence_path=f"cloudtrail/trails/{trail_name}/trail_status.json",
            client=cloudtrail_client,
            method="get_trail_status",
            method_kwargs={
                "Name": trail_name,
            },
        )