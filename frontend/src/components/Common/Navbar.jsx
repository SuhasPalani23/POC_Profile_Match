import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from './Button';
import palette from '../../palette';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <nav style={{
      backgroundColor: palette.colors.background.secondary,
      borderBottom: `1px solid ${palette.colors.border.primary}`,
      padding: `${palette.spacing.md} ${palette.spacing.xl}`,
      position: 'sticky',
      top: 0,
      zIndex: palette.zIndex.sticky,
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <Link 
          to="/dashboard" 
          style={{
            fontSize: palette.typography.fontSize.xl,
            fontWeight: palette.typography.fontWeight.bold,
            textDecoration: 'none',
          }}
        >
          <span className="gradient-text">Founding Mindset</span>
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: palette.spacing.lg }}>
          {/* Requests Link */}
          <Button 
            onClick={() => navigate('/requests')} 
            variant="outline" 
            size="sm"
          >
            Requests
          </Button>

          {/* User Info */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: palette.spacing.md,
          }}>
            <span style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
            }}>
              {user.name}
            </span>
            <span style={{
              backgroundColor: user.role === 'founder' 
                ? 'rgba(19, 239, 183, 0.1)' 
                : 'rgba(156, 163, 175, 0.1)',
              color: user.role === 'founder' 
                ? palette.colors.primary.cyan 
                : palette.colors.text.secondary,
              padding: `${palette.spacing.xs} ${palette.spacing.md}`,
              borderRadius: palette.borderRadius.full,
              fontSize: palette.typography.fontSize.xs,
              fontWeight: palette.typography.fontWeight.medium,
              textTransform: 'uppercase',
            }}>
              {user.role}
            </span>
          </div>

          {/* Profile Edit Button */}
          <Button 
            onClick={() => navigate('/profile/edit')} 
            variant="outline" 
            size="sm"
          >
            Edit Profile
          </Button>

          {/* Logout Button */}
          <Button onClick={handleLogout} variant="secondary" size="sm">
            Logout
          </Button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;