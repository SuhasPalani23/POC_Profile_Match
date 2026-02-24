import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../Common/Button';
import palette from '../../palette';

const UserDashboard = ({ user }) => {
  const navigate = useNavigate();

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: `${palette.spacing['2xl']} clamp(1rem, 3vw, 2rem)`,
    }}>
      <section style={{ minHeight: '44vh', display: 'grid', alignItems: 'end', marginBottom: palette.spacing['2xl'] }}>
        <div>
          <p className="mono-label">Candidate workspace</p>
          <h1 className="hero-title" style={{ marginTop: palette.spacing.sm }}>
            <span className="word-rise word-delay-1">Welcome</span>
            <br />
            <span className="word-rise word-delay-2 gradient-text">{user.name}</span>
          </h1>
          <p style={{
            marginTop: palette.spacing.md,
            color: palette.colors.text.secondary,
            maxWidth: '620px',
          }}>
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

      <div className="surface-card" style={{
        borderRadius: palette.borderRadius.xl,
        padding: palette.spacing['2xl'],
        marginBottom: palette.spacing.xl,
      }}>
        <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Founder mode</p>
        <h2 style={{
          fontFamily: palette.typography.fontFamily.display,
          fontSize: palette.typography.fontSize['3xl'],
          marginBottom: palette.spacing.md,
        }}>
          Ready to launch your own startup brief?
        </h2>
        <p style={{
          color: palette.colors.text.secondary,
          marginBottom: palette.spacing.lg,
          maxWidth: '700px',
        }}>
          Submit an idea and let the matching engine find team members whose skill graph complements your vision.
        </p>
        <Button onClick={() => navigate('/submit-idea')} size="lg">Submit Your Idea</Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: palette.spacing.xl }}>
        {[
          {
            title: 'AI-Powered Matching',
            description: 'Compatibility scoring tuned for startup execution, not vanity metrics.',
          },
          {
            title: 'Instant Results',
            description: 'Top candidate set surfaced quickly with rationale and strengths.',
          },
          {
            title: 'Team Formation',
            description: 'Send requests, build a team, and move directly into collaboration chat.',
          },
        ].map((card) => (
          <div key={card.title} className="surface-card" style={{ borderRadius: palette.borderRadius.lg, padding: palette.spacing.xl }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Capability</p>
            <h3 style={{
              fontFamily: palette.typography.fontFamily.display,
              fontSize: palette.typography.fontSize['2xl'],
              marginBottom: palette.spacing.sm,
            }}>
              {card.title}
            </h3>
            <p style={{ color: palette.colors.text.secondary, fontSize: palette.typography.fontSize.sm, lineHeight: palette.typography.lineHeight.relaxed }}>
              {card.description}
            </p>
          </div>
        ))}
      </div>

      <div className="surface-card" style={{
        marginTop: palette.spacing['2xl'],
        borderRadius: palette.borderRadius.xl,
        padding: palette.spacing['2xl'],
      }}>
        <h3 style={{
          fontFamily: palette.typography.fontFamily.display,
          fontSize: palette.typography.fontSize['3xl'],
          marginBottom: palette.spacing.lg,
        }}>
          Profile Snapshot
        </h3>
        <div style={{ display: 'grid', gap: palette.spacing.lg }}>
          <div>
            <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Email</p>
            <p>{user.email}</p>
          </div>
          {user.bio && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Bio</p>
              <p style={{ color: palette.colors.text.secondary, lineHeight: palette.typography.lineHeight.relaxed }}>
                {user.bio}
              </p>
            </div>
          )}
          {user.skills && user.skills.length > 0 && (
            <div>
              <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Skills</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: palette.spacing.sm }}>
                {user.skills.map((skill, index) => (
                  <span
                    key={index}
                    style={{
                      border: `1px solid ${palette.colors.border.primary}`,
                      color: palette.colors.text.tertiary,
                      padding: `${palette.spacing.xs} ${palette.spacing.md}`,
                      borderRadius: palette.borderRadius.full,
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
      </div>
    </div>
  );
};

export default UserDashboard;
