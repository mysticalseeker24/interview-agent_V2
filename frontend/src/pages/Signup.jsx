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

const Signup = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
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
    
    if (!formData.full_name) {
      newErrors.full_name = 'Full name is required';
    } else if (formData.full_name.length < 2) {
      newErrors.full_name = 'Full name must be at least 2 characters';
    }
    
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
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      const { confirmPassword, ...signupData } = formData;
      const result = await signup(signupData);
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
            Create Account
          </h1>
          <p style={pageSubtitle}>
            Join TalentSync to start practicing interviews
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
            <label style={label} htmlFor="full_name">
              Full Name
            </label>
            <input
              style={{
                ...input,
                borderColor: errors.full_name ? '#dc2626' : '#d1d5db'
              }}
              type="text"
              id="full_name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Enter your full name"
              disabled={loading}
            />
            {errors.full_name && (
              <div style={errorText}>{errors.full_name}</div>
            )}
          </div>

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
              placeholder="Create a password"
              disabled={loading}
            />
            {errors.password && (
              <div style={errorText}>{errors.password}</div>
            )}
          </div>

          <div style={formGroup}>
            <label style={label} htmlFor="confirmPassword">
              Confirm Password
            </label>
            <input
              style={{
                ...input,
                borderColor: errors.confirmPassword ? '#dc2626' : '#d1d5db'
              }}
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm your password"
              disabled={loading}
            />
            {errors.confirmPassword && (
              <div style={errorText}>{errors.confirmPassword}</div>
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
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '2rem',
          paddingTop: '2rem',
          borderTop: '1px solid #e5e7eb'
        }}>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            Already have an account?{' '}
            <Link
              to="/login"
              style={{
                color: '#2563eb',
                fontWeight: '500',
                textDecoration: 'underline'
              }}
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;
