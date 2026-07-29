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
1. Free: Incorporate the AuditOps-SDK into your vendor due diligence process. It's free, holds vendors accountable, and helps your team evaluate risk.
2. Free: Schedule a training for your non-profit (ISACA, IIA, etc), TPRM team, or audit firm. We want to spread the word, and won't give you a sales pitch. Email us at info@auditops.io for more information.
3. Paid: Sign-up for the AuditOps vendor monitoring service! We will keep an eye on your vendors, and make sure they are compliant **every day**, not just once per year.

### How is this different from a vendor’s Trust Center?
If you're buying a house, would you let the seller pick the home inspector? I certainly wouldn't recommend it!

Trust Centers are great for sharing information, but they aren't transparent and allow companies to hide real risks.
* **Transparency:** Exclusions can be added to Trust Centers with no oversight. An AuditOps report can be run in "summary_mode" to let you evaluate risk while still protecting sensitive data.
* **Repeatability:** Test procedures are clearly defined, and backed by real evidence.
* **Cost:** Running the AuditOps-SDK is free and takes less than 5 minutes to set up.

### I already have a SOC 2 report, why do I need this?
This project does not replace SOC 2 or other audit efforts. Think of the AuditOps-SDK as an add-on to your SOC 2 with the following benefits:
* **Cost:** Free
* **Setup Time:** Less than 5 minutes
* **Frequency:** Run daily (instead of once per year)

### Do AuditOps reports contain sensitive data?
It is completely up to you! Use `summary_mode` to anonymize sensitive data (e.g., changing sample id's to "Sample 1", "Sample 2", etc.).
