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
        .map(skill => skill.trim())
        .filter(skill => skill);

      const response = await projectAPI.create({
        title: formData.title,
        description: formData.description,
        required_skills: skillsArray,
      });

      // Wait for 10 seconds (simulating review process)
      setTimeout(async () => {
        await onSubmit(); // Refresh user data
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
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        padding: palette.spacing['2xl'],
      }}>
        <div style={{
          backgroundColor: palette.colors.background.secondary,
          borderRadius: palette.borderRadius.xl,
          border: `1px solid ${palette.colors.border.primary}`,
          padding: palette.spacing['2xl'],
        }}>
          <LoadingAnimation 
            message="Reviewing Your Vision" 
            duration={10000}
          />
        </div>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      <div style={{
        backgroundColor: palette.colors.background.secondary,
        borderRadius: palette.borderRadius.xl,
        border: `1px solid ${palette.colors.border.primary}`,
        padding: palette.spacing['2xl'],
      }}>
        <div style={{ textAlign: 'center', marginBottom: palette.spacing['2xl'] }}>
          <h1 style={{
            fontSize: palette.typography.fontSize['4xl'],
            fontWeight: palette.typography.fontWeight.black,
            marginBottom: palette.spacing.md,
          }}>
            <span className="gradient-text">Submit Your Vision</span>
          </h1>
          <p style={{
            fontSize: palette.typography.fontSize.lg,
            color: palette.colors.text.secondary,
          }}>
            Share your startup idea and let AI find your perfect co-founders
          </p>
        </div>

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
              fontSize: palette.typography.fontSize.base,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.sm,
            }}>
              Project Title *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="e.g., AI-Powered Healthcare Platform"
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

          <div style={{ marginBottom: palette.spacing.lg }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.base,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.sm,
            }}>
              Project Description * (minimum 500 characters)
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              required
              rows={12}
              placeholder="Describe your startup vision, the problem you're solving, your target market, unique value proposition, and what kind of team members you're looking for..."
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
                lineHeight: palette.typography.lineHeight.relaxed,
              }}
              onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
              onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
            />
            <div style={{
              marginTop: palette.spacing.sm,
              fontSize: palette.typography.fontSize.sm,
              color: formData.description.length >= 500 
                ? palette.colors.status.success 
                : palette.colors.text.tertiary,
            }}>
              {formData.description.length} / 500 characters
            </div>
          </div>

          <div style={{ marginBottom: palette.spacing.xl }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.base,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.sm,
            }}>
              Required Skills (comma-separated)
            </label>
            <input
              type="text"
              name="required_skills"
              value={formData.required_skills}
              onChange={handleChange}
              placeholder="e.g., Machine Learning, React, AWS, Product Management"
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

          <div style={{
            display: 'flex',
            gap: palette.spacing.md,
            justifyContent: 'flex-end',
          }}>
            <Button 
              type="button" 
              variant="secondary" 
              onClick={() => navigate('/dashboard')}
            >
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {loading ? 'Submitting...' : 'Submit for Review'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default IdeaSubmission;