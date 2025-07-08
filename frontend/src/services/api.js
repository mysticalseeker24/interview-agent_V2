import axios from 'axios';

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
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
api.interceptors.response.use(
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

// Auth API calls
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  signup: (userData) => api.post('/auth/signup', userData),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }
};

// User API calls
export const userAPI = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
  getSessions: () => api.get('/profile/sessions')
};

// Module API calls
export const moduleAPI = {
  getModules: (params) => api.get('/modules', { params }),
  getModule: (id) => api.get(`/modules/${id}`)
};

// Session API calls
export const sessionAPI = {
  createSession: (data) => api.post('/sessions', data),
  getSession: (id) => api.get(`/sessions/${id}`),
  getSessionReport: (id) => api.get(`/sessions/${id}/report`)
};

// Media API calls
export const mediaAPI = {
  getDevices: () => api.get('/media/devices'),
  uploadChunk: (formData) => api.post('/media/chunk-upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
};

// Transcription API calls
export const transcriptionAPI = {
  transcribeChunk: (chunkId) => api.post(`/transcribe/chunk/${chunkId}`)
};

// Follow-up API calls
export const followupAPI = {
  getFollowup: (data) => api.post('/followup', data)
};

// TTS API calls
export const ttsAPI = {
  generateTTS: (text) => api.post('/tts/generate', { text })
};

// Resume API calls
export const resumeAPI = {
  parseResume: (formData) => api.post('/resume/parse', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
};

export default api;
