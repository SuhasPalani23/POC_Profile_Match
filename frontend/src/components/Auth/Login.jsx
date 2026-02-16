import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';
import { setToken } from '../../utils/auth';
import Button from '../Common/Button';
import palette from '../../palette';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
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

    try {
      const response = await authAPI.login(formData);
      setToken(response.data.token);
      await onLogin();
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
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
        maxWidth: '400px',
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
          <span className="gradient-text">Founding Mindset</span>
        </h1>
        <p style={{
          color: palette.colors.text.secondary,
          textAlign: 'center',
          marginBottom: palette.spacing.xl,
        }}>
          Sign in to your account
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
          <div style={{ marginBottom: palette.spacing.lg }}>
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

          <div style={{ marginBottom: palette.spacing.xl }}>
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

          <Button type="submit" loading={loading} fullWidth>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <p style={{
          marginTop: palette.spacing.lg,
          textAlign: 'center',
          color: palette.colors.text.secondary,
          fontSize: palette.typography.fontSize.sm,
        }}>
          Don't have an account?{' '}
          <Link 
            to="/signup" 
            style={{
              color: palette.colors.primary.cyan,
              textDecoration: 'none',
              fontWeight: palette.typography.fontWeight.medium,
            }}
          >
            Sign up
          </Link>
        </p>

        <p style={{
          marginTop: palette.spacing.md,
          textAlign: 'center',
          color: palette.colors.text.tertiary,
          fontSize: palette.typography.fontSize.xs,
        }}>
          Test account: john.doe@email.com / Test@123
        </p>
      </div>
    </div>
  );
};

export default Login;