"""Object storage for dataset files and avatars.

Every failure in here used to go to print(). On a hosted box that lands in a log
stream nobody reads, which is how object storage was able to be broken for
months without anyone noticing: uploads quietly fell back to local disk, the
host wiped that disk on the next deploy, and the datasets were simply gone.

So each failure is now reported, and the connection is checked once at startup
rather than first discovered when a user's file cannot be found.
"""

import logging
import os
from typing import Optional

import boto3

from app.core.error_tracking import capture, capture_message

logger = logging.getLogger(__name__)


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
                region_name=self.region_name,
            )
            self.enabled = True
        else:
            self.s3_client = None
            self.enabled = False

    def _failed(self, action: str, exc: Exception, **context) -> None:
        """One place for every storage failure to be noticed.

        Credentials are never included - the bucket and endpoint are enough to
        tell a misconfiguration from an outage, and neither is a secret.
        """
        logger.error("S3 %s failed (bucket=%s): %s", action, self.bucket_name, exc)
        capture(exc, action=action, bucket=self.bucket_name, endpoint=self.endpoint_url, **context)

    def check_connection(self) -> tuple:
        """Ask the bucket whether it is really there. Returns (ok, detail).

        Called at startup so a broken configuration announces itself while
        someone is watching a deploy, instead of surfacing weeks later as a
        dataset that has vanished.
        """
        if not self.enabled:
            return False, "No credentials configured (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)."

        try:
            # head_bucket is the cheapest question that still proves the
            # credentials, the endpoint and the bucket name are all correct.
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True, f"Connected to bucket '{self.bucket_name}'."
        except Exception as exc:
            return False, f"Cannot reach bucket '{self.bucket_name}' at {self.endpoint_url or 'AWS'}: {exc}"

    def upload_file(self, file_content: bytes, filename: str) -> bool:
        """Uploads a file to S3"""
        if not self.enabled:
            return False

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_content,
            )
            return True
        except Exception as exc:
            # The most costly failure of the four: the caller carries on with a
            # file that exists only on this machine's disk, and on a host with
            # ephemeral storage that means it is already lost.
            self._failed("upload", exc, filename=filename, consequence="file exists only on local disk")
            return False

    def download_file(self, filename: str, local_path: str) -> bool:
        """Downloads a file from S3 to a local temporary path"""
        if not self.enabled:
            return False

        try:
            self.s3_client.download_file(self.bucket_name, filename, local_path)
            return True
        except Exception as exc:
            self._failed("download", exc, filename=filename)
            return False

    def delete_file(self, filename: str) -> bool:
        """Deletes a file from S3"""
        if not self.enabled:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            return True
        except Exception as exc:
            self._failed("delete", exc, filename=filename)
            return False

    def get_file_bytes(self, filename: str) -> Optional[bytes]:
        """Reads a file straight into memory — used for small assets like
        avatars that get served back through our own endpoint rather than
        processed as a dataset (no need for a local temp file)."""
        if not self.enabled:
            return None

        try:
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)
            return obj["Body"].read()
        except Exception as exc:
            self._failed("read", exc, filename=filename)
            return None


# Global instance
s3_manager = S3StorageManager()


def report_storage_status() -> bool:
    """Log, and report, whether files will actually survive.

    Deliberately loud when storage is unreachable but credentials were given:
    that combination means someone intended persistence and is not getting it,
    which is the exact situation that went unnoticed here.
    """
    ok, detail = s3_manager.check_connection()

    if ok:
        logger.info("Object storage: %s", detail)
        return True

    if not s3_manager.enabled:
        # A deliberate local setup. Worth saying once, not worth alarming over.
        logger.warning(
            "Object storage is off — uploaded files live only on this machine's disk. "
            "On a host with ephemeral storage they will not survive a redeploy."
        )
        return False

    logger.error("Object storage is MISCONFIGURED: %s", detail)
    capture_message(
        "Object storage is configured but unreachable - uploaded files will not survive a redeploy",
        level="error",
        bucket=s3_manager.bucket_name,
        endpoint=s3_manager.endpoint_url,
        detail=detail,
    )
    return False
