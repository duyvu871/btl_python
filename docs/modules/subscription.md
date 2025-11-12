# Subscription Module - Kiến Trúc & Flow (Ngắn Gọn)

## BREAKING CHANGE (Snapshot Plan)
Các endpoint subscription nay trả về plan ở dạng snapshot (`PlanSnapshotResponse`) lấy từ các trường:
- `plan_code_snapshot`
- `plan_name_snapshot`
- `plan_monthly_minutes_snapshot`
- `plan_monthly_usage_limit_snapshot`
Thay vì đọc trực tiếp từ bảng `plans`. Điều này tránh lỗi khi plan bị xóa/deactivate và giữ nguyên quota tới hết cycle.

## Snapshot Fallback (Cập nhật)
Sử dụng các trường snapshot trong `user_subscriptions` để đảm bảo quota vẫn hoạt động khi plan bị deactivate hoặc xóa:
- `plan_code_snapshot`
- `plan_name_snapshot`
- `plan_monthly_minutes_snapshot`
- `plan_monthly_usage_limit_snapshot`

Check quota, thống kê usage, và hiển thị dashboard dựa trên snapshot. Khi cycle reset nếu plan không active hoặc đã xóa → migrate về default plan và cập nhật snapshot mới.

## Ví dụ Response `/subscriptions/me`
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

## Tổng Quan

Module subscription quản lý gói dịch vụ và quota theo pattern:
- **Repository**: Truy vấn database (CRUD + business queries)
- **Use Case**: Business logic (orchestrate repositories)
- **Unit of Work**: Quản lý transaction và repositories
- **Routing**: API endpoints

---

## Cấu Trúc Thư Mục

```
src/modules/subscription/
├── repository.py          # PlanRepository, SubscriptionRepository
├── use_cases/
│   ├── check_quota_use_case.py
│   ├── get_subscription_use_case.py
│   ├── change_plan_use_case.py
│   └── create_subscription_use_case.py
├── schema.py              # Pydantic models
└── routing.py             # FastAPI endpoints
```

---

## 1. Repositories

### PlanRepository
```python
class PlanRepository(BaseRepository[Plan]):
    async def get_by_code(code: str) -> Plan | None
    async def list_active_plans() -> list[Plan]
    async def get_default_plan() -> Plan  # Lấy FREE plan
```

### SubscriptionRepository
```python
class SubscriptionRepository(BaseRepository[UserSubscription]):
    async def get_active_subscription(user_id) -> UserSubscription | None
    async def has_quota(user_id) -> tuple[bool, str]  # (ok, error_msg)
    async def increment_usage(user_id) -> None
    async def update_used_seconds(user_id, seconds) -> None
    async def get_usage_stats(user_id) -> dict
```

---

## 2. Use Cases

### CheckQuotaUseCase
**Nhiệm vụ**: Kiểm tra quota trước khi tạo recording

**Flow**:
1. Lấy active subscription
2. Check `usage_count < monthly_usage_limit`
3. Check `used_seconds < monthly_minutes * 60`
4. Return `(has_quota: bool, error_message: str)`

### GetSubscriptionUseCase
**Nhiệm vụ**: Dashboard - lấy thông tin subscription + usage stats

**Return**:
```python
{
    "plan": {"code": "FREE", "name": "...", "monthly_minutes": 30},
    "cycle": {"start": "2025-11-01", "end": "2025-12-01"},
    "usage": {"count": 3, "remaining": 7, "used_seconds": 450}
}
```

### ChangePlanUseCase
**Nhiệm vụ**: Upgrade/downgrade plan

**Flow**:
1. Validate new plan exists
2. Update `plan_id` trong subscription
3. (Optional) Reset usage nếu `prorate=True`

### CreateSubscriptionUseCase
**Nhiệm vụ**: Tạo subscription khi user đăng ký (gọi từ RegisterUserUseCase)

**Flow**:
1. Lấy FREE plan
2. Tạo subscription với cycle = 1 tháng
3. Return subscription

---

## 3. Unit of Work

Thêm repositories:

```python
class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.plan_repo = PlanRepository(session)              # NEW
        self.subscription_repo = SubscriptionRepository(session)  # NEW
```

---

## 4. Schemas

```python
class ChangePlanRequest(BaseModel):
    plan_code: str
    prorate: bool = False

class SubscriptionResponse(BaseModel):
    plan: PlanResponse
    cycle_start: datetime
    cycle_end: datetime
    usage: UsageResponse
```

---

## 5. API Endpoints

```python
@router.get("/me")
async def get_my_subscription(
    current_user = Depends(get_current_user),
    use_case = Depends(get_subscription_usecase)
):
    return await use_case.execute(current_user.id)

@router.post("/change-plan")
async def change_plan(
    request: ChangePlanRequest,
    current_user = Depends(get_current_user),
    use_case = Depends(get_change_plan_usecase)
):
    await use_case.execute(current_user.id, request.plan_code, request.prorate)
    return {"message": "Plan changed successfully"}

@router.get("/plans")
async def list_plans(uow = Depends(get_uow)):
    return await uow.plan_repo.list_active_plans()
```

---

## 6. Integration với Registration

Update `RegisterUserUseCase`:

```python
class RegisterUserUseCase:
    def __init__(self, uow, verification_use_case, create_subscription_use_case):
        ...

    async def execute(self, user_data):
        # Tạo user
        user = await self.uow.user_repo.create(data)
        
        # Tạo subscription với FREE plan
        await self.create_subscription_use_case.execute(user.id)
        
        # Send verification email
        ...
```

---

## 7. Integration với Recording

Check quota trước khi tạo:

```python
@router.post("/recordings")
async def create_recording(
    request,
    current_user = Depends(get_current_user),
    check_quota = Depends(get_check_quota_usecase),
    uow = Depends(get_uow)
):
    # Check quota
    has_quota, error_msg = await check_quota.execute(current_user.id)
    if not has_quota:
        raise HTTPException(403, detail=error_msg)
    
    # Tạo recording (trigger tự động tăng usage_count)
    recording = await uow.recording_repo.create({...})
    return recording
```

---

## Flow Tổng Hợp

### Registration Flow
```
User đăng ký
  → RegisterUserUseCase
    → Tạo User
    → CreateSubscriptionUseCase (tạo subscription với FREE plan)
    → Send verification email
```

### Check Quota Flow
```
User tạo recording
  → CheckQuotaUseCase
    → Lấy subscription
    → Kiểm tra limits
    → Return (ok/not ok)
  → Nếu OK: Insert recording → Trigger tự động tăng usage_count
```

### Dashboard Flow
```
User xem dashboard
  → GetSubscriptionUseCase
    → Lấy subscription + plan
    → Tính remaining quota
    → Return info
```

### Change Plan Flow
```
User đổi plan
  → ChangePlanUseCase
    → Validate plan
    → Update plan_id
    → (Optional) Reset usage
```

---

## Checklist

- [ ] Tạo PlanRepository và SubscriptionRepository
- [ ] Thêm vào UnitOfWork
- [ ] Tạo 4 use cases
- [ ] Tạo schemas
- [ ] Tạo routing (3 endpoints)
- [ ] Update RegisterUserUseCase
- [ ] Seed FREE plan
- [ ] Setup Celery tasks (reset cycles, cleanup)
