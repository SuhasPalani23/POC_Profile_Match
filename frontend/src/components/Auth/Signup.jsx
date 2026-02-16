import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';
import { setToken } from '../../utils/auth';
import Button from '../Common/Button';
import palette from '../../palette';

const Signup = ({ onSignup }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    bio: '',
    skills: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const skillsArray = formData.skills
        .split(',')
        .map(skill => skill.trim())
        .filter(skill => skill);

      const response = await authAPI.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        bio: formData.bio,
        skills: skillsArray,
      });

      setToken(response.data.token);
      await onSignup();
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: palette.spacing.lg,
    }}>
      <div style={{
        width: '100%',
        maxWidth: '500px',
        backgroundColor: palette.colors.background.secondary,
        padding: palette.spacing['2xl'],
        borderRadius: palette.borderRadius.xl,
        border: `1px solid ${palette.colors.border.primary}`,
      }}>
        <h1 style={{
          fontSize: palette.typography.fontSize['3xl'],
          fontWeight: palette.typography.fontWeight.bold,
          marginBottom: palette.spacing.sm,
          textAlign: 'center',
        }}>
          <span className="gradient-text">Join Founding Mindset</span>
        </h1>
        <p style={{
          color: palette.colors.text.secondary,
          textAlign: 'center',
          marginBottom: palette.spacing.xl,
        }}>
          Create your account to get started
        </p>

        {error && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: `1px solid ${palette.colors.status.error}`,
            color: palette.colors.status.error,
            padding: palette.spacing.md,
            borderRadius: palette.borderRadius.md,
            marginBottom: palette.spacing.lg,
            fontSize: palette.typography.fontSize.sm,
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: palette.spacing.md }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.md }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.md }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={6}
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.md }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Confirm Password
            </label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              minLength={6}
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.md }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Skills (comma-separated)
            </label>
            <input
              type="text"
              name="skills"
              value={formData.skills}
              onChange={handleChange}
              placeholder="e.g., Python, React, Machine Learning"
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.xl }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Bio
            </label>
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows={3}
              placeholder="Tell us about yourself and your founding mindset..."
              style={{
                width: '100%',
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.primary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
                resize: 'vertical',
                fontFamily: palette.typography.fontFamily.primary,
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
          </div>

          <Button type="submit" loading={loading} fullWidth>
            {loading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>

        <p style={{
          marginTop: palette.spacing.lg,
          textAlign: 'center',
          color: palette.colors.text.secondary,
          fontSize: palette.typography.fontSize.sm,
        }}>
          Already have an account?{' '}
          <Link 
            to="/login" 
            style={{
              color: palette.colors.primary.cyan,
              textDecoration: 'none',
              fontWeight: palette.typography.fontWeight.medium,
            }}
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Signup;