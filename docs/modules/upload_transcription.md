# Upload và Transcription Flow

## Tổng quan

Tài liệu này mô tả quy trình upload file audio và transcription tự động.

## Kiến trúc

```
Client → Backend API → MinIO Storage → Queue → Worker → S2T Service → Backend gRPC
```

### Components

1. **Backend API**: Endpoint REST API để upload và mark completed
2. **MinIO Storage**: S3-compatible object storage để lưu audio files
3. **Redis Queue (ARQ)**: Queue system để xử lý background jobs
4. **Transcription Worker**: ARQ worker xử lý transcription jobs
5. **S2T Service**: Service AI để transcribe audio thành text

## Flow chi tiết

### 1. Khởi tạo Upload

**Endpoint**: `POST /api/v1/record/upload`

**Request**:
```json
{
  "language": "vi"  // hoặc "en"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "recording_id": "uuid-here",
    "upload_url": "http://minio:9000/bucket-name",
    "upload_fields": {
      "key": "user-id/recordings/recording-id.wav",
      "Content-Type": "audio/wav",
      "x-amz-meta-language": "vi",
      "x-amz-meta-recording-id": "uuid-here",
      "policy": "...",
      "x-amz-algorithm": "...",
      "x-amz-credential": "...",
      "x-amz-date": "...",
      "x-amz-signature": "..."
    },
    "expires_in": 600
  }
}
```

**Database**: Tạo recording record với status `PENDING`

### 2. Upload File

Client thực hiện multipart/form-data POST đến `upload_url` với:
- Tất cả fields từ `upload_fields`
- File audio với key `file`

**Example với cURL**:
```bash
curl -X POST "http://minio:9000/bucket-name" \
  -F "key=user-id/recordings/recording-id.wav" \
  -F "Content-Type=audio/wav" \
  -F "x-amz-meta-language=vi" \
  -F "x-amz-meta-recording-id=uuid-here" \
  -F "policy=..." \
  -F "x-amz-algorithm=..." \
  -F "x-amz-credential=..." \
  -F "x-amz-date=..." \
  -F "x-amz-signature=..." \
  -F "file=@audio.wav"
```

**Example với JavaScript**:
```javascript
const formData = new FormData();

// Add all upload_fields
Object.entries(uploadFields).forEach(([key, value]) => {
  formData.append(key, value);
});

// Add file
formData.append('file', audioBlob, 'recording.wav');

// Upload
await fetch(uploadUrl, {
  method: 'POST',
  body: formData
});
```

### 3. Mark Upload Completed

**Endpoint**: `POST /api/v1/record/upload/completed`

**Request**:
```json
{
  "recording_id": "uuid-here"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "recording_id": "uuid-here",
    "status": "pending",
    "message": "Upload completed successfully. Transcription job queued.",
    "job_id": "arq-job-id"
  }
}
```

**Logic**:
1. Validate recording ownership
2. Validate recording status = PENDING
3. Verify file exists in MinIO storage
4. Queue transcription job vào Redis
5. Return job_id

### 4. Background Transcription

**Worker**: `transcribe_audio_task`

**Steps**:
1. **Get recording** từ database
2. **Update status** → `PROCESSING`
3. **Generate presigned URL** để download audio từ MinIO
4. **Call S2T Service**:
   - Endpoint: `POST {S2T_API_HOST}/api/v1/transcribe`
   - Body: `{ "audio_url": "...", "recording_id": "...", "language": "vi" }`
5. **S2T Service** xử lý và gọi lại Backend qua gRPC `CompleteRecording`
6. **Backend** update status → `DONE` và save segments

**Error Handling**:
- Nếu lỗi → update status = `FAILED`
- Retry: 1 lần sau 2 phút
- Timeout: 10 phút

## Database Schema

### Recording
```sql
CREATE TABLE recordings (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'upload', 'realtime'
    language VARCHAR(10) NOT NULL,  -- 'vi', 'en'
    status VARCHAR(20) NOT NULL,  -- 'pending', 'processing', 'done', 'failed'
    duration_ms INTEGER DEFAULT 0,
    meta JSONB,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Segment
```sql
CREATE TABLE segments (
    id UUID PRIMARY KEY,
    recording_id UUID NOT NULL,
    idx INTEGER NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    text TEXT NOT NULL
);
```

## Status Flow

```
PENDING → PROCESSING → DONE
    ↓
  FAILED
```

- **PENDING**: Recording created, chưa upload hoặc chưa queue
- **PROCESSING**: Đang transcribe
- **DONE**: Transcription hoàn tất
- **FAILED**: Có lỗi xảy ra

## Configuration

### Environment Variables

```bash
# MinIO
MINIO_ENDPOINT=http://minio:9000
MINIO_SERVER_URL=http://localhost:9000  # Public URL
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=btl-oop-dev

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# S2T Service
S2T_API_HOST=http://s2t:8001

# ARQ Worker
ARQ_QUEUE_NAME=arq:queue
ARQ_MAX_JOBS=10
ARQ_JOB_TIMEOUT=600
```

## Chạy Worker

### Development
```bash
cd backend
arq src.workers.transcribe.WorkerSettings
```

### Production (Docker)
```yaml
# docker-compose.yml
transcribe-worker:
  build:
    context: ./backend
    dockerfile: Dockerfile
  command: arq src.workers.transcribe.WorkerSettings
  depends_on:
    - redis
    - postgres
    - minio
  environment:
    - REDIS_HOST=redis
    - POSTGRES_SERVER=postgres
    - S2T_API_HOST=http://s2t:8001
```

## Testing

### 1. Test Upload Flow

```bash
# 1. Get upload URL
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/record/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language": "vi"}')

RECORDING_ID=$(echo $RESPONSE | jq -r '.data.recording_id')
UPLOAD_URL=$(echo $RESPONSE | jq -r '.data.upload_url')

# 2. Upload file (simplified - need to include all fields)
curl -X POST "$UPLOAD_URL" \
  -F "file=@test.wav" \
  # ... add all upload_fields

# 3. Mark completed
curl -X POST http://localhost:8000/api/v1/record/upload/completed \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"recording_id\": \"$RECORDING_ID\"}"

# 4. Check status
curl http://localhost:8000/api/v1/record/$RECORDING_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Monitor Worker

```bash
# Check Redis queue
redis-cli LLEN arq:transcribe

# Check job status
redis-cli HGETALL arq:job:{job_id}

# Watch logs
docker-compose logs -f transcribe-worker
```

## Error Handling

### Common Errors

1. **File not found in storage**
   - Cause: Upload chưa hoàn tất
   - Solution: Đảm bảo upload thành công trước khi gọi `/completed`

2. **Recording not in PENDING status**
   - Cause: Đã queue rồi hoặc đang processing
   - Solution: Check status trước khi retry

3. **S2T service error**
   - Cause: Service down hoặc file audio invalid
   - Solution: Check S2T service logs, validate audio format

4. **Queue connection failed**
   - Cause: Redis down
   - Solution: Check Redis service

## Security

- ✅ Presigned URL có expiration (10 phút)
- ✅ Validate ownership trước khi queue
- ✅ File size limit: 100MB
- ✅ Content-Type validation
- ✅ Authentication required cho tất cả endpoints

## Performance

- Upload: Parallel với presigned POST
- Queue: Non-blocking, async
- Worker: Max 10 concurrent jobs
- Timeout: 10 phút per job
- Retry: 1 lần nếu failed

## Monitoring

### Metrics to track

1. Upload success rate
2. Transcription completion rate
3. Average processing time
4. Queue depth
5. Worker utilization
6. Error rate by type

### Logging

- Upload initiated: `INFO`
- File uploaded: `INFO`
- Job queued: `INFO`
- Transcription started: `INFO`
- Transcription completed: `INFO`
- Errors: `ERROR` with stack trace

