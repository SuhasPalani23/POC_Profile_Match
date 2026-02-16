import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { matchingAPI, projectAPI } from '../../services/api';
import MatchCard from './MatchCard';
import Button from '../Common/Button';
import palette from '../../palette';

const MatchList = ({ user }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    try {
      // Fetch project details
      const projectResponse = await projectAPI.getProject(projectId);
      setProject(projectResponse.data.project);

      // Fetch matches
      const matchesResponse = await matchingAPI.getMatches(projectId);
      setMatches(matchesResponse.data.matches);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (candidateId) => {
    try {
      await matchingAPI.sendRequest({
        project_id: projectId,
        candidate_id: candidateId,
        message: `Hi! I'd love to discuss collaborating on ${project.title}.`,
      });
      alert('Collaboration request sent successfully!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to send request');
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
      {/* Header */}
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

      {/* Matches */}
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
            We couldn't find suitable matches at this time. Try again later or update your project requirements.
          </p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gap: palette.spacing.xl,
        }}>
          {matches.map((match, index) => (
            <MatchCard 
              key={match.user_id} 
              match={match} 
              rank={index + 1}
              onSendRequest={handleSendRequest}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MatchList;