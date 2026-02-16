import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const ProfileEdit = ({ user, onUpdate }) => {
  const [formData, setFormData] = useState({
    name: user.name || '',
    bio: user.bio || '',
    skills: (user.skills || []).join(', '),
    linkedin: user.linkedin || '',
    professional_title: user.professional_title || '',
    experience_years: user.experience_years || 0,
    location: user.location || '',
  });
  
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!validTypes.includes(file.type)) {
        setError('Only PDF and DOCX files are allowed');
        return;
      }
      
      // Validate file size (10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setResume(file);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const skillsArray = formData.skills
        .split(',')
        .map(skill => skill.trim())
        .filter(skill => skill);

      const updateData = {
        ...formData,
        skills: skillsArray,
        experience_years: parseInt(formData.experience_years)
      };

      const response = await profileAPI.updateProfile(updateData);
      
      setSuccess('Profile updated successfully! Vectors are being updated...');
      setTimeout(() => {
        onUpdate();
      }, 1500);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async () => {
    if (!resume) {
      setError('Please select a resume file');
      return;
    }

    setUploadingResume(true);
    setError('');

    try {
      const formDataResume = new FormData();
      formDataResume.append('resume', resume);

      const response = await profileAPI.uploadResume(formDataResume);
      
      setSuccess('Resume uploaded and analyzed successfully!');
      setResumeAnalysis(response.data.analysis);
      setResume(null);
      
      // Update form with extracted data
      if (response.data.analysis.merged_skills) {
        setFormData(prev => ({
          ...prev,
          skills: response.data.analysis.merged_skills.join(', ')
        }));
      }
      
      setTimeout(() => {
        onUpdate();
      }, 1500);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload resume');
    } finally {
      setUploadingResume(false);
    }
  };

  const handleDeleteResume = async () => {
    if (!window.confirm('Are you sure you want to delete your resume?')) {
      return;
    }

    try {
      await profileAPI.deleteResume();
      setSuccess('Resume deleted successfully');
      setTimeout(() => {
        onUpdate();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete resume');
    }
  };

  return (
    <div style={{
      maxWidth: '900px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      <div style={{
        backgroundColor: palette.colors.background.secondary,
        borderRadius: palette.borderRadius.xl,
        border: `1px solid ${palette.colors.border.primary}`,
        padding: palette.spacing['2xl'],
      }}>
        <div style={{ marginBottom: palette.spacing['2xl'] }}>
          <h1 style={{
            fontSize: palette.typography.fontSize['3xl'],
            fontWeight: palette.typography.fontWeight.black,
            marginBottom: palette.spacing.sm,
          }}>
            <span className="gradient-text">Edit Profile</span>
          </h1>
          <p style={{
            fontSize: palette.typography.fontSize.base,
            color: palette.colors.text.secondary,
          }}>
            Update your profile to improve your match quality
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
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: `1px solid ${palette.colors.status.success}`,
            color: palette.colors.status.success,
            padding: palette.spacing.md,
            borderRadius: palette.borderRadius.md,
            marginBottom: palette.spacing.lg,
          }}>
            {success}
          </div>
        )}

        {/* Resume Upload Section */}
        <div style={{
          backgroundColor: palette.colors.background.primary,
          borderRadius: palette.borderRadius.lg,
          padding: palette.spacing.xl,
          marginBottom: palette.spacing.xl,
          border: `1px solid ${palette.colors.border.primary}`,
        }}>
          <h2 style={{
            fontSize: palette.typography.fontSize.xl,
            fontWeight: palette.typography.fontWeight.semibold,
            marginBottom: palette.spacing.md,
          }}>
            Resume Upload
          </h2>
          <p style={{
            color: palette.colors.text.secondary,
            marginBottom: palette.spacing.lg,
            fontSize: palette.typography.fontSize.sm,
          }}>
            Upload your resume for AI-powered analysis and skill extraction
          </p>

          <div style={{ display: 'flex', gap: palette.spacing.md, alignItems: 'center', marginBottom: palette.spacing.md }}>
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={handleResumeChange}
              style={{
                flex: 1,
                padding: palette.spacing.md,
                backgroundColor: palette.colors.background.secondary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.md,
                color: palette.colors.text.primary,
              }}
            />
            <Button
              onClick={handleResumeUpload}
              loading={uploadingResume}
              disabled={!resume}
            >
              {uploadingResume ? 'Uploading...' : 'Upload & Analyze'}
            </Button>
          </div>

          {user.resume && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: palette.spacing.md,
              padding: palette.spacing.md,
              backgroundColor: 'rgba(19, 239, 183, 0.1)',
              borderRadius: palette.borderRadius.md,
              border: `1px solid ${palette.colors.primary.cyan}`,
            }}>
              <span style={{
                color: palette.colors.primary.cyan,
                fontSize: palette.typography.fontSize.sm,
                flex: 1,
              }}>
                ✓ Resume uploaded
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDeleteResume}
              >
                Delete
              </Button>
            </div>
          )}

          {resumeAnalysis && (
            <div style={{
              marginTop: palette.spacing.lg,
              padding: palette.spacing.lg,
              backgroundColor: palette.colors.background.secondary,
              borderRadius: palette.borderRadius.md,
              border: `1px solid ${palette.colors.border.primary}`,
            }}>
              <h3 style={{
                fontSize: palette.typography.fontSize.base,
                fontWeight: palette.typography.fontWeight.semibold,
                marginBottom: palette.spacing.md,
              }}>
                Resume Analysis Results
              </h3>
              {resumeAnalysis.ai_insights?.summary && (
                <p style={{
                  color: palette.colors.text.secondary,
                  fontSize: palette.typography.fontSize.sm,
                  lineHeight: palette.typography.lineHeight.relaxed,
                  marginBottom: palette.spacing.md,
                }}>
                  {resumeAnalysis.ai_insights.summary}
                </p>
              )}
              {resumeAnalysis.merged_skills && (
                <div>
                  <p style={{
                    color: palette.colors.text.tertiary,
                    fontSize: palette.typography.fontSize.sm,
                    marginBottom: palette.spacing.sm,
                  }}>
                    Extracted Skills:
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: palette.spacing.xs }}>
                    {resumeAnalysis.merged_skills.slice(0, 10).map((skill, index) => (
                      <span
                        key={index}
                        style={{
                          backgroundColor: 'rgba(19, 239, 183, 0.1)',
                          color: palette.colors.primary.cyan,
                          padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
                          borderRadius: palette.borderRadius.md,
                          fontSize: palette.typography.fontSize.xs,
                        }}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Profile Form */}
        <form onSubmit={handleSubmit}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: palette.spacing.lg,
            marginBottom: palette.spacing.lg,
          }}>
            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.sm,
                fontWeight: palette.typography.fontWeight.medium,
                marginBottom: palette.spacing.sm,
              }}>
                Full Name *
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

            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.sm,
                fontWeight: palette.typography.fontWeight.medium,
                marginBottom: palette.spacing.sm,
              }}>
                Professional Title
              </label>
              <input
                type="text"
                name="professional_title"
                value={formData.professional_title}
                onChange={handleChange}
                placeholder="e.g., Senior Software Engineer"
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
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: palette.spacing.lg,
            marginBottom: palette.spacing.lg,
          }}>
            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.sm,
                fontWeight: palette.typography.fontWeight.medium,
                marginBottom: palette.spacing.sm,
              }}>
                Years of Experience
              </label>
              <input
                type="number"
                name="experience_years"
                value={formData.experience_years}
                onChange={handleChange}
                min="0"
                max="50"
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

            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.sm,
                fontWeight: palette.typography.fontWeight.medium,
                marginBottom: palette.spacing.sm,
              }}>
                Location
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g., San Francisco, CA"
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
          </div>

          <div style={{ marginBottom: palette.spacing.lg }}>
            <label style={{
              display: 'block',
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              LinkedIn Profile
            </label>
            <input
              type="url"
              name="linkedin"
              value={formData.linkedin}
              onChange={handleChange}
              placeholder="https://linkedin.com/in/yourprofile"
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
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.sm,
            }}>
              Skills (comma-separated)
            </label>
            <textarea
              name="skills"
              value={formData.skills}
              onChange={handleChange}
              rows={3}
              placeholder="e.g., Python, React, Machine Learning, AWS"
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
              rows={5}
              placeholder="Tell us about yourself and your professional journey..."
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
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEdit;