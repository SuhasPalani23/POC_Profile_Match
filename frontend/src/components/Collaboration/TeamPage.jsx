import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const TeamPage = ({ user }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    collaborationAPI.getTeamMembers(projectId)
      .then(r => setTeam(r.data))
      .catch(e => setError(e.response?.data?.error || 'Failed to load team'))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="cinematic-loader" style={{ minHeight: '70vh' }}>
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center' }}>
          <div className="pulse-ring" style={{ margin: '0 auto 1rem auto' }} />
          <p className="mono-label">Loading team</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: '600px', margin: '4rem auto', padding: palette.spacing['2xl'], textAlign: 'center' }}>
        <div className="surface-card" style={{ borderRadius: palette.borderRadius.xl, padding: palette.spacing['2xl'] }}>
          <p style={{ color: palette.colors.status.error, marginBottom: palette.spacing.lg }}>{error}</p>
          <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  const isFounder = team.founder.user_id === user._id;
  const totalMembers = 1 + (team.team_members?.length || 0);

  const MemberCard = ({ member, isFounderCard = false }) => (
    <div className="surface-card" style={{
      borderRadius: palette.borderRadius.lg,
      padding: palette.spacing.xl,
      border: isFounderCard ? `2px solid ${palette.colors.primary.cyan}` : `1px solid ${palette.colors.border.primary}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: palette.spacing.md, marginBottom: palette.spacing.sm }}>
        <h3 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize.xl }}>
          {member.name}
        </h3>
        {isFounderCard && (
          <span style={{
            backgroundColor: palette.colors.primary.cyan,
            color: palette.colors.background.primary,
            padding: `2px ${palette.spacing.sm}`,
            borderRadius: palette.borderRadius.full,
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '0.12em',
          }}>
            FOUNDER
          </span>
        )}
        {member.user_id === user._id && !isFounderCard && (
          <span style={{
            border: `1px solid ${palette.colors.border.secondary}`,
            color: palette.colors.text.tertiary,
            padding: `2px ${palette.spacing.sm}`,
            borderRadius: palette.borderRadius.full,
            fontSize: 10,
            letterSpacing: '0.12em',
          }}>
            YOU
          </span>
        )}
      </div>

      {member.professional_title && (
        <p style={{ color: palette.colors.text.secondary, fontSize: palette.typography.fontSize.sm, marginBottom: palette.spacing.sm }}>
          {member.professional_title}
        </p>
      )}

      {member.bio && (
        <p style={{
          color: palette.colors.text.secondary,
          fontSize: palette.typography.fontSize.sm,
          lineHeight: palette.typography.lineHeight.relaxed,
          marginBottom: palette.spacing.md,
        }}>
          {member.bio}
        </p>
      )}

      {member.skills?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: palette.spacing.xs, marginBottom: palette.spacing.md }}>
          {member.skills.map((skill, i) => (
            <span key={i} style={{
              border: `1px solid ${isFounderCard ? palette.colors.primary.cyan : palette.colors.border.primary}`,
              color: isFounderCard ? palette.colors.primary.cyan : palette.colors.text.tertiary,
              padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
              borderRadius: palette.borderRadius.md,
              fontSize: palette.typography.fontSize.xs,
            }}>
              {skill}
            </span>
          ))}
        </div>
      )}

      {member.email && (
        <p style={{ color: palette.colors.text.tertiary, fontSize: palette.typography.fontSize.xs }}>{member.email}</p>
      )}
    </div>
  );

  return (
    <div style={{
      maxWidth: '900px',
      margin: '0 auto',
      padding: `${palette.spacing['2xl']} clamp(1rem, 3vw, 2rem)`,
    }}>
      <Button variant="secondary" onClick={() => navigate('/dashboard')} style={{ marginBottom: palette.spacing.xl }}>
        ← Back to Dashboard
      </Button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: palette.spacing['2xl'], flexWrap: 'wrap', gap: palette.spacing.md }}>
        <div>
          <p className="mono-label">Team</p>
          <h1 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize['4xl'], lineHeight: 1 }}>
            {team.project?.title}
          </h1>
          <p style={{ color: palette.colors.text.secondary, marginTop: 4 }}>
            {totalMembers} member{totalMembers !== 1 ? 's' : ''}
          </p>
        </div>
        <Button onClick={() => navigate(`/chat/${projectId}`)}>
          Open Team Chat
        </Button>
      </div>

      {/* Founder */}
      <MemberCard member={team.founder} isFounderCard />

      {/* Members */}
      <div style={{ marginTop: palette.spacing.lg, display: 'grid', gap: palette.spacing.lg }}>
        {team.team_members?.length > 0 ? (
          team.team_members.map(m => <MemberCard key={m.user_id} member={m} />)
        ) : (
          <div className="surface-card" style={{ borderRadius: palette.borderRadius.lg, padding: palette.spacing['2xl'], textAlign: 'center' }}>
            <p style={{ color: palette.colors.text.secondary }}>No other team members yet.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamPage;