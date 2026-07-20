import os
import boto3
from typing import Optional

class S3StorageManager:
    def __init__(self):
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")
        self.bucket_name = os.getenv("AWS_BUCKET_NAME", "datamind-datasets")
        
        # Only initialize client if credentials are provided
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            self.enabled = True
        else:
            self.s3_client = None
            self.enabled = False

    def upload_file(self, file_content: bytes, filename: str) -> bool:
        """Uploads a file to S3"""
        if not self.enabled:
            return False
            
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_content
            )
            return True
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return False

    def download_file(self, filename: str, local_path: str) -> bool:
        """Downloads a file from S3 to a local temporary path"""
        if not self.enabled:
            return False
            
        try:
            self.s3_client.download_file(self.bucket_name, filename, local_path)
            return True
        except Exception as e:
            print(f"Error downloading from S3: {e}")
            return False

    def delete_file(self, filename: str) -> bool:
        """Deletes a file from S3"""
        if not self.enabled:
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            return True
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            return False

# Global instance
s3_manager = S3StorageManager()
