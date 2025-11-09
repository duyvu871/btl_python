"""
gRPC handler for record module.
Provides gRPC services for AI Inference Service to interact with recordings.
"""
import json
from uuid import UUID

from speech_hub.s2t.v1.record_pb2 import QuotaResponse, RecordingResponse
from src.modules.record.schema import (
    CompleteRecordingRequestSchema,
    CreateRecordingRequestSchema,
    UpdateStatusRequestSchema,
)
from src.shared.uow import UnitOfWork


class RecordingGrpcHandler:
    """
    Handler xử lý gRPC calls từ AI Inference Service.
    Orchestrate các use cases.
    """

    def __init__(self, uow: UnitOfWork, use_cases):
        self.uow = uow
        self.create_recording_uc = use_cases.create_recording
        self.complete_recording_uc = use_cases.complete_recording
        self.update_status_uc = use_cases.update_status

    async def CheckQuota(self, request, context) -> QuotaResponse:
        """
        AI service gọi trước khi bắt đầu recording.
        """
        from src.modules.subscription.use_cases import CheckQuotaUseCase

        # Create use case instance
        check_quota_uc = CheckQuotaUseCase(self.uow)

        user_id = UUID(request.user_id)
        has_quota, error_msg = await check_quota_uc.execute(user_id)

        return QuotaResponse(has_quota=has_quota, error_message=error_msg)

    async def CreateRecording(self, request, context) -> RecordingResponse:
        """
        AI service gọi sau khi check quota OK.
        """
        # Convert protobuf → Pydantic
        create_req = CreateRecordingRequestSchema(
            user_id=UUID(request.user_id),
            source=request.source,
            language=request.language,
            meta=json.loads(request.meta_json) if request.meta_json else {}
        )

        # Execute use case
        result = await self.create_recording_uc.execute(create_req)

        return RecordingResponse(
            recording_id=str(result.recording_id),
            status=result.status,
            duration_ms=result.duration_ms
        )

    async def CompleteRecording(self, request, context) -> RecordingResponse:
        """
        AI service gọi sau khi inference xong.
        """
        from src.modules.record.schema import SegmentBase

        complete_req = CompleteRecordingRequestSchema(
            recording_id=UUID(request.recording_id),
            duration_ms=request.duration_ms,
            segments=[
                SegmentBase(
                    idx=seg.idx,
                    start_ms=seg.start_ms,
                    end_ms=seg.end_ms,
                    text=seg.text
                )
                for seg in request.segments
            ]
        )

        result = await self.complete_recording_uc.execute(complete_req)

        return RecordingResponse(
            recording_id=str(result.recording_id),
            status=result.status,
            duration_ms=result.duration_ms
        )

    async def UpdateRecordingStatus(self, request, context) -> RecordingResponse:
        """
        AI service gọi nếu có lỗi.
        """
        update_req = UpdateStatusRequestSchema(
            status=request.status,
            error_message=request.error_message if request.HasField('error_message') else None
        )

        result = await self.update_status_uc.execute(
            UUID(request.recording_id),
            update_req
        )

        return RecordingResponse(
            recording_id=str(result.recording_id),
            status=result.status,
            duration_ms=result.duration_ms
        )
