import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI } from '../../services/api';
import Button from '../Common/Button';
import LoadingAnimation from '../Common/LoadingAnimation';
import palette from '../../palette';

const IdeaSubmission = ({ user, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
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

    if (formData.description.length < 500) {
      setError('Description must be at least 500 characters');
      return;
    }

    setLoading(true);
    setSubmitting(true);

    try {
      const skillsArray = formData.required_skills
        .split(',')
        .map((skill) => skill.trim())
        .filter((skill) => skill);

      const response = await projectAPI.create({
        title: formData.title,
        description: formData.description,
        required_skills: skillsArray,
      });

      setTimeout(async () => {
        await onSubmit();
        navigate(`/matches/${response.data.project._id}`);
      }, 10000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit project');
      setLoading(false);
      setSubmitting(false);
    }
  };

  if (submitting) {
    return (
      <div style={{ maxWidth: '560px', margin: '0 auto', padding: palette.spacing['2xl'] }}>
        <LoadingAnimation message="Reviewing your vision and calibrating fit models." duration={10000} />
      </div>
    );
  }

  const inputStyle = {
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
      maxWidth: '560px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      <p className="mono-label" style={{ marginBottom: palette.spacing.md }}>Founder Submission</p>
      <h1 style={{
        fontFamily: palette.typography.fontFamily.display,
        fontSize: palette.typography.fontSize['4xl'],
        marginBottom: palette.spacing.md,
      }}>
        Submit Your Startup Vision
      </h1>
      <p style={{
        color: palette.colors.text.secondary,
        marginBottom: palette.spacing.xl,
      }}>
        Build the brief that drives your match pipeline.
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

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: palette.spacing.xl }}>
        <div>
          <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
            Project Title *
          </label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            style={inputStyle}
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

        <div>
          <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
            Project Description * (minimum 500 characters)
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            rows={12}
            style={{ ...inputStyle, resize: 'vertical', fontFamily: palette.typography.fontFamily.primary }}
            onFocus={(e) => {
              e.target.style.borderBottomColor = palette.colors.primary.cyan;
              e.target.style.boxShadow = `0 2px 0 ${palette.colors.primary.cyan}`;
            }}
            onBlur={(e) => {
              e.target.style.borderBottomColor = '#333333';
              e.target.style.boxShadow = 'none';
            }}
          />
          <div style={{
            marginTop: palette.spacing.sm,
            fontSize: palette.typography.fontSize.sm,
            color: formData.description.length >= 500 ? palette.colors.primary.cyan : palette.colors.text.tertiary,
          }}>
            {formData.description.length} / 500 characters
          </div>
        </div>

        <div>
          <label className="mono-label" style={{ display: 'block', marginBottom: palette.spacing.sm }}>
            Required Skills (comma-separated)
          </label>
          <input
            type="text"
            name="required_skills"
            value={formData.required_skills}
            onChange={handleChange}
            style={inputStyle}
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

        <div style={{ display: 'flex', gap: palette.spacing.md, justifyContent: 'flex-end' }}>
          <Button type="button" variant="secondary" onClick={() => navigate('/dashboard')}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            {loading ? 'Submitting...' : 'Submit for Review'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default IdeaSubmission;
