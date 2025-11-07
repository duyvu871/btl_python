-- ============================================================================
-- TRIGGER: Increment Usage Count on Recording Creation
-- ============================================================================
-- Purpose: Automatically increment the usage_count in user_subscriptions
--          when a new recording is inserted
-- ============================================================================

-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS increment_usage_on_recording ON recordings;
DROP FUNCTION IF EXISTS trg_increment_usage_on_recording();

-- Create the trigger function
CREATE OR REPLACE FUNCTION trg_increment_usage_on_recording()
RETURNS TRIGGER AS $$
DECLARE
  v_rows_updated INT;
BEGIN
  -- Increment usage_count for the active subscription cycle
  UPDATE user_subscriptions
  SET usage_count = usage_count + 1
  WHERE user_id = NEW.user_id
    AND now() >= cycle_start
    AND now() < cycle_end;

  -- Get the number of rows updated
  GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

  -- Optional: Log if no active subscription was found
  -- This is useful for debugging but can be removed in production
  IF v_rows_updated = 0 THEN
    RAISE WARNING 'No active subscription found for user_id: % when creating recording_id: %',
      NEW.user_id, NEW.id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER increment_usage_on_recording
AFTER INSERT ON recordings
FOR EACH ROW
EXECUTE FUNCTION trg_increment_usage_on_recording();

-- ============================================================================
-- Usage Notes:
-- ============================================================================
-- 1. This trigger fires AFTER INSERT on the recordings table
-- 2. It automatically increments usage_count for the user's active subscription
-- 3. The trigger only updates subscriptions within the current cycle
-- 4. If no active subscription is found, a warning is raised (can be disabled)
-- 5. The trigger works in conjunction with:
--    - sp_check_quota_and_create_recording (checks quota before creation)
--    - sp_complete_recording (updates used_seconds after completion)
--
-- Testing:
-- To test this trigger, insert a recording and verify the usage_count increases:
--   INSERT INTO recordings (user_id, source, language)
--   VALUES ('some-user-uuid', 'upload', 'vi');
--
--   SELECT usage_count FROM user_subscriptions
--   WHERE user_id = 'some-user-uuid'
--     AND now() >= cycle_start AND now() < cycle_end;
-- ============================================================================

