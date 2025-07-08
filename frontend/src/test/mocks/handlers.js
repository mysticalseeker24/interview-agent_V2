import { rest } from 'msw';

const BASE_URLS = {
  USER: 'http://localhost:8001',
  MEDIA: 'http://localhost:8002',
  RESUME: 'http://localhost:8003',
  INTERVIEW: 'http://localhost:8004',
  TRANSCRIPTION: 'http://localhost:8005'
};

export const handlers = [
  // User Service handlers
  rest.post(`${BASE_URLS.USER}/auth/login`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          role: 'candidate',
          created_at: '2024-01-01T00:00:00.000Z'
        }
      })
    );
  }),

  rest.post(`${BASE_URLS.USER}/auth/signup`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        message: 'User registered successfully',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          role: 'candidate',
          created_at: '2024-01-01T00:00:00.000Z'
        }
      })
    );
  }),

  rest.get(`${BASE_URLS.USER}/auth/me`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'candidate',
        created_at: '2024-01-01T00:00:00.000Z'
      })
    );
  }),

  // Media Service handlers
  rest.get(`${BASE_URLS.MEDIA}/api/devices`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        cameras: [
          { deviceId: 'camera1', label: 'Default Camera' },
          { deviceId: 'camera2', label: 'USB Camera' }
        ],
        microphones: [
          { deviceId: 'mic1', label: 'Default Microphone' },
          { deviceId: 'mic2', label: 'USB Microphone' }
        ]
      })
    );
  }),

  rest.post(`${BASE_URLS.MEDIA}/api/permissions/request`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ granted: true, permissions: ['camera', 'microphone'] })
    );
  }),

  // Interview Service handlers
  rest.get(`${BASE_URLS.INTERVIEW}/api/modules`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, title: 'JavaScript Fundamentals', description: 'Test your JavaScript knowledge', category: 'Software', difficulty: 'Medium', duration: '30m' },
        { id: 2, title: 'React Development', description: 'Frontend React interview questions', category: 'Software', difficulty: 'Difficult', duration: '45m' },
        { id: 3, title: 'Data Science Basics', description: 'Introduction to data science concepts', category: 'Data Science', difficulty: 'Easy', duration: '25m' }
      ])
    );
  }),

  rest.post(`${BASE_URLS.INTERVIEW}/api/sessions`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({ session_id: 'mock-session-123', module_id: 1, status: 'pending' })
    );
  }),

  rest.get(`${BASE_URLS.INTERVIEW}/api/sessions/:sessionId`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ session_id: 'mock-session-123', module_id: 1, status: 'active', questions: [{ id: 1, text: 'What is the difference between let and var in JavaScript?', type: 'technical' }] })
    );
  }),

  // Resume Service handlers
  rest.post(`${BASE_URLS.RESUME}/api/resumes/upload`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({ message: 'Resume uploaded successfully', resume_id: 'mock-resume-123', filename: 'test-resume.pdf' })
    );
  }),

  // Default fallback for unhandled requests
  rest.all('*', (req, res, ctx) => {
    console.warn(`Unhandled ${req.method} request to ${req.url.href}`);
    return res(ctx.status(404));
  })
];
