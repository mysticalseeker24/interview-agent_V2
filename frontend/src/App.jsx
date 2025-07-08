import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth.jsx';
import { loading } from './styles';

// Import pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Lobby from './pages/Lobby';
import InterviewRoom from './pages/InterviewRoom';
import Report from './pages/Report';
import Profile from './pages/Profile';
import About from './pages/About';

// Private Route Component
function PrivateRoute({ children }) {
  const { user, loading: authLoading } = useAuth();
  
  if (authLoading) {
    return <div style={loading}>Loading...</div>;
  }
  
  return user ? children : <Navigate to="/login" />;
}

// Public Route Component (redirect to dashboard if logged in)
function PublicRoute({ children }) {
  const { user, loading: authLoading } = useAuth();
  
  if (authLoading) {
    return <div style={loading}>Loading...</div>;
  }
  
  return !user ? children : <Navigate to="/" />;
}

function App() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f9fafb',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif"
    }}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/signup" element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        } />
        <Route path="/about" element={<About />} />
        
        {/* Protected Routes */}
        <Route path="/" element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        } />
        <Route path="/modules/:id" element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        } />
        <Route path="/sessions/:sessionId/lobby" element={
          <PrivateRoute>
            <Lobby />
          </PrivateRoute>
        } />
        <Route path="/sessions/:sessionId/interview" element={
          <PrivateRoute>
            <InterviewRoom />
          </PrivateRoute>
        } />
        <Route path="/sessions/:sessionId/report" element={
          <PrivateRoute>
            <Report />
          </PrivateRoute>
        } />
        <Route path="/profile" element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        } />
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  );
}

export default App;
