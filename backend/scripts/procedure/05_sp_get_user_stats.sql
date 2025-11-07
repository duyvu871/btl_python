-- ============================================================================
-- FUNCTION 5: Get User Statistics (Analytics)
-- ============================================================================
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