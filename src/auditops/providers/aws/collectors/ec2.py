def collect_ec2_ebs_evidence(collector):
    for region in collector.config.in_scope_regions:
        ec2_client = collector.session.client(
            "ec2",
            region_name=region,
        )
        collect_ec2_instances(collector, ec2_client, region)
        collect_ec2_security_groups(collector, ec2_client, region)
        collect_ebs_volumes(collector, ec2_client, region)
        collect_ebs_default_encryption(collector, ec2_client, region)


def collect_ec2_instances(collector, ec2_client, region):
    collector.collect(
        evidence_path = f"ec2/{region}/instances.json",
        client = ec2_client,
        paginator_params = {
            "method_name": "describe_instances",
            "pagination_key": "Reservations",
        },
    )


def collect_ec2_security_groups(collector, ec2_client, region):
    collector.collect(
        evidence_path = f"ec2/{region}/security_groups.json",
        client = ec2_client,
        paginator_params = {
            "method_name": "describe_security_groups",
            "pagination_key": "SecurityGroups",
        },
    )


def collect_ebs_volumes(collector, ec2_client, region):
    collector.collect(
        evidence_path = f"ec2/{region}/volumes.json",
        client = ec2_client,
        paginator_params = {
            "method_name": "describe_volumes",
            "pagination_key": "Volumes",
        },
    )


def collect_ebs_default_encryption(collector, ec2_client, region):
    collector.collect(
        evidence_path = f"ec2/{region}/ebs_encryption_by_default.json",
        client = ec2_client,
        method = "get_ebs_encryption_by_default",
    )