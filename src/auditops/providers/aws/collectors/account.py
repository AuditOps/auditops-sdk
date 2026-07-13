def collect_account_identity(collector):
    sts_client = collector.session.client("sts")

    collector.collect(
        evidence_path = "account/account_identity.json",
        client = sts_client,
        method = "get_caller_identity"
    )