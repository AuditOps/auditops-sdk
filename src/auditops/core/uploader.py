import requests


class Uploader:
    def __init__(self, upload_url, timeout=30):
        self.upload_url = upload_url
        self.timeout = timeout

    def upload(self, file_path, client_email, auditor_email):
        with open(file_path, "rb") as f:
            response = requests.post(
                self.upload_url,
                data={
                    "client_email": client_email,
                    "auditor_email": auditor_email
                },
                files={
                    "file": (
                        file_path,
                        f,
                        "application/zip"
                    )
                },
                timeout=self.timeout
            )

        response.raise_for_status()

        return response.json()