import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { userAPI } from '../services/api';
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
  badge,
  badgeSuccess,
  badgeWarning,
  badgeError,
  header,
  nav,
  logo,
  navLinks,
  navLink,
  loading,
  errorText,
  successText
} from '../styles';

const Profile = () => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    timezone: 'UTC'
  });
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchProfileData();
    fetchSessions();
  }, []);

  const fetchProfileData = async () => {
    try {
      const response = await userAPI.getProfile();
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      setError('Failed to load profile data');
    }
  };

  const fetchSessions = async () => {
    try {
      setIsLoading(true);
      const response = await userAPI.getSessions();
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      setError('Failed to load session history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    
    try {
      setIsUpdating(true);
      setError('');
      setSuccess('');
      
      await userAPI.updateProfile(profile);
      setSuccess('Profile updated successfully!');
    } catch (error) {
      console.error('Error updating profile:', error);
      setError('Failed to update profile');
    } finally {
      setIsUpdating(false);
    }
  };

  const getScoreBadgeStyle = (score) => {
    if (score >= 80) return badgeSuccess;
    if (score >= 60) return badgeWarning;
    return badgeError;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateAverageScore = () => {
    if (sessions.length === 0) return 0;
    const totalScore = sessions.reduce((sum, session) => {
      const sessionScore = session.overall_score || 0;
      return sum + sessionScore;
    }, 0);
    return Math.round(totalScore / sessions.length);
  };

  return (
    <div>
      {/* Header */}
      <header style={header}>
        <nav style={nav}>
          <Link to="/" style={logo}>TalentSync</Link>
          <div style={navLinks}>
            <Link to="/" style={navLink}>Dashboard</Link>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>
              {user?.full_name}
            </span>
            <button
              onClick={logout}
              style={{
                ...secondaryButton,
                padding: '0.5rem 1rem',
                fontSize: '12px'
              }}
            >
              Logout
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main style={container}>
        <div style={{ marginTop: '2rem' }}>
          <h1 style={pageTitle}>Profile</h1>
          <p style={pageSubtitle}>
            Manage your account settings and view your interview history
          </p>

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
            gridTemplateColumns: '1fr 2fr',
            gap: '2rem',
            '@media (max-width: 768px)': {
              gridTemplateColumns: '1fr'
            }
          }}>
            {/* Profile Settings */}
            <div style={card}>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '600',
                marginBottom: '1.5rem'
              }}>
                Account Settings
              </h2>

              <form onSubmit={handleUpdateProfile}>
                <div style={formGroup}>
                  <label style={label} htmlFor="full_name">
                    Full Name
                  </label>
                  <input
                    style={input}
                    type="text"
                    id="full_name"
                    name="full_name"
                    value={profile.full_name}
                    onChange={handleInputChange}
                    disabled={isUpdating}
                  />
                </div>

                <div style={formGroup}>
                  <label style={label} htmlFor="email">
                    Email Address
                  </label>
                  <input
                    style={{
                      ...input,
                      backgroundColor: '#f9fafb',
                      cursor: 'not-allowed'
                    }}
                    type="email"
                    id="email"
                    name="email"
                    value={profile.email}
                    disabled
                  />
                  <p style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    marginTop: '0.25rem'
                  }}>
                    Email cannot be changed
                  </p>
                </div>

                <div style={formGroup}>
                  <label style={label} htmlFor="timezone">
                    Timezone
                  </label>
                  <select
                    style={input}
                    id="timezone"
                    name="timezone"
                    value={profile.timezone}
                    onChange={handleInputChange}
                    disabled={isUpdating}
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                    <option value="Asia/Shanghai">Shanghai</option>
                    <option value="Asia/Kolkata">Mumbai</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isUpdating}
                  style={{
                    ...primaryButton,
                    width: '100%',
                    opacity: isUpdating ? 0.7 : 1,
                    cursor: isUpdating ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isUpdating ? 'Updating...' : 'Update Profile'}
                </button>
              </form>

              {/* Statistics */}
              <div style={{
                marginTop: '2rem',
                paddingTop: '2rem',
                borderTop: '1px solid #e5e7eb'
              }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  marginBottom: '1rem'
                }}>
                  Your Statistics
                </h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '1rem',
                  fontSize: '14px'
                }}>
                  <div style={{
                    textAlign: 'center',
                    padding: '1rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px'
                  }}>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: '700',
                      color: '#2563eb'
                    }}>
                      {sessions.length}
                    </div>
                    <div style={{ color: '#6b7280' }}>
                      Total Interviews
                    </div>
                  </div>
                  <div style={{
                    textAlign: 'center',
                    padding: '1rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px'
                  }}>
                    <div style={{
                      fontSize: '24px',
                      fontWeight: '700',
                      color: '#059669'
                    }}>
                      {calculateAverageScore()}%
                    </div>
                    <div style={{ color: '#6b7280' }}>
                      Average Score
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Interview History */}
            <div style={card}>
              <h2 style={{
                fontSize: '20px',
                fontWeight: '600',
                marginBottom: '1.5rem'
              }}>
                Interview History
              </h2>

              {isLoading ? (
                <div style={loading}>Loading interview history...</div>
              ) : sessions.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '2rem',
                  color: '#6b7280'
                }}>
                  <p>No interviews completed yet.</p>
                  <Link
                    to="/"
                    style={{
                      ...primaryButton,
                      display: 'inline-block',
                      marginTop: '1rem',
                      textDecoration: 'none'
                    }}
                  >
                    Start Your First Interview
                  </Link>
                </div>
              ) : (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem'
                }}>
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      style={{
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '1rem',
                        transition: 'box-shadow 0.2s'
                      }}
                    >
                      <div style={flexBetween}>
                        <div>
                          <h3 style={{
                            fontSize: '16px',
                            fontWeight: '600',
                            marginBottom: '0.25rem'
                          }}>
                            {session.module_title || 'Interview Session'}
                          </h3>
                          <p style={{
                            fontSize: '14px',
                            color: '#6b7280',
                            marginBottom: '0.5rem'
                          }}>
                            {formatDate(session.created_at)} • {session.mode || 'Practice'}
                          </p>
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '1rem'
                        }}>
                          <span style={getScoreBadgeStyle(session.overall_score || 0)}>
                            {session.overall_score || 0}%
                          </span>
                          <Link
                            to={`/sessions/${session.id}/report`}
                            style={{
                              ...secondaryButton,
                              fontSize: '12px',
                              padding: '0.5rem 1rem',
                              textDecoration: 'none'
                            }}
                          >
                            View Report
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Profile;
