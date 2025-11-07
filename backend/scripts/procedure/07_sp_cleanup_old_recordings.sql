-- ============================================================================
-- FUNCTION 7: Clean Up Old Recordings (Maintenance)
-- ============================================================================
CREATE OR REPLACE FUNCTION sp_cleanup_old_recordings(
  in_retention_days INT DEFAULT 90,
  in_batch_size INT DEFAULT 1000
)
RETURNS TABLE(
  deleted_recordings INT,
  deleted_segments INT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_deleted_recordings INT;
  v_deleted_segments INT;
BEGIN
  -- Count segments to be deleted (if needed for logging)
  SELECT COUNT(*) INTO v_deleted_segments
  FROM segments
  WHERE recording_id IN (
    SELECT id FROM recordings
    WHERE created_at < now() - (in_retention_days || ' days')::INTERVAL
      AND status = 'done'
    LIMIT in_batch_size
  );

  -- Delete recordings (cascade will delete segments automatically)
  WITH deleted_recs AS (
    DELETE FROM recordings
    WHERE created_at < now() - (in_retention_days || ' days')::INTERVAL
      AND status = 'done'
    LIMIT in_batch_size
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_deleted_recordings FROM deleted_recs;

  RETURN QUERY SELECT v_deleted_recordings, v_deleted_segments;
END;
$$;