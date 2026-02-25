import React, { useEffect, useRef, useState } from 'react';
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
  const [sentRequests, setSentRequests] = useState({});
  const [displayedCount, setDisplayedCount] = useState(0);
  const [visibleCards, setVisibleCards] = useState({});
  const [expandedCards, setExpandedCards] = useState({});
  const cardsRef = useRef([]);

  useEffect(() => {
    fetchData();
  }, [projectId]);

  useEffect(() => {
    let raf;
    let start;
    const target = matches.length;
    const duration = 900;

    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      setDisplayedCount(Math.round(progress * target));
      if (progress < 1) raf = requestAnimationFrame(step);
    };

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [matches.length]);

  useEffect(() => {
    if (matches.length === 0) return;

    const timer = setTimeout(() => {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const index = Number(entry.target.getAttribute('data-index'));
              setTimeout(() => {
                setVisibleCards((prev) => ({ ...prev, [index]: true }));
              }, index * 100);
            }
          });
        },
        { threshold: 0.01 }
      );

      cardsRef.current.forEach((node) => node && observer.observe(node));

      const fallback = setTimeout(() => {
        const allVisible = {};
        matches.forEach((_, i) => { allVisible[i] = true; });
        setVisibleCards(allVisible);
      }, 600);

      return () => {
        observer.disconnect();
        clearTimeout(fallback);
      };
    }, 100);

    return () => clearTimeout(timer);
  }, [matches]);

  const fetchData = async () => {
    setSentRequests({});
    try {
      const projectResponse = await projectAPI.getProject(projectId);
      setProject(projectResponse.data.project);

      const matchesResponse = await matchingAPI.getMatches(projectId);
      const matchList = matchesResponse.data.matches || [];
      setMatches(matchList);
      localStorage.setItem(`project_match_count_${projectId}`, String(matchList.length));

      if (matchesResponse.data.cached) {
        const allVisible = {};
        matchList.forEach((_, i) => { allVisible[i] = true; });
        setVisibleCards(allVisible);
      }

      const sentRequestsResponse = await collaborationAPI
        .getSentRequestsForProject(projectId)
        .catch(() => ({ data: { candidate_ids: [] } }));

      const persistedSentMap = {};
      (sentRequestsResponse.data?.candidate_ids || []).forEach((candidateId) => {
        persistedSentMap[candidateId] = true;
      });
      setSentRequests(persistedSentMap);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (candidateId, candidateName, isFounder) => {
    if (isFounder) return;
    if (sentRequests[candidateId]) return;

    setSendingTo(candidateId);
    try {
      await matchingAPI.sendRequest({
        project_id: projectId,
        candidate_id: candidateId,
        message: `Hi! I'd love to have you join my project "${project.title}". Your skills would be a great fit for our team!`,
      });
      setSentRequests((prev) => ({ ...prev, [candidateId]: true }));
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to send request';
      if (errorMessage.toLowerCase().includes('already sent')) {
        setSentRequests((prev) => ({ ...prev, [candidateId]: true }));
      } else {
        alert(errorMessage);
      }
    } finally {
      setSendingTo(null);
    }
  };

  const toggleCard = (userId) => {
    setExpandedCards((prev) => ({ ...prev, [userId]: !prev[userId] }));
  };

  if (loading) {
    return (
      <div className="cinematic-loader" style={{ minHeight: '80vh' }}>
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center' }}>
          <div className="pulse-ring" style={{ margin: '0 auto 1.25rem auto' }} />
          <p className="mono-label">Scanning the talent pool</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        maxWidth: '980px',
        margin: '0 auto',
        padding: palette.spacing['2xl'],
        textAlign: 'center',
      }}>
        <div className="surface-card" style={{
          borderRadius: palette.borderRadius.xl,
          padding: palette.spacing['2xl'],
        }}>
          <p className="mono-label" style={{ marginBottom: palette.spacing.md }}>System Alert</p>
          <h2 style={{
            fontFamily: palette.typography.fontFamily.display,
            fontSize: palette.typography.fontSize['3xl'],
            color: palette.colors.status.error,
            marginBottom: palette.spacing.md,
          }}>
            {error}
          </h2>
          <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
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
      <div style={{ marginBottom: palette.spacing['2xl'] }}>
        <Button
          variant="secondary"
          onClick={() => navigate('/dashboard')}
          style={{ marginBottom: palette.spacing.lg }}
        >
          Back to Dashboard
        </Button>

        <h1 style={{
          fontFamily: palette.typography.fontFamily.display,
          fontSize: palette.typography.fontSize['5xl'],
          fontWeight: palette.typography.fontWeight.bold,
          marginBottom: palette.spacing.sm,
          lineHeight: 0.9,
        }}>
          <span className="gradient-text">Match Intelligence</span>
        </h1>
        <p className="mono-label">{displayedCount} / {matches.length} matches found</p>

        {project && (
          <div className="surface-card" style={{
            borderRadius: palette.borderRadius.lg,
            padding: palette.spacing.xl,
            marginTop: palette.spacing.lg,
          }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Project Brief</p>
            <h2 style={{
              fontFamily: palette.typography.fontFamily.display,
              fontSize: palette.typography.fontSize['2xl'],
              marginBottom: palette.spacing.sm,
            }}>
              {project.title}
            </h2>
            {/* Full project description */}
            <p style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
              lineHeight: palette.typography.lineHeight.relaxed,
              whiteSpace: 'pre-wrap',
            }}>
              {project.description}
            </p>
          </div>
        )}
      </div>

      {matches.length === 0 ? (
        <div className="surface-card" style={{
          textAlign: 'center',
          padding: palette.spacing['3xl'],
          borderRadius: palette.borderRadius.xl,
        }}>
          <h3 style={{
            fontFamily: palette.typography.fontFamily.display,
            fontSize: palette.typography.fontSize['3xl'],
            marginBottom: palette.spacing.md,
          }}>
            No Matches Found
          </h3>
          <p style={{ color: palette.colors.text.secondary }}>
            We could not find suitable candidates for this project.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: palette.spacing.xl }}>
          {matches.map((match, index) => {
            const isExpanded = expandedCards[match.user_id];

            return (
              <div
                key={match.user_id}
                ref={(el) => { cardsRef.current[index] = el; }}
                data-index={index}
                className={`surface-card reveal-card ${visibleCards[index] ? 'visible' : ''}`}
                style={{
                  borderRadius: palette.borderRadius.xl,
                  padding: palette.spacing.xl,
                  transition: `opacity 400ms ease, transform 400ms ease`,
                }}
              >
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr auto',
                  gap: palette.spacing.xl,
                  alignItems: 'start',
                }}>
                  {/* Match percentage */}
                  <div style={{ textAlign: 'center', minWidth: '110px' }}>
                    <div style={{
                      fontFamily: palette.typography.fontFamily.mono,
                      fontSize: palette.typography.fontSize['4xl'],
                      color: palette.colors.primary.cyan,
                      lineHeight: 1,
                    }}>
                      {match.match_percentage}%
                    </div>
                    <div className="mono-label" style={{ marginTop: palette.spacing.xs }}>
                      #{index + 1} match
                    </div>
                    <div
                      className="match-avatar"
                      style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '50%',
                        margin: `${palette.spacing.md} auto 0 auto`,
                        background: 'linear-gradient(135deg, #3a3a3a, #0f0f0f)',
                        filter: 'grayscale(1)',
                        transition: `filter ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
                      }}
                    />
                  </div>

                  {/* Candidate info */}
                  <div>
                    <h3 style={{
                      fontFamily: palette.typography.fontFamily.display,
                      fontSize: palette.typography.fontSize['2xl'],
                      marginBottom: palette.spacing.xs,
                    }}>
                      {match.name}
                    </h3>
                    <p className="mono-label" style={{ marginBottom: palette.spacing.md }}>
                      {match.professional_title || match.role}
                      {match.experience_years ? ` · ${match.experience_years}y exp` : ''}
                    </p>

                    {/* All skills shown */}
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: palette.spacing.xs,
                      marginBottom: palette.spacing.md,
                    }}>
                      {(match.skills || []).map((skill, idx) => (
                        <span
                          key={idx}
                          style={{
                            border: `1px solid ${palette.colors.border.primary}`,
                            color: palette.colors.text.tertiary,
                            padding: `${palette.spacing.xs} ${palette.spacing.sm}`,
                            borderRadius: palette.borderRadius.full,
                            fontSize: palette.typography.fontSize.xs,
                            transition: `all ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = palette.colors.primary.cyan;
                            e.currentTarget.style.color = palette.colors.text.primary;
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = palette.colors.border.primary;
                            e.currentTarget.style.color = palette.colors.text.tertiary;
                          }}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>

                    {match.reasoning && (
                      <div style={{
                        backgroundColor: palette.colors.background.tertiary,
                        border: `1px solid ${palette.colors.border.primary}`,
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
                    )}

                    {/* Expandable section for strengths, concerns, bio */}
                    {isExpanded && (
                      <div style={{ marginTop: palette.spacing.md }}>
                        {match.bio && (
                          <div style={{ marginBottom: palette.spacing.md }}>
                            <p className="mono-label" style={{ color: palette.colors.text.tertiary, marginBottom: palette.spacing.xs }}>Bio</p>
                            <p style={{
                              color: palette.colors.text.secondary,
                              fontSize: palette.typography.fontSize.sm,
                              lineHeight: palette.typography.lineHeight.relaxed,
                            }}>
                              {match.bio}
                            </p>
                          </div>
                        )}

                        {match.strengths && match.strengths.length > 0 && (
                          <div style={{ marginBottom: palette.spacing.md }}>
                            <p className="mono-label" style={{
                              color: palette.colors.primary.cyan,
                              marginBottom: palette.spacing.xs,
                            }}>
                              Strengths
                            </p>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                              {match.strengths.map((strength, idx) => (
                                <li key={idx} style={{
                                  color: palette.colors.text.secondary,
                                  fontSize: palette.typography.fontSize.xs,
                                  marginBottom: palette.spacing.xs,
                                }}>
                                  ✓ {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {match.concerns && match.concerns.length > 0 && (
                          <div style={{ marginBottom: palette.spacing.md }}>
                            <p className="mono-label" style={{
                              color: palette.colors.status.warning,
                              marginBottom: palette.spacing.xs,
                            }}>
                              Considerations
                            </p>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                              {match.concerns.map((concern, idx) => (
                                <li key={idx} style={{
                                  color: palette.colors.text.secondary,
                                  fontSize: palette.typography.fontSize.xs,
                                  marginBottom: palette.spacing.xs,
                                }}>
                                  ⚠ {concern}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div style={{ display: 'flex', gap: palette.spacing.md, flexWrap: 'wrap' }}>
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

                    <button
                      type="button"
                      onClick={() => toggleCard(match.user_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: palette.colors.text.tertiary,
                        fontFamily: palette.typography.fontFamily.mono,
                        fontSize: palette.typography.fontSize.xs,
                        letterSpacing: '0.1em',
                        cursor: 'pointer',
                        textTransform: 'uppercase',
                        padding: `${palette.spacing.sm} 0 0 0`,
                      }}
                    >
                      {isExpanded ? 'Hide Details ↑' : 'View Details ↓'}
                    </button>
                  </div>

                  {/* Action button */}
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-end',
                    gap: palette.spacing.sm,
                    minWidth: '150px',
                  }}>
                    {match.is_founder ? (
                      <div style={{
                        padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                        border: `1px solid ${palette.colors.border.primary}`,
                        borderRadius: palette.borderRadius.sm,
                        color: palette.colors.text.tertiary,
                        fontFamily: palette.typography.fontFamily.mono,
                        fontSize: palette.typography.fontSize.xs,
                        letterSpacing: '0.08em',
                        textAlign: 'center',
                        lineHeight: 1.6,
                      }}>
                        ⚠ Founder —<br />not available
                      </div>
                    ) : sentRequests[match.user_id] ? (
                      <div style={{
                        padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                        border: `1px solid ${palette.colors.border.secondary}`,
                        borderRadius: palette.borderRadius.sm,
                        color: '#4ade80',
                        fontFamily: palette.typography.fontFamily.mono,
                        fontSize: palette.typography.fontSize.xs,
                        letterSpacing: '0.08em',
                        textAlign: 'center',
                      }}>
                        ✓ Request Sent
                      </div>
                    ) : (
                      <Button
                        onClick={() => handleSendRequest(match.user_id, match.name, match.is_founder)}
                        loading={sendingTo === match.user_id}
                        disabled={sendingTo !== null || sentRequests[match.user_id]}
                        variant="primary"
                      >
                        Send Request
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MatchList;