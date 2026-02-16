import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const TeamView = ({ project, onBack }) => {
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (project && project._id) {
      fetchTeam();
    } else {
      setError('No project selected');
      setLoading(false);
    }
  }, [project]);

  const fetchTeam = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await collaborationAPI.getTeamMembers(project._id);
      setTeam(response.data);
    } catch (error) {
      console.error('Error fetching team:', error);
      setError(error.response?.data?.error || 'Failed to load team');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: palette.spacing.xl }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: `3px solid ${palette.colors.border.primary}`,
          borderTop: `3px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto',
        }}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        textAlign: 'center',
        padding: palette.spacing['2xl'],
        backgroundColor: palette.colors.background.secondary,
        borderRadius: palette.borderRadius.lg,
        border: `1px solid ${palette.colors.status.error}`,
      }}>
        <p style={{ color: palette.colors.status.error, marginBottom: palette.spacing.lg }}>
          {error}
        </p>
        {onBack && (
          <Button onClick={onBack} variant="secondary">
            Back to Projects
          </Button>
        )}
      </div>
    );
  }

  if (!team) {
    return (
      <div style={{
        textAlign: 'center',
        padding: palette.spacing['2xl'],
      }}>
        <p style={{ color: palette.colors.text.secondary }}>
          No team data available
        </p>
        {onBack && (
          <Button onClick={onBack} variant="secondary" style={{ marginTop: palette.spacing.lg }}>
            Back to Projects
          </Button>
        )}
      </div>
    );
  }

  const totalMembers = 1 + (team.team_members?.length || 0);

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: palette.spacing.xl,
      }}>
        <div>
          <h2 style={{
            fontSize: palette.typography.fontSize['2xl'],
            fontWeight: palette.typography.fontWeight.bold,
            marginBottom: palette.spacing.xs,
          }}>
            {team.project?.title || 'Team Members'}
          </h2>
          <p style={{
            color: palette.colors.text.secondary,
            fontSize: palette.typography.fontSize.sm,
          }}>
            {totalMembers} member{totalMembers !== 1 ? 's' : ''}
          </p>
        </div>
        <Button onClick={() => navigate(`/chat/${project._id}`)}>
          Open Team Chat
        </Button>
      </div>

      {/* Founder */}
      {team.founder && (
        <div style={{
          backgroundColor: palette.colors.background.secondary,
          border: `2px solid ${palette.colors.primary.cyan}`,
          borderRadius: palette.borderRadius.lg,
          padding: palette.spacing.xl,
          marginBottom: palette.spacing.lg,
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}>
            <div style={{ flex: 1 }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: palette.spacing.md,
                marginBottom: palette.spacing.sm,
              }}>
                <h3 style={{
                  fontSize: palette.typography.fontSize.xl,
                  fontWeight: palette.typography.fontWeight.bold,
                }}>
                  {team.founder.name}
                </h3>
                <span style={{
                  backgroundColor: palette.colors.primary.cyan,
                  color: palette.colors.background.primary,
                  padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
                  borderRadius: palette.borderRadius.full,
                  fontSize: palette.typography.fontSize.xs,
                  fontWeight: palette.typography.fontWeight.bold,
                }}>
                  FOUNDER
                </span>
              </div>
              <p style={{
                color: palette.colors.text.secondary,
                fontSize: palette.typography.fontSize.sm,
                marginBottom: palette.spacing.md,
              }}>
                {team.founder.professional_title || 'Project Founder'}
              </p>
              {team.founder.bio && (
                <p style={{
                  color: palette.colors.text.secondary,
                  fontSize: palette.typography.fontSize.sm,
                  lineHeight: palette.typography.lineHeight.relaxed,
                  marginBottom: palette.spacing.md,
                }}>
                  {team.founder.bio}
                </p>
              )}
              {team.founder.skills && team.founder.skills.length > 0 && (
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: palette.spacing.xs,
                }}>
                  {team.founder.skills.slice(0, 5).map((skill, index) => (
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
              )}
            </div>
          </div>
        </div>
      )}

      {/* Team Members */}
      {team.team_members && team.team_members.length > 0 ? (
        <div style={{
          display: 'grid',
          gap: palette.spacing.lg,
        }}>
          {team.team_members.map((member) => (
            <div
              key={member.user_id}
              style={{
                backgroundColor: palette.colors.background.secondary,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.lg,
                padding: palette.spacing.xl,
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{
                    fontSize: palette.typography.fontSize.xl,
                    fontWeight: palette.typography.fontWeight.bold,
                    marginBottom: palette.spacing.xs,
                  }}>
                    {member.name}
                  </h3>
                  <p style={{
                    color: palette.colors.text.secondary,
                    fontSize: palette.typography.fontSize.sm,
                    marginBottom: palette.spacing.md,
                  }}>
                    {member.professional_title || 'Team Member'}
                  </p>
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
                  {member.skills && member.skills.length > 0 && (
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: palette.spacing.xs,
                      marginBottom: palette.spacing.md,
                    }}>
                      {member.skills.slice(0, 5).map((skill, index) => (
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
                  )}
                  <p style={{
                    color: palette.colors.text.tertiary,
                    fontSize: palette.typography.fontSize.xs,
                  }}>
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{
          textAlign: 'center',
          padding: palette.spacing['2xl'],
          backgroundColor: palette.colors.background.secondary,
          borderRadius: palette.borderRadius.lg,
          border: `1px solid ${palette.colors.border.primary}`,
        }}>
          <div style={{ fontSize: '48px', marginBottom: palette.spacing.md }}>👥</div>
          <p style={{ color: palette.colors.text.secondary }}>
            No team members yet. Send collaboration requests to build your team!
          </p>
        </div>
      )}
    </div>
  );
};

export default TeamView;