import React, { useState } from 'react';
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
  const [downloadingResume, setDownloadingResume] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [vectorStatus, setVectorStatus] = useState(''); // 'indexing' | 'done' | ''
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];
    if (!validTypes.includes(file.type)) {
      setError('Only PDF and DOCX files are allowed');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setResume(file);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    setVectorStatus('');

    try {
      const skillsArray = formData.skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await profileAPI.updateProfile({
        ...formData,
        skills: skillsArray,
        experience_years: parseInt(formData.experience_years),
      });

      setSuccess('Profile saved successfully!');
      setVectorStatus('indexing');

      setTimeout(() => {
        setVectorStatus('done');
        onUpdate();
      }, 3500);
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
    setVectorStatus('');

    try {
      const formDataResume = new FormData();
      formDataResume.append('resume', resume);

      const response = await profileAPI.uploadResume(formDataResume);

      setSuccess('Resume uploaded and analysed successfully!');
      setVectorStatus('indexing');
      setResumeAnalysis(response.data.analysis);
      setResume(null);

      if (response.data.analysis?.merged_skills) {
        setFormData((prev) => ({
          ...prev,
          skills: response.data.analysis.merged_skills.join(', '),
        }));
      }

      setTimeout(() => {
        setVectorStatus('done');
        onUpdate();
      }, 3500);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload resume');
    } finally {
      setUploadingResume(false);
    }
  };

  const handleDownloadResume = async () => {
    setDownloadingResume(true);
    setError('');
    try {
      const response = await profileAPI.getResume(user._id);

      // Happy path — response.data is a Blob
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/pdf',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = user.resume || 'resume.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      // When the request fails with responseType:'blob', the error response body
      // is also a Blob. We must read it as text first, then parse as JSON to get
      // a human-readable error message.
      const responseData = err.response?.data;
      if (responseData instanceof Blob) {
        try {
          const text = await responseData.text();
          const json = JSON.parse(text);
          setError(json.error || 'Failed to download resume');
        } catch {
          setError('Failed to download resume');
        }
      } else {
        setError(err.response?.data?.error || 'Failed to download resume');
      }
    } finally {
      setDownloadingResume(false);
    }
  };

  const handleDeleteResume = async () => {
    if (!window.confirm('Are you sure you want to delete your resume?')) return;

    try {
      await profileAPI.deleteResume();
      setSuccess('Resume deleted successfully');
      setVectorStatus('indexing');
      setTimeout(() => {
        setVectorStatus('done');
        onUpdate();
      }, 3500);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete resume');
    }
  };

  const inputStyle = {
    width: '100%',
    padding: palette.spacing.md,
    backgroundColor: palette.colors.background.primary,
    border: `1px solid ${palette.colors.border.primary}`,
    borderRadius: palette.borderRadius.md,
    color: palette.colors.text.primary,
    fontSize: palette.typography.fontSize.base,
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    color: palette.colors.text.primary,
    fontSize: palette.typography.fontSize.sm,
    fontWeight: palette.typography.fontWeight.medium,
    marginBottom: palette.spacing.sm,
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: palette.spacing['2xl'] }}>
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
          <p style={{ fontSize: palette.typography.fontSize.base, color: palette.colors.text.secondary }}>
            Update your profile to improve your match quality
          </p>
        </div>

        {/* Error Banner */}
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

        {/* Success + Vector Status Banner */}
        {success && (
          <div style={{
            backgroundColor: 'rgba(201, 168, 76, 0.08)',
            border: `1px solid ${palette.colors.status.success}`,
            color: palette.colors.status.success,
            padding: palette.spacing.md,
            borderRadius: palette.borderRadius.md,
            marginBottom: palette.spacing.lg,
            display: 'flex',
            alignItems: 'center',
            gap: palette.spacing.md,
          }}>
            <span>✓ {success}</span>
            {vectorStatus === 'indexing' && (
              <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: palette.spacing.sm,
                color: palette.colors.text.secondary,
                fontSize: palette.typography.fontSize.sm,
              }}>
                <span style={{
                  display: 'inline-block',
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  border: `2px solid ${palette.colors.primary.cyan}`,
                  borderTopColor: 'transparent',
                  animation: 'spin 0.8s linear infinite',
                }} />
                Re-indexing your profile for matching…
              </span>
            )}
            {vectorStatus === 'done' && (
              <span style={{ color: palette.colors.primary.cyan, fontSize: palette.typography.fontSize.sm }}>
                ✦ Profile indexed — matches updated
              </span>
            )}
          </div>
        )}

        {/* ── Resume Section ── */}
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
            marginBottom: palette.spacing.sm,
          }}>
            Resume
          </h2>
          <p style={{
            color: palette.colors.text.secondary,
            marginBottom: palette.spacing.lg,
            fontSize: palette.typography.fontSize.sm,
          }}>
            Stored securely in MongoDB — accessible to all team members regardless of machine.
          </p>

          {/* Upload row */}
          <div style={{ display: 'flex', gap: palette.spacing.md, alignItems: 'center', marginBottom: palette.spacing.md, flexWrap: 'wrap' }}>
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={handleResumeChange}
              style={{
                flex: 1,
                minWidth: '200px',
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
              {uploadingResume ? 'Uploading...' : 'Upload & Analyse'}
            </Button>
          </div>

          {/* Current resume status */}
          {user.resume && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: palette.spacing.md,
              padding: palette.spacing.md,
              backgroundColor: 'rgba(201, 168, 76, 0.08)',
              borderRadius: palette.borderRadius.md,
              border: `1px solid ${palette.colors.primary.cyan}`,
              flexWrap: 'wrap',
            }}>
              <span style={{
                color: palette.colors.primary.cyan,
                fontSize: palette.typography.fontSize.sm,
                flex: 1,
                wordBreak: 'break-all',
              }}>
                ✓ {user.resume}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadResume}
                loading={downloadingResume}
              >
                {downloadingResume ? 'Downloading...' : 'Download'}
              </Button>

              <Button variant="secondary" size="sm" onClick={handleDeleteResume}>
                Delete
              </Button>
            </div>
          )}

          {/* Analysis results */}
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

              {resumeAnalysis.merged_skills?.length > 0 && (
                <div>
                  <p style={{
                    color: palette.colors.text.tertiary,
                    fontSize: palette.typography.fontSize.sm,
                    marginBottom: palette.spacing.sm,
                  }}>
                    Extracted Skills:
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: palette.spacing.xs }}>
                    {resumeAnalysis.merged_skills.map((skill, index) => (
                      <span key={index} style={{
                        backgroundColor: 'rgba(201, 168, 76, 0.1)',
                        color: palette.colors.primary.cyan,
                        padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
                        borderRadius: palette.borderRadius.md,
                        fontSize: palette.typography.fontSize.xs,
                      }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Profile Form ── */}
        <form onSubmit={handleSubmit}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: palette.spacing.lg,
            marginBottom: palette.spacing.lg,
          }}>
            <div>
              <label style={labelStyle}>Full Name *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
                onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
              />
            </div>

            <div>
              <label style={labelStyle}>Professional Title</label>
              <input
                type="text"
                name="professional_title"
                value={formData.professional_title}
                onChange={handleChange}
                placeholder="e.g. Senior Software Engineer"
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
                onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
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
              <label style={labelStyle}>Years of Experience</label>
              <input
                type="number"
                name="experience_years"
                value={formData.experience_years}
                onChange={handleChange}
                min="0"
                max="50"
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
                onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
              />
            </div>

            <div>
              <label style={labelStyle}>Location</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. San Francisco, CA"
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
                onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
              />
            </div>
          </div>

          <div style={{ marginBottom: palette.spacing.lg }}>
            <label style={labelStyle}>LinkedIn Profile</label>
            <input
              type="url"
              name="linkedin"
              value={formData.linkedin}
              onChange={handleChange}
              placeholder="https://linkedin.com/in/yourprofile"
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
              onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.lg }}>
            <label style={labelStyle}>Skills (comma-separated)</label>
            <textarea
              name="skills"
              value={formData.skills}
              onChange={handleChange}
              rows={3}
              placeholder="e.g. Python, React, Machine Learning, AWS"
              style={{ ...inputStyle, resize: 'vertical', fontFamily: palette.typography.fontFamily.primary }}
              onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
              onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
            />
          </div>

          <div style={{ marginBottom: palette.spacing.xl }}>
            <label style={labelStyle}>Bio</label>
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows={5}
              placeholder="Tell us about yourself and your professional journey..."
              style={{
                ...inputStyle,
                resize: 'vertical',
                fontFamily: palette.typography.fontFamily.primary,
                lineHeight: palette.typography.lineHeight.relaxed,
              }}
              onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
              onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
            />
          </div>

          <div style={{ display: 'flex', gap: palette.spacing.md, justifyContent: 'flex-end' }}>
            <Button type="button" variant="secondary" onClick={() => navigate('/dashboard')}>
              Cancel
            </Button>
            <Button type="submit" loading={loading} disabled={vectorStatus === 'indexing'}>
              {loading ? 'Saving...' : vectorStatus === 'indexing' ? 'Indexing...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>

      {/* Spin keyframe injected inline */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ProfileEdit;