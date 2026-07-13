
def collect_apigateway_evidence(collector):
    for region in collector.config.in_scope_regions:
        apigateway_client = collector.session.client(
            "apigateway",
            region_name=region,
        )

        collector.collect(
            evidence_path=f"apigateway/{region}/rest_apis.json",
            client=apigateway_client,
            paginator_params={
                "method_name": "get_rest_apis",
                "pagination_key": "items",
            },
        )