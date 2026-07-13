
def collect_wafv2_evidence(collector):
    for region in collector.config.in_scope_regions:
        wafv2_client = collector.session.client(
            "wafv2",
            region_name=region,
        )

        web_acls = collector.collect(
            evidence_path=f"wafv2/{region}/web_acls.json",
            client=wafv2_client,
            method="list_web_acls",
            method_kwargs={
                "Scope": "REGIONAL",
            },
        )

        for web_acl in web_acls.get("WebACLs", []):
            collector.collect(
                evidence_path=f"wafv2/{region}/{web_acl['Name']}_{web_acl['Id']}/resources.json",
                client=wafv2_client,
                method="list_resources_for_web_acl",
                method_kwargs={
                    "WebACLArn": web_acl["ARN"],
                },
            )