import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI } from '../../services/api';
import Button from '../Common/Button';
import TeamView from '../Collaboration/TeamView';
import palette from '../../palette';

const FounderDashboard = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('projects'); // 'projects' or 'team'
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

  const handleViewTeam = (project) => {
    setSelectedProject(project);
    setView('team');
  };

  if (loading) {
    return (
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
    );
  }

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: palette.spacing['2xl'],
    }}>
      {/* Header */}
      {view === 'projects' ? (
        <>
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
                Manage your projects and teams
              </p>
            </div>
            <Button onClick={() => navigate('/submit-idea')} size="lg">
              + New Project
            </Button>
          </div>

          {/* Projects List */}
          {projects.length === 0 ? (
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
              gap: palette.spacing.xl,
            }}>
              {projects.map((project) => (
                <div
                  key={project._id}
                  style={{
                    backgroundColor: palette.colors.background.secondary,
                    border: `1px solid ${palette.colors.border.primary}`,
                    borderRadius: palette.borderRadius.lg,
                    padding: palette.spacing.xl,
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
                      backgroundColor: project.live 
                        ? 'rgba(16, 185, 129, 0.1)' 
                        : 'rgba(251, 191, 36, 0.1)',
                      color: project.live 
                        ? palette.colors.status.success 
                        : palette.colors.status.warning,
                      padding: `${palette.spacing.xs} ${palette.spacing.md}`,
                      borderRadius: palette.borderRadius.full,
                      fontSize: palette.typography.fontSize.xs,
                      fontWeight: palette.typography.fontWeight.semibold,
                      textTransform: 'uppercase',
                    }}>
                      {project.live ? 'Live' : 'Pending'}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 style={{
                    fontSize: palette.typography.fontSize.xl,
                    fontWeight: palette.typography.fontWeight.bold,
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
                  }}>
                    {project.description.substring(0, 150)}...
                  </p>

                  {/* Actions */}
                  <div style={{
                    display: 'flex',
                    gap: palette.spacing.md,
                  }}>
                    {project.live && (
                      <>
                        <Button onClick={() => navigate(`/matches/${project._id}`)}>
                          View Matches
                        </Button>
                        <Button 
                          variant="outline" 
                          onClick={() => handleViewTeam(project)}
                        >
                          View Team
                        </Button>
                        <Button 
                          variant="outline" 
                          onClick={() => navigate(`/chat/${project._id}`)}
                        >
                          Team Chat
                        </Button>
                      </>
                    )}
                    {!project.live && (
                      <Button variant="secondary" disabled>
                        Under Review
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        /* Team View */
        <>
          <Button 
            variant="secondary" 
            onClick={() => setView('projects')}
            style={{ marginBottom: palette.spacing.xl }}
          >
            ← Back to Projects
          </Button>
          <TeamView project={selectedProject} onBack={() => setView('projects')} />
        </>
      )}
    </div>
  );
};

export default FounderDashboard;