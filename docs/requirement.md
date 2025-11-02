# BTL Python Project - Speech-to-Text System

Dự án BTL (Bài Tập Lớn) Python - Hệ thống AI Speech-to-Text (S2T) với khả năng realtime và batch, tích hợp RAG cho hỏi đáp thông minh.

## Tổng Quan Dự Án

Dự án này xây dựng một hệ thống AI hoàn chỉnh cho chuyển đổi giọng nói thành văn bản, bao gồm:
- **Speech-to-Text (S2T)**: Realtime qua WebSocket và batch qua upload file
- **Quản lý người dùng**: Đăng ký, đăng nhập, hồ sơ, gói dịch vụ với quota
- **Quản lý bản ghi**: Lưu trữ recordings và segments
- **Hỏi đáp thông minh**: Semantic search và RAG trên transcripts
- **Infrastructure**: Giám sát và logging

## Phạm Vi Chức Năng (MVP trong 2 tuần)

### Speech-to-Text (S2T)
- **Realtime**: Browser → WebSocket → partial/final transcript với VAD
- **Batch**: Upload file âm thanh → Celery job → transcript với faster-whisper

### Quản lý Người Dùng
- Đăng ký, đăng nhập (JWT access/refresh tokens)
- Hồ sơ user (tên, avatar)
- Gói dịch vụ (plan/subscription): quota phút/tháng + đếm số lần dùng S2T

### Quản lý Bản Ghi
- Lưu Recording + các Segment (start_ms, end_ms, text)
- Danh sách recordings, xem chi tiết, tải transcript (.txt)

### Hỏi Đáp trong Bản Ghi
- Semantic search + RAG đơn giản (với 1 transcript): hỏi → trả lời + highlight đoạn liên quan

### Hệ Thống Kỹ Thuật
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Task Queue**: Celery (cho batch S2T)
- **Database**: PostgreSQL
- **AI**: Faster-whisper (ưu tiên tốc độ)
- **Frontend**: Next.js + Tailwind + shadcn
- **Infrastructure**: Docker + Nginx (proxy WS), Grafana/Loki
- **CI/CD**: GitHub Actions (build, test, lint, docker push, deploy)

### Ngoài Phạm Vi (Không làm trong 2 tuần)
- Billing thực thu
- Mobile app
- Diarization nâng cao
- Multi-tenant organization

## Kiến Trúc Luồng Dữ Liệu

### Realtime S2T
```
Mic → WebSocket /ws/s2t → Buffer + VAD → Decode → Emit partial/segment → Lưu Recording/Segment (khi kết thúc)
```

### Batch S2T
```
Upload → POST /recordings → Tạo job Celery → Worker chạy faster-whisper → Lưu Segment
```

### RAG Pipeline
```
Recording hoàn tất → Build transcript_chunks (+ timestamp map) → Embed → Hybrid upsert Qdrant
/search/semantic (top-K chunk) & /rag/ask (LLM trả lời với citations)
```

## Mô Hình Dữ Liệu (PostgreSQL)

### Users & Profiles
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  name TEXT,
  avatar_url TEXT
);
```

### Plans & Subscriptions
```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,             -- 'FREE', 'PRO'
  name TEXT NOT NULL,
  monthly_minutes INT NOT NULL,          -- phút được phép mỗi tháng
  monthly_usage_limit INT NOT NULL,      -- số lần create STT / tháng
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES plans(id),
  cycle_start TIMESTAMPTZ NOT NULL DEFAULT date_trunc('month', now()),
  cycle_end   TIMESTAMPTZ NOT NULL DEFAULT (date_trunc('month', now()) + INTERVAL '1 month'),
  usage_count INT NOT NULL DEFAULT 0,    -- số lần tạo STT trong chu kỳ
  used_seconds INT NOT NULL DEFAULT 0,   -- tổng giây đã dùng trong chu kỳ
  UNIQUE (user_id, cycle_start)          -- 1 subscription hiệu lực/chu kỳ
);
```

### Recordings & Segments
```sql
CREATE TABLE recordings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source TEXT NOT NULL,                  -- 'realtime' | 'upload'
  language TEXT DEFAULT 'vi',
  status TEXT NOT NULL DEFAULT 'processing', -- 'processing'|'done'|'failed'
  duration_ms INT DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  meta JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recording_id UUID NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
  idx INT NOT NULL,
  start_ms INT NOT NULL,
  end_ms INT NOT NULL,
  text TEXT NOT NULL
);
```

### Chunks cho RAG
```sql
CREATE TABLE transcript_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recording_id UUID NOT NULL REFERENCES recordings(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  start_ms INT NOT NULL,
  end_ms INT NOT NULL,
  text TEXT NOT NULL,
  token_count INT NOT NULL DEFAULT 0,
  UNIQUE (recording_id, chunk_index)
);
```

*Lưu ý*: Vector embeddings lưu ở Qdrant cho hybrid search. Nếu dùng pgvector, thêm cột `embedding VECTOR(768)`.

## Trigger & Procedure

### Trigger: Tự Động Tăng Usage Count
Tăng `usage_count` trong `user_subscriptions` khi INSERT vào `recordings`.

```sql
CREATE OR REPLACE FUNCTION trg_increment_usage_on_recording()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE user_subscriptions
  SET usage_count = usage_count + 1
  WHERE user_id = NEW.user_id
    AND now() >= cycle_start
    AND now() < cycle_end;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_usage_on_recording
AFTER INSERT ON recordings
FOR EACH ROW
EXECUTE FUNCTION trg_increment_usage_on_recording();
```

*Gợi ý*: Kiểm tra quota ở backend trước khi tạo recording để UX tốt hơn.

### Procedure: Đăng Ký Người Dùng Transactional
Đảm bảo tạo user, profile, subscription trong một transaction.

```sql
CREATE OR REPLACE PROCEDURE sp_register_user(
  in_email TEXT,
  in_hashed_pass TEXT,
  in_name TEXT,
  in_default_plan_code TEXT  -- 'FREE'
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id UUID;
  v_plan_id UUID;
BEGIN
  -- Tìm plan
  SELECT id INTO v_plan_id FROM plans WHERE code = in_default_plan_code;
  IF v_plan_id IS NULL THEN
    RAISE EXCEPTION 'default plan % not found', in_default_plan_code;
  END IF;

  -- Tạo user
  INSERT INTO users (email, password_hash)
  VALUES (in_email, in_hashed_pass)
  RETURNING id INTO v_user_id;

  -- Profile
  INSERT INTO user_profiles (user_id, name)
  VALUES (v_user_id, in_name);

  -- Subscription
  INSERT INTO user_subscriptions (user_id, plan_id)
  VALUES (v_user_id, v_plan_id);

EXCEPTION
  WHEN OTHERS THEN
    RAISE;
END;
$$;
```

*Sử dụng*: Từ backend, gọi trong transaction để đảm bảo atomicity.
