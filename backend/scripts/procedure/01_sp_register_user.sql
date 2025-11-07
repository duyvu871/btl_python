-- ============================================================================
-- PROCEDURE 1: Register User (Transactional)
-- ============================================================================
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
  -- Find plan
  SELECT id INTO v_plan_id FROM plans WHERE code = in_default_plan_code;
  IF v_plan_id IS NULL THEN
    RAISE EXCEPTION 'default plan % not found', in_default_plan_code;
  END IF;

  -- Create user
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