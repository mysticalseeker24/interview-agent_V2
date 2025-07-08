# TalentSync Frontend

This is the React-based frontend for the TalentSync AI-powered interview platform. The frontend interacts with multiple backend microservices through a central nginx proxy to provide a seamless interview experience.

## Features

- **User Authentication**: Login and signup functionality with JWT token-based authentication
- **Dashboard**: Browse and select interview modules by domain and difficulty
- **Lobby**: Resume upload and device testing before interviews
- **Interview Room**: Real-time audio recording, transcription, and dynamic question flow
- **Report**: Post-interview performance analytics and AI-generated feedback

## Architecture

The frontend connects to the following backend services:

- **User Service**: Authentication and profile management
- **Interview Service**: Modules, sessions, and question orchestration
- **Resume Service**: Resume parsing for personalized questions
- **Media Service**: Audio recording and storage
- **Transcription Service**: Speech-to-text and text-to-speech
- **Feedback Service**: Post-interview analytics and reports

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm or yarn

### Local Development

#### Option 1: Development with Docker Compose (Recommended)

1. Go to the root directory of the TalentSync project:
   ```
   cd ../
   ```

2. Start all services with Docker Compose:
   ```
   docker-compose up -d
   ```

3. The frontend will be available at http://localhost:3000

#### Option 2: Frontend-only Development

If you want to run just the frontend while connecting to the dockerized backend services:

1. Install dependencies:
   ```
   npm install
   ```

2. Create a `.env` file with the following variables:
   ```
   # Point to the nginx proxy for backend services
   VITE_API_BASE_URL=http://localhost
   VITE_USER_SERVICE_URL=http://localhost/api
   VITE_INTERVIEW_SERVICE_URL=http://localhost/api
   VITE_RESUME_SERVICE_URL=http://localhost/api
   VITE_TRANSCRIPTION_SERVICE_URL=http://localhost/api
   VITE_MEDIA_SERVICE_URL=http://localhost/api
   VITE_FEEDBACK_SERVICE_URL=http://localhost/api
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Access the application at http://localhost:5173

#### Option 3: Full-Stack Development

If you're working on both frontend and backend services:

1. Start backend services using Docker Compose from the root directory:
   ```
   docker-compose up -d nginx postgres redis pinecone-emulator user-service interview-service resume-service transcription-service media-service feedback-service
   ```

2. Install frontend dependencies:
   ```
   npm install
   ```

3. Create a `.env` file as described in Option 2.

4. Start the frontend development server:
   ```
   npm run dev
   ```

5. Access the frontend at http://localhost:5173 (development server) which will connect to the backend services through the nginx proxy at http://localhost

### Building for Production

1. Build the application:
   ```
   npm run build
   ```

2. The optimized build will be in the `dist` directory

## Docker Deployment

The frontend is containerized with Docker and integrated with the other services via Docker Compose.

### Building the Frontend Container Separately

```bash
# Build the Docker image
docker build -t talentsync-frontend .

# Run the container (connects to backend services via nginx)
docker run -p 3000:3000 \
  -e VITE_API_BASE_URL=http://nginx:80 \
  -e VITE_USER_SERVICE_URL=http://nginx:80/api \
  -e VITE_INTERVIEW_SERVICE_URL=http://nginx:80/api \
  -e VITE_RESUME_SERVICE_URL=http://nginx:80/api \
  -e VITE_TRANSCRIPTION_SERVICE_URL=http://nginx:80/api \
  -e VITE_MEDIA_SERVICE_URL=http://nginx:80/api \
  -e VITE_FEEDBACK_SERVICE_URL=http://nginx:80/api \
  --network talentsync-network \
  talentsync-frontend
```

### Using Docker Compose (Recommended)

The frontend is configured in the root `docker-compose.yml` file to work seamlessly with all backend services:

```bash
# From the root directory
docker-compose up -d
```

This starts all services including the frontend, with proper networking and environment variables configured automatically.

### Container Architecture

The frontend container:
- Uses a multi-stage build process for optimized image size
- Runs on Node.js 18 Alpine for a minimal footprint
- Serves the built React application via Vite's production server
- Connects to all backend services through the nginx reverse proxy
- Requires no direct database access (all data accessed via APIs)

## Integration with Backend Services

The frontend communicates with all backend services through a centralized nginx reverse proxy. All API calls are routed to the appropriate service based on the URL path:

- `/api/auth/*` → User Service
- `/api/users/*` → User Service
- `/api/modules/*` → Interview Service
- `/api/sessions/*` → Interview Service
- `/api/resume/*` → Resume Service
- `/api/media/*` → Media Service
- `/api/transcribe/*` → Transcription Service
- `/api/tts/*` → Transcription Service
- `/api/followup/*` → Interview Service
- `/api/feedback/*` → Feedback Service

### API Integration Details

The API integration is managed through the `api.js` file in the `src/services` directory. Key aspects:

1. **Environment-based Configuration**: All API URLs are configured via environment variables, making it easy to switch between development and production environments.

2. **Authentication**: JWT tokens are automatically attached to authenticated requests, with token refresh handled transparently.

3. **Error Handling**: Centralized error handling with appropriate status code management and user-friendly messages.

4. **Service Modularity**: Each backend service has its own set of API functions, allowing for clean separation of concerns.

### Key API Functions by Service

#### User Service
- `loginUser(email, password)`: Authenticate user and retrieve JWT token
- `registerUser(userData)`: Create new user account
- `getUserProfile()`: Retrieve authenticated user's profile

#### Interview Service
- `getModules()`: List available interview modules
- `createSession(moduleId)`: Start a new interview session
- `getNextQuestion(sessionId)`: Fetch the next question in a session
- `submitAnswer(sessionId, questionId, answer)`: Submit answer to a question

#### Resume Service
- `uploadResume(file)`: Upload and parse a resume
- `getResumeDetails(userId)`: Retrieve parsed resume information

#### Media Service
- `startRecording(sessionId)`: Begin audio recording for an interview
- `uploadAudioChunk(sessionId, chunk)`: Send recorded audio chunk for processing

#### Transcription Service
- `transcribeAudio(audioUrl)`: Convert audio to text
- `generateSpeech(text, voice)`: Convert text to audio for AI interviewer

#### Feedback Service
- `getSessionFeedback(sessionId)`: Retrieve comprehensive interview feedback

## Testing

The project includes comprehensive test coverage:

```
# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```
