-- ============================================================================
-- PROCEDURE 4: Reset Monthly Cycles (Maintenance)
-- ============================================================================
CREATE OR REPLACE PROCEDURE sp_reset_monthly_cycles()
LANGUAGE plpgsql
AS $$
DECLARE
  v_cycle_start TIMESTAMPTZ;
  v_cycle_end TIMESTAMPTZ;
  v_affected_count INT;
BEGIN
  v_cycle_start := date_trunc('month', now());
  v_cycle_end := v_cycle_start + INTERVAL '1 month';

  UPDATE user_subscriptions
  SET cycle_start = v_cycle_start,
      cycle_end = v_cycle_end,
      usage_count = 0,
      used_seconds = 0
  WHERE cycle_end <= now();

  GET DIAGNOSTICS v_affected_count = ROW_COUNT;

  RAISE NOTICE 'Reset % subscriptions for new cycle % to %',
    v_affected_count, v_cycle_start, v_cycle_end;
END;
$$;