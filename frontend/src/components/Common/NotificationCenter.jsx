import React from 'react';
import palette from '../../palette';

const NotificationCenter = ({ notifications, onClose }) => {
  if (notifications.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  const getColor = (type) => {
    switch (type) {
      case 'success':
        return palette.colors.status.success;
      case 'error':
        return palette.colors.status.error;
      case 'warning':
        return palette.colors.status.warning;
      case 'info':
      default:
        return palette.colors.primary.cyan;
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: '80px',
      right: palette.spacing.xl,
      zIndex: palette.zIndex.modal,
      display: 'flex',
      flexDirection: 'column',
      gap: palette.spacing.md,
      maxWidth: '400px',
    }}>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className="fade-in"
          style={{
            backgroundColor: palette.colors.background.secondary,
            border: `2px solid ${getColor(notification.type)}`,
            borderRadius: palette.borderRadius.lg,
            padding: palette.spacing.lg,
            boxShadow: palette.shadows.lg,
            display: 'flex',
            alignItems: 'flex-start',
            gap: palette.spacing.md,
            animation: 'fadeIn 0.3s ease-in-out',
          }}
        >
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: palette.borderRadius.full,
            backgroundColor: `${getColor(notification.type)}20`,
            color: getColor(notification.type),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: palette.typography.fontSize.lg,
            fontWeight: palette.typography.fontWeight.bold,
            flexShrink: 0,
          }}>
            {getIcon(notification.type)}
          </div>
          
          <div style={{ flex: 1 }}>
            <p style={{
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.medium,
              marginBottom: palette.spacing.xs,
            }}>
              {notification.message}
            </p>
            
            {notification.data && notification.data.message && (
              <p style={{
                color: palette.colors.text.secondary,
                fontSize: palette.typography.fontSize.xs,
              }}>
                {notification.data.message}
              </p>
            )}
          </div>
          
          <button
            onClick={() => onClose(notification.id)}
            style={{
              background: 'none',
              border: 'none',
              color: palette.colors.text.tertiary,
              cursor: 'pointer',
              padding: palette.spacing.xs,
              fontSize: palette.typography.fontSize.lg,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default NotificationCenter;