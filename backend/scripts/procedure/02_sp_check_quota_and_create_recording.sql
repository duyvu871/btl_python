-- ============================================================================
-- FUNCTION 2: Check Quota and Create Recording (Atomic)
-- ============================================================================
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
