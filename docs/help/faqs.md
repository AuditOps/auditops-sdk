# ❓ Frequently Asked Questions (FAQs)

### Who is AuditOps?
[AuditOps.io](https://auditops.io) is a cyber security company that performs in-depth vendor security reviews. We help companies answer one question: **Are my vendors secure?**

### What is the AuditOps-SDK?
An open-source Python library that proves a company is following security best practices (MFA, encryption, etc). It does this by:
* Collecting evidence
* Performing testing
* Building transparent audit reports

### Who uses AuditOps?
* **Third-party risk teams:** Review AuditOps reports to verify if a vendor is following security best practices.
* **Auditors:** Rely on AuditOps reports and supporting evidence to evaluate controls. Make sure to use the time saved to help your clients evaluate risk!
* **Sales teams:** Share reports that build trust with prospective customers and demonstrate your commitment to security & compliance.

### How is this different from a vendor’s Trust Center?
* **Transparency:** Exclusions can be added to Trust Centers with no oversight. An AuditOps report lets you view what was excluded while still protecting sensitive data.
* **Repeatability:** Test procedures are clearly defined, and backed by real evidence.
* **Cost:** Running the AuditOps-SDK is free and takes less than 5 minutes to set up.

### I already have a SOC 2 report, why do I need this?
AuditOps does not replace SOC 2 or other audit efforts. Think of AuditOps as an add-on to your SOC 2 with the following benefits:
* **Cost:** Free
* **Setup Time:** Less than 5 minutes
* **Frequency:** Run daily (instead of once a year)

### Do AuditOps reports contain sensitive data?
It is completely up to you! Use `summary_mode` to anonymize sensitive data (e.g., changing sample id's to "Sample 1", "Sample 2", etc.).


---

## 📧 How to Request an AuditOps Report

Send your vendor an email similar to the example below. Sit back, grab a coffee, and wait for them to share the report.

> 💡 **Note for Auditors:** Vendor due diligence is the primary use case of this project. Auditors should modify the language below, ensure the report isn’t using `summary_mode`, and request the supporting evidence as a ZIP file.

### Email Template

**To:** `Vendor Sales Team Contact`  
**From:** `TPRM Contact`  
**Subject:** Vendor Due Diligence (AuditOps report)

```text
Hey [Vendor Contact Name],

I hope you’re doing well! 

We are interested in moving forward with [Vendor Company Name]. We understand that you will be hosting our company’s data in Amazon Web Services. As part of our due diligence, we would like to see your most recent AuditOps PDF report. Please make sure it is generated using “summary_mode” to anonymize the report. 

AuditOps is an open-source Python library that verifies your team is following AWS best practices (MFA, access key rotation, etc). This allows us to make an informed decision before we move forward with purchasing your service. 

Below are some resources to explain more about AuditOps, and help you generate the report:
* AuditOps GitHub Project: [Insert GitHub Link]
* AuditOps FAQs: [Insert FAQ Link]
* AWS Setup Instructions: [Insert Setup Guide Link]

We really appreciate your help here. Please let us know if you need anything from us.

Best,

[Your Name]
```