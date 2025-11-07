
-- ============================================================================
-- PROCEDURE 3: Complete Recording with Batch Insert Segments
-- ============================================================================
CREATE OR REPLACE PROCEDURE sp_complete_recording(
  in_recording_id UUID,
  in_duration_ms INT,
  in_segments JSONB  -- [{"idx": 0, "start_ms": 0, "end_ms": 1000, "text": "..."}]
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id UUID;
  v_duration_seconds INT;
BEGIN
  -- Update recording status
  UPDATE recordings
  SET status = 'done',
      duration_ms = in_duration_ms,
      completed_at = now()
  WHERE id = in_recording_id
  RETURNING user_id INTO v_user_id;

  -- Batch insert segments
  INSERT INTO segments (recording_id, idx, start_ms, end_ms, text)
  SELECT
    in_recording_id,
    (seg->>'idx')::INT,
    (seg->>'start_ms')::INT,
    (seg->>'end_ms')::INT,
    seg->>'text'
  FROM jsonb_array_elements(in_segments) AS seg;

  -- Update used_seconds in subscription
  v_duration_seconds := in_duration_ms / 1000;
  UPDATE user_subscriptions
  SET used_seconds = used_seconds + v_duration_seconds
  WHERE user_id = v_user_id
    AND now() >= cycle_start
    AND now() < cycle_end;

EXCEPTION
  WHEN OTHERS THEN
    -- Mark as failed
    UPDATE recordings SET status = 'failed' WHERE id = in_recording_id;
    RAISE;
END;
$$;