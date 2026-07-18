from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AuditContext:
    provider: str
    report_name: str
    evidence_folder: str
    reader: EvidenceReader
    writer: EvidenceWriter
    report_builder: ReportBuilder
    auditor_name: str | "AJ Dehn"
    delete_cached_evidence: bool | False
    config: Any | None = None    
    exclusions: ExclusionManager | None = None

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


class Audit:
    def __init__(self, title=None, auditor_name="AuditOps"):
        self.test_results = None
        self.title = title
        self.auditor_name = auditor_name
        self.scope = None

    def update_scope(self, updated_scope):
        self.scope = updated_scope

    def get_scope(self):
        return self.scope

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
                "scope": {
                    "IMPORTANT_SCOPING_INFO": "COMING SOON"
                },
                "report_date": datetime.now(timezone.utc).strftime('%Y-%m-%d')
            },
            "test_results": [t.to_dict() for t in self.test_results]
        }


# NOTE: Samples default to "is_passing: False" until logic determines sample passes the testing criteria.
@dataclass
class Sample:
    sample_id: Dict[str, Any]
    is_excluded: bool = False
    is_passing: bool = False
    comments: str = ""

    def __str__(self):
        return (
            f"sample_id: {self.sample_id}\n"
            f"is_excluded: {self.is_excluded}\n"
            f"is_passing: {self.is_passing}\n"
            f"comments: {self.comments}\n"
        )

    def to_dict(self):
        return {
            "sample_id": self.sample_id,
            "is_excluded": self.is_excluded,
            "is_passing": self.is_passing,
            "comments": self.comments,
        }


# NOTE: Tests default to "is_passing: True" until there is a failing sample or other logic determines the test has failed.
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


    def to_dict(self):
        result = {
            "test_id": self.test_id,
            "is_excluded": self.is_excluded,
            "test_description": self.test_description,
            "risk_rating": self.risk_rating,
            "is_passing": self.is_passing,
            "comments": self.comments,
            "test_procedures": self.test_procedures,
            "test_attributes": self.test_attributes,
        }
        # Include samples, if present.
        if self.samples:  
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


    def evaluate_samples(self, exclusions=None, provider=None, test_id = None, failure_message: str = None):
        self.total_population = len(self.samples)
        self.num_exclusions = 0
        self.num_findings = 0
        self.num_passing = 0

        for sample in self.samples:
            if exclusions:
                exclusion = exclusions.get_sample_exclusion(provider, self.test_id, sample.sample_id)
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