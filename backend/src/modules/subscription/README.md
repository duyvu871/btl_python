# Subscription Module

Module quản lý subscription plans và quota cho users.

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
    "remaining_count": 7,
    "used_minutes": 7.5,
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

## Testing

```python
# Test check quota
from src.modules.subscription.use_cases import get_check_quota_usecase

has_quota, msg = await check_quota_use_case.execute(user_id)
assert has_quota == True

# Test get subscription
subscription = await get_subscription_use_case.execute(user_id)
assert subscription.plan.code == "FREE"

# Test change plan
response = await change_plan_use_case.execute(
    user_id=user_id,
    plan_code="PREMIUM",
    prorate=True
)
assert response.new_plan.code == "PREMIUM"
```

## Notes

- Plans được seed với giá tính bằng cents (e.g., 999 = $9.99)
- Cycle dates được tính theo UTC
- Default plan là "FREE" với 30 phút/tháng và 10 recordings
- Khi prorate=True, usage sẽ được reset ngay lập tức

