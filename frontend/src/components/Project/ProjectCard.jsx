import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../Common/Button';
import palette from '../../palette';

const ProjectCard = ({ project }) => {
  const navigate = useNavigate();

  const getStatusColor = () => {
    switch (project.status) {
      case 'approved':
        return palette.colors.status.success;
      case 'pending':
        return palette.colors.status.warning;
      case 'rejected':
        return palette.colors.status.error;
      default:
        return palette.colors.text.secondary;
    }
  };

  const getStatusLabel = () => {
    if (project.live) return 'Live';
    return project.status.charAt(0).toUpperCase() + project.status.slice(1);
  };

  return (
    <div style={{
      backgroundColor: palette.colors.background.secondary,
      border: `1px solid ${palette.colors.border.primary}`,
      borderRadius: palette.borderRadius.lg,
      padding: palette.spacing.xl,
      transition: `all ${palette.transitions.normal}`,
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
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
      {/* Status Badge */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: palette.spacing.md,
      }}>
        <span style={{
          backgroundColor: `${getStatusColor()}20`,
          color: getStatusColor(),
          padding: `${palette.spacing.xs} ${palette.spacing.md}`,
          borderRadius: palette.borderRadius.full,
          fontSize: palette.typography.fontSize.xs,
          fontWeight: palette.typography.fontWeight.semibold,
          textTransform: 'uppercase',
        }}>
          {getStatusLabel()}
        </span>
        {project.live && (
          <span style={{
            width: '8px',
            height: '8px',
            backgroundColor: palette.colors.status.success,
            borderRadius: '50%',
            animation: 'pulse 2s ease-in-out infinite',
          }} />
        )}
      </div>

      {/* Title */}
      <h3 style={{
        fontSize: palette.typography.fontSize.xl,
        fontWeight: palette.typography.fontWeight.bold,
        color: palette.colors.text.primary,
        marginBottom: palette.spacing.md,
      }}>
        {project.title}
      </h3>

      {/* Description */}
      <p style={{
        color: palette.colors.text.secondary,
        fontSize: palette.typography.fontSize.sm,
        lineHeight: palette.typography.lineHeight.relaxed,
        marginBottom: palette.spacing.lg,
        flex: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: '-webkit-box',
        WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical',
      }}>
        {project.description}
      </p>

      {/* Skills */}
      {project.required_skills && project.required_skills.length > 0 && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: palette.spacing.xs,
          marginBottom: palette.spacing.lg,
        }}>
          {project.required_skills.slice(0, 3).map((skill, index) => (
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
          {project.required_skills.length > 3 && (
            <span style={{
              color: palette.colors.text.tertiary,
              fontSize: palette.typography.fontSize.xs,
              padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
            }}>
              +{project.required_skills.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div style={{
        display: 'flex',
        gap: palette.spacing.sm,
      }}>
        {project.live ? (
          <Button 
            onClick={() => navigate(`/matches/${project._id}`)}
            fullWidth
          >
            View Matches
          </Button>
        ) : (
          <Button 
            variant="secondary"
            fullWidth
            disabled
          >
            Under Review
          </Button>
        )}
      </div>

      {/* Date */}
      <p style={{
        marginTop: palette.spacing.md,
        color: palette.colors.text.tertiary,
        fontSize: palette.typography.fontSize.xs,
        textAlign: 'center',
      }}>
        Created {new Date(project.created_at).toLocaleDateString()}
      </p>
    </div>
  );
};

export default ProjectCard;