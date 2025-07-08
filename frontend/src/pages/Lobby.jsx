import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mediaAPI, resumeAPI } from '../services/api';
import {
  container,
  card,
  primaryButton,
  secondaryButton,
  input,
  formGroup,
  label,
  flexBetween,
  pageTitle,
  pageSubtitle,
  errorText,
  successText,
  loading
} from '../styles';

const Lobby = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  
  const [devices, setDevices] = useState({
    cameras: [],
    microphones: []
  });
  const [selectedDevices, setSelectedDevices] = useState({
    camera: '',
    microphone: ''
  });
  const [permissions, setPermissions] = useState({
    camera: false,
    microphone: false
  });
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchDevices();
    checkExistingPermissions();
    
    return () => {
      // Cleanup stream on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await mediaAPI.getDevices();
      setDevices(response.data);
      
      // Set default devices
      if (response.data.cameras.length > 0) {
        setSelectedDevices(prev => ({
          ...prev,
          camera: response.data.cameras[0].deviceId
        }));
      }
      if (response.data.microphones.length > 0) {
        setSelectedDevices(prev => ({
          ...prev,
          microphone: response.data.microphones[0].deviceId
        }));
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
      setError('Failed to load media devices');
    }
  };

  const checkExistingPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      setPermissions({
        camera: true,
        microphone: true
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
    } catch (error) {
      console.log('Permissions not granted yet');
    }
  };

  const requestPermissions = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const constraints = {
        video: selectedDevices.camera ? { deviceId: selectedDevices.camera } : true,
        audio: selectedDevices.microphone ? { deviceId: selectedDevices.microphone } : true
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      setPermissions({
        camera: true,
        microphone: true
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
      setSuccess('Camera and microphone access granted!');
    } catch (error) {
      console.error('Error requesting permissions:', error);
      setError('Failed to access camera and microphone. Please check your permissions.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeviceChange = (type, deviceId) => {
    setSelectedDevices(prev => ({
      ...prev,
      [type]: deviceId
    }));
    
    // If permissions are already granted, update the stream
    if (permissions.camera && permissions.microphone) {
      requestPermissions();
    }
  };

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      setError('File size must be less than 5MB');
      return;
    }
    
    setResumeFile(file);
    
    try {
      setIsLoading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      
      await resumeAPI.parseResume(formData);
      setResumeUploaded(true);
      setSuccess('Resume uploaded and parsed successfully!');
    } catch (error) {
      console.error('Error uploading resume:', error);
      setError('Failed to upload resume. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const startInterview = () => {
    if (!permissions.camera || !permissions.microphone) {
      setError('Please grant camera and microphone permissions before starting');
      return;
    }
    
    navigate(`/sessions/${sessionId}/interview`);
  };

  const goBack = () => {
    navigate('/');
  };

  return (
    <div style={container}>
      <div style={{ marginTop: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={pageTitle}>Interview Setup</h1>
          <p style={pageSubtitle}>
            Prepare your environment before starting the interview
          </p>
        </div>

        {error && (
          <div style={{
            ...errorText,
            padding: '1rem',
            backgroundColor: '#fee2e2',
            borderRadius: '8px',
            marginBottom: '2rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{
            ...successText,
            padding: '1rem',
            backgroundColor: '#dcfce7',
            borderRadius: '8px',
            marginBottom: '2rem',
            textAlign: 'center'
          }}>
            {success}
          </div>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '2rem',
          '@media (max-width: 768px)': {
            gridTemplateColumns: '1fr'
          }
        }}>
          {/* Camera Preview */}
          <div style={card}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              marginBottom: '1rem'
            }}>
              Camera Preview
            </h3>
            
            <div style={{
              backgroundColor: '#f3f4f6',
              borderRadius: '8px',
              aspectRatio: '16/9',
              marginBottom: '1rem',
              overflow: 'hidden',
              position: 'relative'
            }}>
              {permissions.camera ? (
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover'
                  }}
                />
              ) : (
                <div style={{
                  ...loading,
                  height: '100%',
                  color: '#6b7280'
                }}>
                  Camera preview will appear here
                </div>
              )}
            </div>

            <div style={formGroup}>
              <label style={label}>Camera</label>
              <select
                style={input}
                value={selectedDevices.camera}
                onChange={(e) => handleDeviceChange('camera', e.target.value)}
              >
                {devices.cameras.map(camera => (
                  <option key={camera.deviceId} value={camera.deviceId}>
                    {camera.label || `Camera ${camera.deviceId.slice(0, 8)}`}
                  </option>
                ))}
              </select>
            </div>

            <div style={formGroup}>
              <label style={label}>Microphone</label>
              <select
                style={input}
                value={selectedDevices.microphone}
                onChange={(e) => handleDeviceChange('microphone', e.target.value)}
              >
                {devices.microphones.map(mic => (
                  <option key={mic.deviceId} value={mic.deviceId}>
                    {mic.label || `Microphone ${mic.deviceId.slice(0, 8)}`}
                  </option>
                ))}
              </select>
            </div>

            {!permissions.camera || !permissions.microphone ? (
              <button
                onClick={requestPermissions}
                disabled={isLoading}
                style={{
                  ...primaryButton,
                  width: '100%',
                  opacity: isLoading ? 0.7 : 1
                }}
              >
                {isLoading ? 'Requesting Access...' : 'Grant Camera & Microphone Access'}
              </button>
            ) : (
              <div style={{
                ...successText,
                textAlign: 'center',
                padding: '0.75rem',
                backgroundColor: '#dcfce7',
                borderRadius: '6px'
              }}>
                ✓ Camera and microphone ready
              </div>
            )}
          </div>

          {/* Setup Controls */}
          <div style={card}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              marginBottom: '1rem'
            }}>
              Interview Preparation
            </h3>

            {/* Resume Upload */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={label}>Resume Upload (Optional)</label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleResumeUpload}
                style={{
                  ...input,
                  padding: '0.5rem'
                }}
                disabled={isLoading}
              />
              <p style={{
                fontSize: '12px',
                color: '#6b7280',
                marginTop: '0.25rem'
              }}>
                Upload your resume for personalized questions (PDF only, max 5MB)
              </p>
              {resumeUploaded && (
                <div style={{
                  ...successText,
                  marginTop: '0.5rem'
                }}>
                  ✓ Resume uploaded successfully
                </div>
              )}
            </div>

            {/* Checklist */}
            <div style={{ marginBottom: '2rem' }}>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '500',
                marginBottom: '1rem'
              }}>
                Pre-Interview Checklist
              </h4>
              <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                  color: permissions.camera ? '#059669' : '#6b7280'
                }}>
                  <span style={{ marginRight: '0.5rem' }}>
                    {permissions.camera ? '✓' : '○'}
                  </span>
                  Camera access granted
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                  color: permissions.microphone ? '#059669' : '#6b7280'
                }}>
                  <span style={{ marginRight: '0.5rem' }}>
                    {permissions.microphone ? '✓' : '○'}
                  </span>
                  Microphone access granted
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                  color: '#6b7280'
                }}>
                  <span style={{ marginRight: '0.5rem' }}>○</span>
                  Find a quiet, well-lit space
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                  color: '#6b7280'
                }}>
                  <span style={{ marginRight: '0.5rem' }}>○</span>
                  Ensure stable internet connection
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{
              display: 'flex',
              gap: '1rem'
            }}>
              <button
                onClick={goBack}
                style={{
                  ...secondaryButton,
                  flex: 1
                }}
              >
                Back to Dashboard
              </button>
              <button
                onClick={startInterview}
                disabled={!permissions.camera || !permissions.microphone || isLoading}
                style={{
                  ...primaryButton,
                  flex: 1,
                  opacity: (!permissions.camera || !permissions.microphone || isLoading) ? 0.5 : 1,
                  cursor: (!permissions.camera || !permissions.microphone || isLoading) ? 'not-allowed' : 'pointer'
                }}
              >
                Start Interview
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Lobby;
