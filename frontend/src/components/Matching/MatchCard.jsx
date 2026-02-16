import React, { useState } from 'react';
import Button from '../Common/Button';
import palette from '../../palette';

const MatchCard = ({ match, rank, onSendRequest }) => {
  const [expanded, setExpanded] = useState(false);
  const [requestSent, setRequestSent] = useState(false);

  const getMatchColor = (percentage) => {
    if (percentage >= 80) return palette.colors.status.success;
    if (percentage >= 60) return palette.colors.primary.cyan;
    if (percentage >= 40) return palette.colors.status.warning;
    return palette.colors.status.error;
  };

  const handleSendRequest = async () => {
    await onSendRequest(match.user_id);
    setRequestSent(true);
  };

  return (
    <div style={{
      backgroundColor: palette.colors.background.secondary,
      border: `2px solid ${palette.colors.border.primary}`,
      borderRadius: palette.borderRadius.xl,
      padding: palette.spacing.xl,
      transition: `all ${palette.transitions.normal}`,
      position: 'relative',
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = palette.colors.primary.cyan;
      e.currentTarget.style.boxShadow = palette.shadows.glow;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = palette.colors.border.primary;
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      {/* Rank Badge */}
      <div style={{
        position: 'absolute',
        top: '-12px',
        left: palette.spacing.xl,
        backgroundColor: palette.colors.background.primary,
        border: `2px solid ${palette.colors.primary.cyan}`,
        borderRadius: palette.borderRadius.full,
        width: '40px',
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: palette.typography.fontWeight.bold,
        fontSize: palette.typography.fontSize.lg,
        color: palette.colors.primary.cyan,
      }}>
        #{rank}
      </div>

      {/* Main Content */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        gap: palette.spacing.xl,
        alignItems: 'start',
        marginTop: palette.spacing.md,
      }}>
        {/* Match Percentage Circle */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}>
          <div style={{
            position: 'relative',
            width: '100px',
            height: '100px',
          }}>
            <svg width="100" height="100" style={{ transform: 'rotate(-90deg)' }}>
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={palette.colors.border.primary}
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={getMatchColor(match.match_percentage)}
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 45}`}
                strokeDashoffset={`${2 * Math.PI * 45 * (1 - match.match_percentage / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: palette.typography.fontSize.xl,
              fontWeight: palette.typography.fontWeight.black,
              color: getMatchColor(match.match_percentage),
            }}>
              {match.match_percentage}%
            </div>
          </div>
          <span style={{
            marginTop: palette.spacing.sm,
            fontSize: palette.typography.fontSize.xs,
            color: palette.colors.text.tertiary,
            fontWeight: palette.typography.fontWeight.medium,
          }}>
            MATCH
          </span>
        </div>

        {/* Candidate Info */}
        <div>
          <h3 style={{
            fontSize: palette.typography.fontSize['2xl'],
            fontWeight: palette.typography.fontWeight.bold,
            marginBottom: palette.spacing.xs,
            color: palette.colors.text.primary,
          }}>
            {match.name}
          </h3>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: palette.spacing.md,
            marginBottom: palette.spacing.md,
          }}>
            <span style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
            }}>
              {match.email}
            </span>
            <span style={{
              backgroundColor: 'rgba(14, 165, 233, 0.1)',
              color: palette.colors.primary.blue,
              padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
              borderRadius: palette.borderRadius.md,
              fontSize: palette.typography.fontSize.xs,
              fontWeight: palette.typography.fontWeight.semibold,
              textTransform: 'uppercase',
            }}>
              {match.role}
            </span>
          </div>

          {/* Skills */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: palette.spacing.xs,
            marginBottom: palette.spacing.md,
          }}>
            {match.skills.slice(0, 5).map((skill, index) => (
              <span
                key={index}
                style={{
                  backgroundColor: 'rgba(19, 239, 183, 0.1)',
                  color: palette.colors.primary.cyan,
                  padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
                  borderRadius: palette.borderRadius.md,
                  fontSize: palette.typography.fontSize.xs,
                  border: `1px solid ${palette.colors.primary.cyan}`,
                }}
              >
                {skill}
              </span>
            ))}
            {match.skills.length > 5 && (
              <span style={{
                color: palette.colors.text.tertiary,
                fontSize: palette.typography.fontSize.xs,
                padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
              }}>
                +{match.skills.length - 5} more
              </span>
            )}
          </div>

          {/* Bio Preview */}
          <p style={{
            color: palette.colors.text.secondary,
            fontSize: palette.typography.fontSize.sm,
            lineHeight: palette.typography.lineHeight.relaxed,
            marginBottom: palette.spacing.md,
            display: expanded ? 'block' : '-webkit-box',
            WebkitLineClamp: expanded ? 'unset' : 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {match.bio}
          </p>

          {/* Reasoning */}
          <div style={{
            backgroundColor: palette.colors.background.primary,
            borderRadius: palette.borderRadius.md,
            padding: palette.spacing.md,
            marginBottom: palette.spacing.md,
          }}>
            <h4 style={{
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.semibold,
              color: palette.colors.primary.cyan,
              marginBottom: palette.spacing.xs,
            }}>
              Why This Match?
            </h4>
            <p style={{
              fontSize: palette.typography.fontSize.sm,
              color: palette.colors.text.secondary,
              lineHeight: palette.typography.lineHeight.relaxed,
            }}>
              {match.reasoning}
            </p>
          </div>

          {/* Expandable Details */}
          {expanded && (
            <div className="fade-in">
              {/* Strengths */}
              {match.strengths && match.strengths.length > 0 && (
                <div style={{ marginBottom: palette.spacing.md }}>
                  <h4 style={{
                    fontSize: palette.typography.fontSize.sm,
                    fontWeight: palette.typography.fontWeight.semibold,
                    color: palette.colors.status.success,
                    marginBottom: palette.spacing.xs,
                  }}>
                    ✓ Key Strengths
                  </h4>
                  <ul style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                  }}>
                    {match.strengths.map((strength, index) => (
                      <li
                        key={index}
                        style={{
                          fontSize: palette.typography.fontSize.sm,
                          color: palette.colors.text.secondary,
                          marginBottom: palette.spacing.xs,
                          paddingLeft: palette.spacing.md,
                          position: 'relative',
                        }}
                      >
                        <span style={{
                          position: 'absolute',
                          left: 0,
                          color: palette.colors.status.success,
                        }}>
                          •
                        </span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Concerns */}
              {match.concerns && match.concerns.length > 0 && (
                <div style={{ marginBottom: palette.spacing.md }}>
                  <h4 style={{
                    fontSize: palette.typography.fontSize.sm,
                    fontWeight: palette.typography.fontWeight.semibold,
                    color: palette.colors.status.warning,
                    marginBottom: palette.spacing.xs,
                  }}>
                    ⚠ Potential Considerations
                  </h4>
                  <ul style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                  }}>
                    {match.concerns.map((concern, index) => (
                      <li
                        key={index}
                        style={{
                          fontSize: palette.typography.fontSize.sm,
                          color: palette.colors.text.secondary,
                          marginBottom: palette.spacing.xs,
                          paddingLeft: palette.spacing.md,
                          position: 'relative',
                        }}
                      >
                        <span style={{
                          position: 'absolute',
                          left: 0,
                          color: palette.colors.status.warning,
                        }}>
                          •
                        </span>
                        {concern}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Links */}
              <div style={{
                display: 'flex',
                gap: palette.spacing.md,
                marginTop: palette.spacing.md,
              }}>
                {match.linkedin && (
                  <a
                    href={match.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: palette.colors.primary.cyan,
                      fontSize: palette.typography.fontSize.sm,
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      gap: palette.spacing.xs,
                    }}
                  >
                    🔗 LinkedIn Profile
                  </a>
                )}
                {match.resume && (
                  <a
                    href={match.resume}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: palette.colors.primary.cyan,
                      fontSize: palette.typography.fontSize.sm,
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      gap: palette.spacing.xs,
                    }}
                  >
                    📄 View Resume
                  </a>
                )}
              </div>
            </div>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            style={{ marginTop: palette.spacing.md }}
          >
            {expanded ? 'Show Less' : 'Show More Details'}
          </Button>
        </div>

        {/* Action Button */}
        <div>
          <Button
            onClick={handleSendRequest}
            disabled={requestSent}
            style={{ whiteSpace: 'nowrap' }}
          >
            {requestSent ? '✓ Request Sent' : 'Send Request'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default MatchCard;