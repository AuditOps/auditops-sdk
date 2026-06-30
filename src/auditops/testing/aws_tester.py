from .models import Test, Sample

class AWSTester:
    def __init__(self, reader):
        self.reader = reader

    def _read(self, path):
        return self.reader.read_json("aws", path)

    def _create_test(self, metadata):
        return Test(test_id=metadata.get("id"), test_description=metadata.get("description"), 
            test_procedures=metadata.get("procedures"), test_attributes=metadata.get("attributes"), 
            table_headers=metadata.get("headers"), risk_rating=metadata.get("risk_rating"))

    def run_tests(self):
        tests = [
            self.test_s3_encryption()
        ]

        return tests        

    def test_s3_encryption(self):
        metadata = {
            "id": "AWS-S3-001",
            "description": "S3 buckets are encrypted at rest.",
            "risk_rating": 2,
            "headers": ["Bucket Name", "Result", "Comments"],
            "attributes": [
                "ServerSideEncryptionConfiguration is present."
            ],
            "procedures": [
                "Obtained a list of S3 buckets by calling the list_buckets() boto3 command.",
                "Saved the list of buckets: s3/buckets.json.",
                "For each S3 bucket, obtained the encryption settings by calling the get_bucket_encryption() boto3 command.",
                "For each S3 bucket, saved the encryption settings: s3/buckets/[bucket_name]/encryption.json.",
                "For each S3 bucket, inspected the encryption settings to determine if they comply with the test attribute(s) below."
            ],      
        }
        test = self._create_test(metadata)

        buckets = self._read("s3/buckets.json")

        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket["Name"]

            sample = Sample(sample_id={"bucket_name": bucket_name})

            encryption = self._read(f"s3/buckets/{bucket_name}/encryption.json")
            
            if encryption.get("ServerSideEncryptionConfiguration"):
                sample.is_passing = True
            else:
                sample.comments = "No encryption configuration found"

            test.samples.append(sample)

        test.evaluate_samples()

        return test