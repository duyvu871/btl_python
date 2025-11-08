"""
MinIO client for S3-compatible object storage.
"""

import boto3
from botocore.exceptions import ClientError
from src.core.config.env import env


class MinIOClient:
    """
    MinIO client using boto3 for S3-compatible operations.
    """

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=env.MINIO_ENDPOINT,
            aws_access_key_id=env.MINIO_ACCESS_KEY,
            aws_secret_access_key=env.MINIO_SECRET_KEY,
            region_name='us-east-1'
        )
        self.bucket_name = env.MINIO_BUCKET_NAME

    def create_bucket(self, bucket_name: str = None) -> bool:
        """
        Create a bucket if it doesn't exist.

        Args:
            bucket_name: Name of the bucket. Defaults to the configured bucket.

        Returns:
            True if created or already exists, False on error.
        """
        bucket = bucket_name or self.bucket_name
        try:
            self.client.head_bucket(Bucket=bucket)
            return True  # Bucket exists
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=bucket)
                    return True
                except ClientError:
                    return False
            else:
                return False

    def upload_file(self, file_path: str, object_key: str, bucket_name: str = None) -> bool:
        """
        Upload a file to MinIO.

        Args:
            file_path: Local path to the file.
            object_key: Key (path) in the bucket.
            bucket_name: Bucket name. Defaults to configured bucket.

        Returns:
            True on success, False on failure.
        """
        bucket = bucket_name or self.bucket_name
        try:
            self.client.upload_file(file_path, bucket, object_key)
            return True
        except ClientError:
            return False

    def download_file(self, object_key: str, file_path: str, bucket_name: str = None) -> bool:
        """
        Download a file from MinIO.

        Args:
            object_key: Key (path) in the bucket.
            file_path: Local path to save the file.
            bucket_name: Bucket name. Defaults to configured bucket.

        Returns:
            True on success, False on failure.
        """
        bucket = bucket_name or self.bucket_name
        try:
            self.client.download_file(bucket, object_key, file_path)
            return True
        except ClientError:
            return False

    def delete_object(self, object_key: str, bucket_name: str = None) -> bool:
        """
        Delete an object from MinIO.

        Args:
            object_key: Key (path) in the bucket.
            bucket_name: Bucket name. Defaults to configured bucket.

        Returns:
            True on success, False on failure.
        """
        bucket = bucket_name or self.bucket_name
        try:
            self.client.delete_object(Bucket=bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def list_objects(self, prefix: str = "", bucket_name: str = None) -> list:
        """
        List objects in the bucket with optional prefix.

        Args:
            prefix: Prefix to filter objects.
            bucket_name: Bucket name. Defaults to configured bucket.

        Returns:
            List of object keys.
        """
        bucket = bucket_name or self.bucket_name
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError:
            return []

    def get_presigned_url(self, object_key: str, expiration: int = 3600, bucket_name: str = None) -> str | None:
        """
        Generate a presigned URL for the object.

        Args:
            object_key: Key (path) in the bucket.
            expiration: Expiration time in seconds. Default 1 hour.
            bucket_name: Bucket name. Defaults to configured bucket.

        Returns:
            Presigned URL or None on failure.
        """
        bucket = bucket_name or self.bucket_name
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError:
            return None


# Global instance
minio_client = MinIOClient()
