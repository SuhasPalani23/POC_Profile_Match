import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { matchingAPI, projectAPI, collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const MatchList = ({ user }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sendingTo, setSendingTo] = useState(null);

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    try {
      const projectResponse = await projectAPI.getProject(projectId);
      setProject(projectResponse.data.project);

      const matchesResponse = await matchingAPI.getMatches(projectId);
      setMatches(matchesResponse.data.matches);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (candidateId, candidateName) => {
    setSendingTo(candidateId);
    try {
      await collaborationAPI.sendRequest({
        project_id: projectId,
        candidate_id: candidateId,
        message: `Hi! I'd love to have you join my project "${project.title}". Your skills would be a great fit for our team!`
      });
      alert(`Request sent to ${candidateName}!`);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to send request');
    } finally {
      setSendingTo(null);
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '80vh',
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: `4px solid ${palette.colors.border.primary}`,
          borderTop: `4px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        padding: palette.spacing['2xl'],
        textAlign: 'center',
      }}>
        <div style={{
          backgroundColor: palette.colors.background.secondary,
          borderRadius: palette.borderRadius.xl,
          border: `1px solid ${palette.colors.status.error}`,
          padding: palette.spacing['3xl'],
        }}>
          <div style={{
            fontSize: palette.typography.fontSize['6xl'],
            marginBottom: palette.spacing.lg,
          }}>
            ⚠️
          </div>
          <h2 style={{
            fontSize: palette.typography.fontSize['2xl'],
            fontWeight: palette.typography.fontWeight.bold,
            color: palette.colors.status.error,
            marginBottom: palette.spacing.md,
          }}>
            {error}
          </h2>
          <Button onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '1400px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      <div style={{ marginBottom: palette.spacing['2xl'] }}>
        <Button 
          variant="secondary" 
          onClick={() => navigate('/dashboard')}
          style={{ marginBottom: palette.spacing.lg }}
        >
          ← Back to Dashboard
        </Button>
        
        <h1 style={{
          fontSize: palette.typography.fontSize['4xl'],
          fontWeight: palette.typography.fontWeight.black,
          marginBottom: palette.spacing.md,
        }}>
          <span className="gradient-text">Top Matches</span>
        </h1>
        
        {project && (
          <div style={{
            backgroundColor: palette.colors.background.secondary,
            borderRadius: palette.borderRadius.lg,
            border: `1px solid ${palette.colors.border.primary}`,
            padding: palette.spacing.xl,
            marginTop: palette.spacing.lg,
          }}>
            <h2 style={{
              fontSize: palette.typography.fontSize.xl,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.sm,
            }}>
              {project.title}
            </h2>
            <p style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.base,
              lineHeight: palette.typography.lineHeight.relaxed,
            }}>
              {project.description.substring(0, 200)}...
            </p>
          </div>
        )}
      </div>

      {matches.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: palette.spacing['3xl'],
          backgroundColor: palette.colors.background.secondary,
          borderRadius: palette.borderRadius.xl,
          border: `1px solid ${palette.colors.border.primary}`,
        }}>
          <div style={{
            fontSize: palette.typography.fontSize['6xl'],
            marginBottom: palette.spacing.lg,
          }}>
            🔍
          </div>
          <h3 style={{
            fontSize: palette.typography.fontSize['2xl'],
            fontWeight: palette.typography.fontWeight.semibold,
            marginBottom: palette.spacing.md,
          }}>
            No Matches Found
          </h3>
          <p style={{
            color: palette.colors.text.secondary,
            fontSize: palette.typography.fontSize.lg,
          }}>
            We couldn't find suitable matches at this time.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: palette.spacing.xl }}>
          {matches.map((match, index) => (
            <div
              key={match.user_id}
              style={{
                backgroundColor: palette.colors.background.secondary,
                border: `2px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.xl,
                padding: palette.spacing.xl,
              }}
            >
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: palette.spacing.xl,
                alignItems: 'start',
              }}>
                {/* Rank & Match % */}
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    fontSize: palette.typography.fontSize['4xl'],
                    fontWeight: palette.typography.fontWeight.black,
                    color: palette.colors.primary.cyan,
                  }}>
                    {match.match_percentage}%
                  </div>
                  <div style={{
                    fontSize: palette.typography.fontSize.xs,
                    color: palette.colors.text.tertiary,
                  }}>
                    #{index + 1} MATCH
                  </div>
                </div>

                {/* Candidate Info */}
                <div>
                  <h3 style={{
                    fontSize: palette.typography.fontSize['2xl'],
                    fontWeight: palette.typography.fontWeight.bold,
                    marginBottom: palette.spacing.sm,
                  }}>
                    {match.name}
                  </h3>
                  
                  <p style={{
                    color: palette.colors.text.secondary,
                    fontSize: palette.typography.fontSize.sm,
                    marginBottom: palette.spacing.md,
                  }}>
                    {match.role}
                  </p>

                  {/* Skills */}
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: palette.spacing.xs,
                    marginBottom: palette.spacing.md,
                  }}>
                    {match.skills.slice(0, 6).map((skill, idx) => (
                      <span
                        key={idx}
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

                  {/* Reasoning */}
                  <div style={{
                    backgroundColor: palette.colors.background.primary,
                    padding: palette.spacing.md,
                    borderRadius: palette.borderRadius.md,
                    marginBottom: palette.spacing.md,
                  }}>
                    <p style={{
                      fontSize: palette.typography.fontSize.sm,
                      color: palette.colors.text.secondary,
                      lineHeight: palette.typography.lineHeight.relaxed,
                    }}>
                      {match.reasoning}
                    </p>
                  </div>

                  {/* Strengths */}
                  {match.strengths && match.strengths.length > 0 && (
                    <div style={{ marginBottom: palette.spacing.sm }}>
                      <p style={{
                        fontSize: palette.typography.fontSize.xs,
                        color: palette.colors.status.success,
                        fontWeight: palette.typography.fontWeight.semibold,
                        marginBottom: palette.spacing.xs,
                      }}>
                        ✓ Strengths
                      </p>
                      <ul style={{
                        listStyle: 'none',
                        padding: 0,
                        margin: 0,
                      }}>
                        {match.strengths.slice(0, 3).map((strength, idx) => (
                          <li
                            key={idx}
                            style={{
                              fontSize: palette.typography.fontSize.xs,
                              color: palette.colors.text.secondary,
                              marginBottom: palette.spacing.xs,
                            }}
                          >
                            • {strength}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <Button
                  onClick={() => handleSendRequest(match.user_id, match.name)}
                  loading={sendingTo === match.user_id}
                  disabled={sendingTo !== null}
                >
                  Send Request
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MatchList;