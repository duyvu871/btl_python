# Subscription Module

Module quản lý subscription plans và quota cho users.

## BREAKING CHANGE (Snapshot Plan)
Từ phiên bản hiện tại, dữ liệu `plan` trả về trong các endpoint subscription (`/subscriptions/me`, `/subscriptions/change-plan`) KHÔNG còn là `PlanResponse` đọc trực tiếp từ bảng `plans`, mà là `PlanSnapshotResponse` dựng từ các trường snapshot trong bảng `user_subscriptions`:
- code
- name
- monthly_minutes
- monthly_usage_limit

Điều này giúp:
- Không lỗi khi plan bị xóa / deactivate (plan_id=NULL).
- Giữ nguyên quota đến hết cycle hiện tại.
- Dễ audit lịch sử sử dụng theo cycle.

## Snapshot Dùng Cho Fallback
Các trường snapshot trong `user_subscriptions`:
- `plan_code_snapshot`
- `plan_name_snapshot`
- `plan_monthly_minutes_snapshot`
- `plan_monthly_usage_limit_snapshot`

Mọi quota check và hiển thị UI dùng các trường trên.
Khi plan bị deactivate hoặc xóa: `plan_id` có thể NULL nhưng snapshot vẫn đảm bảo hoạt động đến hết `cycle_end`.
Sau khi rollover (reset cycle) nếu plan không còn active → migrate sang default plan và cập nhật snapshot mới.

## Ví dụ Response Mới (`/subscriptions/me`)
```json
{
  "plan": {
    "code": "FREE",
    "name": "Free Plan",
    "monthly_minutes": 30,
    "monthly_usage_limit": 10
  },
  "cycle_start": "2025-11-01T00:00:00Z",
  "cycle_end": "2025-12-01T00:00:00Z",
  "usage": {
    "usage_count": 3,
    "monthly_usage_limit": 10,
    "remaining_count": 7,
    "used_seconds": 450,
    "monthly_seconds": 1800,
    "remaining_seconds": 1350,
    "used_minutes": 7.5,
    "monthly_minutes": 30,
    "remaining_minutes": 22.5
  }
}
```

## Cấu trúc

```
subscription/
├── repository.py          # PlanRepository, SubscriptionRepository
├── schema.py             # Pydantic schemas
├── routing.py            # API endpoints
└── use_cases/            # Business logic
    ├── check_quota_use_case.py
    ├── get_subscription_use_case.py
    ├── change_plan_use_case.py
    └── create_subscription_use_case.py
```

## Use Cases

### 1. CheckQuotaUseCase
Kiểm tra xem user có còn quota để tạo recording mới không.

**Input**: `user_id: UUID`
**Output**: `(has_quota: bool, error_message: str)`

**Sử dụng**:
```python
has_quota, error_msg = await check_quota_use_case.execute(user_id)
if not has_quota:
    raise HTTPException(403, detail=error_msg)
```

### 2. GetSubscriptionUseCase
Lấy thông tin subscription hiện tại của user (cho dashboard).

**Input**: `user_id: UUID`
**Output**: `SubscriptionDetailResponse`

**Response structure**:
```json
{
  "plan": {
    "code": "FREE",
    "name": "Free Plan",
    "monthly_minutes": 30,
    "monthly_usage_limit": 10
  },
  "cycle_start": "2025-11-01T00:00:00Z",
  "cycle_end": "2025-12-01T00:00:00Z",
  "usage": {
    "usage_count": 3,
    "monthly_usage_limit": 10,
    "remaining_count": 7,
    "used_seconds": 450,
    "monthly_seconds": 1800,
    "remaining_seconds": 1350,
    "used_minutes": 7.5,
    "monthly_minutes": 30,
    "remaining_minutes": 22.5
  }
}
```

### 3. ChangePlanUseCase
Thay đổi subscription plan (upgrade/downgrade).

**Input**: 
- `user_id: UUID`
- `plan_code: str` (e.g., "BASIC", "PREMIUM")
- `prorate: bool` (reset usage khi đổi plan)

**Output**: `ChangePlanResponse`

### 4. CreateSubscriptionUseCase
Tạo subscription mới cho user (gọi khi user đăng ký).

**Input**: `user_id: UUID`
**Output**: `UserSubscription`

**Note**: Tự động gán FREE plan cho user mới.

## API Endpoints

### GET `/subscriptions/me`
Lấy subscription của current user.

**Auth**: Required
**Response**: `SubscriptionDetailResponse`

### GET `/subscriptions/check-quota`
Kiểm tra quota của current user.

**Auth**: Required
**Response**: `QuotaCheckResponse`

### POST `/subscriptions/change-plan`
Đổi plan cho current user.

**Auth**: Required
**Request Body**:
```json
{
  "plan_code": "PREMIUM",
  "prorate": false
}
```

### GET `/subscriptions/plans`
Liệt kê tất cả plans có sẵn.

**Auth**: Not required
**Response**: `List[PlanResponse]`

## Repositories

### PlanRepository
```python
# Get plan by code
plan = await uow.plan_repo.get_by_code("FREE")

# List all plans
plans = await uow.plan_repo.list_active_plans()

# Get default plan
default_plan = await uow.plan_repo.get_default_plan()
```

### SubscriptionRepository
```python
# Get active subscription
subscription = await uow.subscription_repo.get_active_subscription(user_id)

# Check quota
has_quota, error = await uow.subscription_repo.has_quota(user_id)

# Get usage stats
stats = await uow.subscription_repo.get_usage_stats(user_id)

# Increment usage (TODO: implement)
await uow.subscription_repo.increment_usage(user_id)

# Update used seconds (TODO: implement)
await uow.subscription_repo.update_used_seconds(user_id, 120)
```

## Integration

### 1. User Registration
Khi user đăng ký, tự động tạo subscription với FREE plan:

```python
# In RegisterUserUseCase
user = await self.uow.user_repo.create(data)
await self.create_subscription_use_case.execute(user.id)
```

### 2. Recording Creation
Trước khi tạo recording, check quota:

```python
# In CreateRecordingEndpoint
has_quota, error_msg = await check_quota.execute(current_user.id)
if not has_quota:
    raise HTTPException(403, detail=error_msg)
    
# Create recording
recording = await uow.recording_repo.create({...})
```

### 3. Recording Completion
Sau khi hoàn thành recording, update used_seconds:

```python
# In CompleteRecordingUseCase
await uow.subscription_repo.update_used_seconds(user_id, duration_seconds)
```

## Database Triggers

Module này dựa vào stored procedures:
- **Trigger**: Tự động tăng `usage_count` khi insert recording
- **SP**: `sp_complete_recording` - Cập nhật `used_seconds`
- **SP**: `sp_reset_monthly_cycles` - Reset cycle hàng tháng

## Setup

### 1. Seed Plans
```bash
cd backend
python -m scripts.seed_plans
```

### 2. Chạy Migrations
Plans và UserSubscription tables đã được tạo bởi alembic migrations.

## TODO Items

Team members cần implement các phần sau trong `repository.py`:

### SubscriptionRepository

1. **increment_usage(user_id)**
   - Tăng `usage_count` lên 1
   - Có thể dùng SQL UPDATE hoặc fetch + update

2. **update_used_seconds(user_id, seconds)**
   - Cộng `seconds` vào `used_seconds`
   - Tương tự increment_usage

3. **reset_cycle(user_id)**
   - Reset `usage_count = 0`
   - Reset `used_seconds = 0`
   - Update `cycle_start` = ngày 1 tháng hiện tại
   - Update `cycle_end` = ngày 1 tháng sau

**Hint**: Có thể tham khảo implementation trong `UserRepository` để biết cách query.

## Fallback khi Plan bị xóa / deactivate (Cập nhật)
1. Soft delete: `is_active=False`; default plan (`is_default=True`) không được phép deactivate.
2. Quota & hiển thị sử dụng snapshot: tránh lỗi khi `plan_id=NULL`.
3. Change plan / create subscription: luôn gọi `apply_plan_snapshot(plan)`.
4. Reset cycle: nếu plan inactive hoặc NULL → gán default plan + cập nhật snapshot.

### Business Guard Gợi Ý
- Chặn thao tác deactivate/delete nếu `plan.is_default == True`.
- Khi deactivate, trả về danh sách subscriptions bị ảnh hưởng để có thể ghi audit log.

## Testing Fallback

1. Tạo user + subscription với plan PREMIUM.
2. Deactivate plan PREMIUM (`is_active = False`).
3. Gọi `CheckQuotaUseCase` vẫn dùng snapshot PREMIUM cho tới cycle_end.
4. Simulate cycle rollover job → subscription chuyển sang FREE và snapshot update theo FREE.
5. Verify usage counters reset / giữ nguyên đúng rule.

## Notes

- Plans được seed với giá tính bằng cents (e.g., 999 = $9.99)
- Cycle dates được tính theo UTC
- Default plan là "FREE" với 30 phút/tháng và 10 recordings
- Khi prorate=True, usage sẽ được reset ngay lập tức

- Mọi tính toán quota phải dựa vào snapshot.
- UI có thể hiển thị tên plan từ snapshot kể cả khi plan gốc đã bị ẩn.
