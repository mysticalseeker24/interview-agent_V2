import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { sessionAPI } from '../services/api';
import {
  container,
  card,
  primaryButton,
  secondaryButton,
  flexBetween,
  pageTitle,
  pageSubtitle,
  badge,
  badgeSuccess,
  badgeWarning,
  badgeError,
  loading,
  errorText
} from '../styles';

const Report = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
  }, [sessionId]);

  const fetchReport = async () => {
    try {
      setIsLoading(true);
      const response = await sessionAPI.getSessionReport(sessionId);
      setReportData(response.data);
    } catch (error) {
      console.error('Error fetching report:', error);
      setError('Failed to load interview report');
    } finally {
      setIsLoading(false);
    }
  };

  const retakePractice = async () => {
    try {
      // Create a new practice session with the same module
      const response = await sessionAPI.createSession({
        module_id: reportData.module_id,
        mode: 'practice'
      });
      const newSessionId = response.data.session_id;
      navigate(`/sessions/${newSessionId}/lobby`);
    } catch (error) {
      console.error('Error creating new session:', error);
      setError('Failed to start new practice session');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const getScoreBadgeStyle = (score) => {
    if (score >= 80) return badgeSuccess;
    if (score >= 60) return badgeWarning;
    return badgeError;
  };

  const getPerformanceLevel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 70) return 'Average';
    if (score >= 60) return 'Below Average';
    return 'Needs Improvement';
  };

  if (isLoading) {
    return <div style={loading}>Loading your interview report...</div>;
  }

  if (error) {
    return (
      <div style={container}>
        <div style={{
          ...errorText,
          textAlign: 'center',
          padding: '2rem',
          backgroundColor: '#fee2e2',
          borderRadius: '8px',
          marginTop: '2rem'
        }}>
          {error}
        </div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div style={container}>
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          color: '#6b7280',
          marginTop: '2rem'
        }}>
          No report data available
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = [
    {
      metric: 'Correctness',
      value: reportData.scores?.correctness || 0,
      fullMark: 100
    },
    {
      metric: 'Fluency',
      value: reportData.scores?.fluency || 0,
      fullMark: 100
    },
    {
      metric: 'Depth',
      value: reportData.scores?.depth || 0,
      fullMark: 100
    },
    {
      metric: 'Communication',
      value: reportData.scores?.communication || 0,
      fullMark: 100
    }
  ];

  const overallScore = chartData.reduce((sum, item) => sum + item.value, 0) / chartData.length;

  return (
    <div style={container}>
      <div style={{ marginTop: '2rem' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={pageTitle}>Interview Report</h1>
          <p style={pageSubtitle}>
            Here's how you performed in your interview
          </p>
        </div>

        {/* Overall Score */}
        <div style={{
          ...card,
          textAlign: 'center',
          marginBottom: '2rem',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#ffffff'
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            marginBottom: '1rem'
          }}>
            Overall Performance
          </h2>
          <div style={{
            fontSize: '48px',
            fontWeight: '700',
            marginBottom: '0.5rem'
          }}>
            {Math.round(overallScore)}%
          </div>
          <div style={{
            fontSize: '18px',
            opacity: 0.9
          }}>
            {getPerformanceLevel(overallScore)}
          </div>
          {reportData.percentile && (
            <div style={{
              fontSize: '14px',
              opacity: 0.8,
              marginTop: '0.5rem'
            }}>
              Better than {reportData.percentile}% of candidates
            </div>
          )}
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '2rem',
          '@media (max-width: 768px)': {
            gridTemplateColumns: '1fr'
          }
        }}>
          {/* Detailed Scores */}
          <div style={card}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: '600',
              marginBottom: '1.5rem'
            }}>
              Detailed Scores
            </h3>

            {/* Score Chart */}
            <div style={{ height: '300px', marginBottom: '2rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="metric" 
                    fontSize={12}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis fontSize={12} />
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Score']}
                    labelStyle={{ color: '#1f2937' }}
                  />
                  <Bar 
                    dataKey="value" 
                    fill="#2563eb"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Individual Scores */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {chartData.map((item) => (
                <div key={item.metric} style={flexBetween}>
                  <span style={{ fontWeight: '500' }}>{item.metric}</span>
                  <span style={getScoreBadgeStyle(item.value)}>
                    {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Feedback & Recommendations */}
          <div style={card}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: '600',
              marginBottom: '1.5rem'
            }}>
              Feedback & Recommendations
            </h3>

            {reportData.narrative ? (
              <div style={{
                fontSize: '14px',
                lineHeight: '1.6',
                color: '#374151',
                marginBottom: '2rem'
              }}>
                {reportData.narrative}
              </div>
            ) : (
              <div style={{
                fontSize: '14px',
                lineHeight: '1.6',
                color: '#374151',
                marginBottom: '2rem'
              }}>
                <p style={{ marginBottom: '1rem' }}>
                  <strong>Strengths:</strong> You demonstrated good communication skills and provided relevant examples.
                </p>
                <p style={{ marginBottom: '1rem' }}>
                  <strong>Areas for Improvement:</strong> Consider providing more specific details and quantifiable results in your responses.
                </p>
                <p>
                  <strong>Recommendations:</strong> Practice the STAR method (Situation, Task, Action, Result) for behavioral questions.
                </p>
              </div>
            )}

            {/* Key Insights */}
            <div style={{
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '2rem'
            }}>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '0.5rem'
              }}>
                Key Insights
              </h4>
              <ul style={{
                fontSize: '14px',
                color: '#6b7280',
                paddingLeft: '1rem'
              }}>
                <li>Response time averaged 15 seconds per question</li>
                <li>Used technical terminology appropriately</li>
                <li>Maintained good eye contact throughout</li>
                <li>Could improve on providing concrete examples</li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}>
              {reportData.mode === 'practice' && (
                <button
                  onClick={retakePractice}
                  style={{
                    ...primaryButton,
                    width: '100%'
                  }}
                >
                  Retake Practice Interview
                </button>
              )}
              <button
                onClick={() => navigate('/')}
                style={{
                  ...secondaryButton,
                  width: '100%'
                }}
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Session Details */}
        <div style={{
          ...card,
          marginTop: '2rem'
        }}>
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '1rem'
          }}>
            Session Details
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            fontSize: '14px'
          }}>
            <div>
              <span style={{ color: '#6b7280' }}>Session ID:</span>
              <div style={{ fontWeight: '500' }}>{sessionId}</div>
            </div>
            <div>
              <span style={{ color: '#6b7280' }}>Date:</span>
              <div style={{ fontWeight: '500' }}>
                {reportData.created_at ? 
                  new Date(reportData.created_at).toLocaleDateString() : 
                  new Date().toLocaleDateString()
                }
              </div>
            </div>
            <div>
              <span style={{ color: '#6b7280' }}>Duration:</span>
              <div style={{ fontWeight: '500' }}>
                {reportData.duration || '20 minutes'}
              </div>
            </div>
            <div>
              <span style={{ color: '#6b7280' }}>Mode:</span>
              <div style={{ fontWeight: '500', textTransform: 'capitalize' }}>
                {reportData.mode || 'Practice'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Report;
