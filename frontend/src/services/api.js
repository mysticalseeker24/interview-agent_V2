import axios from 'axios';

// Service URLs from environment - all going through nginx proxy
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80';
const USER_SERVICE_URL = `${API_BASE_URL}/api`;
const INTERVIEW_SERVICE_URL = `${API_BASE_URL}/api`;
const RESUME_SERVICE_URL = `${API_BASE_URL}/api`;
const TRANSCRIPTION_SERVICE_URL = `${API_BASE_URL}/api`;
const MEDIA_SERVICE_URL = `${API_BASE_URL}/api`;

// Create axios instances for each service
const createApiInstance = (baseURL) => {
  // Configure axios instance
  const config = {
    baseURL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' }
  };
  const instance = axios.create(config);

  // Request interceptor to add auth token
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle auth errors
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Clear token and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

// Service instances
const userService = createApiInstance(USER_SERVICE_URL);
const interviewService = createApiInstance(INTERVIEW_SERVICE_URL);
const resumeService = createApiInstance(RESUME_SERVICE_URL);
const transcriptionService = createApiInstance(TRANSCRIPTION_SERVICE_URL);
const mediaService = createApiInstance(MEDIA_SERVICE_URL);

// Main API instance (user service)
export const api = userService;

// Auth API calls (User Service)
export const authAPI = {
  login: (credentials) => userService.post('/auth/login', credentials),
  signup: (userData) => userService.post('/auth/signup', userData),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }
};

// User API calls (User Service)
export const userAPI = {
  getProfile: () => userService.get('/users/me'),
  updateProfile: (data) => userService.put('/users/me', data)
};

// Module API calls (Interview Service)
export const moduleAPI = {
  getModules: (params) => interviewService.get('/modules', { params }),
  getModule: (id) => interviewService.get(`/modules/${id}`)
};

// Session API calls (Interview Service)
export const sessionAPI = {
  createSession: (data) => interviewService.post('/sessions', data),
  getSession: (id) => interviewService.get(`/sessions/${id}`),
  getSessionReport: (id) => interviewService.get(`/sessions/${id}/report`),
  getSessions: () => interviewService.get('/profile/sessions')
};

// Media API calls (Media Service)
export const mediaAPI = {
  getDevices: () => mediaService.get('/media/devices'),
  uploadChunk: (formData) => mediaService.post('/media/chunk-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
};

// Transcription API calls (Transcription Service)
export const transcriptionAPI = {
  transcribeChunk: (chunkId) => transcriptionService.post(`/transcribe/chunk/${chunkId}`)
};

// Follow-up API calls (Interview Service)
export const followupAPI = {
  getFollowup: (data) => interviewService.post('/followup', data)
};

// TTS API calls (Transcription Service)
export const ttsAPI = {
  generateTTS: (text) => transcriptionService.post('/tts/generate', { text })
};

// Resume API calls (Resume Service)
export const resumeAPI = {
  parseResume: (formData) => resumeService.post('/resume/parse', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
};

export default api;
