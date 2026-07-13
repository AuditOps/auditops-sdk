
def collect_guardduty_evidence(collector):
    for region in collector.config.in_scope_regions:
        guardduty_client = collector.session.client(
            "guardduty",
            region_name=region,
        )

        detectors = collector.collect(
            evidence_path=f"guardduty/{region}/detectors.json",
            client=guardduty_client,
            paginator_params={
                "method_name": "list_detectors",
                "pagination_key": "DetectorIds",
            },
        )

        for detector_id in detectors.get("DetectorIds", []):
            collector.collect(
                evidence_path=f"guardduty/{region}/{detector_id}/detector.json",
                client=guardduty_client,
                method="get_detector",
                method_kwargs={
                    "DetectorId": detector_id,
                },
            )