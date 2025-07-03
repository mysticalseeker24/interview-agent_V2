# TalentSync - Project Overview & Feature Specification

## 1. Introduction
**TalentSync** is an end-to-end AI-powered interview platform designed to simulate real-world technical interviews. It offers domain-specific modules, adaptive AI-driven questioning, real-time audio/video interview capabilities, and detailed performance analytics.

### 1.1 Mission
Enable candidates to practice, assess, and improve their interviewing skills through personalized, data-driven mock interviews, while giving recruiters a rich talent pipeline with structured insights.

---

## 2. Core Features & Workflow

### 2.1 User Journey Overview
1. **Sign Up / Login**: Candidate creates an account or logs in.  
2. **Dashboard / Home**: Browse interview modules via category tabs and filters.  
3. **Module Selection**: Choose from 8 domains (Software Eng, DevOps, Kubernetes, DSA, ML, AI Eng, LLMs, Resume-Driven).  
4. **Onboarding Lobby**: Upload resume (for resume-driven domain), perform camera/mic test, and review interview tips.  
5. **Interview Session**: Real-time audio/video Q&A with adaptive AI interviewer.  
6. **Post-Interview**: Automatic transcription, scoring, and AI-generated feedback.  
7. **Profile & History**: View past session reports, retake practice interviews, manage account settings.

### 2.2 Feature Breakdown

#### Feature 1: Dynamic Interview Module Library
- **Objective**: Centralized, categorized library of interview topics.  
- **Components**:  
  - **Categorized Modules**: Eight core domains.  
  - **Card-Based UI**: Responsive grid with ModuleCards.  
  - **Dynamic Filtering**: Filter by difficulty, duration, mode, and search.  
- **Workflow**:  
  1. Frontend fetches modules via `GET /api/modules`.  
  2. User selects module → Details or Start actions.

#### Feature 2: Advanced AI Interviewer Logic
- **Objective**: Personalized, adaptive Q&A based on candidate’s profile and responses.  
- **Components**:  
  - **Resume-Driven Q&A**: Parse resume → generate bespoke questions.  
  - **Adaptive Engine**: Use semantic similarity and template matching for follow-ups.  
  - **Interview Modes**: Practice (private), General (formal), Invite-only (code-based).  
- **Workflow**:  
  1. Resume service extracts skills/projects.  
  2. Interview service seeds question queue (core + resume-driven).  
  3. After each answer: transcription → keyword extraction → RAG retrieval or template selection → next question.

#### Feature 3: Real-Time Audio/Video Interface
- **Objective**: Professional browser-based video interview experience.  
- **Components**:  
  - **Pre-Interview Lobby**: Device selection (camera, mic, speaker) + live preview + tips.  
  - **Interview Room**: Live `<video>` feed, prompt area, timer, recording indicator.  
  - **Error Handling**: Reconnect flows for dropped devices.  
- **Workflow**:  
  1. Lobby page performs `getUserMedia` and `enumerateDevices`.  
  2. On proceed: InterviewRoom opens, uses MediaRecorder for local recordings.

#### Feature 4: Comprehensive Performance Analytics & Feedback
- **Objective**: Data-driven, multi-faceted performance reports.  
- **Components**:  
  - **Automated Transcription**: Whisper + AssemblyAI hybrid.  
  - **Scoring Metrics**: Correctness (semantic similarity), completeness, fluency (wpm, filler counts), depth.  
  - **Percentile Ranking**: Compare against historical sessions.  
  - **AI-Generated Feedback**: LLM-crafted narrative.  
- **Workflow**:  
  1. Post-session, audio blobs → transcription service → text with timestamps.  
  2. Background task (Celery) processes scores, percentiles, and LLM feedback.  
  3. Results persisted; user notified.

#### Feature 5: Profile Management & History
- **Objective**: Central hub for candidate’s interviews and settings.  
- **Components**:  
  - **Session History**: List of past interviews with links to reports.  
  - **Practice Retake**: Quick restart for practice mode.  
  - **Account Settings**: Email, password, data privacy consents.  

---

## 3. Page Inventory

| Page Name                  | Route                         | Key Purpose                                |
|----------------------------|-------------------------------|--------------------------------------------|
| Sign Up / Register         | `/signup`                     | Account creation                           |
| Sign In / Login            | `/login`                      | Authentication                             |
| Home / Dashboard           | `/`                           | Browse & filter modules                    |
| About / How It Works       | `/about`                      | Platform overview                          |
| Module Details             | `/modules/:moduleId`          | Module metadata & start actions            |
| Onboarding Lobby           | `/sessions/:id/lobby`         | Resume upload & device checks              |
| Interview Room             | `/sessions/:id/interview`     | Live Q&A via video/audio                   |
| Post-Interview Report      | `/sessions/:id/report`        | Performance analytics & feedback           |
| Profile / History          | `/profile`                    | Past sessions & settings                   |
| Admin Portal (optional)    | `/admin/*`                    | Manage modules/questions, view analytics   |

---

*Document: TalentSync — Project Overview & Feature Specification*

