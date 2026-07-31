from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import mimetypes
import requests


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
            # NOTE: Avoid collision if upload_url was passed.
            kwargs.pop("upload_url", None)
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
            client: boto3 S3 client

        Optional kwargs:
            key: S3 object key (defaults to file name)
        """

        bucket = kwargs.get("bucket")
        client = kwargs.get("client")
        key = kwargs.get("key", file_path.name)

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
