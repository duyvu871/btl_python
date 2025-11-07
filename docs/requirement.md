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
  user_name TEXT UNIQUE NOT NULL,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  role TEXT NOT NULL DEFAULT 'user',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  name TEXT,
  avatar_url TEXT
);
```
*Lưu ý*: One-to-one relationship - mỗi user chỉ có 1 profile. Xóa user sẽ tự động xóa profile.

### Plans & Subscriptions
```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,             -- 'FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE'
  name TEXT NOT NULL,
  description TEXT,
  plan_type TEXT NOT NULL DEFAULT 'free',
  plan_cost INT NOT NULL DEFAULT 0,
  plan_discount INT NOT NULL DEFAULT 0,
  monthly_minutes INT NOT NULL,          -- phút được phép mỗi tháng
  monthly_usage_limit INT NOT NULL,      -- số lần create STT / tháng
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES plans(id),
  cycle_start TIMESTAMPTZ NOT NULL DEFAULT date_trunc('month', now()),
  cycle_end   TIMESTAMPTZ NOT NULL DEFAULT (date_trunc('month', now()) + INTERVAL '1 month'),
  usage_count INT NOT NULL DEFAULT 0,    -- số lần tạo STT trong chu kỳ
  used_seconds INT NOT NULL DEFAULT 0,   -- tổng giây đã dùng trong chu kỳ
  CONSTRAINT unique_user_subscription UNIQUE (user_id)
);
```
*Lưu ý*: One-to-one relationship - mỗi user chỉ có 1 subscription active. Xóa user sẽ tự động xóa subscription.

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
*Lưu ý*: Cascade delete - xóa recording sẽ tự động xóa tất cả segments.

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
  CONSTRAINT unique_recording_chunk UNIQUE (recording_id, chunk_index)
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
  in_user_name TEXT,
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
  INSERT INTO users (email, user_name, password_hash)
  VALUES (in_email, in_user_name, in_hashed_pass)
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

### Procedure: Check Quota và Tạo Recording (Atomic)
Kiểm tra quota và tạo recording trong 1 transaction, tránh race conditions.

```sql
CREATE OR REPLACE FUNCTION sp_check_quota_and_create_recording(
  in_user_id UUID,
  in_source TEXT,
  in_language TEXT DEFAULT 'vi',
  in_meta JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE(
  recording_id UUID,
  quota_ok BOOLEAN,
  error_message TEXT
) 
LANGUAGE plpgsql
AS $$
DECLARE
  v_subscription user_subscriptions%ROWTYPE;
  v_plan plans%ROWTYPE;
  v_recording_id UUID;
BEGIN
  -- Get active subscription
  SELECT * INTO v_subscription 
  FROM user_subscriptions 
  WHERE user_id = in_user_id 
    AND now() >= cycle_start 
    AND now() < cycle_end;
  
  IF NOT FOUND THEN
    RETURN QUERY SELECT NULL::UUID, FALSE, 'No active subscription found';
    RETURN;
  END IF;
  
  -- Get plan limits
  SELECT * INTO v_plan FROM plans WHERE id = v_subscription.plan_id;
  
  -- Check usage count
  IF v_subscription.usage_count >= v_plan.monthly_usage_limit THEN
    RETURN QUERY SELECT NULL::UUID, FALSE, 
      format('Monthly usage limit reached (%s recordings)', v_plan.monthly_usage_limit);
    RETURN;
  END IF;
  
  -- Check used seconds
  IF v_subscription.used_seconds >= (v_plan.monthly_minutes * 60) THEN
    RETURN QUERY SELECT NULL::UUID, FALSE, 
      format('Monthly minutes limit reached (%s minutes)', v_plan.monthly_minutes);
    RETURN;
  END IF;
  
  -- Create recording (trigger will increment usage_count)
  INSERT INTO recordings (user_id, source, language, meta)
  VALUES (in_user_id, in_source, in_language, in_meta)
  RETURNING id INTO v_recording_id;
  
  RETURN QUERY SELECT v_recording_id, TRUE, ''::TEXT;
END;
$$;
```

*Lợi ích*: Atomic check + create, giảm race conditions, chỉ 1 roundtrip thay vì 3-4 queries.

### Procedure: Hoàn Tất Recording với Batch Insert Segments
Cập nhật recording status và insert nhiều segments cùng lúc.

```sql
CREATE OR REPLACE PROCEDURE sp_complete_recording(
  in_recording_id UUID,
  in_duration_ms INT,
  in_segments JSONB  -- [{"idx": 0, "start_ms": 0, "end_ms": 1000, "text": "..."}]
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id UUID;
  v_duration_seconds INT;
BEGIN
  -- Update recording status
  UPDATE recordings 
  SET status = 'done',
      duration_ms = in_duration_ms,
      completed_at = now()
  WHERE id = in_recording_id
  RETURNING user_id INTO v_user_id;
  
  -- Batch insert segments
  INSERT INTO segments (recording_id, idx, start_ms, end_ms, text)
  SELECT 
    in_recording_id,
    (seg->>'idx')::INT,
    (seg->>'start_ms')::INT,
    (seg->>'end_ms')::INT,
    seg->>'text'
  FROM jsonb_array_elements(in_segments) AS seg;
  
  -- Update used_seconds in subscription
  v_duration_seconds := in_duration_ms / 1000;
  UPDATE user_subscriptions
  SET used_seconds = used_seconds + v_duration_seconds
  WHERE user_id = v_user_id
    AND now() >= cycle_start
    AND now() < cycle_end;
    
EXCEPTION
  WHEN OTHERS THEN
    -- Mark as failed
    UPDATE recordings SET status = 'failed' WHERE id = in_recording_id;
    RAISE;
END;
$$;
```

*Lợi ích*: Transactional, batch insert nhanh hơn loops, tự động update used_seconds.

### Procedure: Reset Monthly Cycles (Maintenance)
Chạy hàng tháng để reset subscription cycles.

```sql
CREATE OR REPLACE PROCEDURE sp_reset_monthly_cycles()
LANGUAGE plpgsql
AS $$
DECLARE
  v_cycle_start TIMESTAMPTZ;
  v_cycle_end TIMESTAMPTZ;
  v_affected_count INT;
BEGIN
  v_cycle_start := date_trunc('month', now());
  v_cycle_end := v_cycle_start + INTERVAL '1 month';
  
  UPDATE user_subscriptions
  SET cycle_start = v_cycle_start,
      cycle_end = v_cycle_end,
      usage_count = 0,
      used_seconds = 0
  WHERE cycle_end <= now();
  
  GET DIAGNOSTICS v_affected_count = ROW_COUNT;
  
  RAISE NOTICE 'Reset % subscriptions for new cycle % to %', 
    v_affected_count, v_cycle_start, v_cycle_end;
END;
$$;
```

*Sử dụng*: Schedule với pg_cron hoặc Celery periodic task (chạy vào 00:00 ngày 1 hàng tháng).

### Function: Lấy User Statistics (Analytics)
Tính toán thống kê user tối ưu cho dashboard.

```sql
CREATE OR REPLACE FUNCTION sp_get_user_stats(in_user_id UUID)
RETURNS TABLE(
  total_recordings BIGINT,
  total_duration_minutes NUMERIC,
  total_segments BIGINT,
  current_cycle_usage INT,
  current_cycle_seconds INT,
  quota_usage_percent NUMERIC,
  quota_minutes_percent NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_subscription user_subscriptions%ROWTYPE;
  v_plan plans%ROWTYPE;
BEGIN
  -- Get subscription
  SELECT * INTO v_subscription 
  FROM user_subscriptions 
  WHERE user_id = in_user_id 
    AND now() >= cycle_start 
    AND now() < cycle_end;
  
  IF NOT FOUND THEN
    RETURN QUERY SELECT 0::BIGINT, 0::NUMERIC, 0::BIGINT, 0, 0, 0::NUMERIC, 0::NUMERIC;
    RETURN;
  END IF;
  
  SELECT * INTO v_plan FROM plans WHERE id = v_subscription.plan_id;
  
  RETURN QUERY
  SELECT 
    COUNT(r.id)::BIGINT AS total_recordings,
    COALESCE(SUM(r.duration_ms) / 60000.0, 0) AS total_duration_minutes,
    (SELECT COUNT(*) FROM segments s JOIN recordings r2 ON s.recording_id = r2.id 
     WHERE r2.user_id = in_user_id)::BIGINT AS total_segments,
    v_subscription.usage_count,
    v_subscription.used_seconds,
    CASE 
      WHEN v_plan.monthly_usage_limit > 0 
      THEN (v_subscription.usage_count::NUMERIC / v_plan.monthly_usage_limit * 100)
      ELSE 0 
    END AS quota_usage_percent,
    CASE 
      WHEN v_plan.monthly_minutes > 0 
      THEN (v_subscription.used_seconds::NUMERIC / (v_plan.monthly_minutes * 60) * 100)
      ELSE 0 
    END AS quota_minutes_percent
  FROM recordings r
  WHERE r.user_id = in_user_id;
END;
$$;
```

*Lợi ích*: 1 query thay vì nhiều queries riêng lẻ, giảm latency cho dashboard.

### Procedure: Upgrade/Downgrade Plan (Future)
Xử lý logic chuyển đổi gói dịch vụ.

```sql
CREATE OR REPLACE PROCEDURE sp_change_user_plan(
  in_user_id UUID,
  in_new_plan_code TEXT,
  in_prorate BOOLEAN DEFAULT FALSE,
  OUT success BOOLEAN,
  OUT message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_new_plan_id UUID;
  v_old_plan_id UUID;
  v_subscription_id UUID;
BEGIN
  success := FALSE;
  
  -- Find new plan
  SELECT id INTO v_new_plan_id FROM plans WHERE code = in_new_plan_code;
  IF v_new_plan_id IS NULL THEN
    message := format('Plan %s not found', in_new_plan_code);
    RETURN;
  END IF;
  
  -- Get current subscription
  SELECT id, plan_id INTO v_subscription_id, v_old_plan_id
  FROM user_subscriptions
  WHERE user_id = in_user_id
    AND now() >= cycle_start
    AND now() < cycle_end;
    
  IF v_subscription_id IS NULL THEN
    message := 'No active subscription found';
    RETURN;
  END IF;
  
  IF v_old_plan_id = v_new_plan_id THEN
    message := 'Already on this plan';
    RETURN;
  END IF;
  
  -- Update plan
  UPDATE user_subscriptions
  SET plan_id = v_new_plan_id
  WHERE id = v_subscription_id;
  
  -- If prorate, reset usage
  IF in_prorate THEN
    UPDATE user_subscriptions
    SET usage_count = 0,
        used_seconds = 0
    WHERE id = v_subscription_id;
  END IF;
  
  success := TRUE;
  message := format('Successfully changed plan to %s', in_new_plan_code);
END;
$$;
```

### Function: Clean Up Old Data (Maintenance)
Xóa recordings/segments cũ theo retention policy.

```sql
CREATE OR REPLACE FUNCTION sp_cleanup_old_recordings(
  in_retention_days INT DEFAULT 90,
  in_batch_size INT DEFAULT 1000
)
RETURNS TABLE(
  deleted_recordings INT,
  deleted_segments INT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_deleted_recordings INT;
  v_deleted_segments INT;
BEGIN
  -- Count segments to be deleted (if needed for logging)
  SELECT COUNT(*) INTO v_deleted_segments
  FROM segments
  WHERE recording_id IN (
    SELECT id FROM recordings
    WHERE created_at < now() - (in_retention_days || ' days')::INTERVAL
      AND status = 'done'
    LIMIT in_batch_size
  );
  
  -- Delete recordings (cascade will delete segments automatically)
  WITH deleted_recs AS (
    DELETE FROM recordings
    WHERE created_at < now() - (in_retention_days || ' days')::INTERVAL
      AND status = 'done'
    LIMIT in_batch_size
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_deleted_recordings FROM deleted_recs;
  
  RETURN QUERY SELECT v_deleted_recordings, v_deleted_segments;
END;
$$;
```

*Sử dụng*: Chạy định kỳ để giải phóng database storage, có thể customize retention theo plan.

