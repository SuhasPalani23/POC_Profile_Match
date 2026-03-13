import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';
import { setToken } from '../../utils/auth';
import Button from '../Common/Button';
import palette from '../../palette';

const EyeIcon = ({ closed = false, blinking = false }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    style={{
      transform: blinking ? 'scaleY(0.08)' : 'scaleY(1)',
      transformOrigin: 'center',
      transition: 'transform 300ms cubic-bezier(0.16, 1, 0.3, 1)',
    }}
  >
    {closed ? (
      <>
        <path d="M3 3l18 18" />
        <path d="M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-.58" />
        <path d="M9.88 5.09A10.94 10.94 0 0112 5c5 0 9.27 3.11 11 7-1 2.24-2.76 4.16-5 5.3" />
        <path d="M6.61 6.61C4.62 7.88 3.13 9.76 2 12c.71 1.58 1.81 3.02 3.2 4.2" />
      </>
    ) : (
      <>
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
        <circle cx="12" cy="12" r="3" />
      </>
    )}
  </svg>
);

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isEyeBlinking, setIsEyeBlinking] = useState(false);
  const [isCapsLockOn, setIsCapsLockOn] = useState(false);
  const [isCompact, setIsCompact] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onResize = () => setIsCompact(window.innerWidth <= 1080);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleTogglePasswordVisibility = () => {
    setIsEyeBlinking(true);
    setShowPassword((prev) => !prev);
    setTimeout(() => setIsEyeBlinking(false), 220);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handlePasswordKeyEvent = (e) => {
    setIsCapsLockOn(e.getModifierState && e.getModifierState('CapsLock'));
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
      display: 'grid',
      gridTemplateColumns: isCompact ? '1fr' : '1.2fr 1fr',
      gap: palette.spacing['2xl'],
      padding: `clamp(1.5rem, 4vw, 4rem)`,
      alignItems: 'center',
    }}>
      <section style={{ padding: `0 clamp(0rem, 2vw, 3rem)` }}>
        <p className="mono-label">Founder Employee Matching Platform</p>
        <h1 className="hero-title" style={{ marginTop: palette.spacing.md }}>
          <span className="word-rise word-delay-1">Find</span>
          <br />
          <span className="word-rise word-delay-2 gradient-text">Exceptional Talent</span>
        </h1>
        <p style={{
          marginTop: palette.spacing.lg,
          maxWidth: '560px',
          color: palette.colors.text.secondary,
          lineHeight: palette.typography.lineHeight.relaxed,
        }}>
          Precision matching for founders building serious teams. Enter the platform and review ranked candidates engineered for startup fit.
        </p>
        <div style={{
          marginTop: palette.spacing.xl,
          height: '1px',
          backgroundColor: palette.colors.border.primary,
          transform: 'scaleX(0)',
        }} className="rule-draw" />
      </section>

      <div className="surface-card" style={{
        width: '100%',
        maxWidth: '560px',
        justifySelf: 'end',
        padding: 'clamp(1.5rem, 4vw, 3rem)',
        borderRadius: palette.borderRadius.xl,
      }}>
        <p className="mono-label" style={{ marginBottom: palette.spacing.md }}>Secure Access</p>
        <h2 style={{
          fontFamily: palette.typography.fontFamily.display,
          fontSize: palette.typography.fontSize['4xl'],
          marginBottom: palette.spacing.lg,
          fontWeight: palette.typography.fontWeight.semibold,
        }}>
          Sign In
        </h2>

        {error && (
          <div style={{
            backgroundColor: 'rgba(216, 107, 107, 0.08)',
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
            <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
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
                padding: `${palette.spacing.sm} 0`,
                backgroundColor: 'transparent',
                border: 'none',
                borderBottom: '1px solid #333333',
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                outline: 'none',
                transition: `border-color ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1), box-shadow ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
              }}
              onFocus={(e) => {
                e.target.style.borderBottomColor = palette.colors.primary.cyan;
                e.target.style.boxShadow = `0 2px 0 ${palette.colors.primary.cyan}`;
              }}
              onBlur={(e) => {
                e.target.style.borderBottomColor = '#333333';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.xl }}>
            <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                style={{
                  width: '100%',
                  padding: `${palette.spacing.sm} 0`,
                  paddingRight: '44px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: '1px solid #333333',
                  color: palette.colors.text.primary,
                  fontSize: palette.typography.fontSize.base,
                  outline: 'none',
                  transition: `border-color ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1), box-shadow ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
                }}
                onFocus={(e) => {
                  e.target.style.borderBottomColor = palette.colors.primary.cyan;
                  e.target.style.boxShadow = `0 2px 0 ${palette.colors.primary.cyan}`;
                }}
                onBlur={(e) => {
                  e.target.style.borderBottomColor = '#333333';
                  e.target.style.boxShadow = 'none';
                  setIsCapsLockOn(false);
                }}
                onKeyDown={handlePasswordKeyEvent}
                onKeyUp={handlePasswordKeyEvent}
              />
              <button
                type="button"
                onClick={handleTogglePasswordVisibility}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                style={{
                  position: 'absolute',
                  top: '50%',
                  right: 0,
                  transform: 'translateY(-50%)',
                  border: 'none',
                  background: 'transparent',
                  color: palette.colors.primary.cyan,
                  padding: 0,
                  lineHeight: 0,
                }}
              >
                <EyeIcon closed={showPassword} blinking={isEyeBlinking} />
              </button>
            </div>
            {isCapsLockOn && (
              <p style={{
                marginTop: palette.spacing.xs,
                color: '#D1D5DB',
                fontSize: palette.typography.fontSize.xs,
              }}>
                Caps Lock is on
              </p>
            )}
          </div>

          <Button type="submit" loading={loading} fullWidth>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <p style={{
          marginTop: palette.spacing.lg,
          color: palette.colors.text.secondary,
          fontSize: palette.typography.fontSize.sm,
        }}>
          Don&apos;t have an account?{' '}
          <Link
            to="/signup"
            style={{
              color: palette.colors.primary.cyan,
              textDecoration: 'none',
            }}
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
