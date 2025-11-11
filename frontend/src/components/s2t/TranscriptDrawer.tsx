import { useEffect, useRef, useState } from "react";
import {
    Drawer,
    Stack,
    Box,
    Group,
    ActionIcon,
    Paper,
    ScrollArea,
    Badge,
    Center,
    Loader,
    Slider,
} from "@mantine/core";
import { IconPlayerPlay, IconPlayerPause, IconVolume, IconVolumeOff, IconPlayerSkipBack, IconPlayerSkipForward, IconPlayerTrackPrev, IconPlayerTrackNext, IconReload } from "@tabler/icons-react";
import { Howl } from 'howler';
import type { RecordingDetail } from "@/api/record.ts";
import { cn } from "@/lib/utils.ts";

interface TranscriptDrawerProps {
  opened: boolean;
  onClose: () => void;
  recording: RecordingDetail | null;
}

export function TranscriptDrawer({
  opened,
  onClose,
  recording,
}: TranscriptDrawerProps) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const activeWordRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const soundRef = useRef<Howl | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize Howler when recording changes
  useEffect(() => {
    // Cleanup previous sound
    if (soundRef.current) {
      soundRef.current.unload();
      soundRef.current = null;
    }

    if (!recording?.audio_url) return;

    setIsLoading(true);

    soundRef.current = new Howl({
      src: [recording.audio_url],
      html5: true,
      volume: volume,
      onload: () => {
        setIsLoading(false);
      },
      onloaderror: (_id, error) => {
        console.error('Audio load error:', error);
        setIsLoading(false);
      },
      onplay: () => {
        setIsPlaying(true);
        updateProgress();
      },
      onpause: () => {
        setIsPlaying(false);
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      },
      onend: () => {
        setIsPlaying(false);
        setCurrentTime(0);
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      },
    });

    return () => {
      if (soundRef.current) {
        soundRef.current.unload();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [recording?.audio_url]);

  // Update progress continuously while playing
  const updateProgress = () => {
    if (soundRef.current && soundRef.current.playing()) {
      const seek = soundRef.current.seek();
      setCurrentTime(seek * 1000); // Convert to ms
      animationFrameRef.current = requestAnimationFrame(updateProgress);
    }
  };

  // Update volume
  useEffect(() => {
    if (soundRef.current) {
      soundRef.current.volume(isMuted ? 0 : volume);
    }
  }, [volume, isMuted]);

  // Auto-scroll to active segment
  useEffect(() => {
    if (activeWordRef.current && scrollAreaRef.current) {
      activeWordRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [currentTime]);

  const togglePlayback = () => {
    if (!soundRef.current) return;

    if (isPlaying) {
      soundRef.current.pause();
    } else {
      soundRef.current.play();
    }
  };

  const handleWordClick = (startMs: number) => {
    if (!soundRef.current) return;

    soundRef.current.seek(startMs / 1000); // Convert to seconds
    setCurrentTime(startMs);

    if (!isPlaying) {
      soundRef.current.play();
    }
  };

  const handleSeek = (value: number) => {
    if (!soundRef.current || !recording) return;

    const seekTime = (value / 100) * recording.duration_ms;
    soundRef.current.seek(seekTime / 1000); // Convert to seconds
    setCurrentTime(seekTime);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const skipBackward = () => {
    if (!soundRef.current || !recording) return;
    const newTime = Math.max(0, currentTime - 10000); // Skip 10 seconds back
    soundRef.current.seek(newTime / 1000);
    setCurrentTime(newTime);
  };

  const skipForward = () => {
    if (!soundRef.current || !recording) return;
    const newTime = Math.min(recording.duration_ms, currentTime + 10000); // Skip 10 seconds forward
    soundRef.current.seek(newTime / 1000);
    setCurrentTime(newTime);
  };

  const previousSegment = () => {
    if (!soundRef.current || !recording) return;

    // Find previous segment
    const currentSegmentIndex = recording.segments.findIndex(
      seg => currentTime >= seg.start_ms && currentTime <= seg.end_ms
    );

    if (currentSegmentIndex > 0) {
      const prevSegment = recording.segments[currentSegmentIndex - 1];
      soundRef.current.seek(prevSegment.start_ms / 1000);
      setCurrentTime(prevSegment.start_ms);
    } else if (currentSegmentIndex === -1 && recording.segments.length > 0) {
      // If not in any segment, go to last segment before current time
      const prevSegments = recording.segments.filter(seg => seg.end_ms < currentTime);
      if (prevSegments.length > 0) {
        const prevSegment = prevSegments[prevSegments.length - 1];
        soundRef.current.seek(prevSegment.start_ms / 1000);
        setCurrentTime(prevSegment.start_ms);
      }
    }
  };

  const nextSegment = () => {
    if (!soundRef.current || !recording) return;

    // Find next segment
    const nextSeg = recording.segments.find(seg => seg.start_ms > currentTime);

    if (nextSeg) {
      soundRef.current.seek(nextSeg.start_ms / 1000);
      setCurrentTime(nextSeg.start_ms);
    }
  };

  const resetPlayback = () => {
    if (!soundRef.current) return;
    soundRef.current.seek(0);
    setCurrentTime(0);
    if (isPlaying) {
      soundRef.current.pause();
    }
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  };

  if (!recording) {
    return (
      <Drawer
        opened={opened}
        onClose={onClose}
        position="right"
        size="xl"
        title="Transcript"
      >
        <Center h="100%">
          <Loader />
        </Center>
      </Drawer>
    );
  }

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      size="xl"
      title={
        <Group gap="sm">
          <span className="font-semibold text-lg">Transcript</span>
          <Badge
            color={recording.status === "COMPLETED" ? "green" : "blue"}
            variant="light"
          >
            {recording.status}
          </Badge>
        </Group>
      }
      styles={{
        body: {
          height: "calc(100% - 60px)",
          display: "flex",
          flexDirection: "column",
          padding: 0,
        },
        header: {
          // borderBottom: '1px solid var(--mantine-color-gray-3)',
        },
      }}
    >
      <Stack gap={0} h="100%" style={{ flex: 1 }}>
        {/* Lyrics/Transcript Display */}
        <ScrollArea
          style={{ flex: 1 }}
          type="auto"
          offsetScrollbars
          viewportRef={scrollAreaRef}
        >
          <Box p="xl">
            {recording.segments.length === 0 ? (
              <Center h={200}>
                <span className="text-gray-500">No transcript available</span>
              </Center>
            ) : (
              <Stack gap="lg">
                {recording.segments.map((segment) => {
                  const isSegmentActive =
                    currentTime >= segment.start_ms &&
                    currentTime <= segment.end_ms;
                  const isSegmentPassed = currentTime > segment.end_ms;

                  return (
                    <Box
                      key={segment.id}
                      ref={isSegmentActive ? activeWordRef : null}
                      className={cn(
                        "p-4 py-0 rounded-xl transition-all duration-300"
                        // isSegmentActive
                        //   ? 'bg-blue-50 border-blue-200'
                        //   : 'bg-transparent border-transparent'
                      )}
                    >
                      {/* Timestamp */}
                      <span className="text-xs text-gray-200 font-medium mb-2 block font-mono tracking-wide">
                        {formatTime(segment.start_ms)} -{" "}
                        {formatTime(segment.end_ms)}
                      </span>

                      {/* Segment text with word highlighting */}
                      <div className="text-lg leading-relaxed">
                        {segment.words.length > 0 ? (
                          segment.words.map((word, wordIndex) => {
                            const isWordActive =
                              currentTime >= word.start_ms &&
                              currentTime <= word.end_ms;
                            // const isWordPassed = currentTime > word.end_ms;

                            return (
                              <span
                                key={`${word.id}-${wordIndex}`}
                                onClick={() => handleWordClick(word.start_ms)}
                                className={cn(
                                  "cursor-pointer px-0.5 mx-0.5 rounded-md inline-block transition-all duration-200",
                                  isWordActive && "text-blue-500 ",
                                  // !isWordActive && isWordPassed && 'font-semibold text-gray-900',
                                  // !isWordActive && !isWordPassed && 'font-medium text-gray-500',
                                  "hover:text-blue-500 "
                                )}
                              >
                                {word.text}
                              </span>
                            );
                          })
                        ) : (
                          // Fallback if no words available, show segment text
                          <span
                            onClick={() => handleWordClick(segment.start_ms)}
                            className={cn(
                              "cursor-pointer",
                              isSegmentActive && "text-blue-800 font-semibold",
                              !isSegmentActive &&
                                isSegmentPassed &&
                                "text-gray-900 font-medium",
                              !isSegmentActive &&
                                !isSegmentPassed &&
                                "text-gray-500 font-medium"
                            )}
                          >
                            {segment.text}
                          </span>
                        )}
                      </div>
                    </Box>
                  );
                })}
              </Stack>
            )}
          </Box>
        </ScrollArea>

         {/* Enhanced Player Controls */}
        <Paper
          p="md"
          pb="lg"
          radius={0}
          style={{
            borderTop: "1px solid var(--mantine-color-default-border)",
            backgroundColor: "var(--mantine-color-body)",
          }}
        >
          <Stack gap="md">

            {/* Time and Volume Row */}
            <Group justify="space-between" wrap="nowrap">
              {/* Time Display */}
              <Box>
                <span className="text-sm text-gray-600 font-mono tabular-nums">
                  {formatTime(currentTime)} / {formatTime(recording.duration_ms)}
                </span>
              </Box>

              {/* Volume Control */}
              <Group gap="xs">
                <ActionIcon
                  size="md"
                  variant="subtle"
                  color="gray"
                  onClick={toggleMute}
                  disabled={!recording.audio_url}
                  aria-label={isMuted ? "Unmute" : "Mute"}
                  title={isMuted ? "Unmute" : "Mute"}
                >
                  {isMuted ? <IconVolumeOff size={18} /> : <IconVolume size={18} />}
                </ActionIcon>
                <Box w={80}>
                  <Slider
                    value={isMuted ? 0 : Math.floor(volume * 100)}
                    onChange={(val) => setVolume(val / 100)}
                    min={0}
                    max={100}
                    size="xs"
                    color="blue"
                    disabled={!recording.audio_url || isMuted}
                  />
                </Box>
              </Group>
            </Group>

            {/* Seekable Progress Bar */}
            <Box>
              <Slider
                value={Math.floor((currentTime / recording.duration_ms) * 100)}
                onChange={handleSeek}
                min={0}
                max={100}
                step={0.1}
                size="sm"
                color="blue"
                disabled={!recording.audio_url}
                styles={{
                  bar: {
                    transition: isPlaying ? 'none' : 'width 0.3s ease',
                  },
                }}
              />
            </Box>

            {/* Main Controls Row */}
            <Group justify="center" gap="xs" mt={"md"}>
              {/* Reset */}
              <ActionIcon
                size="md"
                radius="xl"
                variant="subtle"
                color="gray"
                onClick={resetPlayback}
                disabled={!recording.audio_url || isLoading}
                aria-label="Reset"
                title="Reset to start"
              >
                <IconReload size={18} />
              </ActionIcon>

              {/* Previous Segment */}
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="blue"
                onClick={previousSegment}
                disabled={!recording.audio_url || isLoading}
                aria-label="Previous segment"
                title="Previous segment"
              >
                <IconPlayerTrackPrev size={20} />
              </ActionIcon>

              {/* Skip Backward 10s */}
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="blue"
                onClick={skipBackward}
                disabled={!recording.audio_url || isLoading}
                aria-label="Skip backward 10s"
                title="Skip backward 10s"
              >
                <IconPlayerSkipBack size={20} />
              </ActionIcon>

              {/* Play/Pause - Main Button */}
              <ActionIcon
                size="xl"
                radius="xl"
                variant="filled"
                color="blue"
                onClick={togglePlayback}
                disabled={!recording.audio_url || isLoading}
                loading={isLoading}
                aria-label={isPlaying ? "Pause" : "Play"}
                title={isPlaying ? "Pause" : "Play"}
              >
                {isPlaying ? (
                  <IconPlayerPause size={24} />
                ) : (
                  <IconPlayerPlay size={24} />
                )}
              </ActionIcon>

              {/* Skip Forward 10s */}
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="blue"
                onClick={skipForward}
                disabled={!recording.audio_url || isLoading}
                aria-label="Skip forward 10s"
                title="Skip forward 10s"
              >
                <IconPlayerSkipForward size={20} />
              </ActionIcon>

              {/* Next Segment */}
              <ActionIcon
                size="lg"
                radius="xl"
                variant="light"
                color="blue"
                onClick={nextSegment}
                disabled={!recording.audio_url || isLoading}
                aria-label="Next segment"
                title="Next segment"
              >
                <IconPlayerTrackNext size={20} />
              </ActionIcon>
            </Group>


            {/* Info Row */}
            <Group justify="space-between" wrap="wrap" gap="xs">
              <span className="text-xs text-gray-500">
                {recording.segments.reduce((sum, seg) => sum + seg.words.length, 0)} words • {recording.segments.length} segments
              </span>
              <span className="text-xs text-gray-500">
                Language: {recording.language.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">
                {recording.source === 'upload' ? '📁 Upload' : '🎤 Realtime'}
              </span>
              <span className="text-xs text-gray-500">
                {new Date(recording.created_at).toLocaleDateString()}
              </span>
            </Group>

            {/* Audio Not Available Warning */}
            {!recording.audio_url && (
              <Box className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-md">
                ⚠️ Audio file not available for playback
              </Box>
            )}
          </Stack>
        </Paper>
      </Stack>
    </Drawer>
  );
}
