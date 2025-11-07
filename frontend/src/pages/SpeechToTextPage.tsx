import React, { useRef, useState, useEffect } from 'react';
import { Button, Text, Box, Paper, Title } from '@mantine/core';
import { useAuth } from '@/providers/AuthProvider';

interface TranscriptionItem {
  start_time: number;
  end_time: number;
  text: string;
}

const CLOSE_SIGNAL = "CLOSE";

export const SpeechToTextPage: React.FC = () => {
  const { accessToken } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [cumulativeText, setCumulativeText] = useState('');
  const [error, setError] = useState('');
  const websocketRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<AudioWorkletNode | null>(null);

  const [targetLanguage, setTargetLanguage] = useState<string>('vi');

  const addTranscription = (text: string) => {
    setCumulativeText(prev => prev + text);
  };

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const startRecording = async () => {
    try {
      setIsRecording(true);
      setCumulativeText('');

      // Get user media stream
      mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });

      // Load the AudioWorklet module
      await audioContextRef.current.audioWorklet.addModule('/audio-worklet-processor.js');

      // Create source and worklet node
      const source = audioContextRef.current.createMediaStreamSource(mediaStreamRef.current);
      const workletNode = new AudioWorkletNode(audioContextRef.current, 'audio-worklet-processor');

      // Handle messages from the worklet
      workletNode.port.onmessage = (event) => {
        const audioData = event.data; // Float32Array
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          websocketRef.current.send(audioData.buffer);
        }
      };

      // Open WebSocket connection
      websocketRef.current = new WebSocket(`ws://localhost:8001/ws/s2t?token=${accessToken}`);

      websocketRef.current.onopen = () => {
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({
            target_language: targetLanguage,
          }));
        }
        console.log('WebSocket connection opened.');
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as TranscriptionItem;
          addTranscription(message.text);
        } catch (error) {
          console.error('Error parsing JSON:', error);
        }
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      websocketRef.current.onclose = () => {
        console.log('WebSocket connection closed.');
        stopRecording();
      };

      // Connect nodes
      source.connect(workletNode);
      workletNode.connect(audioContextRef.current.destination);

      // Store reference to workletNode for cleanup
      processorRef.current = workletNode;

      setError('');
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Failed to access microphone');
      stopRecording();
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(CLOSE_SIGNAL);
      websocketRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
  };

  return (
    <Box style={{ maxWidth: 600, margin: '0 auto', padding: '2rem' }}>
      <Title order={2} mb="md">Speech to Text</Title>
      <Paper shadow="sm" p="md" mb="md">
        <Text size="sm" c="dimmed" mb="sm">
          Select language and click "Start Recording" to begin transcribing your audio in real-time.
        </Text>
        <select
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
          style={{ marginBottom: '1rem', padding: '0.5rem' }}
        >
          <option value="vi">Vietnamese</option>
          <option value="en">English</option>
          <option value="ja">Japanese</option>
          <option value="ko">Korean</option>
          <option value="zh">Chinese</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="es">Spanish</option>
          <option value="ru">Russian</option>
          <option value="it">Italian</option>
          <option value="pt">Portuguese</option>
          <option value="nl">Dutch</option>
          <option value="ar">Arabic</option>
          <option value="tr">Turkish</option>
          <option value="th">Thai</option>
          <option value="id">Indonesian</option>
          <option value="hi">Hindi</option>
          <option value="ms">Malay</option>
          <option value="bn">Bengali</option>
          <option value="fil">Filipino</option>
          <option value="ur">Urdu</option>
        </select>
        <Button
          onClick={isRecording ? stopRecording : startRecording}
          color={isRecording ? 'red' : 'blue'}
          size="lg"
          fullWidth
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </Button>
        {error && (
          <Text c="red" mt="sm">
            {error}
          </Text>
        )}
      </Paper>
      <Paper shadow="sm" p="md">
        <Title order={4} mb="sm">Transcription:</Title>
        <Text style={{ whiteSpace: 'pre-wrap' }}>
          {cumulativeText || 'No transcription yet...'}
        </Text>
      </Paper>
    </Box>
  );
};
