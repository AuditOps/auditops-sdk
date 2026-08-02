# Frequently Asked Questions (FAQs)

### Who is AuditOps?
[AuditOps.io](https://auditops.io) is a cyber security company that performs in-depth vendor security reviews. We help companies answer one question: **Are my vendors secure?**

### What is the AuditOps-SDK?
An open-source Python library that proves cloud tools (ex. AWS) are following security best practices. It does this by:
* Automatically collecting evidence
* Performing testing (ex. MFA, key rotation, encryption, etc)
* Building transparent audit reports

### Who uses the AuditOps-SDK?
* **Third-party risk teams:** Review AuditOps reports to verify your vendors are following security best practices.
* **Auditors:** Rely on AuditOps reports and supporting evidence to evaluate controls.
* **Sales teams:** Share reports that build trust with prospective customers and demonstrate your commitment to security & compliance.

### How can I support this project?
1. **Free**: Incorporate the AuditOps-SDK into your vendor due diligence process. It's free, holds vendors accountable, and helps your team evaluate risk.
   - Check out these [instructions](request_report.md) to request a report from your vendor.
2. **Free**: Share an AuditOps report with prospective customers to brag about your security posture. It's free, secure (sensitive data is anonymized), and helps build trust prospective clients.
   - Check out these [instructions](share_report.md) to share a report with your customer's.
3. **Free**: Schedule a training for your non-profit (ISACA, IIA, etc), TPRM team, or audit firm. We want to spread the word, and won't make it a sales pitch.
   - Email info@auditops.io for more information.
5. **Paid**: Reach out to AuditOps to learn about our vendor monitoring service! We will keep an eye on your vendors, and make sure they are compliant **every day**, not just once per year.
   - Email info@auditops.io for more information.

### Why should I incorporate AuditOps into my third-party risk process?
1. No added cost to your vendors. This is a free way to evaluate risk and the scan can be run in 5 minutes.
2. Real risk reduction. Following AWS best practices like MFA, access key rotation, etc. decrease the likelihood a vendor has a security incident.
3. Raising the bar. An AuditOps scan will go into more depth than almost any other due diligence request. If your vendor isn't following best practices, they will either need to share a less than ideal report OR improve their security posture to send you a clean report.

### Why should I incorporate AuditOps into my third-party risk process?
1. **Faster vendor assessments**: Traditional security questionnaires take weeks to complete and review. An AuditOps scan can be run in ~5 minutes and creates a standardized report that helps your team assess risk.
2. **Objective technical evidence**: Instead of relying solely on questionnaire responses, AuditOps evaluates your vendor's AWS environment against security best practices.
3. **Encourages stronger security practices**: Vendors receive immediate feedback (ex. missing MFA, public S3 bucket, unencrypted databases, etc). Your vendors want to win your business, so they will be motivated to remediate before sharing the report back with you.
4. **No licensing cost for vendors**: AuditOps is free for vendors to run, reducing friction during the due diligence process and making it easier to request a technical security assessment.

### How is this different from a vendor’s Trust Center?
When buying a house, you wouldn't let the seller pick the home inspector. The same applies to third-party risk management.

Trust Centers are great for sharing information, but lack transparency and could provide a false sense of security.
* **Transparency:** Exclusions can be added to Trust Centers with no oversight. An AuditOps report can be run in "summary_mode" to let you evaluate what vendors excluded from the requirements without sharing sensitive data.
* **Repeatability:** Test procedures are clearly defined, and backed by real evidence.
* **Cost:** Running the AuditOps-SDK is free and takes less than 5 minutes to set up.

### I already have a SOC 2 report, why do I need this?
This project does not replace SOC 2 or other audit efforts. Think of the AuditOps-SDK as an add-on to SOC 2 with the following benefits:
* **Cost:** Free
* **Setup Time:** Less than 5 minutes
* **Transparency:** Clear instructions of how testing was performed, and what was excluded.

### Do reports from the AuditOps-SDK contain sensitive data?
It is completely up to you! Use `summary_mode` to anonymize sensitive data (e.g., changing sample id's to "Sample 1", "Sample 2", etc.).
