-- ============================================================================
-- TRIGGER: Increment Usage Count on Recording Creation
-- ============================================================================
-- Description:
--   - Increments usage_count when a new recording is created
--   - Validates quota before allowing recording creation
--   - Race-condition safe with row-level locking
--   - used_minutes is handled separately when recording completes
-- ============================================================================

DROP TRIGGER IF EXISTS increment_usage_on_recording ON recordings;
DROP FUNCTION IF EXISTS trg_increment_usage_on_recording();

CREATE OR REPLACE FUNCTION trg_increment_usage_on_recording()
RETURNS TRIGGER AS $$
DECLARE
  v_subscription_id UUID;
  v_usage_count INT;
  v_monthly_limit INT;
BEGIN
  -- Lock subscription row and get current usage (prevents race conditions)
  SELECT
    us.id,
    us.usage_count,
    us.plan_monthly_usage_limit_snapshot
  INTO
    v_subscription_id,
    v_usage_count,
    v_monthly_limit
  FROM user_subscriptions us
  WHERE us.user_id = NEW.user_id
    AND CURRENT_TIMESTAMP >= us.cycle_start
    AND CURRENT_TIMESTAMP < us.cycle_end
  FOR UPDATE OF us;  -- Row-level lock on subscription

  -- Validate subscription exists
  IF v_subscription_id IS NULL THEN
    RAISE EXCEPTION 'No active subscription found for user_id=%', NEW.user_id
      USING HINT = 'User must have an active subscription to create recordings';
  END IF;

  -- Validate quota limit
  IF v_usage_count >= v_monthly_limit THEN
    RAISE EXCEPTION 'Monthly recording quota exceeded for user_id=%', NEW.user_id
      USING
        HINT = FORMAT('Current usage: %s/%s recordings', v_usage_count, v_monthly_limit),
        ERRCODE = 'check_violation';
  END IF;

  -- Atomically increment usage count
  UPDATE user_subscriptions
  SET
    usage_count = usage_count + 1,
    updated_at = CURRENT_TIMESTAMP
  WHERE id = v_subscription_id
    AND usage_count < v_monthly_limit;  -- Additional safety check

  -- Verify update succeeded
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Failed to increment usage count for user_id=%', NEW.user_id
      USING HINT = 'Concurrent quota limit reached';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger that fires AFTER INSERT
CREATE TRIGGER increment_usage_on_recording
AFTER INSERT ON recordings
FOR EACH ROW
EXECUTE FUNCTION trg_increment_usage_on_recording();

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Trigger fires AFTER INSERT to ensure recording ID exists
-- 2. FOR UPDATE lock prevents concurrent modifications to same subscription
-- 3. Double-check in UPDATE (usage_count < v_monthly_limit) prevents edge cases
-- 4. used_minutes is NOT handled here - it's calculated when recording completes
-- 5. CURRENT_TIMESTAMP used for consistency with subscription cycle checks
-- ============================================================================

