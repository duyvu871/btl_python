# Record Module - Architecture & Flow

## Tổng Quan

Module record là **cầu nối giữa REST API (Frontend) và gRPC Service (AI Inference)**:
- Frontend tạo recording qua REST API
- AI service (s2t) nhận audio, xử lý inference, gọi gRPC để lưu kết quả
- Backend quản lý metadata, status và transcription segments

**Key Points**:
- ✅ AI inference chạy ở service riêng (s2t service)
- ✅ Backend chỉ quản lý metadata và persist data
- ✅ Communication: REST (Frontend) + gRPC (AI Service)

---

## Cấu Trúc Module

```
src/modules/record/
├── repository.py              # RecordingRepository, SegmentRepository
├── use_cases/
│   ├── create_recording_use_case.py      # Tạo recording (check quota)
│   ├── complete_recording_use_case.py    # Lưu segments (từ gRPC)
│   ├── update_status_use_case.py         # Update status (từ gRPC)
│   ├── get_recording_use_case.py         # Xem kết quả
│   └── list_recordings_use_case.py       # List với filter
├── grpc/
│   └── handler.py             # gRPC endpoint handler (backend)
├── schema.py                  # Request/Response models
└── routing.py                 # REST API endpoints (upload, view)
```

## Architecture Diagram

```
┌─────────────────┐
│    Frontend     │
└────────┬────────┘
         │
         ├─── WebSocket ──────────────────┐
         │                                 │
         ├─── REST API (upload, view) ───┐│
         │                                ││
         ▼                                ▼▼
┌─────────────────────────────┐   ┌──────────────────────┐
│   AI Inference Service      │   │   Backend (Main)     │
│   (s2t - Separate Service)  │   │                      │
├─────────────────────────────┤   ├──────────────────────┤
│ • Nhận audio stream         │   │ • gRPC Services:     │
│ • AI Inference (Whisper)    │   │   - CheckQuota       │
│ • Real-time transcription   │   │   - CreateRecording  │
│ • WebSocket to Frontend     │◄──┤   - CompleteRec...   │
│                             │gRPC│   - UpdateStatus     │
│                             ├───►│                      │
└─────────────────────────────┘   │ • REST API:          │
                                   │   - Upload file      │
                                   │   - View results     │
                                   │                      │
                                   │ • Database           │
                                   │ • Storage (S3)       │
                                   │ • Queue (Celery)     │
                                   └──────────────────────┘
```

**Communication Channels**:
1. **Frontend ↔ AI Service**: WebSocket (realtime streaming)
2. **Frontend ↔ Backend**: REST API (upload file, view results)
3. **AI Service ↔ Backend**: gRPC (use cases: quota, DB operations)

---

## Database Models

### Recording
```
id, user_id, source ('realtime'|'upload'), language, 
status ('processing'|'done'|'failed'), duration_ms,
created_at, completed_at, meta (JSON)
```

### Segment
```
id, recording_id, idx, start_ms, end_ms, text
```

---

## Use Cases

Tất cả use cases đều được **expose qua gRPC** để AI Inference Service gọi vào.

### 1. CheckQuotaUseCase
**Flow**: Get subscription → Check usage_count vs limit → Check used_seconds vs limit → Return

**Gọi từ**: AI Service qua gRPC (trước khi bắt đầu recording)

**gRPC Method**: `CheckQuota(user_id)`

---

### 2. CreateRecordingUseCase
**Flow**: 
1. Tạo recording (status='processing')
2. DB trigger tự động tăng usage_count
3. Return recording_id

**Gọi từ**: AI Service qua gRPC (sau khi check quota OK)

**gRPC Method**: `CreateRecording(user_id, source, language)`

**Note**: Không check quota ở đây vì đã check ở bước trước

---

### 3. CompleteRecordingUseCase
**Flow**: 
1. Validate recording exists và status='processing'
2. Bulk create segments
3. Update status='done', duration_ms, completed_at
4. Update subscription.used_seconds (duration_ms / 1000)
5. Commit transaction

**Gọi từ**: AI Service qua gRPC (sau khi inference xong)

**gRPC Method**: `CompleteRecording(recording_id, segments[], duration_ms)`

---

### 4. UpdateStatusUseCase
**Flow**: 
1. Update status='failed'
2. Save error_message vào meta
3. KHÔNG update used_seconds (user không bị charge)

**Gọi từ**: AI Service qua gRPC (nếu inference lỗi)

**gRPC Method**: `UpdateRecordingStatus(recording_id, status, error_message)`

---

### 5. GetRecordingUseCase
**Flow**: Get recording + segments, validate ownership

**Gọi từ**: REST API (Frontend xem kết quả)

**REST Endpoint**: `GET /recordings/{id}`

---

### 6. ListRecordingsUseCase
**Flow**: List với pagination + filters

**Gọi từ**: REST API (Frontend dashboard)

**REST Endpoint**: `GET /recordings`

---

## Repositories

### RecordingRepository
```python
- get_by_id_with_segments(id) -> Recording with segments loaded
- list_user_recordings(user_id, page, filters) -> (recordings, total)
- update_status(id, status, duration_ms, completed_at) -> bool
- get_user_stats(user_id) -> dict (total, duration, counts)
```

### SegmentRepository
```python
- get_by_recording(recording_id) -> list[Segment]
- bulk_create(segments_data) -> list[Segment]
- get_transcript_text(recording_id) -> str
- search_segments(recording_id, query) -> list[Segment]
```

---

## REST API Endpoints

**REST API chỉ dùng cho**:
1. Upload file (Frontend → Backend → Queue → AI Service)
2. Xem kết quả recordings (Frontend query)
3. Quản lý recordings (list, delete)

**Realtime recording KHÔNG dùng REST API**, mà dùng WebSocket trực tiếp tới AI Service.

| Method | Endpoint | Description | Used By |
|--------|----------|-------------|---------|
| POST | /recordings/upload | Upload audio file | Frontend |
| GET | /recordings/{id} | Lấy recording + segments | Frontend |
| GET | /recordings | List với pagination/filters | Frontend |
| GET | /recordings/stats | Thống kê user recordings | Frontend |
| DELETE | /recordings/{id} | Xóa recording | Frontend |

### POST /recordings/upload (cho Upload File)
```
Flow:
1. Frontend upload file
2. Backend check quota
3. Upload to S3/MinIO
4. Create recording (status='processing')
5. Queue job to Celery
6. Return: recording_id, upload_url
7. Worker download từ S3 → gRPC call to AI Service
8. AI Service inference → gRPC CompleteRecording
```

### GET /recordings/{id}
Lấy recording detail + tất cả segments để hiển thị transcript.

### GET /recordings
List recordings với filters: status, source, pagination.

### GET /recordings/stats
Thống kê: total recordings, duration, completed/processing/failed counts.

### GET /recordings/{id}/events (Optional - SSE)
**Server-Sent Events endpoint** để stream status updates (thay WebSocket).

```
Flow:
1. Frontend: const eventSource = new EventSource('/recordings/{id}/events')
2. Backend: Stream events khi status thay đổi
3. Frontend: eventSource.onmessage = (e) => { if (e.data.status === 'done') ... }
```

**Alternative**: Dùng polling đơn giản (GET /recordings/{id} mỗi 2-3 giây)

**Note**: Backend KHÔNG có WebSocket. Chỉ có:
- REST API (HTTP)
- gRPC server (cho AI service)
- (Optional) SSE endpoint

---

## gRPC Interface

Backend cung cấp **gRPC services** để AI Inference Service gọi vào thực thi các use cases.

### Service Definition (proto)
```protobuf
// Backend cung cấp các services này
service RecordingBackendService {
    // 1. Check quota trước khi bắt đầu recording
    rpc CheckQuota(CheckQuotaRequest) returns (QuotaResponse);
    
    // 2. Tạo recording mới (sau khi check quota OK)
    rpc CreateRecording(CreateRecordingRequest) returns (RecordingResponse);
    
    // 3. Hoàn thành recording + lưu segments
    rpc CompleteRecording(CompleteRecordingRequest) returns (RecordingResponse);
    
    // 4. Update status nếu có lỗi
    rpc UpdateRecordingStatus(UpdateStatusRequest) returns (RecordingResponse);
    
    // 5. Increment usage count (nếu cần manual)
    rpc IncrementUsage(IncrementUsageRequest) returns (IncrementUsageResponse);
}

// AI Inference Service expose streaming endpoint (không phải backend)
service TranscriptionService {
    // Stream audio và nhận real-time transcription
    rpc StreamTranscribe(stream AudioChunk) returns (stream TranscriptSegment);
}
```

### gRPC Messages
```protobuf
message CheckQuotaRequest {
    string user_id = 1;
}

message QuotaResponse {
    bool has_quota = 1;
    string error_message = 2;
}

message CreateRecordingRequest {
    string user_id = 1;
    string source = 2;        // 'realtime' | 'upload'
    string language = 3;      // 'vi', 'en'
    string meta_json = 4;     // JSON string
}

message CompleteRecordingRequest {
    string recording_id = 1;
    int32 duration_ms = 2;
    repeated SegmentData segments = 3;
}

message SegmentData {
    int32 idx = 1;
    int32 start_ms = 2;
    int32 end_ms = 3;
    string text = 4;
}

message UpdateStatusRequest {
    string recording_id = 1;
    string status = 2;        // 'processing' | 'done' | 'failed'
    optional string error_message = 3;
}

message RecordingResponse {
    string recording_id = 1;
    string status = 2;
    int32 duration_ms = 3;
}
```

### Backend gRPC Handler Implementation
```python
class RecordingGrpcHandler:
    """
    Handler xử lý gRPC calls từ AI Inference Service.
    Orchestrate các use cases.
    """
    
    def __init__(self, uow: UnitOfWork, use_cases):
        self.uow = uow
        self.check_quota_uc = use_cases.check_quota
        self.create_recording_uc = use_cases.create_recording
        self.complete_recording_uc = use_cases.complete_recording
        self.update_status_uc = use_cases.update_status
    
    async def CheckQuota(self, request, context) -> QuotaResponse:
        """AI service gọi trước khi bắt đầu recording."""
        user_id = UUID(request.user_id)
        has_quota, error_msg = await self.check_quota_uc.execute(user_id)
        return QuotaResponse(has_quota=has_quota, error_message=error_msg)

    async def CreateRecording(self, request, context) -> RecordingResponse:
        """AI service gọi sau khi check quota OK."""
        # Convert protobuf → Pydantic
        create_req = CreateRecordingRequestSchema(
            user_id=UUID(request.user_id),
            source=request.source,
            language=request.language,
            meta=json.loads(request.meta_json) if request.meta_json else {}
        )

        # Execute use case
        recording = await self.create_recording_uc.execute(create_req)

        # Convert → protobuf
        return RecordingResponse(
            recording_id=str(recording.id),
            status=recording.status,
            duration_ms=recording.duration_ms
        )

    async def CompleteRecording(self, request, context) -> RecordingResponse:
        """AI service gọi sau khi inference xong."""
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

        recording = await self.complete_recording_uc.execute(complete_req)

        return RecordingResponse(
            recording_id=str(recording.id),
            status=recording.status,
            duration_ms=recording.duration_ms
        )

    async def UpdateRecordingStatus(self, request, context) -> RecordingResponse:
        """AI service gọi nếu có lỗi."""
        update_req = UpdateStatusRequestSchema(
            status=request.status,
            error_message=request.error_message if request.HasField('error_message') else None
        )

        recording = await self.update_status_uc.execute(
            UUID(request.recording_id),
            update_req
        )

        return RecordingResponse(
            recording_id=str(recording.id),
            status=recording.status,
            duration_ms=recording.duration_ms
        )
```

### AI Inference Service (s2t) - Client Side
```python
class RecordingService:
    """
    AI Inference Service sử dụng gRPC client để gọi vào Backend.
    """
    
    def __init__(self, grpc_channel):
        self.backend_stub = RecordingBackendServiceStub(grpc_channel)
    
    async def start_realtime_transcription(self, user_id: str, audio_stream):
        """
        Flow realtime recording:
        1. Check quota
        2. Create recording
        3. Stream audio & inference
        4. Complete recording
        """
        # Step 1: Check quota
        quota_resp = await self.backend_stub.CheckQuota(
            CheckQuotaRequest(user_id=user_id)
        )
        
        if not quota_resp.has_quota:
            raise QuotaExceededError(quota_resp.error_message)
        
        # Step 2: Create recording
        recording_resp = await self.backend_stub.CreateRecording(
            CreateRecordingRequest(
                user_id=user_id,
                source='realtime',
                language='vi'
            )
        )
        recording_id = recording_resp.recording_id
        
        try:
            # Step 3: Process audio stream & inference
            segments = []
            async for audio_chunk in audio_stream:
                # AI inference here (Whisper/ASR)
                segment = await self.transcribe_chunk(audio_chunk)
                segments.append(segment)
                
                # Stream segment to frontend via WebSocket
                await self.send_to_frontend(segment)
            
            # Step 4: Complete recording
            await self.backend_stub.CompleteRecording(
                CompleteRecordingRequest(
                    recording_id=recording_id,
                    duration_ms=sum(s.end_ms - s.start_ms for s in segments),
                    segments=segments
                )
            )
            
            return recording_id
            
        except Exception as e:
            # Update status to failed
            await self.backend_stub.UpdateRecordingStatus(
                UpdateStatusRequest(
                    recording_id=recording_id,
                    status='failed',
                    error_message=str(e)
                )
            )
            raise
```


---

## Integration với Subscription

### Flow Integration qua gRPC

```
[AI Service] gRPC: CheckQuota(user_id)
    ↓
[Backend] CheckQuotaUseCase
    ↓ Get subscription
    ↓ Check: usage_count < monthly_usage_limit?
    ↓ Check: used_seconds < monthly_minutes * 60?
    ↓ Return: (has_quota, error_message)
    
[AI Service] Nếu has_quota=false → reject request
             Nếu has_quota=true → continue
    ↓
[AI Service] gRPC: CreateRecording(user_id, ...)
    ↓
[Backend] CreateRecordingUseCase
    ↓ Insert recording (status='processing')
    ↓ DB Trigger: increment usage_count
    ↓ Return: recording_id
    
[AI Service] Inference...
    ↓
[AI Service] gRPC: CompleteRecording(recording_id, segments, duration)
    ↓
[Backend] CompleteRecordingUseCase
    ↓ Save segments
    ↓ Update status='done'
    ↓ Update subscription.used_seconds += (duration_ms / 1000)
    ↓ Commit
```

### Use Case Implementations

**CheckQuotaUseCase** (được gọi từ gRPC):
```
Input: user_id
Logic:
  1. Get subscription
  2. Return (False, "error") nếu:
     - usage_count >= monthly_usage_limit
     - used_seconds >= monthly_minutes * 60
  3. Return (True, "") nếu OK
```

**CreateRecordingUseCase** (được gọi từ gRPC):
```
Input: user_id, source, language, meta
Logic:
  1. Insert recording (status='processing')
  2. DB trigger tự động increment usage_count
  3. Return recording
Note: KHÔNG check quota ở đây (đã check trước đó)
```

**CompleteRecordingUseCase** (được gọi từ gRPC):
```
Input: recording_id, segments[], duration_ms
Logic:
  1. Validate recording exists
  2. Bulk insert segments
  3. Update recording: status='done', duration_ms, completed_at
  4. Update subscription: used_seconds += (duration_ms / 1000)
  5. Commit transaction
```

---

## Flow Diagrams

### Realtime Recording Flow
```
[Frontend] 
  ↓ 1. User bắt đầu recording
  ↓ WebSocket connect
[AI Inference Service - s2t]
  ↓ 2. gRPC call: CheckQuota(user_id)
[Backend gRPC Service]
  ↓ CheckQuotaUseCase → validate limits
  ↓ Return: has_quota=true/false
[AI Inference Service]
  ↓ 3. Nếu OK: gRPC call: CreateRecording(user_id, source='realtime')
[Backend gRPC Service]
  ↓ CreateRecordingUseCase → Insert DB (status='processing')
  ↓ DB Trigger: increment usage_count
  ↓ Return: recording_id
[AI Inference Service]
  ↓ 4. Bắt đầu nhận audio stream từ Frontend
  ↓ Real-time inference (Whisper/ASR)
  ↓ Tạo segments on-the-fly
  ↓ Stream segments về Frontend (WebSocket)
[Frontend]
  ↓ Hiển thị transcript real-time
[AI Inference Service]
  ↓ 5. Khi user dừng: gRPC call: CompleteRecording(recording_id, segments, duration_ms)
[Backend gRPC Service]
  ↓ CompleteRecordingUseCase
  ↓   → Bulk create segments
  ↓   → Update status='done', duration_ms
  ↓   → Update subscription.used_seconds
  ↓ Return: success
[Frontend]
  ↓ 6. Redirect to /recordings/{id} để xem kết quả
```

**Services Responsibilities**:
- **Frontend**: UI, WebSocket connection, display real-time transcript
- **AI Inference (s2t)**: Nhận audio, inference, quản lý stream, gọi gRPC vào backend
- **Backend gRPC**: Cung cấp use cases qua gRPC (quota, DB operations)

---

### Upload File Flow
```
[Frontend]
  ↓ 1. User upload file audio
  ↓ POST /recordings/upload (REST API)
[Backend REST API]
  ↓ 2. CheckQuotaUseCase → validate
  ↓ 3. Upload file to Storage (S3/MinIO)
  ↓ 4. CreateRecordingUseCase (status='processing')
  ↓ 5. Queue job (RabbitMQ/Redis)
  ↓ Return: recording_id, job_id
[Frontend]
  ↓ WebSocket subscribe: /recordings/{id}/status
[Celery Worker]
  ↓ 6. Dequeue job
  ↓ Download audio from S3
  ↓ gRPC call to AI Inference Service
[AI Inference Service]
  ↓ 7. Batch inference (xử lý file)
  ↓ Generate segments
  ↓ 8. gRPC call: CompleteRecording(recording_id, segments, duration)
[Backend gRPC Service]
  ↓ CompleteRecordingUseCase
  ↓   → Save segments to DB
  ↓   → Update status='done'
  ↓   → Update used_seconds
  ↓ 9. WebSocket emit: recording_completed
[Frontend]
  ↓ Nhận notification
  ↓ Redirect to /recordings/{id}
```

**Services Responsibilities**:
- **Frontend**: Upload file, nhận WebSocket notification
- **Backend REST API**: Check quota, upload S3, queue job
- **Celery Worker**: Download file, orchestrate inference
- **AI Inference (s2t)**: Batch inference, gọi gRPC để save
- **Backend gRPC**: Save kết quả vào DB

---

### Error Handling Flow
```
[AI Inference Service]
  ↓ Inference failed (timeout, OOM, invalid audio, etc.)
  ↓ gRPC call: UpdateRecordingStatus(recording_id, status='failed', error_msg)
[Backend gRPC Service]
  ↓ UpdateStatusUseCase
  ↓   → Update status='failed', meta={error: "..."}
  ↓   → KHÔNG update used_seconds (user không bị charge)
  ↓   → KHÔNG increment usage_count (hoặc rollback nếu đã increment)
  ↓ WebSocket emit: recording_failed
[Frontend]
  ↓ Show error message
  ↓ User có thể retry (không mất quota)
```

---

## Database Trigger

### Auto Increment Usage Count
```sql
CREATE TRIGGER trigger_increment_usage
AFTER INSERT ON recordings
FOR EACH ROW
EXECUTE FUNCTION increment_usage_on_recording();
```

Function tự động tăng `usage_count` trong `user_subscriptions` khi insert recording.

---

## Unit of Work Update

```python
class UnitOfWork:
    def __init__(self, session):
        # ...existing repos...
        self.recording_repo = RecordingRepository(session)
        self.segment_repo = SegmentRepository(session)
```

---

## Implementation Checklist

### Phase 1: Core
- [ ] RecordingRepository, SegmentRepository
- [ ] 5 use cases
- [ ] REST API endpoints (5 routes)
- [ ] Schemas (Request/Response)
- [ ] Database trigger

### Phase 2: gRPC
- [ ] Protobuf definition
- [ ] gRPC handler implementation
- [ ] Integration với use cases

### Phase 3: Advanced
- [ ] WebSocket/SSE notifications
- [ ] File upload (S3/MinIO)
- [ ] Celery tasks
- [ ] Full-text search
- [ ] Export (PDF, DOCX, SRT)

---

## Kết Luận

### Vai Trò Các Services

#### 1. AI Inference Service (s2t)
**Nhiệm vụ chính**:
- Nhận audio stream từ Frontend (WebSocket)
- Xử lý AI inference (Whisper/ASR)
- Stream transcript real-time về Frontend
- **Gọi gRPC vào Backend** để:
  - Check quota trước khi bắt đầu
  - Tạo recording trong DB
  - Lưu segments sau khi xong
  - Update status nếu lỗi

**Không làm**:
- Không quản lý database
- Không quản lý subscription/quota
- Không quản lý storage

---

#### 2. Backend (Main App)
**Nhiệm vụ chính**:
- **Cung cấp gRPC Services** để AI service gọi vào:
  - `CheckQuota(user_id)` → CheckQuotaUseCase
  - `CreateRecording(...)` → CreateRecordingUseCase
  - `CompleteRecording(...)` → CompleteRecordingUseCase
  - `UpdateStatus(...)` → UpdateStatusUseCase
- Quản lý database (recordings, segments, subscriptions)
- Quản lý storage (S3/MinIO)
- Cung cấp REST API cho Frontend (upload, view results)

**Không làm**:
- Không xử lý audio streaming
- Không chạy AI inference

---

#### 3. Frontend
**Nhiệm vụ chính**:
- **Realtime**: WebSocket trực tiếp tới AI Service
- **Upload**: REST API tới Backend
- **View**: REST API tới Backend để lấy kết quả
- Display transcript, UI/UX

---

### Communication Flow Summary

```
Realtime Recording:
Frontend ─(WebSocket)─► AI Service ─(gRPC)─► Backend (Use Cases)

Upload File:
Frontend ─(REST)─► Backend ─(Queue)─► Worker ─(gRPC)─► AI Service ─(gRPC)─► Backend

View Results:
Frontend ─(REST)─► Backend (Query DB)
```

---

### Key Takeaways

1. ✅ **AI Service làm ALL việc inference**, Backend chỉ cung cấp use cases
2. ✅ **gRPC là cầu nối** giữa AI Service và Backend use cases
3. ✅ **Backend expose gRPC services**, không phải gRPC client
4. ✅ **Separation of concerns**: AI logic ở s2t, Business logic ở backend
5. ✅ **Scalability**: AI service và Backend scale độc lập
