import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const UserDashboard = ({ user }) => {
  const navigate = useNavigate();
  const [myProjects, setMyProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  useEffect(() => {
    collaborationAPI.getMyProjects()
      .then(r => setMyProjects(r.data.projects || []))
      .catch(() => {})
      .finally(() => setLoadingProjects(false));
  }, []);

  const handleLeaveProject = async (collaborationId, projectTitle) => {
    if (!window.confirm(`Leave "${projectTitle}"?`)) return;
    try {
      await collaborationAPI.leaveProject(collaborationId);
      setMyProjects(prev => prev.filter(p => p.collaboration_id !== collaborationId));
    } catch {
      alert('Failed to leave project');
    }
  };

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: `${palette.spacing['2xl']} clamp(1rem, 3vw, 2rem)`,
    }}>
      {/* Hero */}
      <section style={{ minHeight: '44vh', display: 'grid', alignItems: 'end', marginBottom: palette.spacing['2xl'] }}>
        <div>
          <p className="mono-label">Candidate workspace</p>
          <h1 className="hero-title" style={{ marginTop: palette.spacing.sm }}>
            <span className="word-rise word-delay-1">Welcome</span>
            <br />
            <span className="word-rise word-delay-2 gradient-text">{user.name}</span>
          </h1>
          <p style={{ marginTop: palette.spacing.md, color: palette.colors.text.secondary, maxWidth: '620px' }}>
            Position your profile, align your skills, and receive founder project invites with measurable fit.
          </p>
          <div style={{
            marginTop: palette.spacing.xl,
            height: '1px',
            backgroundColor: palette.colors.border.primary,
            transform: 'scaleX(0)',
          }} className="rule-draw" />
        </div>
      </section>

      {/* ── My Teams ── */}
      <section style={{ marginBottom: palette.spacing['2xl'] }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: palette.spacing.lg }}>
          <div>
            <p className="mono-label">Active Memberships</p>
            <h2 style={{
              fontFamily: palette.typography.fontFamily.display,
              fontSize: palette.typography.fontSize['3xl'],
              marginTop: 4,
            }}>
              My Teams
            </h2>
          </div>
        </div>

        {loadingProjects ? (
          <div style={{ textAlign: 'center', padding: palette.spacing.xl }}>
            <div className="pulse-ring" style={{ margin: '0 auto' }} />
          </div>
        ) : myProjects.length === 0 ? (
          <div className="surface-card" style={{
            borderRadius: palette.borderRadius.lg,
            padding: palette.spacing['2xl'],
            textAlign: 'center',
          }}>
            <p style={{ fontSize: '2.5rem', marginBottom: palette.spacing.md }}></p>
            <p style={{ color: palette.colors.text.secondary, marginBottom: palette.spacing.md }}>
              You haven't joined any teams yet. Accept a collaboration request to get started.
            </p>
            <Button variant="secondary" onClick={() => navigate('/requests')}>
              View Collaboration Requests
            </Button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: palette.spacing.lg }}>
            {myProjects.map(item => (
              <div
                key={item.collaboration_id}
                className="surface-card"
                style={{ borderRadius: palette.borderRadius.lg, padding: palette.spacing.xl }}
              >
                {/* Project title & founder */}
                <div style={{ marginBottom: palette.spacing.md }}>
                  <h3 style={{
                    fontFamily: palette.typography.fontFamily.display,
                    fontSize: palette.typography.fontSize['2xl'],
                    marginBottom: palette.spacing.xs,
                  }}>
                    {item.project.title}
                  </h3>
                  <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.tertiary }}>
                    Founded by <span style={{ color: palette.colors.primary.cyan }}>{item.founder.name}</span>
                  </p>
                  {item.joined_at && (
                    <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.tertiary }}>
                      Joined {new Date(item.joined_at).toLocaleDateString()}
                    </p>
                  )}
                </div>

                {/* Description preview */}
                <p style={{
                  color: palette.colors.text.secondary,
                  fontSize: palette.typography.fontSize.sm,
                  lineHeight: palette.typography.lineHeight.relaxed,
                  marginBottom: palette.spacing.lg,
                  overflow: 'hidden',
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                }}>
                  {item.project.description}
                </p>

                {/* Actions */}
                <div style={{ display: 'flex', gap: palette.spacing.sm, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Button
                    size="sm"
                    onClick={() => navigate(`/chat/${item.project._id}`)}
                  >
                    Team Chat
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/team/${item.project._id}`)}
                  >
                    View Team
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleLeaveProject(item.collaboration_id, item.project.title)}
                    style={{ borderColor: palette.colors.status.error, color: palette.colors.status.error }}
                  >
                    Leave
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Founder mode CTA */}
      <div className="surface-card" style={{ borderRadius: palette.borderRadius.xl, padding: palette.spacing['2xl'], marginBottom: palette.spacing.xl }}>
        <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Founder mode</p>
        <h2 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize['3xl'], marginBottom: palette.spacing.md }}>
          Ready to launch your own startup brief?
        </h2>
        <p style={{ color: palette.colors.text.secondary, marginBottom: palette.spacing.lg, maxWidth: '700px' }}>
          Submit an idea and let the matching engine find team members whose skill graph complements your vision.
        </p>
        <Button onClick={() => navigate('/submit-idea')} size="lg">Submit Your Idea</Button>
      </div>

      {/* Platform capabilities */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: palette.spacing.xl, marginBottom: palette.spacing['2xl'] }}>
        {[
          { title: 'AI-Powered Matching', description: 'Compatibility scoring tuned for startup execution, not vanity metrics.' },
          { title: 'Instant Results', description: 'Top candidate set surfaced quickly with rationale and strengths.' },
          { title: 'Team Formation', description: 'Send requests, build a team, and move directly into collaboration chat.' },
        ].map(card => (
          <div key={card.title} className="surface-card" style={{ borderRadius: palette.borderRadius.lg, padding: palette.spacing.xl }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Capability</p>
            <h3 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize['2xl'], marginBottom: palette.spacing.sm }}>
              {card.title}
            </h3>
            <p style={{ color: palette.colors.text.secondary, fontSize: palette.typography.fontSize.sm, lineHeight: palette.typography.lineHeight.relaxed }}>
              {card.description}
            </p>
          </div>
        ))}
      </div>

      {/* Profile snapshot */}
      <div className="surface-card" style={{ borderRadius: palette.borderRadius.xl, padding: palette.spacing['2xl'] }}>
        <h3 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize['3xl'], marginBottom: palette.spacing.lg }}>
          Profile Snapshot
        </h3>
        <div style={{ display: 'grid', gap: palette.spacing.lg }}>
          <div>
            <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Email</p>
            <p>{user.email}</p>
          </div>
          {user.professional_title && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Title</p>
              <p>{user.professional_title}</p>
            </div>
          )}
          {user.location && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Location</p>
              <p style={{ color: palette.colors.text.secondary }}>{user.location}</p>
            </div>
          )}
          {user.experience_years > 0 && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Experience</p>
              <p style={{ color: palette.colors.text.secondary }}>{user.experience_years} years</p>
            </div>
          )}
          {user.bio && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Bio</p>
              <p style={{ color: palette.colors.text.secondary, lineHeight: palette.typography.lineHeight.relaxed }}>{user.bio}</p>
            </div>
          )}
          {user.skills && user.skills.length > 0 && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Skills ({user.skills.length})</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: palette.spacing.sm }}>
                {user.skills.map((skill, index) => (
                  <span key={index} style={{
                    border: `1px solid ${palette.colors.border.primary}`,
                    color: palette.colors.text.tertiary,
                    padding: `${palette.spacing.xs} ${palette.spacing.md}`,
                    borderRadius: palette.borderRadius.full,
                    fontSize: palette.typography.fontSize.xs,
                  }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
          {user.linkedin && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>LinkedIn</p>
              <a href={user.linkedin} target="_blank" rel="noopener noreferrer"
                style={{ color: palette.colors.primary.cyan, fontSize: palette.typography.fontSize.sm }}>
                {user.linkedin}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;