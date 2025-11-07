-- ============================================================================
-- PROCEDURE 6: Change User Plan (Upgrade/Downgrade)
-- ============================================================================
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