def collect_s3_evidence(collector):
    s3_client = collector.session.client("s3")

    buckets = collector.collect(
        evidence_path="s3/buckets.json",
        client=s3_client,
        method="list_buckets",
    )

    for bucket in buckets.get("Buckets", []):
        bucket_name = bucket["Name"]

        # Encryption
        collector.collect(
            evidence_path=f"s3/buckets/{bucket_name}/encryption.json",
            client=s3_client,
            method="get_bucket_encryption",
            method_kwargs={"Bucket": bucket_name},
            ignore_codes=["ServerSideEncryptionConfigurationNotFoundError"],
            warn_codes=["AccessDenied"],
        )

        # Public access block
        collector.collect(
            evidence_path=f"s3/buckets/{bucket_name}/public_access_block.json",
            client=s3_client,
            method="get_public_access_block",
            method_kwargs={"Bucket": bucket_name},
            ignore_codes=["NoSuchPublicAccessBlockConfiguration"],
            warn_codes=["AccessDenied"],
        )

        # Bucket policy
        collector.collect(
            evidence_path=f"s3/buckets/{bucket_name}/policy.json",
            client=s3_client,
            method="get_bucket_policy",
            method_kwargs={"Bucket": bucket_name},
            ignore_codes=["NoSuchBucketPolicy"],
            warn_codes=["AccessDenied"],
        )
        
        # Bucket tags
        collector.collect(
            evidence_path=f"s3/buckets/{bucket_name}/tags.json",
            client=s3_client,
            method="get_bucket_tagging",
            method_kwargs={"Bucket": bucket_name},
            ignore_codes=["NoSuchTagSet"],
            warn_codes=["AccessDenied"],
        )