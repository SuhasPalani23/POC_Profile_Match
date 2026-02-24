import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI, matchingAPI, collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import TeamView from '../Collaboration/TeamView';
import palette from '../../palette';

const MATCH_COUNT_TIMEOUT_MS = 5000;

const FounderDashboard = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('projects');
  const [stats, setStats] = useState({
    projects: 0,
    matches: 0,
    requests: 0,
  });
  const navigate = useNavigate();

  useEffect(() => {
    const cachedStatsRaw = localStorage.getItem(`founder_dashboard_stats_${user._id}`);
    if (cachedStatsRaw) {
      try {
        const cachedStats = JSON.parse(cachedStatsRaw);
        setStats((prev) => ({
          ...prev,
          projects: typeof cachedStats.projects === 'number' ? cachedStats.projects : prev.projects,
          matches: typeof cachedStats.matches === 'number' ? cachedStats.matches : prev.matches,
          requests: typeof cachedStats.requests === 'number' ? cachedStats.requests : prev.requests,
        }));
      } catch (error) {
        console.error('Error reading cached dashboard stats:', error);
      }
    }

    fetchProjects();
  }, []);

  useEffect(() => {
    localStorage.setItem(`founder_dashboard_stats_${user._id}`, JSON.stringify(stats));
  }, [stats, user._id]);

  const withTimeout = (promise, timeoutMs, fallbackValue) =>
    Promise.race([
      promise,
      new Promise((resolve) => setTimeout(() => resolve(fallbackValue), timeoutMs)),
    ]);

  const getCachedProjectMatchCount = (projectId) => {
    const raw = localStorage.getItem(`project_match_count_${projectId}`);
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const fetchProjects = async () => {
    try {
      const response = await projectAPI.getMyProjects();
      const projectList = response.data.projects || [];
      const liveProjects = projectList.filter((project) => project.live);
      const cachedMatchTotal = liveProjects.reduce(
        (sum, project) => sum + getCachedProjectMatchCount(project._id),
        0
      );
      setProjects(projectList);
      setStats((prev) => ({
        ...prev,
        projects: projectList.length,
        matches: cachedMatchTotal || prev.matches,
      }));
      loadSupplementaryStats(projectList);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSupplementaryStats = async (projectList) => {
    try {
      const liveProjects = projectList.filter((project) => project.live);

      const matchesByProject = await Promise.all(
        liveProjects.map((project) =>
          withTimeout(
            matchingAPI
              .getMatches(project._id)
              .then((res) => res.data?.matches?.length || 0)
              .catch(() => 0),
            MATCH_COUNT_TIMEOUT_MS,
            null
          )
        )
      );

      const resolvedMatchCounts = matchesByProject.filter(
        (count) => typeof count === 'number'
      );
      const totalMatches = resolvedMatchCounts.reduce((sum, count) => sum + count, 0);

      const requestsResponse = await collaborationAPI.getMyRequests().catch(
        () => ({ data: { requests: [] } })
      );

      const pendingRequests = (requestsResponse.data?.requests || []).filter(
        (request) => request.status === 'pending'
      ).length;

      setStats((prev) => ({
        ...prev,
        matches:
          resolvedMatchCounts.length === liveProjects.length ? totalMatches : prev.matches,
        requests: pendingRequests,
      }));
    } catch (error) {
      console.error('Error loading supplementary stats:', error);
    }
  };

  const handleViewTeam = (project) => {
    setSelectedProject(project);
    setView('team');
  };

  if (loading) {
    return (
      <div className="cinematic-loader" style={{ minHeight: '70vh' }}>
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
          <div className="pulse-ring" style={{ margin: '0 auto 1rem auto' }} />
          <p className="mono-label">Calibrating founder dashboard</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: `${palette.spacing['2xl']} clamp(1rem, 3vw, 2rem)`,
    }}>
      {view === 'projects' ? (
        <>
          <section style={{
            minHeight: '40vh',
            display: 'grid',
            alignItems: 'end',
            marginBottom: palette.spacing['2xl'],
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1.2fr auto',
              alignItems: 'end',
              gap: palette.spacing.xl,
            }}>
              <div>
                <p className="mono-label">Founder command center</p>
                <h1 className="hero-title" style={{ marginTop: palette.spacing.sm }}>
                  <span className="word-rise word-delay-1">Founder</span>
                  <br />
                  <span className="word-rise word-delay-2 gradient-text">Dashboard</span>
                </h1>
                <p style={{
                  marginTop: palette.spacing.md,
                  color: palette.colors.text.secondary,
                  maxWidth: '620px',
                }}>
                  Manage projects, monitor response flow, and move from idea to team formation with precision.
                </p>
              </div>
              <Button onClick={() => navigate('/submit-idea')} size="lg">
                New Project
              </Button>
            </div>
            <div style={{
              marginTop: palette.spacing.xl,
              height: '1px',
              backgroundColor: palette.colors.border.primary,
              transform: 'scaleX(0)',
            }} className="rule-draw" />
          </section>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: palette.spacing.lg,
            marginBottom: palette.spacing['2xl'],
          }}>
            {[
              { label: 'Projects', value: stats.projects, helper: 'Ideas submitted', accent: true },
              { label: 'Matches', value: stats.matches, helper: 'Candidates discovered' },
              { label: 'Requests', value: stats.requests, helper: 'Pending invites' },
            ].map((item) => (
              <div
                key={item.label}
                className="surface-card"
                style={{
                  borderRadius: palette.borderRadius.xl,
                  padding: palette.spacing.xl,
                  background: item.accent
                    ? 'linear-gradient(130deg, rgba(201, 168, 76, 0.16), rgba(12, 12, 12, 1))'
                    : palette.colors.background.secondary,
                }}
              >
                <p className="mono-label">{item.label}</p>
                <p style={{
                  margin: `${palette.spacing.sm} 0 ${palette.spacing.xs} 0`,
                  fontFamily: palette.typography.fontFamily.mono,
                  fontSize: palette.typography.fontSize['4xl'],
                  color: item.accent ? palette.colors.primary.cyan : palette.colors.text.primary,
                }}>
                  {item.value}
                </p>
                <p style={{ color: palette.colors.text.secondary, fontSize: palette.typography.fontSize.sm }}>
                  {item.helper}
                </p>
              </div>
            ))}
          </div>

          {projects.length === 0 ? (
            <div className="surface-card" style={{
              textAlign: 'center',
              padding: palette.spacing['3xl'],
              borderRadius: palette.borderRadius.xl,
            }}>
              <h3 style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize['3xl'], marginBottom: palette.spacing.md }}>
                No Projects Yet
              </h3>
              <p style={{ color: palette.colors.text.secondary, marginBottom: palette.spacing.xl }}>
                Submit your first project to activate candidate matching.
              </p>
              <Button onClick={() => navigate('/submit-idea')}>Submit First Project</Button>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: palette.spacing.xl }}>
              {projects.map((project) => (
                <div
                  key={project._id}
                  className="surface-card"
                  style={{ borderRadius: palette.borderRadius.lg, padding: palette.spacing.xl }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: palette.spacing.md }}>
                    <span className="mono-label" style={{ color: project.live ? palette.colors.primary.cyan : palette.colors.text.tertiary }}>
                      {project.live ? 'LIVE' : 'PENDING REVIEW'}
                    </span>
                  </div>

                  <h3 style={{
                    fontFamily: palette.typography.fontFamily.display,
                    fontSize: palette.typography.fontSize['2xl'],
                    marginBottom: palette.spacing.md,
                  }}>
                    {project.title}
                  </h3>
                  <p style={{
                    color: palette.colors.text.secondary,
                    fontSize: palette.typography.fontSize.sm,
                    lineHeight: palette.typography.lineHeight.relaxed,
                    marginBottom: palette.spacing.lg,
                  }}>
                    {project.description.substring(0, 160)}...
                  </p>

                  <div style={{ display: 'flex', gap: palette.spacing.md, flexWrap: 'wrap' }}>
                    {project.live ? (
                      <>
                        <Button onClick={() => navigate(`/matches/${project._id}`)}>View Matches</Button>
                        <Button variant="outline" onClick={() => handleViewTeam(project)}>View Team</Button>
                        <Button variant="outline" onClick={() => navigate(`/chat/${project._id}`)}>Team Chat</Button>
                      </>
                    ) : (
                      <Button variant="secondary" disabled>Under Review</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          <Button
            variant="secondary"
            onClick={() => setView('projects')}
            style={{ marginBottom: palette.spacing.xl }}
          >
            Back to Projects
          </Button>
          <TeamView project={selectedProject} onBack={() => setView('projects')} />
        </>
      )}
    </div>
  );
};

export default FounderDashboard;
