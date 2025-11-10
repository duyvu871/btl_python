-- ============================================================================
-- TRIGGER: Increment Usage Count on Recording Creation (Race-Condition Safe)
-- ============================================================================

DROP TRIGGER IF EXISTS increment_usage_on_recording ON recordings;
DROP FUNCTION IF EXISTS trg_increment_usage_on_recording();

CREATE OR REPLACE FUNCTION trg_increment_usage_on_recording()
RETURNS TRIGGER AS $$
DECLARE
  v_rows_updated INT;
  v_current_usage INT;
  v_usage_limit INT;
BEGIN
  -- Lock and get current subscription with quota check
  SELECT usage_count, monthly_usage_limit
  INTO v_current_usage, v_usage_limit
  FROM user_subscriptions us
  INNER JOIN plans p ON us.plan_id = p.id
  WHERE us.user_id = NEW.user_id
    AND now() >= us.cycle_start
    AND now() < us.cycle_end
  FOR UPDATE OF us;  -- Lock the subscription row

  -- Check if subscription exists
  IF NOT FOUND THEN
    RAISE EXCEPTION 'No active subscription found for user_id: %', NEW.user_id;
  END IF;

  -- Check quota limit (defensive check)
  IF v_current_usage >= v_usage_limit THEN
    RAISE EXCEPTION 'Usage quota exceeded for user_id: %. Current: %, Limit: %',
      NEW.user_id, v_current_usage, v_usage_limit;
  END IF;

  -- Atomic increment with verification
  UPDATE user_subscriptions
  SET usage_count = usage_count + 1
  WHERE user_id = NEW.user_id
    AND now() >= cycle_start
    AND now() < cycle_end
    AND usage_count < v_usage_limit;  -- Double-check in UPDATE

  GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

  -- Ensure update succeeded
  IF v_rows_updated = 0 THEN
    RAISE EXCEPTION 'Failed to increment usage for user_id: %', NEW.user_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_usage_on_recording
AFTER INSERT ON recordings
FOR EACH ROW
EXECUTE FUNCTION trg_increment_usage_on_recording();
