from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
from datetime import datetime, timezone
from pathlib import Path
from .reporting.pdf_report_builder import PDFReportBuilder
from .evidence.reader import EvidenceReader
from .evidence.writer import EvidenceWriter
from .exclusions import ExclusionManager
import json, logging, os, shutil
from zipfile import ZipFile, ZIP_DEFLATED
import mimetypes
import requests

logger = logging.getLogger(__name__)


@dataclass
class AuditHelpers:
    reader: EvidenceReader
    writer: EvidenceWriter
    report_builder: PDFReportBuilder
    publisher: Publisher

    @classmethod
    def create(cls, exclusions_file: str | None = None):
        return cls(
            reader=EvidenceReader(),
            writer=EvidenceWriter(),
            report_builder=PDFReportBuilder(),
            publisher=Publisher(),
        )


@dataclass(slots=True)
class Audit:
    # Required fields
    helpers: AuditHelpers
    title: str

    # Audit configuration
    config: object | None = None            # Defines key variables for audit testing (ex. minimum password length)
    exclusions: ExclusionManager = field(default_factory=ExclusionManager)

    # Report metadata
    auditor_name: str = "AuditOps"
    report_name: str | None = None          # Defines the file name of the PDF and JSON report (ex. "aws_us_prod").
    report_date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    # Execution
    summary_mode: bool = False              # Anonymizes sample data when set to true.
    audit_folder: str | None = None         # Will be under the "tmp" folder (ex. "aws/us_prod"). Contains two subfolders: "audit_evidence" and "reports"
    delete_cached_evidence: bool = True     # Deletes previously gathered evidence (set to "False" when troubleshooting)

    # Results
    scope: list[str] = field(default_factory=list)
    test_results: list[Test] = field(default_factory=list)

    def __post_init__(self):
        self.report_name = self.report_name or self.title

    def get_scope_formatted(self):
        html = []

        for item in self.scope:
            if ":" in item:
                label, value = item.split(":", 1)
                html.append(f"<b>{label}:</b> {value}")
            else:
                html.append(item)

        html_output = "<br/>".join(html)

        return html_output

    def to_dict(self):
        return {
            "metadata": {
                "scope": self.scope,
                "report_date": self.report_date
            },
            "test_results": [t.to_dict(summary_mode=self.summary_mode) for t in self.test_results]
        }
    
    def run(self, collector, tester):
        self.collect_evidence(collector)
        self.perform_testing(tester)
        self.save_reports()


    def upload(self, destination: str, **kwargs):
        logger.info(f"Uploading to {destination}.")
        return self.publisher.publish(self, destination=destination, **kwargs)

    def collect_evidence(self, collector):
        audit_folder = self.reader.root_dir / self.audit_folder

        if self.delete_cached_evidence:
            # NOTE: Deleting the full audit folder (evidence + reports).
            # NOTE: Avoids confusion if the end user changes the report name.
            if audit_folder.exists():
                logger.info(f"Deleting audit folder: {audit_folder}.")

                # Delete audit folder.
                try:
                    if os.path.exists(audit_folder):
                        shutil.rmtree(audit_folder)
                except FileNotFoundError as e:
                    logger.error("Error: %s : %s" % (audit_folder, e.strerror))

        elif audit_folder.exists():
            logger.info(f"Using cached evidence in: {audit_folder}")
        
        logger.info(f"Gathering evidence for: {self.report_name}")
        
        collector.gather_evidence(self)

    def perform_testing(self, tester):
        logger.info(f"Performing testing for: {self.report_name}")
        tester.run_tests(self)

    def save_reports(self):
        # Saves a JSON and PDF report to the "reports" folder.
        self.report_dir.mkdir(parents=True, exist_ok=True)

        with self.json_report_path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, default=str)

        self.report_builder.build(
            self,
            str(self.pdf_report_path),
            summary_mode=self.summary_mode,
        )

    @property
    def reader(self):
        return self.helpers.reader

    @property
    def writer(self):
        return self.helpers.writer

    @property
    def report_builder(self):
        return self.helpers.report_builder

    @property
    def publisher(self):
        return self.helpers.publisher

    @property
    def report_dir(self) -> Path:
        path = Path(self.reader.root_dir) / self.audit_folder / "reports"
        return path

    @property
    def audit_folder_dir(self) -> Path:
        path = Path(self.reader.root_dir) / self.audit_folder
        return path

    @property
    def json_report_path(self) -> Path:
        return self.report_dir / f"{self.report_name}.json"

    @property
    def pdf_report_path(self) -> Path:
        return self.report_dir / f"{self.report_name}.pdf"


class Publisher:
    """Uploads audit reports (JSON + PDF) or full audit package to a supported destination."""

    VALID_DESTINATIONS = {"s3", "portal", "auditops"}
    VALID_PACKAGES = {"full", "json", "pdf"}

    def publish(self, audit, destination: str, package: str = "json", **kwargs):
        """
        package options:
            json    -> JSON report only (default)
            full    -> Zip of report directory
            pdf     -> PDF report only
        
        destination options:
            s3          -> For audit package retention
            auditops    -> For vendor due diligence and/or audit support requests
            portal      -> Other web application (ex. auditor upload page)

        kwargs:
            Destination-specific upload parameters.
        """

        destination = destination.lower()
        package = package.lower()

        if destination not in self.VALID_DESTINATIONS:
            raise ValueError(
                f"Invalid destination '{destination}'. "
                f"Valid options: {', '.join(sorted(self.VALID_DESTINATIONS))}."
            )

        if package not in self.VALID_PACKAGES:
            raise ValueError(
                f"Invalid package '{package}'. "
                f"Valid options: {', '.join(sorted(self.VALID_PACKAGES))}."
            )

        upload_file = self._get_upload_file(audit, package)

        if destination == "s3":
            self._upload_s3(upload_file, **kwargs)

        elif destination == "portal":
            self._upload_portal(upload_file, **kwargs)

        elif destination == "auditops":
            self._upload_portal(upload_file, upload_url="https://upload.auditops.io", **kwargs)

    def _get_upload_file(self, audit, package: str) -> Path:
        """Return the file that should be uploaded."""

        if package == "json":
            return audit.json_report_path

        if package == "pdf":
            return audit.pdf_report_path

        return self._build_zip(audit)

    def _build_zip(self, audit) -> Path:
        """Create a zip containing the entire directory (reports and evidence)."""

        zip_path = audit.audit_folder_dir / f"{audit.report_name}.zip"

        with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
            for file in audit.audit_folder_dir.rglob("*"):
                if file == zip_path:
                    continue

                if file.is_file():
                    zip_file.write(
                        file,
                        arcname=file.relative_to(audit.audit_folder_dir),
                    )

        return zip_path

    def _upload_s3(self, file_path: Path, **kwargs):
        """
        Upload a report or full audit package to Amazon S3.

        Required kwargs:
            bucket: str
            boto3_client: boto3 S3 client

        Optional kwargs:
            key: S3 object key (defaults to file name)
            extra_args: dict of ExtraArgs passed to upload_file()
        """

        bucket = kwargs.get("bucket")
        client = kwargs.get("client")
        key = kwargs.get("key", file_path.name)
        extra_args = kwargs.get("extra_args")

        if not bucket:
            raise ValueError("'bucket' is required when uploading to S3.")

        if client is None:
            raise ValueError("'client' is required when uploading to S3.")

        if not file_path.exists():
            raise FileNotFoundError(f"Upload file does not exist: {file_path}")

        client.upload_file(
            Filename=str(file_path),
            Bucket=bucket,
            Key=key
        )

        return {
            "bucket": bucket,
            "key": key,
        }

    def _upload_portal(self, file_path: Path, *, upload_url: str, client_email: str, timeout: int = 30,):
        """Upload a report to an auditor portal."""

        content_type = (
            mimetypes.guess_type(file_path)[0]
            or "application/octet-stream"
        )

        with file_path.open("rb") as f:
            response = requests.post(
                upload_url,
                data={
                    "client_email": client_email,
                },
                files={
                    "file": (
                        file_path.name,
                        f,
                        content_type,
                    )
                },
                timeout=timeout,
            )

        response.raise_for_status()

        return response.json()


@dataclass
class Sample:
    sample_id: Dict[str, Any]
    is_excluded: bool = False
    is_passing: bool = False        # NOTE: Default is "False" until logic determines the sample passes the testing criteria.
    comments: str = ""

    def __str__(self):
        return (
            f"sample_id: {self.sample_id}\n"
            f"is_excluded: {self.is_excluded}\n"
            f"is_passing: {self.is_passing}\n"
            f"comments: {self.comments}\n"
        )

    def to_dict(self, sample_number=None):
        # NOTE: sample_number is used if the audit is performed in "summary_mode".
        if sample_number:
            # Anonymyze the sample_id.
            sample_id = "Sample " + str(sample_number)
        else:
            sample_id = self.sample_id
        
        return {
            "sample_id": sample_id,
            "is_excluded": self.is_excluded,
            "is_passing": self.is_passing,
            "comments": self.comments,
        }


@dataclass
class Test:
    test_id: str
    test_description: str
    test_procedures: List[str]
    test_attributes: List[str]
    # Rating Matrix: 0 - Informational, 1 - Low, 2 - Medium, 3 - High.
    risk_rating: int
    table_headers: Optional[List[str]] = None
    samples: List["Sample"] = field(default_factory=list)
    # NOTE: Default is "True" until there is a failing sample or other logic determines the test has failed.
    is_passing: bool = True
    is_excluded: bool = False
    comments: str = ""
    num_findings: int = 0
    num_exclusions: int = 0
    num_passing: int = 0
    total_population: int = 0

    def __str__(self):
        return (
            f"test_id: {self.test_id}\n"
            f"test_description: {self.test_description}\n"
            f"risk_rating: {self.risk_rating}\n"
            f"is_passing: {self.is_passing}\n"
            f"comments: {self.comments}\n"         
        )

    def to_dict(self, summary_mode=False):
        result = {
            "test_id": self.test_id,
            "is_excluded": self.is_excluded,
            "is_passing": self.is_passing,            
            "test_description": self.test_description,
            "risk_rating": self.risk_rating,
            "comments": self.comments,
            "test_procedures": self.test_procedures,
            "test_attributes": self.test_attributes,
        }
        # Include samples, if present.
        if self.samples:          
            if summary_mode:
                # Anonymize samples when using summary mode.
                anonymized_samples = []
                for i, sample in enumerate(self.samples, start=1):
                    anonymized_samples.append(sample.to_dict(sample_number=i))
                result["samples"] = anonymized_samples
            else:
                result["samples"] = [s.to_dict() for s in self.samples]

        return result

    def get_risk_rating_str(self):
        if self.risk_rating == 0: return "Informational"
        elif self.risk_rating == 1: return "Low"
        elif self.risk_rating == 2: return "Medium"
        elif self.risk_rating == 3: return "High"
        else:
            raise ValueError(f"Invalid risk rating: {self.risk_rating}. Accepted values are 0 - 3.")

    def add_sample(self, sample):
        self.samples.append(sample)

    def evaluate_samples(self, exclusions=None, test_id = None, failure_message: str = None):
        self.total_population = len(self.samples)
        self.num_exclusions = 0
        self.num_findings = 0
        self.num_passing = 0

        for sample in self.samples:
            if exclusions:
                exclusion = exclusions.get_sample_exclusion(self.test_id, sample.sample_id)
                if exclusion:
                    sample.is_excluded = True
                    sample.comments = exclusion.rationale

            if sample.is_excluded:
                self.num_exclusions += 1
                continue

            if not sample.is_passing:
                self.num_findings += 1

        self.is_passing = self.num_findings == 0
        
        self.num_passing = self.total_population - self.num_findings - self.num_exclusions

        if failure_message:
            self.set_failure_summary(failure_message)

    def set_failure_summary(self, message: str):
        if self.is_passing:
            return

        # Make sure message ends with a period.
        message = message.rstrip()
        if not message.endswith("."):
            message += "."
        
        self.comments = (
            f"Exceptions Noted. {self.num_findings} of {self.total_population} {message}"
        )