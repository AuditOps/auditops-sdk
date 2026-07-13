
def collect_lambda_evidence(collector):
    for region in collector.config.in_scope_regions:
        lambda_client = collector.session.client("lambda", region_name=region)

        functions = collector.collect(
            evidence_path = f"lambda/{region}/functions.json",
            client = lambda_client,
            paginator_params={
                "method_name": "list_functions",
                "pagination_key": "Functions",
            },
        )

        for function in functions.get("Functions", []):
            function_name = function["FunctionName"]

            # TODO: Consider collecting lambda function configuration evidence.
            # NOTE: Includes function's environment variables. May contain secrets (API keys, passwords, etc)
            """
            collector.collect(
                f"lambda/{region}/functions/{function_name}/configuration.json",
                lambda_client,
                method="get_function_configuration",
                method_kwargs={
                    "FunctionName": function["FunctionArn"],
                },
            )
            """

            collector.collect(
                f"lambda/{region}/functions/{function_name}/tags.json",
                lambda_client,
                method="list_tags",
                method_kwargs={
                    "Resource": function["FunctionArn"],
                },
            )