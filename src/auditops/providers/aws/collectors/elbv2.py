
def collect_elbv2_evidence(collector):
    for region in collector.config.in_scope_regions:
        elbv2_client = collector.session.client(
            "elbv2",
            region_name=region,
        )

        collector.collect(
            evidence_path=f"elbv2/{region}/load_balancers.json",
            client=elbv2_client,
            paginator_params={
                "method_name": "describe_load_balancers",
                "pagination_key": "LoadBalancers",
            },
        )