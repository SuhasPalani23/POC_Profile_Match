import React, { useState } from 'react';
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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isPasswordEyeBlinking, setIsPasswordEyeBlinking] = useState(false);
  const [isConfirmEyeBlinking, setIsConfirmEyeBlinking] = useState(false);
  const [isPasswordCapsLockOn, setIsPasswordCapsLockOn] = useState(false);
  const [isConfirmCapsLockOn, setIsConfirmCapsLockOn] = useState(false);
  const navigate = useNavigate();

  const handleTogglePasswordVisibility = () => {
    setIsPasswordEyeBlinking(true);
    setShowPassword((prev) => !prev);
    setTimeout(() => setIsPasswordEyeBlinking(false), 220);
  };

  const handleToggleConfirmPasswordVisibility = () => {
    setIsConfirmEyeBlinking(true);
    setShowConfirmPassword((prev) => !prev);
    setTimeout(() => setIsConfirmEyeBlinking(false), 220);
  };

  const handlePasswordKeyEvent = (e) => {
    setIsPasswordCapsLockOn(e.getModifierState && e.getModifierState('CapsLock'));
  };

  const handleConfirmPasswordKeyEvent = (e) => {
    setIsConfirmCapsLockOn(e.getModifierState && e.getModifierState('CapsLock'));
  };

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
        .map((skill) => skill.trim())
        .filter((skill) => skill);

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

  const inputBaseStyle = {
    width: '100%',
    padding: `${palette.spacing.sm} 0`,
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '1px solid #333333',
    color: palette.colors.text.primary,
    fontSize: palette.typography.fontSize.base,
    outline: 'none',
    transition: `border-color ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1), box-shadow ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      padding: `clamp(1.5rem, 4vw, 4rem)`,
    }}>
      <div className="surface-card" style={{
        width: '100%',
        maxWidth: '680px',
        padding: 'clamp(1.5rem, 4vw, 3rem)',
        borderRadius: palette.borderRadius.xl,
      }}>
        <p className="mono-label" style={{ marginBottom: palette.spacing.md }}>Onboarding</p>
        <h1 style={{
          fontFamily: palette.typography.fontFamily.display,
          fontSize: palette.typography.fontSize['4xl'],
          marginBottom: palette.spacing.sm,
        }}>
          Join the Founder Network
        </h1>
        <p style={{
          color: palette.colors.text.secondary,
          marginBottom: palette.spacing.xl,
        }}>
          Build your profile and enter the match engine.
        </p>
        <div style={{
          marginBottom: palette.spacing.xl,
          height: '1px',
          backgroundColor: palette.colors.border.primary,
          transform: 'scaleX(0)',
        }} className="rule-draw" />

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

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: palette.spacing.lg }}>
          {[
            { label: 'Full Name', name: 'name', type: 'text', required: true },
            { label: 'Email', name: 'email', type: 'email', required: true },
            { label: 'Skills (comma-separated)', name: 'skills', type: 'text', required: false },
          ].map((field) => (
            <div key={field.name}>
              <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
                {field.label}
              </label>
              <input
                type={field.type}
                name={field.name}
                value={formData[field.name]}
                onChange={handleChange}
                required={field.required}
                style={inputBaseStyle}
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
          ))}

          <div>
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
                minLength={6}
                style={{ ...inputBaseStyle, paddingRight: '44px' }}
                onFocus={(e) => {
                  e.target.style.borderBottomColor = palette.colors.primary.cyan;
                  e.target.style.boxShadow = `0 2px 0 ${palette.colors.primary.cyan}`;
                }}
                onBlur={(e) => {
                  e.target.style.borderBottomColor = '#333333';
                  e.target.style.boxShadow = 'none';
                  setIsPasswordCapsLockOn(false);
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
                <EyeIcon closed={showPassword} blinking={isPasswordEyeBlinking} />
              </button>
            </div>
            {isPasswordCapsLockOn && (
              <p style={{ marginTop: palette.spacing.xs, color: '#D1D5DB', fontSize: palette.typography.fontSize.xs }}>
                Caps Lock is on
              </p>
            )}
          </div>

          <div>
            <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
              Confirm Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                minLength={6}
                style={{ ...inputBaseStyle, paddingRight: '44px' }}
                onFocus={(e) => {
                  e.target.style.borderBottomColor = palette.colors.primary.cyan;
                  e.target.style.boxShadow = `0 2px 0 ${palette.colors.primary.cyan}`;
                }}
                onBlur={(e) => {
                  e.target.style.borderBottomColor = '#333333';
                  e.target.style.boxShadow = 'none';
                  setIsConfirmCapsLockOn(false);
                }}
                onKeyDown={handleConfirmPasswordKeyEvent}
                onKeyUp={handleConfirmPasswordKeyEvent}
              />
              <button
                type="button"
                onClick={handleToggleConfirmPasswordVisibility}
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
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
                <EyeIcon closed={showConfirmPassword} blinking={isConfirmEyeBlinking} />
              </button>
            </div>
            {isConfirmCapsLockOn && (
              <p style={{ marginTop: palette.spacing.xs, color: '#D1D5DB', fontSize: palette.typography.fontSize.xs }}>
                Caps Lock is on
              </p>
            )}
          </div>

          <div>
            <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
              Bio
            </label>
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows={3}
              placeholder="Tell us about yourself and your founding mindset..."
              style={{ ...inputBaseStyle, resize: 'vertical', fontFamily: palette.typography.fontFamily.primary }}
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

          <Button type="submit" loading={loading} fullWidth>
            {loading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>

        <p style={{
          marginTop: palette.spacing.lg,
          color: palette.colors.text.secondary,
          fontSize: palette.typography.fontSize.sm,
        }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: palette.colors.primary.cyan, textDecoration: 'none' }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Signup;
