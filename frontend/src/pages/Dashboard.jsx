import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { moduleAPI, sessionAPI } from '../services/api';
import {
  container,
  card,
  primaryButton,
  secondaryButton,
  input,
  formGroup,
  label,
  flexBetween,
  gridResponsive,
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
  loading
} from '../styles';

const Dashboard = () => {
  const [modules, setModules] = useState([]);
  const [filteredModules, setFilteredModules] = useState([]);
  const [filters, setFilters] = useState({
    category: 'All',
    difficulty: 'All',
    mode: 'All',
    search: ''
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const categories = [
    'All', 'Software', 'Data Science', 'Finance', 'Product', 
    'Business', 'Consulting', 'Writing', 'Design', 'Legal', 
    'Media', 'Engineering', 'Statistics', 'Marketing', 
    'Biology', 'Security', 'Blockchain'
  ];

  const difficulties = ['All', 'Easy', 'Medium', 'Difficult'];
  const modes = ['All', 'Practice', 'Assessment'];

  useEffect(() => {
    fetchModules();
  }, []);

  useEffect(() => {
    filterModules();
  }, [modules, filters]);

  const fetchModules = async () => {
    try {
      setIsLoading(true);
      const response = await moduleAPI.getModules();
      setModules(response.data);
    } catch (error) {
      setError('Failed to load modules');
      console.error('Error fetching modules:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterModules = () => {
    let filtered = modules;

    if (filters.category !== 'All') {
      filtered = filtered.filter(module => 
        module.category?.toLowerCase() === filters.category.toLowerCase()
      );
    }

    if (filters.difficulty !== 'All') {
      filtered = filtered.filter(module => 
        module.difficulty?.toLowerCase() === filters.difficulty.toLowerCase()
      );
    }

    if (filters.search) {
      filtered = filtered.filter(module =>
        module.title?.toLowerCase().includes(filters.search.toLowerCase()) ||
        module.description?.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    setFilteredModules(filtered);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const getDifficultyBadgeStyle = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy':
        return badgeSuccess;
      case 'medium':
        return badgeWarning;
      case 'difficult':
        return badgeError;
      default:
        return badge;
    }
  };

  const startInterview = async (moduleId, mode = 'practice') => {
    try {
      const response = await sessionAPI.createSession({
        module_id: moduleId,
        mode
      });
      const sessionId = response.data.session_id;
      navigate(`/sessions/${sessionId}/lobby`);
    } catch (error) {
      setError('Failed to start interview session');
      console.error('Error creating session:', error);
    }
  };

  if (isLoading) {
    return <div style={loading}>Loading modules...</div>;
  }

  return (
    <div>
      {/* Header */}
      <header style={header}>
        <nav style={nav}>
          <div style={logo}>TalentSync</div>
          <div style={navLinks}>
            <a href="/profile" style={navLink}>Profile</a>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>
              Welcome, {user?.full_name}
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
          <h1 style={pageTitle}>Interview Practice</h1>
          <p style={pageSubtitle}>
            Choose from our collection of expert-vetted interview modules
          </p>

          {error && (
            <div style={{
              padding: '1rem',
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              borderRadius: '8px',
              marginBottom: '2rem'
            }}>
              {error}
            </div>
          )}

          {/* Filters */}
          <div style={{
            ...card,
            marginBottom: '2rem'
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div style={formGroup}>
                <label style={label}>Category</label>
                <select
                  style={input}
                  value={filters.category}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                >
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>

              <div style={formGroup}>
                <label style={label}>Difficulty</label>
                <select
                  style={input}
                  value={filters.difficulty}
                  onChange={(e) => handleFilterChange('difficulty', e.target.value)}
                >
                  {difficulties.map(difficulty => (
                    <option key={difficulty} value={difficulty}>
                      {difficulty}
                    </option>
                  ))}
                </select>
              </div>

              <div style={formGroup}>
                <label style={label}>Search</label>
                <input
                  style={input}
                  type="text"
                  placeholder="Search modules..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Module Grid */}
          <div style={gridResponsive}>
            {filteredModules.map((module) => (
              <div
                key={module.id}
                style={{
                  ...card,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  ':hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                  }
                }}
              >
                {/* Module Header */}
                <div style={{
                  ...flexBetween,
                  marginBottom: '1rem'
                }}>
                  <span style={getDifficultyBadgeStyle(module.difficulty)}>
                    {module.difficulty}
                  </span>
                  <span style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    backgroundColor: '#f3f4f6',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px'
                  }}>
                    {module.duration || '20m'}
                  </span>
                </div>

                {/* Module Content */}
                <h3 style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '0.5rem',
                  color: '#1f2937'
                }}>
                  {module.title}
                </h3>

                <p style={{
                  fontSize: '14px',
                  color: '#6b7280',
                  marginBottom: '1.5rem',
                  lineHeight: '1.5'
                }}>
                  {module.description || 'Practice your interview skills with this module'}
                </p>

                {/* Module Actions */}
                <div style={{
                  display: 'flex',
                  gap: '0.5rem'
                }}>
                  <button
                    onClick={() => startInterview(module.id, 'practice')}
                    style={{
                      ...primaryButton,
                      flex: 1,
                      fontSize: '14px'
                    }}
                  >
                    Start Practice
                  </button>
                  <button
                    onClick={() => startInterview(module.id, 'assessment')}
                    style={{
                      ...secondaryButton,
                      flex: 1,
                      fontSize: '14px'
                    }}
                  >
                    Assessment
                  </button>
                </div>
              </div>
            ))}
          </div>

          {filteredModules.length === 0 && !isLoading && (
            <div style={{
              textAlign: 'center',
              padding: '3rem',
              color: '#6b7280'
            }}>
              <p>No modules found matching your criteria.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
