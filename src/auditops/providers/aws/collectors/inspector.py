from datetime import datetime, timedelta, timezone

def collect_inspector_overdue_findings(collector, inspector_client, region):
    INSPECTOR_SLA_DAYS = collector.config.inspector_sla_days

    resource_types = [
        "AWS_EC2_INSTANCE",
        "AWS_LAMBDA_FUNCTION",
    ]

    for severity, sla_days in INSPECTOR_SLA_DAYS.items():
        cutoff = datetime.now(timezone.utc) - timedelta(days=sla_days)

        # Separate evidence paths for cached results and combined findings.
        ec2_lambda_path = (
            f"inspector/{region}/{severity.lower()}_ec2_lambda_overdue.json"
        )
        ecr_path = (
            f"inspector/{region}/{severity.lower()}_ecr_overdue.json"
        )
        findings_path = (
            f"inspector/{region}/{severity.lower()}_overdue.json"
        )

        # Collect overdue EC2 and Lambda findings.
        findings = collector.collect(
            evidence_path=ec2_lambda_path,
            client=inspector_client,
            paginator_params={
                "method_name": "list_findings",
                "pagination_key": "findings",
                "params": {
                    "filterCriteria": {
                        "findingStatus": [
                            {"comparison": "EQUALS", "value": "ACTIVE"},
                        ],
                        "severity": [
                            {"comparison": "EQUALS", "value": severity},
                        ],
                        "resourceType": [
                            {"comparison": "EQUALS", "value": resource_type}
                            for resource_type in resource_types
                        ],
                        "firstObservedAt": [
                            {"endInclusive": cutoff},
                        ],
                    },
                },
            },
        )

        # Collect overdue ECR findings for images currently in use.
        ecr_findings = collector.collect(
            evidence_path=ecr_path,
            client=inspector_client,
            paginator_params={
                "method_name": "list_findings",
                "pagination_key": "findings",
                "params": {
                    "filterCriteria": {
                        "findingStatus": [
                            {"comparison": "EQUALS", "value": "ACTIVE"},
                        ],
                        "severity": [
                            {"comparison": "EQUALS", "value": severity},
                        ],
                        "resourceType": [
                            {
                                "comparison": "EQUALS",
                                "value": "AWS_ECR_CONTAINER_IMAGE",
                            },
                        ],
                        "ecrImageInUseCount": [
                            {"lowerInclusive": 1},
                        ],
                        "firstObservedAt": [
                            {"endInclusive": cutoff},
                        ],
                    },
                },
            },
        )

        # Combine the results into one evidence file.
        combined_findings = {
            **findings,
            "findings": (
                findings.get("findings", [])
                + ecr_findings.get("findings", [])
            ),
        }

        collector.writer.save_json(
            f"{collector.audit_folder}/audit_evidence/{findings_path}",
            combined_findings,
        )

def collect_inspector_evidence(collector):
    sts_client = collector.session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    for region in collector.config.in_scope_regions:
        inspector_client = collector.session.client(
            "inspector2",
            region_name=region,
        )

        collector.collect(
            evidence_path=f"inspector/{region}/account_status.json",
            client=inspector_client,
            method="batch_get_account_status",
            method_kwargs={
                "accountIds": [account_id],
            },
        )

        collector.collect(
            evidence_path=f"inspector/{region}/coverage.json",
            client=inspector_client,
            paginator_params={
                "method_name": "list_coverage",
                "pagination_key": "coveredResources",
            },
        )

        collect_inspector_overdue_findings(collector, inspector_client, region)