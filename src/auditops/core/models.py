from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
from datetime import datetime, timezone
from pathlib import Path
from .reporting.pdf_report_builder import PDFReportBuilder
from .evidence.reader import EvidenceReader
from .evidence.writer import EvidenceWriter
from .exclusions import ExclusionManager


@dataclass
class AuditHelpers:
    reader: EvidenceReader
    writer: EvidenceWriter
    report_builder: PDFReportBuilder

    @classmethod
    def create(cls, exclusions_file: str | None = None):
        return cls(
            reader=EvidenceReader(),
            writer=EvidenceWriter(),
            report_builder=PDFReportBuilder(),
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
    evidence_folder: str | None = None      # Subfolder location for audit evidence and reports.
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
    def report_dir(self) -> Path:
        path = Path(self.reader.root_dir) / "reports"
        if self.evidence_folder:
            path /= self.evidence_folder
        return path

    @property
    def json_report_path(self) -> Path:
        return self.report_dir / f"{self.report_name}.json"

    @property
    def pdf_report_path(self) -> Path:
        return self.report_dir / f"{self.report_name}.pdf"


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