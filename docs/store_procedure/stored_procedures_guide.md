# Stored Procedures & Functions - Hướng Dẫn Best Practices

## Tổng Quan

Document này mô tả các stored procedures/functions được thiết kế cho BTL Python S2T System, lợi ích của chúng, và cách sử dụng hiệu quả.

## Tại Sao Sử Dụng Stored Procedures?

### 1. **Performance (Hiệu Suất)**
- **Giảm Network Roundtrips**: 1 call thay vì 3-5 queries
- **Query Plan Caching**: PostgreSQL cache execution plans
- **Batch Operations**: Insert nhiều rows cùng lúc nhanh hơn loops

### 2. **Atomicity (Tính Nguyên Tử)**
- **Transactional Logic**: Tất cả thành công hoặc tất cả rollback
- **Race Condition Prevention**: Check-then-act trong 1 transaction
- **Data Consistency**: Đảm bảo integrity constraints

### 3. **Business Logic Centralization**
- **Single Source of Truth**: Logic ở database, không duplicate
- **Easy Testing**: Test logic độc lập với application code
- **Version Control**: Migration scripts track changes

### 4. **Security**
- **Permission Control**: Grant execute on procedure, không cần table access
- **SQL Injection Prevention**: Parameterized queries
- **Audit Trail**: Log trong procedure

## Danh Sách Procedures/Functions

### 1. `sp_register_user` - Đăng Ký User Transactional

**Mục đích**: Tạo user, profile, subscription trong 1 transaction atomically.

**Signature**:
```sql
CALL sp_register_user(
  in_email TEXT,
  in_user_name TEXT,
  in_hashed_pass TEXT,
  in_name TEXT,
  in_default_plan_code TEXT
);
```

**Python Usage**:
```python
from sqlalchemy import text

async def register_user(
    db: AsyncSession,
    email: str,
    user_name: str,
    password: str,
    name: str
) -> None:
    hashed_password = hash_password(password)
    
    await db.execute(
        text("""
            CALL sp_register_user(
                :email, :user_name, :hashed_pass, :name, :plan_code
            )
        """),
        {
            "email": email,
            "user_name": user_name,
            "hashed_pass": hashed_password,
            "name": name,
            "plan_code": "FREE"
        }
    )
    await db.commit()
```

**Lợi ích**:
- ✅ Atomic: Tất cả hoặc không gì (rollback nếu có lỗi)
- ✅ Consistent: Luôn có profile + subscription khi có user
- ✅ Fast: 1 roundtrip thay vì 3 separate inserts

---

### 2. `sp_check_quota_and_create_recording` - Kiểm Tra Quota & Tạo Recording

**Mục đích**: Atomic check quota + create recording, tránh race conditions.

**Signature**:
```sql
SELECT * FROM sp_check_quota_and_create_recording(
  in_user_id UUID,
  in_source TEXT,
  in_language TEXT DEFAULT 'vi',
  in_meta JSONB DEFAULT '{}'::jsonb
);

-- Returns:
-- recording_id UUID
-- quota_ok BOOLEAN
-- error_message TEXT
```

**Python Usage**:
```python
async def create_recording_with_quota_check(
    db: AsyncSession,
    user_id: UUID,
    source: str,
    language: str = "vi"
) -> tuple[UUID | None, bool, str]:
    result = await db.execute(
        text("""
            SELECT * FROM sp_check_quota_and_create_recording(
                :user_id, :source, :language
            )
        """),
        {"user_id": user_id, "source": source, "language": language}
    )
    row = result.fetchone()
    await db.commit()
    
    return row.recording_id, row.quota_ok, row.error_message

# Usage in endpoint
recording_id, quota_ok, error_msg = await create_recording_with_quota_check(
    db, current_user.id, "realtime"
)

if not quota_ok:
    raise HTTPException(status_code=403, detail=error_msg)
```

**Lợi ích**:
- ✅ No Race Condition: Check & create trong 1 transaction
- ✅ Performance: 1 query thay vì: get subscription → get plan → check → insert
- ✅ Better UX: Rõ ràng lý do từ chối (usage limit vs minutes limit)

**Scenario Prevented**:
```
Without procedure:
Thread A: Check quota (OK) ──┐
Thread B: Check quota (OK) ──┤
                              ├─> Both pass
Thread A: Create recording ───┤
Thread B: Create recording ───┘─> Quota exceeded but both created!

With procedure:
Thread A: Check+Create (Atomic) ✓
Thread B: Check+Create (Atomic) ✗ Quota exceeded
```

---

### 3. `sp_complete_recording` - Hoàn Tất Recording với Segments

**Mục đích**: Update recording + batch insert segments + update used_seconds.

**Signature**:
```sql
CALL sp_complete_recording(
  in_recording_id UUID,
  in_duration_ms INT,
  in_segments JSONB
);

-- in_segments format:
-- [{"idx": 0, "start_ms": 0, "end_ms": 1000, "text": "..."}]
```

**Python Usage**:
```python
async def complete_recording(
    db: AsyncSession,
    recording_id: UUID,
    duration_ms: int,
    segments: list[dict]
) -> None:
    import json
    
    await db.execute(
        text("""
            CALL sp_complete_recording(
                :recording_id, :duration_ms, :segments::jsonb
            )
        """),
        {
            "recording_id": recording_id,
            "duration_ms": duration_ms,
            "segments": json.dumps(segments)
        }
    )
    await db.commit()

# Usage in Celery worker
segments = [
    {"idx": 0, "start_ms": 0, "end_ms": 3000, "text": "First segment"},
    {"idx": 1, "start_ms": 3000, "end_ms": 6000, "text": "Second segment"},
    # ... 100 more segments
]

await complete_recording(db, recording_id, 60000, segments)
```

**Lợi ích**:
- ✅ Batch Insert: 100x nhanh hơn insert từng segment
- ✅ Atomic: Recording status + segments + used_seconds cùng update
- ✅ Error Handling: Auto mark failed nếu có lỗi

**So Sánh Hiệu Suất**:
```
Cách thủ công (100 segments):
- UPDATE recordings: 1 query (10ms)
- INSERT segments x 100: 100 queries (1000ms)
- UPDATE subscription: 1 query (10ms)
Tổng: ~1020ms

Với procedure:
- CALL sp_complete_recording: 1 query (50ms)
Tổng: ~50ms (nhanh hơn 20x!)
```

---

### 4. `sp_reset_monthly_cycles` - Reset Chu Kỳ Hàng Tháng

**Mục đích**: Scheduled maintenance để reset usage mỗi tháng.

**Signature**:
```sql
CALL sp_reset_monthly_cycles();
```

**Python Usage (Celery Beat)**:
```python
from celery import Celery
from celery.schedules import crontab

@celery.task
async def reset_monthly_cycles():
    """Run at 00:00 on 1st day of every month"""
    async with get_db() as db:
        await db.execute(text("CALL sp_reset_monthly_cycles()"))
        await db.commit()
        logger.info("Monthly cycles reset completed")

# In celery config
celery.conf.beat_schedule = {
    'reset-monthly-cycles': {
        'task': 'tasks.reset_monthly_cycles',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
}
```

**Phương Án Thay Thế: pg_cron**:
```sql
-- Cài đặt pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule reset hàng tháng
SELECT cron.schedule(
    'reset-monthly-cycles',
    '0 0 1 * *',  -- Vào 00:00 ngày 1 hàng tháng
    'CALL sp_reset_monthly_cycles()'
);
```

**Lợi ích**:
- ✅ Tin cậy: Scheduling ở database level (pg_cron)
- ✅ Có log: RAISE NOTICE hiển thị số lượng affected
- ✅ Idempotent: An toàn khi chạy nhiều lần

---

### 5. `sp_get_user_stats` - Lấy Thống Kê User

**Mục đích**: Dashboard analytics với 1 query thay vì nhiều queries.

**Signature**:
```sql
SELECT * FROM sp_get_user_stats(in_user_id UUID);

-- Returns:
-- total_recordings BIGINT
-- total_duration_minutes NUMERIC
-- total_segments BIGINT
-- current_cycle_usage INT
-- current_cycle_seconds INT
-- quota_usage_percent NUMERIC
-- quota_minutes_percent NUMERIC
```

**Python Usage**:
```python
async def get_user_dashboard_stats(
    db: AsyncSession,
    user_id: UUID
) -> dict:
    result = await db.execute(
        text("SELECT * FROM sp_get_user_stats(:user_id)"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    
    return {
        "total_recordings": row.total_recordings,
        "total_duration_minutes": float(row.total_duration_minutes),
        "total_segments": row.total_segments,
        "current_cycle": {
            "usage_count": row.current_cycle_usage,
            "used_seconds": row.current_cycle_seconds,
            "quota_usage_percent": float(row.quota_usage_percent),
            "quota_minutes_percent": float(row.quota_minutes_percent),
        }
    }

# FastAPI endpoint
@router.get("/dashboard/stats")
async def dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stats = await get_user_dashboard_stats(db, current_user.id)
    return stats
```

**Lợi ích**:
- ✅ Performance: 1 query thay vì 5-6 queries
- ✅ Consistency: Tất cả stats từ same snapshot
- ✅ Reusability: Dùng cho multiple endpoints

---

### 6. `sp_change_user_plan` - Đổi Gói Dịch Vụ

**Mục đích**: Upgrade/downgrade plan với validation logic.

**Signature**:
```sql
CALL sp_change_user_plan(
  in_user_id UUID,
  in_new_plan_code TEXT,
  in_prorate BOOLEAN DEFAULT FALSE,
  OUT success BOOLEAN,
  OUT message TEXT
);
```

**Python Usage**:
```python
async def change_user_plan(
    db: AsyncSession,
    user_id: UUID,
    new_plan_code: str,
    prorate: bool = False
) -> tuple[bool, str]:
    result = await db.execute(
        text("""
            CALL sp_change_user_plan(
                :user_id, :plan_code, :prorate, NULL, NULL
            )
        """),
        {"user_id": user_id, "plan_code": new_plan_code, "prorate": prorate}
    )
    
    # Get OUT parameters
    row = result.fetchone()
    await db.commit()
    
    return row.success, row.message

# Usage
success, message = await change_user_plan(db, user_id, "PREMIUM", prorate=True)
if not success:
    raise HTTPException(status_code=400, detail=message)
```

**Lợi ích**:
- ✅ Validation: Check plan exists, user has subscription, not same plan
- ✅ Clear Error Messages: Return specific reason for failure
- ✅ Future-proof: Add billing logic later inside procedure

---

### 7. `sp_cleanup_old_recordings` - Dọn Dẹp Dữ Liệu Cũ

**Mục đích**: Retention policy - xóa recordings cũ để tiết kiệm storage.

**Signature**:
```sql
SELECT * FROM sp_cleanup_old_recordings(
  in_retention_days INT DEFAULT 90,
  in_batch_size INT DEFAULT 1000
);

-- Returns:
-- deleted_recordings INT
-- deleted_segments INT
```

**Python Usage (Celery)**:
```python
@celery.task
async def cleanup_old_data():
    """Run daily to clean up old recordings"""
    async with get_db() as db:
        result = await db.execute(
            text("""
                SELECT * FROM sp_cleanup_old_recordings(
                    :retention_days, :batch_size
                )
            """),
            {"retention_days": 90, "batch_size": 1000}
        )
        row = result.fetchone()
        await db.commit()
        
        logger.info(
            f"Cleanup completed: {row.deleted_recordings} recordings, "
            f"{row.deleted_segments} segments deleted"
        )

# Schedule daily at 2 AM
celery.conf.beat_schedule = {
    'cleanup-old-recordings': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

**Lợi ích**:
- ✅ Batch Processing: Xóa 1000 records mỗi lần để tránh locks
- ✅ Quản Lý Storage: Giải phóng không gian database
- ✅ Linh Hoạt: Có thể dùng retention khác nhau theo plan (tương lai)

---

## Best Practices

### 1. Xử Lý Lỗi (Error Handling)
```python
from sqlalchemy.exc import SQLAlchemyError

async def call_procedure_safely(db, procedure_call):
    try:
        result = await db.execute(text(procedure_call))
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Procedure failed: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
```

### 2. Logging
```python
import logging

logger = logging.getLogger(__name__)

async def register_user_with_logging(db, email, user_name, password, name):
    logger.info(f"Registering user: {email}")
    try:
        await db.execute(
            text("CALL sp_register_user(:email, :user_name, :pass, :name, :plan)"),
            {...}
        )
        await db.commit()
        logger.info(f"User registered successfully: {email}")
    except Exception as e:
        logger.error(f"Registration failed for {email}: {e}")
        raise
```

### 3. Testing
```python
import pytest
from sqlalchemy import text

@pytest.mark.asyncio
async def test_register_user(db_session):
    # Setup: Ensure FREE plan exists
    await db_session.execute(
        text("INSERT INTO plans (code, name, monthly_minutes, monthly_usage_limit) "
             "VALUES ('FREE', 'Free Plan', 30, 10)")
    )
    await db_session.commit()
    
    # Test
    await db_session.execute(
        text("CALL sp_register_user(:email, :user_name, :pass, :name, :plan)"),
        {
            "email": "test@example.com",
            "user_name": "testuser",
            "pass": "hashed_pass",
            "name": "Test User",
            "plan": "FREE"
        }
    )
    await db_session.commit()
    
    # Verify
    result = await db_session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": "test@example.com"}
    )
    user = result.fetchone()
    assert user is not None
    
    # Verify profile created
    result = await db_session.execute(
        text("SELECT * FROM user_profiles WHERE user_id = :user_id"),
        {"user_id": user.id}
    )
    profile = result.fetchone()
    assert profile is not None
    
    # Verify subscription created
    result = await db_session.execute(
        text("SELECT * FROM user_subscriptions WHERE user_id = :user_id"),
        {"user_id": user.id}
    )
    subscription = result.fetchone()
    assert subscription is not None
```

### 4. Migration Management
```python
# In alembic migration
from alembic import op

def upgrade():
    # Run SQL file with all procedures
    with open('scripts/create_procedures.sql', 'r') as f:
        sql = f.read()
        op.execute(sql)

def downgrade():
    # Drop all procedures
    op.execute("DROP PROCEDURE IF EXISTS sp_register_user")
    op.execute("DROP FUNCTION IF EXISTS sp_check_quota_and_create_recording")
    # ... drop all
```

## Mẹo Tối Ưu Performance

### 1. Sử Dụng EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT * FROM sp_check_quota_and_create_recording(
    '123e4567-e89b-12d3-a456-426614174000',
    'realtime',
    'vi'
);
```

### 2. Tối Ưu Index
```sql
-- Index cho quota checks (cycle_start, cycle_end)
CREATE INDEX idx_user_subscriptions_active_cycle 
ON user_subscriptions(user_id, cycle_start, cycle_end) 
WHERE cycle_end > now();

-- Index cho recordings cleanup
CREATE INDEX idx_recordings_cleanup 
ON recordings(created_at, status) 
WHERE status = 'done';
```

### 3. Connection Pooling
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Connection pool
    max_overflow=10,
    pool_pre_ping=True,  # Check connection health
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

## Giám Sát (Monitoring)

### 1. Query Performance
```sql
-- Bật pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- Giám sát hiệu suất procedure
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%sp_%'
ORDER BY mean_exec_time DESC;
```

### 2. Application Metrics
```python
from prometheus_client import Histogram

procedure_duration = Histogram(
    'procedure_duration_seconds',
    'Time spent in stored procedures',
    ['procedure_name']
)

async def call_procedure_with_metrics(name, procedure_call):
    with procedure_duration.labels(procedure_name=name).time():
        result = await db.execute(text(procedure_call))
        await db.commit()
    return result
```

## Tổng Kết

| Procedure | Trường Hợp Sử Dụng | Lợi Ích Chính |
|-----------|----------|-------------|
| `sp_register_user` | Đăng ký user | Atomic user + profile + subscription |
| `sp_check_quota_and_create_recording` | Yêu cầu S2T | Không có race conditions |
| `sp_complete_recording` | Sau khi S2T xong | Batch insert segments |
| `sp_reset_monthly_cycles` | Job hàng tháng | Reset quotas |
| `sp_get_user_stats` | Dashboard | 1 query cho tất cả stats |
| `sp_change_user_plan` | Nâng cấp plan | Validated plan change |
| `sp_cleanup_old_recordings` | Maintenance | Quản lý storage |

**Lợi Ích Tổng Thể**:
- 🚀 **Nhanh hơn 20-50x** cho batch operations
- 🔒 **Không có race-condition** cho quota checks
- 🛡️ **Atomic transactions** đảm bảo tính nhất quán dữ liệu
- 📊 **Giám sát tốt hơn** với logic tập trung
- 🧪 **Testing dễ hơn** với database logic độc lập

