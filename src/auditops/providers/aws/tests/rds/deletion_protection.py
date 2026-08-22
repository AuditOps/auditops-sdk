from auditops.core.models import Sample
from auditops.core.utils import create_test


def check_rds_deletion_protection(tester):
    metadata = {
        "test_id": "aws-rds-005",
        "test_description": "RDS instances have deletion protection enabled at the cluster or instance level.",
        "risk_rating": 2,
        "test_procedures": [
            "For each in-scope region, obtained a list of RDS instances and RDS clusters using describe_db_instances() and describe_db_clusters() boto3 commands.",
            "Saved the list of RDS instances: rds/[region_name]/db_instances.json and DB clusters: rds/[region_name]/db_clusters.json.",
            "Inspected each RDS instance to determine if 'DeletionProtection' was set to 'true' at the instance or cluster level."
        ],
        "test_attributes": [],
        "table_headers": ["Region", "DB Instance", "Result", "Comments"],
    }

    test = create_test(tester, metadata)

    cluster_maps = {}

    for region in tester.config.in_scope_regions:
        clusters = tester.read(f"rds/{region}/db_clusters.json")

        if not clusters:
            return test.fail(f"ERROR: Unable to retrieve required evidence (rds/{region}/db_clusters.json).")


        cluster_maps[region] = {
            cluster["DBClusterIdentifier"]: cluster.get("DeletionProtection", False)
            for cluster in clusters.get("DBClusters", [])
        }

    for region in tester.config.in_scope_regions:
        instances = tester.read(f"rds/{region}/db_instances.json")

        if not instances:
            return test.fail(f"ERROR: Unable to retrieve required evidence (rds/{region}/db_instances.json).")


        for db_instance in instances.get("DBInstances", []):
            sample = Sample(
                sample_id={
                    "region": region,
                    "db_instance": db_instance["DBInstanceIdentifier"],
                }
            )

            instance_protection = db_instance.get("DeletionProtection", False)
            cluster_id = db_instance.get("DBClusterIdentifier")
            cluster_protection = cluster_maps[region].get(cluster_id, False) if cluster_id else False

            sample.is_passing = instance_protection or cluster_protection

            if not sample.is_passing:
                if cluster_id:
                    sample.comments = (
                        "Deletion protection is not enabled at either the instance or cluster level."
                    )
                else:
                    sample.comments = (
                        "Deletion protection is not enabled at the instance level."
                    )

            test.samples.append(sample)

    test.evaluate_samples(
        tester.exclusions,
        failure_message="RDS instance(s) do not have deletion protection enabled."    
    )

    return test