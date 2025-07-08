import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  container,
  card,
  primaryButton,
  input,
  formGroup,
  label,
  errorText,
  flexCenter,
  pageTitle,
  pageSubtitle
} from '../styles';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setLoading(true);
    setErrors({});
    
    try {
      const result = await login(formData);
      if (result.success) {
        navigate('/');
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      ...flexCenter,
      minHeight: '100vh',
      padding: '2rem'
    }}>
      <div style={{
        ...card,
        width: '100%',
        maxWidth: '400px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            ...pageTitle,
            fontSize: '28px',
            marginBottom: '0.5rem'
          }}>
            Welcome Back
          </h1>
          <p style={pageSubtitle}>
            Sign in to your TalentSync account
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {errors.general && (
            <div style={{
              ...errorText,
              textAlign: 'center',
              marginBottom: '1rem',
              padding: '0.75rem',
              backgroundColor: '#fee2e2',
              borderRadius: '6px'
            }}>
              {errors.general}
            </div>
          )}

          <div style={formGroup}>
            <label style={label} htmlFor="email">
              Email Address
            </label>
            <input
              style={{
                ...input,
                borderColor: errors.email ? '#dc2626' : '#d1d5db'
              }}
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              disabled={loading}
            />
            {errors.email && (
              <div style={errorText}>{errors.email}</div>
            )}
          </div>

          <div style={formGroup}>
            <label style={label} htmlFor="password">
              Password
            </label>
            <input
              style={{
                ...input,
                borderColor: errors.password ? '#dc2626' : '#d1d5db'
              }}
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              disabled={loading}
            />
            {errors.password && (
              <div style={errorText}>{errors.password}</div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              ...primaryButton,
              width: '100%',
              marginTop: '1rem',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '2rem',
          paddingTop: '2rem',
          borderTop: '1px solid #e5e7eb'
        }}>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            Don't have an account?{' '}
            <Link
              to="/signup"
              style={{
                color: '#2563eb',
                fontWeight: '500',
                textDecoration: 'underline'
              }}
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
