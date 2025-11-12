"""
Use case for generating presigned upload URL for recordings.
"""
from dataclasses import dataclass
from uuid import UUID

from src.core.s3.minio.client import MinIOClient, minio_client
from src.shared.uow import UnitOfWork


@dataclass
class GenerateUploadUrlUseCaseResult:
    upload_url: str
    upload_fields: dict
    expires_in: int
    object_key: str

class GenerateUploadUrlUseCase:
    """
    Use case for generating presigned POST URL for uploading audio files.
    This can be used for:
    - Initial recording creation
    - Regenerating expired URLs
    - Retrying failed uploads
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        recording_id: UUID,
        user_id: UUID,
        language: str,
        expire_seconds: int = 600,  # 10 minutes
        max_upload_bytes: int = 100 * 1024 * 1024,  # 100 MB
    ) -> GenerateUploadUrlUseCaseResult:
        """
        Generate presigned POST URL for uploading audio file.

        Args:
            recording_id: UUID of the recording
            user_id: UUID of the user who owns the recording
            language: Language code for the recording
            expire_seconds: URL expiration time in seconds (default: 600 = 10 minutes)
            max_upload_bytes: Maximum file size in bytes (default: 100 MB)
        Returns:
            Dictionary containing:
            {
                'upload_url': str,  # Presigned POST URL
                'upload_fields': dict,  # Form fields to include in POST request
                'expires_in': int,  # Expiration time in seconds
                'object_key': str  # S3 object key for reference
            }
        """
        # 1. Ensure MinIO bucket exists
        minio_client.create_bucket()

        # 2. Generate object key
        object_key = f"{user_id}/recordings/{recording_id}.wav"

        # 3. Define required form fields
        fields = {
            "Content-Type": "audio/wav",
            "x-amz-meta-language": language,
            "x-amz-meta-recording-id": str(recording_id),
        }

        # 4. Define upload conditions
        conditions = [
            ["starts-with", "$Content-Type", "audio/"],
            ["content-length-range", 1, max_upload_bytes],
            ["eq", "$key", object_key],
            ["eq", "$x-amz-meta-language", language],
            ["eq", "$x-amz-meta-recording-id", str(recording_id)]
        ]

        # 5. Generate presigned POST URL
        presigned_post = minio_client.client.generate_presigned_post(
            Bucket=minio_client.bucket_name,
            Key=object_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expire_seconds,
        )

        # 6. Replace internal URL with public URL
        public_url = MinIOClient.replace_internal_to_public_url(presigned_post['url'])

        return GenerateUploadUrlUseCaseResult(
            upload_url=public_url,
            upload_fields=presigned_post['fields'],
            expires_in=expire_seconds,
            object_key=object_key,
        )


def get_generate_upload_url_usecase(uow: UnitOfWork) -> GenerateUploadUrlUseCase:
    """Dependency injector for GenerateUploadUrlUseCase."""
    return GenerateUploadUrlUseCase(uow)

