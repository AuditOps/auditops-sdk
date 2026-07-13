
def collect_rds_evidence(collector):
    for region in collector.config.in_scope_regions:
        rds_client = collector.session.client("rds", region_name=region)

        collector.collect(
            evidence_path=f"rds/{region}/db_instances.json",
            client=rds_client,
            paginator_params={
                "method_name": "describe_db_instances",
                "pagination_key": "DBInstances",
            },
        )

        collector.collect(
            evidence_path=f"rds/{region}/db_clusters.json",
            client=rds_client,
            paginator_params={
                "method_name": "describe_db_clusters",
                "pagination_key": "DBClusters",
            },
        )