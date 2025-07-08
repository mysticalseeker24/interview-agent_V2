import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mediaAPI, transcriptionAPI, followupAPI, ttsAPI } from '../services/api';
import {
  container,
  card,
  primaryButton,
  secondaryButton,
  flexBetween,
  flexCenter,
  pageTitle,
  errorText,
  loading
} from '../styles';

const InterviewRoom = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioRef = useRef(null);
  
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [sequenceIndex, setSequenceIndex] = useState(0);
  const [timer, setTimer] = useState(0);
  const [error, setError] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [interviewComplete, setInterviewComplete] = useState(false);

  // Recording configuration
  const CHUNK_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
  const OVERLAP_DURATION = 5 * 1000; // 5 seconds overlap

  useEffect(() => {
    initializeInterview();
    
    return () => {
      cleanup();
    };
  }, []);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const initializeInterview = async () => {
    try {
      // Get media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false
      });
      streamRef.current = stream;

      // Set initial question
      setCurrentQuestion("Hello! Welcome to your interview. Please introduce yourself and tell me about your background.");
      
      // Play TTS for initial question
      await playTTS("Hello! Welcome to your interview. Please introduce yourself and tell me about your background.");
      
      // Start recording
      startRecording();
    } catch (error) {
      console.error('Error initializing interview:', error);
      setError('Failed to initialize interview. Please check your microphone permissions.');
    }
  };

  const startRecording = () => {
    if (!streamRef.current) return;

    try {
      const mediaRecorder = new MediaRecorder(streamRef.current, {
        mimeType: 'audio/webm'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          await handleChunkUpload(event.data);
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Recording error occurred');
      };

      // Start recording with chunk intervals
      mediaRecorder.start();
      setIsRecording(true);
      
      // Set up chunk recording intervals
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.requestData();
          scheduleNextChunk();
        }
      }, CHUNK_DURATION);

    } catch (error) {
      console.error('Error starting recording:', error);
      setError('Failed to start recording');
    }
  };

  const scheduleNextChunk = () => {
    if (!interviewComplete) {
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.requestData();
          scheduleNextChunk();
        }
      }, CHUNK_DURATION - OVERLAP_DURATION);
    }
  };

  const handleChunkUpload = async (audioBlob) => {
    try {
      setIsProcessing(true);
      
      // Upload chunk
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('sequence_index', sequenceIndex.toString());
      formData.append('file', audioBlob, `chunk_${sequenceIndex}.webm`);
      
      const uploadResponse = await mediaAPI.uploadChunk(formData);
      const chunkId = uploadResponse.data.chunk_id;
      
      // Transcribe chunk
      const transcriptionResponse = await transcriptionAPI.transcribeChunk(chunkId);
      const transcript = transcriptionResponse.data.transcript;
      
      if (transcript && transcript.trim()) {
        // Get follow-up question
        const followupResponse = await followupAPI.getFollowup({
          session_id: sessionId,
          answer_text: transcript
        });
        
        const nextQuestion = followupResponse.data.follow_up_question;
        
        if (nextQuestion) {
          setCurrentQuestion(nextQuestion);
          await playTTS(nextQuestion);
        } else {
          // Interview complete
          completeInterview();
        }
      }
      
      setSequenceIndex(prev => prev + 1);
    } catch (error) {
      console.error('Error processing chunk:', error);
      setError('Error processing audio. Interview will continue.');
    } finally {
      setIsProcessing(false);
    }
  };

  const playTTS = async (text) => {
    try {
      const response = await ttsAPI.generateTTS(text);
      const audioUrl = response.data.audio_url;
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
      }
    } catch (error) {
      console.error('Error playing TTS:', error);
      // Continue without TTS if it fails
    }
  };

  const completeInterview = () => {
    setInterviewComplete(true);
    stopRecording();
    
    // Navigate to report after a short delay
    setTimeout(() => {
      navigate(`/sessions/${sessionId}/report`);
    }, 2000);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const cleanup = () => {
    stopRecording();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  const endInterview = () => {
    if (window.confirm('Are you sure you want to end the interview? Your progress will be saved.')) {
      completeInterview();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (interviewComplete) {
    return (
      <div style={{
        ...flexCenter,
        minHeight: '100vh',
        flexDirection: 'column',
        textAlign: 'center'
      }}>
        <div style={card}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            marginBottom: '1rem',
            color: '#059669'
          }}>
            Interview Complete!
          </h2>
          <p style={{
            color: '#6b7280',
            marginBottom: '1rem'
          }}>
            Thank you for completing the interview. Generating your report...
          </p>
          <div style={loading}>
            <div className="spin" style={{
              width: '24px',
              height: '24px',
              border: '2px solid #e5e7eb',
              borderTop: '2px solid #2563eb',
              borderRadius: '50%'
            }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#1f2937',
      color: '#ffffff',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <header style={{
        padding: '1rem 2rem',
        borderBottom: '1px solid #374151',
        ...flexBetween
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: isRecording ? '#ef4444' : '#6b7280'
          }}></div>
          <span style={{ fontSize: '14px', fontWeight: '500' }}>
            {isRecording ? 'Recording' : 'Paused'}
          </span>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '2rem'
        }}>
          <div style={{ fontSize: '18px', fontWeight: '600' }}>
            {formatTime(timer)}
          </div>
          <div style={{ fontSize: '14px', color: '#9ca3af' }}>
            Sequence: {sequenceIndex + 1}
          </div>
        </div>

        <button
          onClick={endInterview}
          style={{
            ...secondaryButton,
            backgroundColor: '#ef4444',
            color: '#ffffff',
            border: 'none'
          }}
        >
          End Interview
        </button>
      </header>

      {/* Main Content */}
      <main style={{
        flex: 1,
        ...flexCenter,
        padding: '2rem'
      }}>
        <div style={{
          maxWidth: '800px',
          width: '100%',
          textAlign: 'center'
        }}>
          {error && (
            <div style={{
              ...errorText,
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '2rem'
            }}>
              {error}
            </div>
          )}

          {/* Current Question */}
          <div style={{
            backgroundColor: '#374151',
            borderRadius: '12px',
            padding: '2rem',
            marginBottom: '2rem'
          }}>
            <h2 style={{
              fontSize: '20px',
              fontWeight: '600',
              marginBottom: '1rem',
              color: '#f9fafb'
            }}>
              Current Question
            </h2>
            <p style={{
              fontSize: '18px',
              lineHeight: '1.6',
              color: '#e5e7eb'
            }}>
              {currentQuestion}
            </p>
          </div>

          {/* Status Indicators */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <div style={{
              backgroundColor: '#374151',
              borderRadius: '8px',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{
                fontSize: '24px',
                fontWeight: '700',
                color: isRecording ? '#10b981' : '#6b7280',
                marginBottom: '0.5rem'
              }}>
                {isRecording ? '●' : '○'}
              </div>
              <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                Audio Recording
              </div>
            </div>

            <div style={{
              backgroundColor: '#374151',
              borderRadius: '8px',
              padding: '1rem',
              textAlign: 'center'
            }}>
              <div style={{
                fontSize: '24px',
                fontWeight: '700',
                color: isProcessing ? '#f59e0b' : '#6b7280',
                marginBottom: '0.5rem'
              }}>
                {isProcessing ? '⟳' : '✓'}
              </div>
              <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                Processing
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div style={{
            backgroundColor: '#1e293b',
            borderRadius: '8px',
            padding: '1.5rem',
            border: '1px solid #334155'
          }}>
            <h3 style={{
              fontSize: '16px',
              fontWeight: '600',
              marginBottom: '1rem',
              color: '#f1f5f9'
            }}>
              Interview Tips
            </h3>
            <ul style={{
              textAlign: 'left',
              fontSize: '14px',
              color: '#cbd5e1',
              lineHeight: '1.6'
            }}>
              <li>Speak clearly and at a moderate pace</li>
              <li>Take your time to think before answering</li>
              <li>Provide specific examples when possible</li>
              <li>The interview will automatically progress based on your responses</li>
            </ul>
          </div>
        </div>
      </main>

      {/* Hidden audio element for TTS */}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
};

export default InterviewRoom;
