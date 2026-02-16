import React, { useState, useEffect } from 'react';
import { collaborationAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const CollaborationRequests = ({ user, onRequestUpdate }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const response = await collaborationAPI.getMyRequests();
      setRequests(response.data.requests.filter(r => r.status === 'pending'));
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (collaborationId) => {
    setProcessingId(collaborationId);
    try {
      await collaborationAPI.acceptRequest(collaborationId);
      setRequests(requests.filter(r => r._id !== collaborationId));
      if (onRequestUpdate) onRequestUpdate();
    } catch (error) {
      console.error('Error accepting request:', error);
      alert('Failed to accept request');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (collaborationId) => {
    setProcessingId(collaborationId);
    try {
      await collaborationAPI.rejectRequest(collaborationId);
      setRequests(requests.filter(r => r._id !== collaborationId));
      if (onRequestUpdate) onRequestUpdate();
    } catch (error) {
      console.error('Error rejecting request:', error);
      alert('Failed to reject request');
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: palette.spacing.xl }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: `3px solid ${palette.colors.border.primary}`,
          borderTop: `3px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto',
        }}></div>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: palette.spacing['2xl'],
        color: palette.colors.text.secondary,
      }}>
        <div style={{ fontSize: '48px', marginBottom: palette.spacing.md }}>📬</div>
        <p>No pending collaboration requests</p>
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gap: palette.spacing.lg,
    }}>
      {requests.map((request) => (
        <div
          key={request._id}
          style={{
            backgroundColor: palette.colors.background.secondary,
            border: `2px solid ${palette.colors.primary.cyan}`,
            borderRadius: palette.borderRadius.lg,
            padding: palette.spacing.xl,
          }}
        >
          {/* Project Info */}
          <div style={{ marginBottom: palette.spacing.lg }}>
            <h3 style={{
              fontSize: palette.typography.fontSize.xl,
              fontWeight: palette.typography.fontWeight.bold,
              marginBottom: palette.spacing.sm,
            }}>
              {request.project.title}
            </h3>
            <p style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
              lineHeight: palette.typography.lineHeight.relaxed,
              marginBottom: palette.spacing.md,
            }}>
              {request.project.description.substring(0, 200)}...
            </p>
          </div>

          {/* Founder Info */}
          <div style={{
            backgroundColor: palette.colors.background.primary,
            borderRadius: palette.borderRadius.md,
            padding: palette.spacing.md,
            marginBottom: palette.spacing.lg,
          }}>
            <p style={{
              fontSize: palette.typography.fontSize.xs,
              color: palette.colors.text.tertiary,
              marginBottom: palette.spacing.xs,
            }}>
              FROM
            </p>
            <h4 style={{
              fontSize: palette.typography.fontSize.base,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.xs,
            }}>
              {request.founder.name}
            </h4>
            <p style={{
              fontSize: palette.typography.fontSize.sm,
              color: palette.colors.text.secondary,
              marginBottom: palette.spacing.sm,
            }}>
              {request.founder.professional_title || 'Founder'}
            </p>
            {request.founder.bio && (
              <p style={{
                fontSize: palette.typography.fontSize.sm,
                color: palette.colors.text.secondary,
                lineHeight: palette.typography.lineHeight.relaxed,
              }}>
                {request.founder.bio.substring(0, 150)}...
              </p>
            )}
          </div>

          {/* Message */}
          {request.message && (
            <div style={{
              backgroundColor: 'rgba(19, 239, 183, 0.1)',
              border: `1px solid ${palette.colors.primary.cyan}`,
              borderRadius: palette.borderRadius.md,
              padding: palette.spacing.md,
              marginBottom: palette.spacing.lg,
            }}>
              <p style={{
                fontSize: palette.typography.fontSize.xs,
                color: palette.colors.primary.cyan,
                fontWeight: palette.typography.fontWeight.semibold,
                marginBottom: palette.spacing.xs,
              }}>
                MESSAGE
              </p>
              <p style={{
                fontSize: palette.typography.fontSize.sm,
                color: palette.colors.text.primary,
                lineHeight: palette.typography.lineHeight.relaxed,
              }}>
                "{request.message}"
              </p>
            </div>
          )}

          {/* Actions */}
          <div style={{
            display: 'flex',
            gap: palette.spacing.md,
          }}>
            <Button
              onClick={() => handleAccept(request._id)}
              loading={processingId === request._id}
              disabled={processingId !== null}
              fullWidth
            >
              Accept & Join Team
            </Button>
            <Button
              onClick={() => handleReject(request._id)}
              variant="secondary"
              loading={processingId === request._id}
              disabled={processingId !== null}
              fullWidth
            >
              Decline
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default CollaborationRequests;