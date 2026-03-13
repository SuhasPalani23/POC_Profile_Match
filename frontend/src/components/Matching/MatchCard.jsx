import React, { useState } from 'react';
import { matchingAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const MatchCard = ({ match, projectId, rank, initialRequestSent = false }) => {
  const [expanded, setExpanded] = useState(false);
  const [requestSent, setRequestSent] = useState(initialRequestSent);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const handleSendRequest = async () => {
    setSending(true);
    setError('');
    try {
      await matchingAPI.sendRequest({
        project_id: projectId,
        candidate_id: match.user_id,
        message: `I'd love to have you join our team!`,
      });
      setRequestSent(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send request');
    } finally {
      setSending(false);
    }
  };

  const getMatchColor = (percentage) => {
    if (percentage >= 80) return '#4ade80';
    if (percentage >= 60) return palette.colors.primary.cyan;
    if (percentage >= 40) return '#facc15';
    return '#f87171';
  };

  const matchColor = getMatchColor(match.match_percentage);
  const circumference = 2 * Math.PI * 28;
  const strokeDashoffset =
    circumference - (match.match_percentage / 100) * circumference;

  return (
    <div
      className="surface-card reveal-card"
      style={{
        borderRadius: palette.borderRadius.md,
        padding: palette.spacing.lg,
        marginBottom: palette.spacing.md,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Rank Badge */}
      <div
        style={{
          position: 'absolute',
          top: palette.spacing.md,
          right: palette.spacing.md,
          width: '28px',
          height: '28px',
          borderRadius: palette.borderRadius.full,
          border: `1px solid ${palette.colors.border.secondary}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: palette.typography.fontFamily.mono,
          fontSize: palette.typography.fontSize.xs,
          color: palette.colors.text.tertiary,
        }}
      >
        #{rank}
      </div>

      {/* Main Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          gap: palette.spacing.lg,
          alignItems: 'center',
        }}
      >
        {/* Match Circle */}
        <div style={{ position: 'relative', width: '72px', height: '72px' }}>
          <svg width="72" height="72" style={{ transform: 'rotate(-90deg)' }}>
            <circle
              cx="36"
              cy="36"
              r="28"
              fill="none"
              stroke={palette.colors.border.primary}
              strokeWidth="3"
            />
            <circle
              cx="36"
              cy="36"
              r="28"
              fill="none"
              stroke={matchColor}
              strokeWidth="3"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              style={{
                transition:
                  'stroke-dashoffset 1s cubic-bezier(0.16,1,0.3,1)',
              }}
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: palette.typography.fontFamily.mono,
              fontSize: palette.typography.fontSize.sm,
              color: matchColor,
            }}
          >
            {match.match_percentage}%
          </div>
        </div>

        {/* Candidate Info */}
        <div>
          <h3
            style={{
              fontFamily: palette.typography.fontFamily.display,
              fontSize: palette.typography.fontSize.xl,
              color: palette.colors.text.primary,
              marginBottom: palette.spacing.xs,
            }}
          >
            {match.name}
          </h3>

          <p
            style={{
              fontFamily: palette.typography.fontFamily.mono,
              fontSize: palette.typography.fontSize.xs,
              color: palette.colors.primary.cyan,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              marginBottom: palette.spacing.sm,
            }}
          >
            {match.professional_title || 'Professional'} ·{' '}
            {match.experience_years}y exp
          </p>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: palette.spacing.xs,
            }}
          >
            {match.skills?.slice(0, 5).map((skill, i) => (
              <span
                key={i}
                style={{
                  fontFamily: palette.typography.fontFamily.mono,
                  fontSize: palette.typography.fontSize.xs,
                  color: palette.colors.text.secondary,
                  border: `1px solid ${palette.colors.border.primary}`,
                  borderRadius: palette.borderRadius.sm,
                  padding: `2px ${palette.spacing.sm}`,
                }}
              >
                {skill}
              </span>
            ))}

            {match.skills?.length > 5 && (
              <span
                style={{
                  fontFamily: palette.typography.fontFamily.mono,
                  fontSize: palette.typography.fontSize.xs,
                  color: palette.colors.text.tertiary,
                  padding: `2px ${palette.spacing.sm}`,
                }}
              >
                +{match.skills.length - 5} more
              </span>
            )}
          </div>
        </div>

        {/* Action Section */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: palette.spacing.sm,
            minWidth: '160px',
          }}
        >
          {match.is_founder ? (
            <div
              style={{
                padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                border: `1px solid ${palette.colors.border.primary}`,
                borderRadius: palette.borderRadius.sm,
                color: palette.colors.text.tertiary,
                fontFamily: palette.typography.fontFamily.mono,
                fontSize: palette.typography.fontSize.xs,
                letterSpacing: '0.08em',
                textAlign: 'center',
              }}
            >
              ⚠ Founder — not available
            </div>
          ) : requestSent ? (
            <div
              style={{
                padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                border: `1px solid ${palette.colors.border.secondary}`,
                borderRadius: palette.borderRadius.sm,
                color: '#4ade80',
                fontFamily: palette.typography.fontFamily.mono,
                fontSize: palette.typography.fontSize.xs,
                letterSpacing: '0.08em',
              }}
            >
              ✓ Request Sent
            </div>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={handleSendRequest}
              loading={sending}
              disabled={sending}
            >
              Send Invite
            </Button>
          )}

          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'none',
              border: 'none',
              color: palette.colors.text.tertiary,
              fontFamily: palette.typography.fontFamily.mono,
              fontSize: palette.typography.fontSize.xs,
              letterSpacing: '0.1em',
              cursor: 'pointer',
              textTransform: 'uppercase',
            }}
          >
            {expanded ? 'Hide Details' : 'View Details'}
          </button>
        </div>
      </div>

      {error && (
        <p
          style={{
            marginTop: palette.spacing.sm,
            fontFamily: palette.typography.fontFamily.mono,
            fontSize: palette.typography.fontSize.xs,
            color: palette.colors.status.error,
          }}
        >
          {error}
        </p>
      )}

      {/* Expanded Section */}
      {expanded && (
        <div
          style={{
            marginTop: palette.spacing.lg,
            paddingTop: palette.spacing.lg,
            borderTop: `1px solid ${palette.colors.border.primary}`,
          }}
        >
          {match.reasoning && (
            <div
              style={{
                marginBottom: palette.spacing.md,
                padding: palette.spacing.md,
                border: `1px solid ${palette.colors.border.primary}`,
                borderLeft: `3px solid ${palette.colors.primary.cyan}`,
                borderRadius: palette.borderRadius.sm,
              }}
            >
              <p className="mono-label">Why This Match?</p>
              <p
                style={{
                  fontSize: palette.typography.fontSize.sm,
                  color: palette.colors.text.secondary,
                }}
              >
                {match.reasoning}
              </p>
            </div>
          )}

          {/* Links */}
          <div
            style={{
              display: 'flex',
              gap: palette.spacing.md,
              marginTop: palette.spacing.md,
            }}
          >
            {match.linkedin && (
              <a
                href={match.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontFamily: palette.typography.fontFamily.mono,
                  fontSize: palette.typography.fontSize.xs,
                  color: palette.colors.primary.cyan,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                LinkedIn ↗
              </a>
            )}

            {match.resume && (
              <a
                href={`/api/profile/resume/${match.user_id}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontFamily: palette.typography.fontFamily.mono,
                  fontSize: palette.typography.fontSize.xs,
                  color: palette.colors.primary.cyan,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                Resume ↗
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchCard;