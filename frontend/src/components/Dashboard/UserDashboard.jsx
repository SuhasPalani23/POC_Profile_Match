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
      padding: palette.spacing['2xl'],
    }}>
      {/* Hero Section */}
      <div style={{
        textAlign: 'center',
        marginBottom: palette.spacing['3xl'],
      }}>
        <h1 style={{
          fontSize: palette.typography.fontSize['5xl'],
          fontWeight: palette.typography.fontWeight.black,
          marginBottom: palette.spacing.lg,
        }}>
          Welcome, <span className="gradient-text">{user.name}</span>
        </h1>
        <p style={{
          fontSize: palette.typography.fontSize.xl,
          color: palette.colors.text.secondary,
          maxWidth: '700px',
          margin: '0 auto',
        }}>
          Ready to turn your vision into reality? Submit your startup idea and let our AI find your perfect co-founders.
        </p>
      </div>

      {/* Call to Action Card */}
      <div style={{
        backgroundColor: palette.colors.background.secondary,
        borderRadius: palette.borderRadius.xl,
        border: `1px solid ${palette.colors.border.primary}`,
        padding: palette.spacing['2xl'],
        marginBottom: palette.spacing.xl,
        textAlign: 'center',
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          background: palette.colors.primary.gradient,
          borderRadius: palette.borderRadius.full,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto',
          marginBottom: palette.spacing.lg,
          fontSize: palette.typography.fontSize['3xl'],
        }}>
          💡
        </div>
        <h2 style={{
          fontSize: palette.typography.fontSize['2xl'],
          fontWeight: palette.typography.fontWeight.bold,
          marginBottom: palette.spacing.md,
        }}>
          Enter Founder Mode
        </h2>
        <p style={{
          color: palette.colors.text.secondary,
          marginBottom: palette.spacing.xl,
          fontSize: palette.typography.fontSize.lg,
        }}>
          Share your startup idea and discover talented individuals who complement your vision.
        </p>
        <Button 
          onClick={() => navigate('/submit-idea')}
          size="lg"
        >
          Submit Your Idea
        </Button>
      </div>

      {/* Info Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: palette.spacing.xl,
      }}>
        {[
          {
            icon: '🤖',
            title: 'AI-Powered Matching',
            description: 'Our advanced AI analyzes your project and matches you with the most suitable co-founders based on skills and mindset.'
          },
          {
            icon: '⚡',
            title: 'Instant Results',
            description: 'Get your top 5 matches in seconds. See compatibility scores, strengths, and potential concerns for each candidate.'
          },
          {
            icon: '🚀',
            title: 'Build Your Team',
            description: 'Send collaboration requests and start building your dream team. Connect with passionate individuals ready to create.'
          },
        ].map((card, index) => (
          <div
            key={index}
            style={{
              backgroundColor: palette.colors.background.secondary,
              borderRadius: palette.borderRadius.lg,
              border: `1px solid ${palette.colors.border.primary}`,
              padding: palette.spacing.xl,
              transition: `all ${palette.transitions.normal}`,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = palette.colors.primary.cyan;
              e.currentTarget.style.transform = 'translateY(-4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = palette.colors.border.primary;
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{
              fontSize: palette.typography.fontSize['4xl'],
              marginBottom: palette.spacing.md,
            }}>
              {card.icon}
            </div>
            <h3 style={{
              fontSize: palette.typography.fontSize.xl,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.sm,
            }}>
              {card.title}
            </h3>
            <p style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.base,
              lineHeight: palette.typography.lineHeight.relaxed,
            }}>
              {card.description}
            </p>
          </div>
        ))}
      </div>

      {/* Profile Section */}
      <div style={{
        marginTop: palette.spacing['3xl'],
        backgroundColor: palette.colors.background.secondary,
        borderRadius: palette.borderRadius.xl,
        border: `1px solid ${palette.colors.border.primary}`,
        padding: palette.spacing['2xl'],
      }}>
        <h3 style={{
          fontSize: palette.typography.fontSize['2xl'],
          fontWeight: palette.typography.fontWeight.bold,
          marginBottom: palette.spacing.lg,
        }}>
          Your Profile
        </h3>
        <div style={{
          display: 'grid',
          gap: palette.spacing.lg,
        }}>
          <div>
            <label style={{
              display: 'block',
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
              marginBottom: palette.spacing.xs,
            }}>
              Email
            </label>
            <p style={{
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.base,
            }}>
              {user.email}
            </p>
          </div>
          {user.bio && (
            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.secondary,
                fontSize: palette.typography.fontSize.sm,
                marginBottom: palette.spacing.xs,
              }}>
                Bio
              </label>
              <p style={{
                color: palette.colors.text.primary,
                fontSize: palette.typography.fontSize.base,
                lineHeight: palette.typography.lineHeight.relaxed,
              }}>
                {user.bio}
              </p>
            </div>
          )}
          {user.skills && user.skills.length > 0 && (
            <div>
              <label style={{
                display: 'block',
                color: palette.colors.text.secondary,
                fontSize: palette.typography.fontSize.sm,
                marginBottom: palette.spacing.sm,
              }}>
                Skills
              </label>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: palette.spacing.sm,
              }}>
                {user.skills.map((skill, index) => (
                  <span
                    key={index}
                    style={{
                      backgroundColor: 'rgba(19, 239, 183, 0.1)',
                      color: palette.colors.primary.cyan,
                      padding: `${palette.spacing.xs} ${palette.spacing.md}`,
                      borderRadius: palette.borderRadius.full,
                      fontSize: palette.typography.fontSize.sm,
                      border: `1px solid ${palette.colors.primary.cyan}`,
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