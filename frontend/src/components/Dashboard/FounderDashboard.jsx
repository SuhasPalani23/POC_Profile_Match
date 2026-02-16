import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI } from '../../services/api';
import Button from '../Common/Button';
import ProjectCard from '../Project/ProjectCard';
import palette from '../../palette';

const FounderDashboard = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await projectAPI.getMyProjects();
      setProjects(response.data.projects);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: palette.spacing['2xl'],
      }}>
        <div>
          <h1 style={{
            fontSize: palette.typography.fontSize['4xl'],
            fontWeight: palette.typography.fontWeight.black,
            marginBottom: palette.spacing.sm,
          }}>
            <span className="gradient-text">Founder Dashboard</span>
          </h1>
          <p style={{
            fontSize: palette.typography.fontSize.lg,
            color: palette.colors.text.secondary,
          }}>
            Manage your projects and team matches
          </p>
        </div>
        <Button onClick={() => navigate('/submit-idea')} size="lg">
          + New Project
        </Button>
      </div>

      {/* Projects Section */}
      {loading ? (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px',
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
      ) : projects.length === 0 ? (
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
            📋
          </div>
          <h3 style={{
            fontSize: palette.typography.fontSize['2xl'],
            fontWeight: palette.typography.fontWeight.semibold,
            marginBottom: palette.spacing.md,
          }}>
            No Projects Yet
          </h3>
          <p style={{
            color: palette.colors.text.secondary,
            fontSize: palette.typography.fontSize.lg,
            marginBottom: palette.spacing.xl,
          }}>
            Start by submitting your first project idea!
          </p>
          <Button onClick={() => navigate('/submit-idea')}>
            Submit Your First Idea
          </Button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: palette.spacing.xl,
        }}>
          {projects.map((project) => (
            <ProjectCard key={project._id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
};

export default FounderDashboard;