# Purpose
Gather evidence, perform testing, and create audit reports in ~25 lines of code per tool.

## Use cases:
- Vendor Due Diligence: Evaluate your vendors actual security posture (transparent and timely reports allows you to truly evaluate risk).
- Audits: Automatically collect and upload high quality evidence directly to your auditor (no screenshots required).

## What this library does:
1. Evidence Collection: Gathers evidence (JSON files) directly from your vendor's API or SDK.
2. Testing: Logic based configuration tests (encryption, MFA, key rotation, etc) against your cloud environment.
3. Report Building: Builds JSON & PDF reports that summarize findings from each test & tool.
4. Upload: Share full audit packages (evidence & audit reports) with auditors, customers, and regulators.

## Philosophy:
1. Lightweight: You can setup this library in minutes, and it doesn't require intensive integrations with your cloud providers. This eliminates vendor lock-in and gives you control over how your data is processed.
2. Repeatability: Clear instructions explain how evidence was gathered and describes the test procedures that were performed. Share your AuditOps report + supporting evidence, and kindly ask your auditor to re-perform the work that was already done.
3. Anti-Checkbox: We all know that compliance has become a check-box exercise. We hope you'll use this library to fight against it and start holding everyone to higher standard.